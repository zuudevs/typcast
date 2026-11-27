/**
 * The semantic validation engine of the TypeScript SDK.
 *
 * The engine checks the rules of the document IR that span more than one
 * node: the shape of a table, the uniqueness of a module alias, and the size
 * of a raw node. It reports every problem it finds and throws no error for a
 * semantic problem.
 */

export {
  DEFAULT_MAX_RAW_BYTES,
  resolveOptions,
} from "./config.js";
export type { ResolvedOptions, TypcastOptions } from "./config.js";
export { validateDocument } from "./engine.js";
export { utf8Length } from "./encoding.js";
