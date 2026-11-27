/** The page description of the document IR. */

import {
  CODE_INVALID_LENGTH,
  CODE_REQUIRED_FIELD,
  safeText,
  safeValue,
  throwValidation,
} from "../diagnostics.js";
import { requireEnum, requireInstance, requireString } from "./base.js";

/** The units of a length. */
export const LENGTH_UNITS = ["pt", "mm", "cm", "in", "em"] as const;

/** The unit of a length. */
export type LengthUnit = (typeof LENGTH_UNITS)[number];

/** The orientations of a page. */
export const ORIENTATIONS = ["portrait", "landscape"] as const;

/** The orientation of a page. */
export type Orientation = (typeof ORIENTATIONS)[number];

/** A numeric length with a unit. */
export class Length {
  readonly value: number;
  readonly unit: LengthUnit;

  constructor(value: number, unit: LengthUnit) {
    if (typeof value !== "number") {
      throwValidation(
        CODE_REQUIRED_FIELD,
        "'/value' must be a number.",
        "/value",
      );
    }
    if (!Number.isFinite(value)) {
      throwValidation(
        CODE_INVALID_LENGTH,
        "'/value' must be a finite number.",
        "/value",
        { value: String(value) },
      );
    }
    if (value < 0) {
      throwValidation(
        CODE_INVALID_LENGTH,
        `'/value' must not be negative, got ${value}.`,
        "/value",
        { value },
      );
    }
    if (!LENGTH_UNITS.includes(unit)) {
      throwValidation(
        CODE_INVALID_LENGTH,
        `'/unit' must be one of ${LENGTH_UNITS.join(", ")}, got '${safeText(unit)}'.`,
        "/unit",
        // The details of a diagnostic must be JSON-serializable, so a value of
        // an unknown type is represented by its type name.
        { allowed: [...LENGTH_UNITS], value: safeValue(unit) },
      );
    }
    this.value = value;
    this.unit = unit;
    Object.freeze(this);
  }

  toJSON(): Record<string, unknown> {
    return { value: this.value, unit: this.unit };
  }

  /**
   * Returns a length in centimeters.
   *
   * The factory is the one of the examples of the SDK API. Every other unit
   * is written with the constructor, because the contract names no factory
   * for it.
   */
  static cm(value: number): Length {
    return new Length(value, "cm");
  }
}

/** The four margins of a page. */
export class Margin {
  readonly top: Length;
  readonly right: Length;
  readonly bottom: Length;
  readonly left: Length;

  constructor(top: Length, right: Length, bottom: Length, left: Length) {
    this.top = requireInstance(top, Length, "/top");
    this.right = requireInstance(right, Length, "/right");
    this.bottom = requireInstance(bottom, Length, "/bottom");
    this.left = requireInstance(left, Length, "/left");
    Object.freeze(this);
  }

  toJSON(): Record<string, unknown> {
    return {
      top: this.top.toJSON(),
      right: this.right.toJSON(),
      bottom: this.bottom.toJSON(),
      left: this.left.toJSON(),
    };
  }
}

/**
 * The paper, the orientation, and the margin of a document.
 *
 * The paper value belongs to the catalog in
 * `specs/catalogs/enums/paper-variants.csv`. The catalog is owned by the
 * contract layer, so the model checks the type of the value and leaves the
 * catalog check to the validation layer.
 */
export class Page {
  readonly paper: string;
  readonly orientation: Orientation;
  readonly margin: Margin;

  constructor(paper: string, orientation: Orientation, margin: Margin) {
    this.paper = requireString(paper, "/paper");
    this.orientation = requireEnum(orientation, ORIENTATIONS, "/orientation");
    this.margin = requireInstance(margin, Margin, "/margin");
    Object.freeze(this);
  }

  toJSON(): Record<string, unknown> {
    return {
      paper: this.paper,
      orientation: this.orientation,
      margin: this.margin.toJSON(),
    };
  }
}
