/** The metadata of the document IR. */

import { CODE_INVALID_DATE, safeText, throwValidation } from "../diagnostics.js";
import { requireBoundedString } from "./base.js";

// The pattern holds the ASCII digits only. The `\d` of JavaScript matches
// the ASCII digits alone, and the pattern has no `m` flag, so the text must
// end with the date.
const DATE_PATTERN = /^([0-9]{4})-([0-9]{2})-([0-9]{2})$/;

const MAX_TEXT_LENGTH = 512;

const DAYS_IN_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];

/** Returns the number of days of a month of the proleptic Gregorian calendar. */
function daysInMonth(year: number, month: number): number {
  if (month === 2) {
    const leap = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
    return leap ? 29 : 28;
  }
  return DAYS_IN_MONTH[month - 1] ?? 0;
}

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
    this.title = requireBoundedString(title, "/title", MAX_TEXT_LENGTH);
    this.author =
      author === null
        ? null
        : requireBoundedString(author, "/author", MAX_TEXT_LENGTH, true);
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
      `'/date' must be a calendar date in YYYY-MM-DD form, got '${safeText(value)}'.`,
      "/date",
      { value },
    );
  }
  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  // The calendar is checked with arithmetic and not with a date value. The
  // `Date.UTC` function maps a year below 100 to the year 1900 and above, so
  // a date such as `0001-01-01` would be read as a year of 1901. The Python
  // SDK accepts that date, and the two SDKs must accept the same dates.
  const valid =
    year >= 1 &&
    month >= 1 &&
    month <= 12 &&
    day >= 1 &&
    day <= daysInMonth(year, month);
  if (!valid) {
    throwValidation(
      CODE_INVALID_DATE,
      `'/date' is not a calendar date: '${safeText(value)}'.`,
      "/date",
      { value },
    );
  }
  return value;
}
