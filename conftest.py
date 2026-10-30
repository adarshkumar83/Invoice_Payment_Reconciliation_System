
import os
import pytest

import database.database as database


# Every test gets its own empty database file
@pytest.fixture
def db(tmp_path, monkeypatch):

    monkeypatch.setattr(
        database,
        "DB_PATH",
        os.path.join(str(tmp_path), "test.db")
    )

    database.create_tables()

    return database
