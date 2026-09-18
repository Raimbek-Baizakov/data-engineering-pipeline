import csv
from pathlib import Path

import psycopg2


BASE_DIR = Path(__file__).resolve().parent.parent

CSV_FILE = BASE_DIR / "data" / "customers.csv"


DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 5433,
    "database": "analytics",
    "user": "postgres",
    "password": "1234",
}


def extract():
    with open(CSV_FILE, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return list(reader)


def transform(rows):
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

    return transformed


def load(rows):
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

    cursor.close()
    connection.close()


def main():
    print("Extract...")
    rows = extract()
    print(f"Получено записей: {len(rows)}")

    print("Transform...")
    rows = transform(rows)

    print("Load...")
    load(rows)

    print("ETL успешно завершён!")


if __name__ == "__main__":
    main()
