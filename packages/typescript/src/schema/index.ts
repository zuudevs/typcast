/**
 * The instance validation of the document IR against the JSON Schema contract.
 *
 * The package holds a validator for the subset of JSON Schema 2020-12 that the
 * schema contract of the document IR uses. The contract itself is embedded in
 * the SDK as a generated source file, so an instance is checked against the
 * same documents that the release publishes, and the SDK needs no file of the
 * repository at run time.
 */

export {
  ANNOTATION_KEYWORDS,
  ASSERTION_KEYWORDS,
  SCHEMA_ROOT,
  schemaKeywords,
  validateSchema,
} from "./validator.js";
export { SCHEMAS } from "./schemas.generated.js";
