/** The metadata of the document IR. */

import { CODE_INVALID_DATE, throwValidation } from "../diagnostics.js";
import { requireString } from "./base.js";

const DATE_PATTERN = /^(\d{4})-(\d{2})-(\d{2})$/;

/** The title, the author, and the date of a document. */
export class Metadata {
  readonly title: string;
  readonly author: string | null;
  readonly date: string | null;

  constructor(
    title: string,
    author: string | null = null,
    date: string | null = null,
  ) {
    this.title = requireString(title, "/title");
    this.author =
      author === null ? null : requireString(author, "/author", true);
    this.date = date === null ? null : checkDate(date);
    Object.freeze(this);
  }

  toJSON(): Record<string, unknown> {
    const value: Record<string, unknown> = { title: this.title };
    if (this.author !== null) {
      value["author"] = this.author;
    }
    if (this.date !== null) {
      value["date"] = this.date;
    }
    return value;
  }
}

function checkDate(value: string): string {
  if (typeof value !== "string") {
    throwValidation(CODE_INVALID_DATE, "'/date' must be a string.", "/date");
  }
  const match = DATE_PATTERN.exec(value);
  if (match === null) {
    throwValidation(
      CODE_INVALID_DATE,
      `'/date' must be a calendar date in YYYY-MM-DD form, got '${value}'.`,
      "/date",
      { value },
    );
  }
  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  const parsed = new Date(Date.UTC(year, month - 1, day));
  if (
    parsed.getUTCFullYear() !== year ||
    parsed.getUTCMonth() !== month - 1 ||
    parsed.getUTCDate() !== day
  ) {
    throwValidation(
      CODE_INVALID_DATE,
      `'/date' is not a calendar date: '${value}'.`,
      "/date",
      { value },
    );
  }
  return value;
}
