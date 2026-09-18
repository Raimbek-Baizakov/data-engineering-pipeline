from src.etl import transform, validate

def test_validate_accepts_valid_rows():
    rows = [
        {
            "first_name": "Ivan",
            "last_name": "Ivanov",
            "email": "ivan@gmail.com",
            "age": "25",
            "city": "Almaty",
        }
    ]
    valid_rows, rejected_rows = validate(rows)

    assert len(valid_rows) == 1
    assert len(rejected_rows) == 0


def test_validate_rejects_invalid_email():
    rows = [
        {
            "first_name": "Ivan",
            "last_name": "Ivanov",
            "email": "invalid-email",
            "age": "25",
            "city": "Almaty",
        }
    ]

    valid_rows, rejected_rows = validate(rows)

    assert len(valid_rows) == 0
    assert len(rejected_rows) == 1
    assert "invalid email" in rejected_rows[0]["error"]


def test_validate_rejects_invalid_age():
    rows = [
        {
            "first_name": "Ivan",
            "last_name": "Ivanov",
            "email": "ivan@gmail.com",
            "age": "abc",
            "city": "Almaty",
        }
    ]

    valid_rows, rejected_rows = validate(rows)

    assert len(valid_rows) == 0
    assert len(rejected_rows) == 1
    assert "age is not an integer" in rejected_rows[0]["error"]


def test_validate_rejects_age_out_of_range():
    rows = [
        {
            "first_name": "Ivan",
            "last_name": "Ivanov",
            "email": "ivan@gmail.com",
            "age": "150",
            "city": "Almaty",
        }
    ]

    valid_rows, rejected_rows = validate(rows)

    assert len(valid_rows) == 0
    assert len(rejected_rows) == 1
    assert "age out of range" in rejected_rows[0]["error"]


def test_transform_cleans_data():
    rows = [
        {
            "first_name": " Ivan ",
            "last_name": " Ivanov ",
            "email": " IVAN@GMAIL.COM ",
            "age": "25",
            "city": " almaty ",
        }
    ]

    result = transform(rows)

    assert result[0]["first_name"] == "Ivan"
    assert result[0]["last_name"] == "Ivanov"
    assert result[0]["email"] == "ivan@gmail.com"
    assert result[0]["age"] == 25
    assert result[0]["city"] == "Almaty"