/**
 * Minimal declarations of the Node.js APIs that the contract runner uses.
 *
 * The repository pins the TypeScript compiler but not the Node.js type
 * definitions, and the contract runner needs no other Node.js API. The
 * declarations keep the runner type-checked without a toolchain change.
 */

declare module "node:fs" {
  export function existsSync(path: string): boolean;
  export function readFileSync(path: string, encoding: "utf-8"): string;
  export function readdirSync(path: string): string[];
}

declare module "node:path" {
  export function dirname(path: string): string;
  export function join(...parts: string[]): string;
}

declare module "node:url" {
  export function fileURLToPath(url: string): string;
}

declare const process: {
  readonly env: Readonly<Record<string, string | undefined>>;
  cwd(): string;
  exit(code?: number): never;
};
