import csv
from pathlib import Path

from typcast_codegen.errors import CodegenError


def read_csv_column(csv_path: Path, column_name: str) -> list[str]:
    """Read a non-empty column from a CSV file.

    Empty physical rows are ignored. A partially populated row with an empty
    requested value is treated as invalid input rather than silently omitted.
    """
    try:
        with csv_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
            reader = csv.DictReader(csv_file)

            if reader.fieldnames is None:
                raise CodegenError(f"{csv_path}: CSV file is empty or has no header.")

            if column_name not in reader.fieldnames:
                available = ", ".join(reader.fieldnames)
                raise CodegenError(
                    f"{csv_path}: column {column_name!r} was not found. "
                    f"Available columns: {available}."
                )

            values: list[str] = []

            for line_number, row in enumerate(reader, start=2):
                if row is None:
                    continue

                if all(
                    value is None or not value.strip()
                    for value in row.values()
                ):
                    continue

                value = row.get(column_name)

                if value is None or not value.strip():
                    raise CodegenError(
                        f"{csv_path}:{line_number}: column "
                        f"{column_name!r} contains an empty value."
                    )

                values.append(value.strip())

    except CodegenError:
        raise
    except (OSError, UnicodeError, csv.Error) as error:
        raise CodegenError(f"Unable to read CSV file {csv_path}: {error}") from error

    if not values:
        raise CodegenError(
            f"{csv_path}: column {column_name!r} does not contain any values."
        )

    return values
