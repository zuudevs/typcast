"""The reader of a CSV catalog of enums."""

from __future__ import annotations

import csv
from pathlib import Path

from typcast_enumgen.errors import EnumgenError

__all__ = ["read_catalog_column"]


def read_catalog_column(catalog_path: Path, column_name: str) -> list[str]:
    """Returns the values of a column of a CSV catalog.

    The rules are the rules of the schema generator, so both tools read a
    catalog the same way. The encoding is UTF-8 and a byte order mark is
    accepted. A file without a header row is an error. A fully blank row is
    skipped, and a row whose requested value is empty is an error, because a
    silent omission would change the public enum. The values keep the order
    of the catalog.
    """
    try:
        with catalog_path.open("r", encoding="utf-8-sig", newline="") as catalog_file:
            reader = csv.DictReader(catalog_file)

            if reader.fieldnames is None:
                raise EnumgenError(
                    f"{catalog_path}: CSV file is empty or has no header."
                )

            if column_name not in reader.fieldnames:
                available = ", ".join(reader.fieldnames)
                raise EnumgenError(
                    f"{catalog_path}: column {column_name!r} was not found. "
                    f"Available columns: {available}."
                )

            values: list[str] = []

            for line_number, row in enumerate(reader, start=2):
                if row is None:
                    continue

                if all(value is None or not value.strip() for value in row.values()):
                    continue

                value = row.get(column_name)

                if value is None or not value.strip():
                    raise EnumgenError(
                        f"{catalog_path}:{line_number}: column "
                        f"{column_name!r} contains an empty value."
                    )

                values.append(value.strip())

    except EnumgenError:
        raise
    except (OSError, UnicodeError, csv.Error) as error:
        raise EnumgenError(
            f"Unable to read CSV file {catalog_path}: {error}"
        ) from error

    if not values:
        raise EnumgenError(
            f"{catalog_path}: column {column_name!r} does not contain any values."
        )

    duplicates = sorted(
        {value for value in values if values.count(value) > 1}
    )
    if duplicates:
        raise EnumgenError(
            f"{catalog_path}: column {column_name!r} contains the duplicate "
            f"value(s) {', '.join(duplicates)}."
        )

    return values
