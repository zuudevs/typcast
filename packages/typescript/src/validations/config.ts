/**
 * The configuration of the validation engine.
 *
 * The configuration holds the limits that the semantic rules use. ADR-0017
 * makes the raw size limit the only configurable limit, and the Python SDK
 * applies the same rule in `src/typcast/validations/config.py`.
 */

import {
  CODE_INVALID_RAW_LIMIT,
  safeText,
  safeValue,
  throwConfig,
} from "../diagnostics.js";

/** The configuration of the validation engine. */
export interface TypcastOptions {
  /**
   * The maximum number of bytes of a raw node.
   *
   * The value must be an integer that is not negative. The limit of the
   * current release is the only configurable limit; the compilation fields
   * arrive with the asset layer and the compiler adapter, because they belong
   * to the layers that read files and run the Typst compiler.
   */
  maxRawBytes?: number;
}

/**
 * The default maximum number of bytes of a raw node.
 *
 * The value is the one MiB of ADR-0017, written as the number of bytes.
 */
export const DEFAULT_MAX_RAW_BYTES = 1_048_576;

/** The configuration of the validation engine with every value resolved. */
export interface ResolvedOptions {
  /** The maximum number of bytes of a raw node. */
  readonly maxRawBytes: number;
}

/**
 * Returns the configuration with every value resolved and checked.
 *
 * An interface holds no constructor, so a value of the options is checked
 * when the options are read. The Python SDK checks the value of its
 * configuration when the configuration is built, and both SDKs report the
 * same diagnostic for the same value.
 */
export function resolveOptions(options?: TypcastOptions): ResolvedOptions {
  if (options === undefined || options.maxRawBytes === undefined) {
    return { maxRawBytes: DEFAULT_MAX_RAW_BYTES };
  }
  return { maxRawBytes: checkedLimit(options.maxRawBytes) };
}

/**
 * Returns the raw size limit after checking that it is a valid one.
 *
 * The limit is a number of bytes, so it must be an integer that the number
 * domain of the IR holds and that is not negative. The Python SDK applies
 * the same rules, so that both SDKs reject the same value with the same
 * diagnostic.
 */
function checkedLimit(value: number): number {
  if (typeof value !== "number" || !Number.isInteger(value)) {
    throwInvalidLimit(value, "must be an integer");
  }
  if (value < 0) {
    throwInvalidLimit(value, "must not be negative");
  }
  return value;
}

/** Raises the diagnostic of an invalid raw size limit. */
function throwInvalidLimit(value: number, rule: string): never {
  throwConfig(
    CODE_INVALID_RAW_LIMIT,
    `'/max_raw_bytes' ${rule}, got '${safeText(value)}'.`,
    "/max_raw_bytes",
    { value: safeValue(value) },
  );
}
