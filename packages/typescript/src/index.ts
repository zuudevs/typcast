/**
 * Typcast: the TypeScript SDK for generating Typst documents.
 *
 * The package exposes the immutable document model of the IR. The model
 * serializes to the language-neutral document IR and reads it back, and the
 * validation engine checks the semantic rules of a document. The builder, the
 * emitter, and the compiler adapter are not part of this release.
 */

export {
  CODE_EMPTY_CONTENT,
  CODE_INVALID_DATE,
  CODE_INVALID_ENUM,
  CODE_INVALID_HEADING_LEVEL,
  CODE_INVALID_LENGTH,
  CODE_INVALID_MODULE_ALIAS,
  CODE_INVALID_RAW_LIMIT,
  CODE_MALFORMED_JSON,
  CODE_MODULE_ALIAS_AND_ITEMS,
  CODE_NOT_SERIALIZABLE,
  CODE_RAW_TOO_LARGE,
  CODE_REQUIRED_FIELD,
  CODE_ROOT_SHAPE,
  CODE_STRING_TOO_LONG,
  CODE_TABLE_SHAPE,
  CODE_UNKNOWN_FIELD,
  CODE_UNSUPPORTED_VERSION,
  ConfigError,
  PHASE_API,
  PHASE_COMPILER,
  PHASE_CONFIG,
  PHASE_EMIT,
  PHASE_IO,
  PHASE_SERIALIZATION,
  PHASE_VALIDATION,
  SEVERITY_ERROR,
  SEVERITY_INFO,
  SEVERITY_WARNING,
  SerializationError,
  TypcastError,
  ValidationError,
} from "./diagnostics.js";
export type { Diagnostic, SourceLocation } from "./diagnostics.js";
export {
  Bold,
  Document,
  Heading,
  Image,
  Italic,
  Length,
  LineBreak,
  Link,
  ListBlock,
  Margin,
  Metadata,
  Module,
  Monospace,
  PAPER_VARIANTS,
  Page,
  PageBreak,
  Paragraph,
  RawBlock,
  RawSpan,
  Table,
  TableColumn,
  Text,
} from "./models/index.js";
export type {
  Alignment,
  Block,
  LengthUnit,
  Orientation,
  RawFormat,
  Span,
} from "./models/index.js";
export {
  DEFAULT_MAX_RAW_BYTES,
  resolveOptions,
  utf8Length,
  validateDocument,
} from "./validations/index.js";
export type {
  ResolvedOptions,
  TypcastOptions,
} from "./validations/index.js";
export { SCHEMA_VERSION, VERSION } from "./version.js";
