import os
import shutil
import pytest
from fastapi.testclient import TestClient
from pathlib import Path

# импорт на приложението
from main import app, STORAGE_DIR

client = TestClient(app)


# ---------------------------
# Fixtures
# ---------------------------

@pytest.fixture(scope="function", autouse=True)
def clean_storage():
    """
    Почистваме storage/ преди всеки тест.
    """
    if STORAGE_DIR.exists():
        shutil.rmtree(STORAGE_DIR)
    STORAGE_DIR.mkdir()
    yield
    shutil.rmtree(STORAGE_DIR)


# ---------------------------
# Tests
# ---------------------------

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["message"] == "File Storage API"


def test_upload_file():
    file_content = b"hello test"
    files = {"file": ("test.txt", file_content, "text/plain")}

    response = client.post("/files", files=files)

    assert response.status_code == 200
    data = response.json()

    assert data["filename"] == "test.txt"
    assert data["size"] == len(file_content)
    assert (STORAGE_DIR / "test.txt").exists()


def test_upload_invalid_filename():
    # Текущото API използва os.path.basename, така че "../hack.txt" става "hack.txt"
    files = {"file": ("../hack.txt", b"hacked", "text/plain")}
    response = client.post("/files", files=files)

    # API-то ще върне 200, не 400
    assert response.status_code == 200

    data = response.json()
    assert data["filename"] == "hack.txt"   # basename("../hack.txt")
    assert (STORAGE_DIR / "hack.txt").exists()



def test_get_uploaded_file():
    files = {"file": ("myfile.bin", b"1234", "application/octet-stream")}
    client.post("/files", files=files)

    response = client.get("/files/myfile.bin")

    assert response.status_code == 200
    assert response.content == b"1234"


def test_get_missing_file():
    response = client.get("/files/nonexistent.txt")
    assert response.status_code == 404


def test_list_files():
    client.post("/files", files={"file": ("a.txt", b"1", "text/plain")})
    client.post("/files", files={"file": ("b.txt", b"2", "text/plain")})

    response = client.get("/files")

    assert response.status_code == 200
    data = response.json()

    assert data["count"] == 2
    assert set(data["files"]) == {"a.txt", "b.txt"}


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "healthy"
    assert "timestamp" in data


def test_metrics():
    client.post("/files", files={"file": ("x.txt", b"123", "text/plain")})

    response = client.get("/metrics")

    assert response.status_code == 200
    data = response.json()

    assert data["files_current"] == 1
    assert data["files_stored_total"] >= 1
    assert data["total_storage_bytes"] >= 3
