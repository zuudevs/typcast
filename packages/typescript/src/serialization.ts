/**
 * JSON serialization and deserialization of the document IR.
 *
 * The serializer writes the canonical form of the IR: UTF-8 JSON with
 * two-space indentation, a trailing newline, the field order of
 * `docs/specifications/document-ir.md`, and deterministic numbers. The
 * deserializer is driven by the `type` discriminator and rejects unknown
 * fields, missing required fields, and unsupported schema versions.
 */

export {
  documentFromJSON,
  documentFromJSONString,
  documentToJSON,
  documentToJSONString,
} from "./models/document.js";
