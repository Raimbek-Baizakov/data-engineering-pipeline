import csv
import logging
import os
import re
import time
from pathlib import Path

import psycopg2
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent

CSV_FILE = BASE_DIR / "data" / "customers.csv"

REJECTED_FILE = BASE_DIR / "data" / "rejected_customers.csv"

load_dotenv(BASE_DIR / ".env")

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


def extract():
    logger.info("Extract started")
    if not CSV_FILE.exists():
        raise FileNotFoundError(
            f"CSV file not found {CSV_FILE}"
        )
    with open(CSV_FILE, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        rows = list(reader)

    logger.info(
        "Extract completed: %d rows",
        len(rows)
    )

    return rows


REQUIRED_FIELDS = [
    "first_name",
    "last_name",
    "email",
    "age",
    "city",
]

EMAIL_PATTERN = re.compile(
    r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
)


def validate(rows):
    logger.info("Validation started")

    valid_rows = []
    rejected_rows = []

    for row_number, row in enumerate(rows, start=2):
        errors = []

        for field in REQUIRED_FIELDS:
            value = row.get(field)

            if value is None or not value.strip():
                errors.append(f"{field} is empty")

        email = row.get("email", "").strip().lower()

        if email and not EMAIL_PATTERN.match(email):
            errors.append("invalid email")

        age = row.get("age", "").strip()

        try:
            age_value = int(age)

            if not 0 <= age_value <= 120:
                errors.append("age out of range")

        except ValueError:
            errors.append("age is not an integer")

        if errors:
            rejected_rows.append(
                {
                    "row_number": row_number,
                    "first_name": row.get("first_name", ""),
                    "last_name": row.get("last_name", ""),
                    "email": row.get("email", ""),
                    "age": row.get("age", ""),
                    "city": row.get("city", ""),
                    "error": "; ".join(errors),
                }
            )

            logger.warning(
                "Row %d rejected: %s",
                row_number,
                ", ".join(errors),
            )

            continue

        valid_rows.append(row)

    logger.info(
        "Validation completed: %d valid, %d invalid",
        len(valid_rows),
        len(rejected_rows),
    )

    return valid_rows, rejected_rows

def save_rejected(rows):
    if not rows:
        logger.info("No rejected rows")


        with open(
            REJECTED_FILE,
            "w",
            newline="",
            encoding="utf-8",
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=[
                    "row_number",
                    "first_name",
                    "last_name",
                    "email",
                    "age",
                    "city",
                    "error",
                ],
            )

            writer.writeheader()

        return

    logger.info(
        "Saving %d rejected rows to %s",
        len(rows),
        REJECTED_FILE,
    )

    with open(
        REJECTED_FILE,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "row_number",
                "first_name",
                "last_name",
                "email",
                "age",
                "city",
                "error",
            ],
        )

        writer.writeheader()
        writer.writerows(rows)

    logger.info("Rejected rows saved")

def transform(rows):
    logger.info("Transform started")

    transformed = []

    for row in rows:
        first_name = row["first_name"].strip()
        last_name = row["last_name"].strip()

        email = row["email"].strip().lower()

        age = int(row["age"])

        city = row["city"].strip().title()

        transformed.append(
            {
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "age": age,
                "city": city,
            }
        )
    logger.info(
        "Transform completed: %d rows",
        len(transformed)
    )

    return transformed


def load(rows):

    logger.info("Load started")

    connection = None
    cursor = None

    try:
        connection = psycopg2.connect(**DB_CONFIG)

        cursor = connection.cursor()

        query = """
            INSERT INTO customers (
                first_name,
                last_name,
                email,
                age,
                city
            )
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (email)
            DO UPDATE SET
                first_name = EXCLUDED.first_name,
                last_name = EXCLUDED.last_name,
                age = EXCLUDED.age,
                city = EXCLUDED.city;
        """

        for row in rows:
            cursor.execute(
                query,
                (
                    row["first_name"],
                    row["last_name"],
                    row["email"],
                    row["age"],
                    row["city"],
                ),
            )

        connection.commit()
        logger.info(
            "Load completed: %d rows",
            len(rows)
        )
    except Exception:
        if connection:
            connection.rollback()

        logger.exception("Load failed")

        raise

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()



def main():
    start_time = time.perf_counter()
    logger.info("ETL pipeline started")

    try:
        rows = extract()

        rows, rejected_rows = validate(rows)

        save_rejected(rejected_rows)

        rows = transform(rows)

        load(rows)

        elapsed = time.perf_counter() - start_time
        logger.info(
            "ETL pipeline completed successfully "
            "in %.2f seconds",
            elapsed,
        )
    except Exception:
        elapsed = time.perf_counter() - start_time
        logger.error(
            "ETL pipeline failed after %.2f seconds",
            elapsed,
        )
        raise

if __name__ == "__main__":
    main()
