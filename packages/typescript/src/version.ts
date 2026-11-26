/**
 * The schema version of the document IR.
 *
 * The version follows `docs/specifications/compatibility.md`: a reader
 * supports the same major version, a minor version less than or equal to its
 * own, and any patch version of the supported minor.
 */

import {
  CODE_UNSUPPORTED_VERSION,
  throwSerialization,
} from "./diagnostics.js";

export const SCHEMA_VERSION = "1.0.0";
export const SUPPORTED_SCHEMA_MAJOR = 1;
export const SUPPORTED_SCHEMA_MINOR = 0;

/**
 * The version of the TypeScript package.
 *
 * It matches the version of the package manifest, and the repository gate
 * checks that the two agree. It is not the version of the schema, which the
 * `SCHEMA_VERSION` export names.
 */
export const VERSION = "0.1.0";

const VERSION_PATTERN = /^(\d+)\.(\d+)\.(\d+)$/;

/** Returns the major, minor, and patch numbers of a version string. */
export function parseSchemaVersion(value: string): [number, number, number] {
  const match = VERSION_PATTERN.exec(value);
  if (match === null) {
    throwSerialization(
      CODE_UNSUPPORTED_VERSION,
      `'schemaVersion' must be a semantic version, got '${value}'.`,
      "/schemaVersion",
      { value },
    );
  }
  return [Number(match[1]), Number(match[2]), Number(match[3])];
}

/** Returns the version numbers of a supported version string. */
export function checkSchemaVersion(value: string): [number, number, number] {
  if (typeof value !== "string") {
    throwSerialization(
      CODE_UNSUPPORTED_VERSION,
      "'schemaVersion' must be a string.",
      "/schemaVersion",
    );
  }
  const [major, minor, patch] = parseSchemaVersion(value);
  if (major !== SUPPORTED_SCHEMA_MAJOR || minor > SUPPORTED_SCHEMA_MINOR) {
    throwSerialization(
      CODE_UNSUPPORTED_VERSION,
      `'schemaVersion' '${value}' is not supported; this SDK reads ` +
        `${SUPPORTED_SCHEMA_MAJOR}.${SUPPORTED_SCHEMA_MINOR}.x.`,
      "/schemaVersion",
      {
        value,
        supportedMajor: SUPPORTED_SCHEMA_MAJOR,
        supportedMinor: SUPPORTED_SCHEMA_MINOR,
      },
    );
  }
  return [major, minor, patch];
}
