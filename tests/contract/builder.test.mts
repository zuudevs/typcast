/**
 * Cross-language contract checks for the fluent builder.
 *
 * The shared fixtures under `tests/fixtures/builder/` are the single source of
 * truth of the contract. The manifest names the scenarios and the operations
 * of the builder, and every scenario names the canonical JSON that the
 * builder must produce. This runner reads the manifest, builds every scenario
 * with the TypeScript SDK, and checks that the canonical JSON of the document
 * matches the fixture byte for byte.
 *
 * The Python runner `tests/contract/test_builder.py` reads the same manifest
 * and the same fixtures, so a drift in either SDK fails one of the two
 * contract targets.
 */

import { existsSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import {
  Document,
  DocumentBuilder,
  Length,
  bold,
  column,
  italic,
  lineBreak,
  link,
  monospace,
  rawInline,
  text,
} from "../../packages/typescript/lib/src/index.js";
import type {
  Alignment,
  Content,
  Orientation,
  RawFormat,
} from "../../packages/typescript/lib/src/index.js";

const MANIFEST_NAME = "manifest.json";

interface Operation {
  readonly op: string;
  readonly [key: string]: unknown;
}

interface Scenario {
  readonly name: string;
  readonly file: string;
  readonly operations: readonly Operation[];
}

interface Manifest {
  readonly scenarios: readonly Scenario[];
}

function hasManifest(directory: string): boolean {
  try {
    readFileSync(join(directory, MANIFEST_NAME), "utf-8");
    return true;
  } catch {
    return false;
  }
}

function findFixtureRoot(): string {
  const candidates: string[] = [];
  const runfiles = process.env["RUNFILES_DIR"];
  const workspace = process.env["TEST_WORKSPACE"] ?? "_main";
  if (runfiles !== undefined) {
    candidates.push(join(runfiles, workspace, "tests", "fixtures", "builder"));
    candidates.push(join(runfiles, "tests", "fixtures", "builder"));
  }
  let current = dirname(fileURLToPath(import.meta.url));
  for (;;) {
    candidates.push(join(current, "tests", "fixtures", "builder"));
    const parent = dirname(current);
    if (parent === current) {
      break;
    }
    current = parent;
  }
  candidates.push(join(process.cwd(), "tests", "fixtures", "builder"));
  for (const candidate of candidates) {
    if (hasManifest(candidate)) {
      return candidate;
    }
  }
  throw new Error("builder fixtures not found; run the target through Bazel");
}

function loadManifest(root: string): Manifest {
  const text = readFileSync(join(root, MANIFEST_NAME), "utf-8");
  const value: unknown = JSON.parse(text);
  if (typeof value !== "object" || value === null) {
    throw new Error("the fixture manifest must be a JSON object");
  }
  const record = value as Record<string, unknown>;
  return { scenarios: record["scenarios"] as readonly Scenario[] };
}

/** Returns the content value of one item of a content collection. */
function spanOf(item: unknown): Content {
  if (typeof item === "string") {
    return item;
  }
  const record = item as Record<string, unknown>;
  const kind = record["span"];
  if (kind === "text") {
    return text(record["value"] as string);
  }
  if (kind === "bold") {
    return bold(...contentOf(record["content"] as readonly unknown[]));
  }
  if (kind === "italic") {
    return italic(...contentOf(record["content"] as readonly unknown[]));
  }
  if (kind === "monospace") {
    return monospace(...contentOf(record["content"] as readonly unknown[]));
  }
  if (kind === "link") {
    return link(
      record["href"] as string,
      ...contentOf(record["content"] as readonly unknown[]),
    );
  }
  if (kind === "line_break") {
    return lineBreak();
  }
  if (kind === "raw_inline") {
    return rawInline(
      record["value"] as string,
      record["format"] as RawFormat,
    );
  }
  throw new Error(`unknown span helper: ${String(kind)}`);
}

/** Returns the content values of a content collection. */
function contentOf(items: readonly unknown[]): readonly Content[] {
  return items.map((item) => spanOf(item));
}

/** Builds the document of a scenario with the TypeScript builder. */
function buildScenario(operations: readonly Operation[]): Document {
  const builder = new DocumentBuilder();
  for (const operation of operations) {
    switch (operation.op) {
      case "title": {
        builder.title(operation["value"] as string);
        break;
      }
      case "author": {
        builder.author(operation["value"] as string);
        break;
      }
      case "date": {
        builder.date(operation["value"] as string);
        break;
      }
      case "page": {
        const margin = operation["margin"] as
          | { readonly value: number; readonly unit: string }
          | undefined;
        builder.page({
          paper: (operation["paper"] as string | undefined) ?? "a4",
          orientation:
            (operation["orientation"] as Orientation | undefined) ?? "portrait",
          ...(margin === undefined
            ? {}
            : { margin: new Length(margin.value, margin.unit as "cm") }),
        });
        break;
      }
      case "heading": {
        builder.heading(
          operation["level"] as number,
          ...contentOf(operation["content"] as readonly unknown[]),
        );
        break;
      }
      case "paragraph": {
        builder.paragraph(
          ...contentOf(operation["content"] as readonly unknown[]),
        );
        break;
      }
      case "bullet_list": {
        builder.bulletList(
          (operation["items"] as readonly unknown[][]).map((item) =>
            contentOf(item),
          ),
        );
        break;
      }
      case "numbered_list": {
        builder.numberedList(
          (operation["items"] as readonly unknown[][]).map((item) =>
            contentOf(item),
          ),
        );
        break;
      }
      case "table": {
        const columns = (
          operation["columns"] as readonly {
            readonly header: readonly unknown[];
            readonly align?: string;
          }[]
        ).map(
          (entry) =>
            column(
              contentOf(entry.header),
              (entry.align ?? "left") as Alignment,
            ),
        );
        const rows = (operation["rows"] as readonly unknown[][][]).map((row) =>
          row.map((cell) => contentOf(cell)),
        );
        builder.table({ columns, rows });
        break;
      }
      case "image": {
        const caption = operation["caption"] as readonly unknown[] | undefined;
        builder.image(
          operation["path"] as string,
          caption === undefined
            ? { alt: operation["alt"] as string }
            : {
                alt: operation["alt"] as string,
                caption: contentOf(caption),
              },
        );
        break;
      }
      case "page_break": {
        builder.pageBreak();
        break;
      }
      case "raw": {
        builder.raw(operation["value"] as string, {
          format: (operation["format"] as RawFormat | undefined) ?? "markup",
        });
        break;
      }
      case "module": {
        const alias = operation["alias"] as string | undefined;
        const items = operation["items"] as readonly string[] | undefined;
        builder.module(operation["path"] as string, {
          ...(alias === undefined ? {} : { alias }),
          ...(items === undefined ? {} : { items }),
        });
        break;
      }
      default: {
        throw new Error(`unknown builder operation: ${operation.op}`);
      }
    }
  }
  return builder.build();
}

const failures: string[] = [];

function check(condition: boolean, message: string): void {
  if (!condition) {
    failures.push(message);
  }
}

function main(): void {
  const root = findFixtureRoot();
  const manifest = loadManifest(root);

  const listed = new Set<string>();
  for (const scenario of manifest.scenarios) {
    listed.add(scenario.file);
    if (!existsSync(join(root, scenario.file))) {
      failures.push(
        `${scenario.file}: the manifest names a file that does not exist`,
      );
    }
  }

  for (const scenario of manifest.scenarios) {
    const expected = readFileSync(join(root, scenario.file), "utf-8");
    let document: Document;
    try {
      document = buildScenario(scenario.operations);
    } catch (error) {
      failures.push(
        `${scenario.name}: the scenario must build, but it failed with ${String(error)}`,
      );
      continue;
    }
    check(
      document.toJSONString() === expected,
      `${scenario.name}: the builder must produce the canonical JSON of the fixture`,
    );
    const again = Document.fromJSONString(document.toJSONString());
    check(
      JSON.stringify(again.toJSON()) === JSON.stringify(document.toJSON()),
      `${scenario.name}: the document must round trip through the reader`,
    );
  }

  if (failures.length > 0) {
    for (const failure of failures) {
      console.error(`ERROR ${failure}`);
    }
    console.error(`failures: ${failures.length}`);
    process.exit(1);
    return;
  }
  console.log(`scenarios: ${manifest.scenarios.length}`);
  console.log("failures: 0");
}

main();
