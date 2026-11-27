/** The immutable document model of Typcast. */

export {
  ALIGNMENTS,
  BlockBase,
  Heading,
  Image,
  ListBlock,
  PageBreak,
  Paragraph,
  RawBlock,
  Table,
  TableColumn,
  requireBlocks,
  toJSONBlockArray,
} from "./blocks.js";
export type { Alignment, Block } from "./blocks.js";
export {
  Document,
  documentFromJSON,
  documentFromJSONString,
  documentToJSON,
  documentToJSONString,
} from "./document.js";
export { Metadata } from "./metadata.js";
export { Module, requireModules } from "./module.js";
export {
  LENGTH_UNITS,
  Length,
  Margin,
  ORIENTATIONS,
  PAPER_VARIANTS,
  Page,
} from "./page.js";
export type { LengthUnit, Orientation } from "./page.js";
export {
  Bold,
  Italic,
  LineBreak,
  Link,
  Monospace,
  RAW_FORMATS,
  RawSpan,
  SpanBase,
  Text,
  requireSpans,
  toJSONArray,
} from "./spans.js";
export type { RawFormat, Span } from "./spans.js";
