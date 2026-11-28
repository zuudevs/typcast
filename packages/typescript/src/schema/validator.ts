/**
 * The validation of an instance of the document IR against the JSON Schema
 * contract.
 *
 * The module holds a validator for the subset of JSON Schema 2020-12 that the
 * schema contract of the document IR uses. The contract itself is embedded in
 * the SDK as a generated source file, so an instance is checked against the
 * same documents that the release publishes, and the SDK needs no file of the
 * repository at run time.
 *
 * The validator is a layer of its own. The reader keeps its own error
 * contract, and the semantic engine keeps the rules that JSON Schema cannot
 * express. ADR 0027 records the decision.
 *
 * The Python SDK applies the same rules in `src/typcast/schema/validator.py`,
 * so that both SDKs report the same diagnostics for the same instance.
 */

import {
  CODE_SCHEMA_UNSUPPORTED_KEYWORD,
  CODE_SCHEMA_VIOLATION,
  safeText,
  safeValue,
  validationDiagnostic,
} from "../diagnostics.js";
import type { Diagnostic } from "../diagnostics.js";
import { SCHEMAS } from "./schemas.generated.js";

/** A schema document of the contract. */
type SchemaObject = Readonly<Record<string, unknown>>;

/** The schema of the document IR. The bundle names it at the root. */
export const SCHEMA_ROOT = "validator.schema.json";

/**
 * The keywords that carry no assertion. A schema may hold them, and the
 * validator ignores them.
 */
export const ANNOTATION_KEYWORDS: ReadonlySet<string> = new Set([
  "$comment",
  "$defs",
  "$id",
  "$schema",
  "default",
  "deprecated",
  "description",
  "examples",
  "readOnly",
  "title",
  "writeOnly",
]);

/**
 * The keywords that the validator implements. Every other keyword is a
 * violation of its own, so the validator never passes an instance that a rule
 * of the schema would reject.
 */
export const ASSERTION_KEYWORDS: ReadonlySet<string> = new Set([
  "$ref",
  "additionalProperties",
  "const",
  "enum",
  "exclusiveMinimum",
  "items",
  "maxLength",
  "maximum",
  "minItems",
  "minLength",
  "minimum",
  "not",
  "oneOf",
  "pattern",
  "properties",
  "required",
  "type",
  "unevaluatedProperties",
]);

/**
 * The number of the allowed values that a message lists. A catalog holds more
 * values than that, and a message that lists all of them is unreadable, so
 * the message names the number of the values and the details hold the list.
 */
const MAXIMUM_LISTED_VALUES = 8;

/** Raised when the schema contract itself is malformed. */
class SchemaError extends Error {}

/**
 * Returns the diagnostics of the schema contract for the value.
 *
 * The value is a JSON value. The function reports every rule that the value
 * breaks and throws no error, so that a caller can show all of the problems
 * at once.
 */
export function validateSchema(value: unknown): readonly Diagnostic[] {
  const unsupported = unsupportedKeywords(SCHEMAS);
  if (unsupported.length > 0) {
    return unsupported.map((entry) => unsupportedViolation(entry[0], entry[1]));
  }
  const evaluator = new Evaluator(SCHEMAS);
  const [diagnostics] = evaluator.evaluate(value, SCHEMAS[SCHEMA_ROOT], "", SCHEMA_ROOT);
  return diagnostics;
}

/**
 * Returns the keywords that the schema contract uses.
 *
 * The function walks every schema document of the contract, so a keyword that
 * the validator does not implement is visible before a document is validated.
 */
export function schemaKeywords(): readonly string[] {
  const found = new Set<string>();
  for (const document of Object.values(SCHEMAS)) {
    walk(document, found);
  }
  return [...found].sort();
}

/**
 * Returns the keywords that the validator does not implement.
 *
 * The result names the document that holds the keyword and the keyword
 * itself, so that a caller can find the place that needs a new rule.
 */
function unsupportedKeywords(
  documents: Readonly<Record<string, unknown>>,
): readonly (readonly [string, string])[] {
  const unsupported: (readonly [string, string])[] = [];
  for (const path of Object.keys(documents).sort()) {
    const found = new Set<string>();
    walk(documents[path], found);
    for (const keyword of [...found].sort()) {
      if (
        ANNOTATION_KEYWORDS.has(keyword) ||
        ASSERTION_KEYWORDS.has(keyword)
      ) {
        continue;
      }
      unsupported.push([path, keyword]);
    }
  }
  return unsupported;
}

/** Collects the keywords of a schema document and of its subschemas. */
function walk(schema: unknown, found: Set<string>): void {
  const object = asObject(schema);
  if (object === undefined) {
    return;
  }
  for (const [keyword, value] of Object.entries(object)) {
    found.add(keyword);
    if ((keyword === "properties" || keyword === "$defs") && isObject(value)) {
      for (const subschema of Object.values(value)) {
        walk(subschema, found);
      }
    } else if (
      (keyword === "items" ||
        keyword === "additionalProperties" ||
        keyword === "unevaluatedProperties" ||
        keyword === "not") &&
      isObject(value)
    ) {
      walk(value, found);
    } else if (
      (keyword === "oneOf" || keyword === "anyOf" || keyword === "allOf") &&
      Array.isArray(value)
    ) {
      for (const subschema of value) {
        walk(subschema, found);
      }
    }
  }
}

/** Applies the keywords of a schema to an instance. */
class Evaluator {
  private readonly schemas: Readonly<Record<string, unknown>>;

  constructor(schemas: Readonly<Record<string, unknown>>) {
    this.schemas = schemas;
  }

  /**
   * Returns the diagnostics of the value and the properties it evaluates.
   *
   * The properties are the names that the schema evaluates, and the keyword
   * `unevaluatedProperties` needs them.
   */
  evaluate(
    value: unknown,
    schema: unknown,
    path: string,
    base: string,
  ): readonly [readonly Diagnostic[], ReadonlySet<string>] {
    const diagnostics: Diagnostic[] = [];
    const evaluated = new Set<string>();
    const object = asObject(schema);
    if (object === undefined) {
      throw new SchemaError(`the schema of '${location(path)}' is not an object`);
    }

    if (object["$ref"] !== undefined) {
      const [target, targetBase] = this.resolve(object["$ref"], base);
      const [subDiagnostics, subEvaluated] = this.evaluate(
        value,
        target,
        path,
        targetBase,
      );
      diagnostics.push(...subDiagnostics);
      for (const name of subEvaluated) {
        evaluated.add(name);
      }
    }

    if (object["type"] !== undefined && !matchesType(value, object["type"])) {
      diagnostics.push(typeViolation(path, object["type"], value));
    }

    if (object["const"] !== undefined && !equal(value, object["const"])) {
      diagnostics.push(constViolation(path, object["const"], value));
    }

    if (object["enum"] !== undefined && !enumHolds(value, object["enum"])) {
      diagnostics.push(enumViolation(path, object["enum"], value));
    }

    const valueObject = asObject(value);
    if (valueObject !== undefined) {
      diagnostics.push(
        ...this.evaluateObject(valueObject, object, path, base, evaluated),
      );
    }

    if (Array.isArray(value)) {
      diagnostics.push(...this.evaluateArray(value, object, path, base));
    }

    if (typeof value === "string") {
      diagnostics.push(...this.evaluateText(value, object, path));
    }

    if (isNumber(value)) {
      diagnostics.push(...this.evaluateNumber(value, object, path));
    }

    if (object["not"] !== undefined) {
      const [subDiagnostics] = this.evaluate(value, object["not"], path, base);
      if (subDiagnostics.length === 0) {
        diagnostics.push(notViolation(path));
      }
    }

    const [unionDiagnostics, unionEvaluated] = this.evaluateUnion(
      value,
      object,
      path,
      base,
    );
    diagnostics.push(...unionDiagnostics);
    for (const name of unionEvaluated) {
      evaluated.add(name);
    }

    if (valueObject !== undefined && object["unevaluatedProperties"] !== undefined) {
      diagnostics.push(
        ...this.evaluateUnevaluated(valueObject, object, path, base, evaluated),
      );
    }

    return [diagnostics, evaluated];
  }

  /**
   * Applies the object keywords of the schema.
   *
   * The set of the evaluated properties holds the properties that the keywords
   * of the schema and the schemas that it references evaluate, because the
   * keyword `unevaluatedProperties` rejects every property that none of them
   * evaluates.
   */
  private evaluateObject(
    value: Readonly<Record<string, unknown>>,
    schema: SchemaObject,
    path: string,
    base: string,
    evaluated: Set<string>,
  ): readonly Diagnostic[] {
    const diagnostics: Diagnostic[] = [];
    const properties = asObject(schema["properties"] ?? {});
    if (properties === undefined) {
      throw new SchemaError(
        `the properties of '${location(path)}' are not an object`,
      );
    }

    for (const [name, subschema] of Object.entries(properties)) {
      if (Object.hasOwn(value, name)) {
        const [subDiagnostics] = this.evaluate(
          value[name],
          subschema,
          `${path}/${escapeToken(name)}`,
          base,
        );
        diagnostics.push(...subDiagnostics);
        evaluated.add(name);
      }
    }

    const required = schema["required"] ?? [];
    if (!Array.isArray(required)) {
      throw new SchemaError(
        `the required list of '${location(path)}' is not an array`,
      );
    }
    for (const name of required) {
      if (typeof name === "string" && !Object.hasOwn(value, name)) {
        diagnostics.push(requiredViolation(path, name));
      }
    }

    if (schema["additionalProperties"] !== undefined) {
      const extra = schema["additionalProperties"];
      for (const name of Object.keys(value).sort()) {
        if (Object.hasOwn(properties, name)) {
          continue;
        }
        if (extra === false) {
          diagnostics.push(unknownViolation(path, name));
        } else {
          const [subDiagnostics] = this.evaluate(
            value[name],
            extra,
            `${path}/${escapeToken(name)}`,
            base,
          );
          diagnostics.push(...subDiagnostics);
        }
        evaluated.add(name);
      }
    }

    return diagnostics;
  }

  /**
   * Applies the keyword `unevaluatedProperties` of the schema.
   *
   * The keyword rejects every property that no keyword of the schema and no
   * schema that it references evaluates. The check runs after every other
   * keyword, because the union keywords evaluate properties too.
   */
  private evaluateUnevaluated(
    value: Readonly<Record<string, unknown>>,
    schema: SchemaObject,
    path: string,
    base: string,
    evaluated: Set<string>,
  ): readonly Diagnostic[] {
    const diagnostics: Diagnostic[] = [];
    const extra = schema["unevaluatedProperties"];
    for (const name of Object.keys(value).sort()) {
      if (evaluated.has(name)) {
        continue;
      }
      if (extra === false) {
        diagnostics.push(unevaluatedViolation(path, name));
      } else {
        const [subDiagnostics] = this.evaluate(
          value[name],
          extra,
          `${path}/${escapeToken(name)}`,
          base,
        );
        diagnostics.push(...subDiagnostics);
      }
      evaluated.add(name);
    }
    return diagnostics;
  }

  /** Applies the array keywords of the schema. */
  private evaluateArray(
    value: readonly unknown[],
    schema: SchemaObject,
    path: string,
    base: string,
  ): readonly Diagnostic[] {
    const diagnostics: Diagnostic[] = [];
    const minimum = schema["minItems"];
    if (typeof minimum === "number" && value.length < minimum) {
      diagnostics.push(minItemsViolation(path, minimum));
    }
    if (schema["items"] !== undefined) {
      value.forEach((item, index) => {
        const [subDiagnostics] = this.evaluate(
          item,
          schema["items"],
          `${path}/${index}`,
          base,
        );
        diagnostics.push(...subDiagnostics);
      });
    }
    return diagnostics;
  }

  /** Applies the string keywords of the schema. */
  private evaluateText(
    value: string,
    schema: SchemaObject,
    path: string,
  ): readonly Diagnostic[] {
    const diagnostics: Diagnostic[] = [];
    const minimum = schema["minLength"];
    if (typeof minimum === "number" && codePointLength(value) < minimum) {
      diagnostics.push(minLengthViolation(path, minimum));
    }
    const maximum = schema["maxLength"];
    if (typeof maximum === "number" && codePointLength(value) > maximum) {
      diagnostics.push(maxLengthViolation(path, maximum));
    }
    const pattern = schema["pattern"];
    if (typeof pattern === "string" && !matchesPattern(pattern, value)) {
      diagnostics.push(patternViolation(path, pattern));
    }
    return diagnostics;
  }

  /** Applies the number keywords of the schema. */
  private evaluateNumber(
    value: number,
    schema: SchemaObject,
    path: string,
  ): readonly Diagnostic[] {
    const diagnostics: Diagnostic[] = [];
    const minimum = schema["minimum"];
    if (typeof minimum === "number" && value < minimum) {
      diagnostics.push(minimumViolation(path, minimum, value));
    }
    const maximum = schema["maximum"];
    if (typeof maximum === "number" && value > maximum) {
      diagnostics.push(maximumViolation(path, maximum, value));
    }
    const exclusive = schema["exclusiveMinimum"];
    if (typeof exclusive === "number" && value <= exclusive) {
      diagnostics.push(exclusiveMinimumViolation(path, exclusive, value));
    }
    return diagnostics;
  }

  /**
   * Applies the union keyword of the schema.
   *
   * The union of the contract uses a `type` discriminator with a `const` value
   * in every branch. When the value names a discriminator that one branch
   * declares, the violations of that branch are the useful ones, so they are
   * reported instead of the violation of the union.
   */
  private evaluateUnion(
    value: unknown,
    schema: SchemaObject,
    path: string,
    base: string,
  ): readonly [readonly Diagnostic[], ReadonlySet<string>] {
    const diagnostics: Diagnostic[] = [];
    const evaluated = new Set<string>();
    const branches = schema["oneOf"];
    if (branches === undefined) {
      return [diagnostics, evaluated];
    }
    if (!Array.isArray(branches)) {
      throw new SchemaError(
        `the branches of '${location(path)}' are not an array`,
      );
    }
    const results: (readonly [
      readonly Diagnostic[],
      ReadonlySet<string>,
    ])[] = [];
    let matched = 0;
    for (const branch of branches) {
      const [subDiagnostics, subEvaluated] = this.evaluate(
        value,
        branch,
        path,
        base,
      );
      results.push([subDiagnostics, subEvaluated]);
      if (subDiagnostics.length === 0) {
        matched += 1;
      }
    }
    if (matched === 1) {
      for (const [subDiagnostics, subEvaluated] of results) {
        if (subDiagnostics.length === 0) {
          for (const name of subEvaluated) {
            evaluated.add(name);
          }
        }
      }
      return [diagnostics, evaluated];
    }
    const index = matchingBranch(value, branches);
    if (index !== undefined) {
      diagnostics.push(...results[index]![0]);
      for (const name of results[index]![1]) {
        evaluated.add(name);
      }
      return [diagnostics, evaluated];
    }
    diagnostics.push(unionViolation(path, matched, branches));
    return [diagnostics, evaluated];
  }

  /**
   * Resolves a reference against the document that holds it.
   *
   * A reference that starts with `#` names a location inside the document
   * itself. Every other reference names a file of the bundle, relative to the
   * directory of the document that holds it, and it may carry a pointer to a
   * location inside that file.
   */
  private resolve(
    reference: unknown,
    base: string,
  ): readonly [unknown, string] {
    if (typeof reference !== "string" || reference.length === 0) {
      throw new SchemaError(`the reference of '${base}' must be a non-empty text`);
    }
    const hash = reference.indexOf("#");
    const filePart = hash === -1 ? reference : reference.slice(0, hash);
    const pointer = hash === -1 ? "" : reference.slice(hash + 1);
    let target: unknown;
    let targetBase: string;
    if (filePart === "") {
      target = this.schemas[base];
      targetBase = base;
    } else {
      targetBase = normalizePath(joinPath(directoryOf(base), filePart));
      target = this.schemas[targetBase];
    }
    if (target === undefined) {
      throw new SchemaError(
        `the bundle holds no schema document at '${targetBase}'`,
      );
    }
    if (pointer !== "") {
      target = resolvePointer(target, pointer, reference);
    }
    return [target, targetBase];
  }
}

// ---------------------------------------------------------------------------
// The JSON value helpers
// ---------------------------------------------------------------------------

/** Returns the value as a JSON object, or undefined when it is none. */
function asObject(value: unknown): Record<string, unknown> | undefined {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    return undefined;
  }
  return value as Record<string, unknown>;
}

/** Returns whether the value is a JSON object. */
function isObject(value: unknown): value is Record<string, unknown> {
  return asObject(value) !== undefined;
}

/** Returns whether the value is a JSON number. */
function isNumber(value: unknown): value is number {
  return typeof value === "number";
}

/** Returns whether the value matches the type of the schema. */
function matchesType(value: unknown, expected: unknown): boolean {
  const names = Array.isArray(expected) ? expected : [expected];
  for (const name of names) {
    if (name === "object" && asObject(value) !== undefined) {
      return true;
    }
    if (name === "array" && Array.isArray(value)) {
      return true;
    }
    if (name === "string" && typeof value === "string") {
      return true;
    }
    if (name === "boolean" && typeof value === "boolean") {
      return true;
    }
    if (name === "null" && value === null) {
      return true;
    }
    if (name === "number" && isNumber(value)) {
      return true;
    }
    if (name === "integer" && isNumber(value) && Number.isInteger(value)) {
      return true;
    }
  }
  return false;
}

/** Returns whether the value is a member of the enumeration of the schema. */
function enumHolds(value: unknown, allowed: unknown): boolean {
  if (!Array.isArray(allowed)) {
    return false;
  }
  return allowed.some((candidate) => equal(value, candidate));
}

/** Returns whether two JSON values are equal. */
function equal(left: unknown, right: unknown): boolean {
  if (typeof left === "boolean" || typeof right === "boolean") {
    return left === right;
  }
  if (isNumber(left) && isNumber(right)) {
    return left === right;
  }
  if (typeof left === "string" && typeof right === "string") {
    return left === right;
  }
  if (left === null || right === null) {
    return left === null && right === null;
  }
  if (Array.isArray(left) && Array.isArray(right)) {
    return (
      left.length === right.length &&
      left.every((item, index) => equal(item, right[index]))
    );
  }
  const leftObject = asObject(left);
  const rightObject = asObject(right);
  if (leftObject !== undefined && rightObject !== undefined) {
    const leftKeys = Object.keys(leftObject);
    const rightKeys = Object.keys(rightObject);
    return (
      leftKeys.length === rightKeys.length &&
      leftKeys.every((name) => Object.hasOwn(rightObject, name)) &&
      leftKeys.every((name) => equal(leftObject[name], rightObject[name]))
    );
  }
  return false;
}

/** Escapes a token of a JSON Pointer as RFC 6901 defines it. */
function escapeToken(token: string): string {
  return token.replace(/~/gu, "~0").replace(/\//gu, "~1");
}

/** Returns the path of a location as a diagnostic names it. */
function location(path: string): string {
  return path === "" ? "/" : path;
}

/** Returns the number of the code points of the text. */
function codePointLength(text: string): number {
  return [...text].length;
}

/**
 * Returns the branch whose discriminator matches the value.
 *
 * The union of the contract names a `type` discriminator with a `const` value
 * in every branch. The branch whose discriminator matches the value is the one
 * that describes the value, so its violations are the useful ones.
 */
function matchingBranch(
  value: unknown,
  branches: readonly unknown[],
): number | undefined {
  const object = asObject(value);
  if (object === undefined) {
    return undefined;
  }
  const discriminator = object["type"];
  if (typeof discriminator !== "string") {
    return undefined;
  }
  const matches: number[] = [];
  branches.forEach((branch, index) => {
    const branchObject = asObject(branch);
    if (branchObject === undefined) {
      return;
    }
    const properties = asObject(branchObject["properties"]);
    if (properties === undefined) {
      return;
    }
    const typeSchema = asObject(properties["type"]);
    if (typeSchema === undefined) {
      return;
    }
    if (typeSchema["const"] === discriminator) {
      matches.push(index);
    }
  });
  return matches.length === 1 ? matches[0] : undefined;
}

/** Returns the discriminator values of the branches of a union. */
function discriminators(branches: readonly unknown[]): readonly string[] {
  const values: string[] = [];
  for (const branch of branches) {
    const branchObject = asObject(branch);
    if (branchObject === undefined) {
      continue;
    }
    const properties = asObject(branchObject["properties"]);
    if (properties === undefined) {
      continue;
    }
    const typeSchema = asObject(properties["type"]);
    if (typeSchema === undefined) {
      continue;
    }
    const constant = typeSchema["const"];
    if (typeof constant === "string") {
      values.push(constant);
    }
  }
  return values;
}

/** Returns the directory of a path of the bundle. */
function directoryOf(path: string): string {
  const index = path.lastIndexOf("/");
  return index === -1 ? "" : path.slice(0, index);
}

/** Joins two paths of the bundle. */
function joinPath(directory: string, name: string): string {
  if (directory === "") {
    return name;
  }
  return directory.endsWith("/") ? `${directory}${name}` : `${directory}/${name}`;
}

/** Normalizes a path of the bundle. */
function normalizePath(path: string): string {
  const segments: string[] = [];
  for (const segment of path.split("/")) {
    if (segment === "" || segment === ".") {
      continue;
    }
    if (segment === "..") {
      segments.pop();
      continue;
    }
    segments.push(segment);
  }
  return segments.join("/");
}

/** Returns the value that a JSON Pointer names in a document. */
function resolvePointer(
  document: unknown,
  pointer: string,
  reference: string,
): unknown {
  if (!pointer.startsWith("/")) {
    throw new SchemaError(
      `the reference '${reference}' carries a pointer that is not a JSON Pointer`,
    );
  }
  let value = document;
  for (const token of pointer.split("/").slice(1)) {
    const name = token.replace(/~1/gu, "/").replace(/~0/gu, "~");
    const object = asObject(value);
    if (object !== undefined) {
      if (!Object.hasOwn(object, name)) {
        throw new SchemaError(
          `the reference '${reference}' names no value of the document`,
        );
      }
      value = object[name];
      continue;
    }
    if (Array.isArray(value)) {
      const index = Number(name);
      if (!Number.isInteger(index) || index < 0 || index >= value.length) {
        throw new SchemaError(
          `the reference '${reference}' names no value of the document`,
        );
      }
      value = value[index];
      continue;
    }
    throw new SchemaError(
      `the reference '${reference}' names no value of the document`,
    );
  }
  return value;
}

// ---------------------------------------------------------------------------
// The patterns of the schema
// ---------------------------------------------------------------------------

/**
 * Returns whether the text matches the pattern of the schema.
 *
 * The pattern of a schema is a pattern of ECMAScript, and it matches anywhere
 * in the text. The engine of ECMAScript differs from the engine of Python in
 * the meaning of the anchor `$` and in the meaning of the character classes
 * such as `\d`, so the Python SDK translates the pattern before it compiles
 * it.
 */
function matchesPattern(pattern: string, value: string): boolean {
  let compiled: RegExp;
  try {
    compiled = new RegExp(pattern);
  } catch (error) {
    throw new SchemaError(
      `the pattern '${pattern}' is not a valid regular expression: ${String(error)}`,
    );
  }
  return compiled.test(value);
}

// ---------------------------------------------------------------------------
// The violations
// ---------------------------------------------------------------------------

/** Builds the diagnostic of a value of the wrong type. */
function typeViolation(
  path: string,
  expected: unknown,
  value: unknown,
): Diagnostic {
  const names = Array.isArray(expected) ? expected : [expected];
  const name = names.map((item) => String(item)).join(", ");
  return validationDiagnostic(
    CODE_SCHEMA_VIOLATION,
    `'${location(path)}' must be a JSON ${name}.`,
    path === "" ? null : path,
    { keyword: "type", expected: name, value: safeValue(value) },
  );
}

/** Builds the diagnostic of a value that is not a constant. */
function constViolation(
  path: string,
  expected: unknown,
  value: unknown,
): Diagnostic {
  return validationDiagnostic(
    CODE_SCHEMA_VIOLATION,
    `'${location(path)}' must be '${safeText(expected)}'.`,
    path === "" ? null : path,
    {
      keyword: "const",
      expected: safeValue(expected),
      value: safeValue(value),
    },
  );
}

/** Builds the diagnostic of a value that is not a member of an enumeration. */
function enumViolation(
  path: string,
  allowed: unknown,
  value: unknown,
): Diagnostic {
  const names = Array.isArray(allowed) ? allowed.map((item) => String(item)) : [];
  const message =
    names.length > MAXIMUM_LISTED_VALUES
      ? `'${location(path)}' must be one of the ${names.length} allowed values, got '${safeText(value)}'.`
      : `'${location(path)}' must be one of ${names.join(", ")}, got '${safeText(value)}'.`;
  return validationDiagnostic(
    CODE_SCHEMA_VIOLATION,
    message,
    path === "" ? null : path,
    {
      keyword: "enum",
      allowed: Array.isArray(allowed) ? [...allowed] : [],
      value: safeValue(value),
    },
  );
}

/** Builds the diagnostic of a missing field. */
function requiredViolation(path: string, name: string): Diagnostic {
  const target = `${path}/${escapeToken(name)}`;
  return validationDiagnostic(
    CODE_SCHEMA_VIOLATION,
    `'${target}' is required.`,
    target,
    { keyword: "required", field: name },
  );
}

/** Builds the diagnostic of an unknown field. */
function unknownViolation(path: string, name: string): Diagnostic {
  const target = `${path}/${escapeToken(name)}`;
  return validationDiagnostic(
    CODE_SCHEMA_VIOLATION,
    `'${target}' is not a known field.`,
    target,
    { keyword: "additionalProperties", field: name },
  );
}

/** Builds the diagnostic of a field that no keyword evaluates. */
function unevaluatedViolation(path: string, name: string): Diagnostic {
  const target = `${path}/${escapeToken(name)}`;
  return validationDiagnostic(
    CODE_SCHEMA_VIOLATION,
    `'${target}' is not a known field.`,
    target,
    { keyword: "unevaluatedProperties", field: name },
  );
}

/** Builds the diagnostic of an array that is too short. */
function minItemsViolation(path: string, limit: number): Diagnostic {
  const message =
    limit === 1
      ? `'${location(path)}' must not be empty.`
      : `'${location(path)}' must hold at least ${limit} items.`;
  return validationDiagnostic(
    CODE_SCHEMA_VIOLATION,
    message,
    path === "" ? null : path,
    { keyword: "minItems", minItems: limit },
  );
}

/** Builds the diagnostic of a text that is too short. */
function minLengthViolation(path: string, limit: number): Diagnostic {
  const message =
    limit === 1
      ? `'${location(path)}' must not be empty.`
      : `'${location(path)}' must hold at least ${limit} code points.`;
  return validationDiagnostic(
    CODE_SCHEMA_VIOLATION,
    message,
    path === "" ? null : path,
    { keyword: "minLength", minLength: limit },
  );
}

/** Builds the diagnostic of a text that is too long. */
function maxLengthViolation(path: string, limit: number): Diagnostic {
  return validationDiagnostic(
    CODE_SCHEMA_VIOLATION,
    `'${location(path)}' must not hold more than ${limit} code points.`,
    path === "" ? null : path,
    { keyword: "maxLength", maxLength: limit },
  );
}

/** Builds the diagnostic of a text that does not match a pattern. */
function patternViolation(path: string, pattern: string): Diagnostic {
  return validationDiagnostic(
    CODE_SCHEMA_VIOLATION,
    `'${location(path)}' must match the pattern ${pattern}.`,
    path === "" ? null : path,
    { keyword: "pattern", pattern },
  );
}

/** Builds the diagnostic of a number below the minimum. */
function minimumViolation(
  path: string,
  limit: number,
  value: number,
): Diagnostic {
  return validationDiagnostic(
    CODE_SCHEMA_VIOLATION,
    `'${location(path)}' must not be less than ${limit}.`,
    path === "" ? null : path,
    { keyword: "minimum", minimum: limit, value: safeValue(value) },
  );
}

/** Builds the diagnostic of a number above the maximum. */
function maximumViolation(
  path: string,
  limit: number,
  value: number,
): Diagnostic {
  return validationDiagnostic(
    CODE_SCHEMA_VIOLATION,
    `'${location(path)}' must not be greater than ${limit}.`,
    path === "" ? null : path,
    { keyword: "maximum", maximum: limit, value: safeValue(value) },
  );
}

/** Builds the diagnostic of a number at the exclusive minimum. */
function exclusiveMinimumViolation(
  path: string,
  limit: number,
  value: number,
): Diagnostic {
  return validationDiagnostic(
    CODE_SCHEMA_VIOLATION,
    `'${location(path)}' must be greater than ${limit}.`,
    path === "" ? null : path,
    {
      keyword: "exclusiveMinimum",
      exclusiveMinimum: limit,
      value: safeValue(value),
    },
  );
}

/** Builds the diagnostic of a value that matches a forbidden schema. */
function notViolation(path: string): Diagnostic {
  return validationDiagnostic(
    CODE_SCHEMA_VIOLATION,
    `'${location(path)}' must not match the schema.`,
    path === "" ? null : path,
    { keyword: "not" },
  );
}

/** Builds the diagnostic of a value that matches no alternative. */
function unionViolation(
  path: string,
  matched: number,
  branches: readonly unknown[],
): Diagnostic {
  const message =
    matched === 0
      ? `'${location(path)}' must match one alternative of the schema, but matches none.`
      : `'${location(path)}' must match one alternative of the schema, but matches ${matched}.`;
  const details: Record<string, unknown> = { keyword: "oneOf", matched };
  const allowed = discriminators(branches);
  if (allowed.length > 0) {
    details["allowed"] = allowed;
  }
  return validationDiagnostic(
    CODE_SCHEMA_VIOLATION,
    message,
    path === "" ? null : path,
    details,
  );
}

/** Builds the diagnostic of a keyword that the validator does not implement. */
function unsupportedViolation(document: string, keyword: string): Diagnostic {
  return validationDiagnostic(
    CODE_SCHEMA_UNSUPPORTED_KEYWORD,
    `The schema '${document}' uses the keyword '${keyword}', which the validator does not implement.`,
    null,
    { keyword, schema: document },
  );
}
