/**
 * The Typst emitter of the document IR.
 *
 * The module holds the emitter of the TypeScript SDK. The Python SDK applies
 * the same rules in `src/typcast/emitter/emitter.py`, so that both SDKs
 * produce the same bytes for the same document.
 */

export {
  EMITTER_HEADER,
  emitTypst,
  escapeString,
  escapeText,
  formatLength,
  normalizePath,
} from "./emitter.js";
