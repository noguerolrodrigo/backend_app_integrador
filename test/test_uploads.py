from unittest.mock import patch

BASE_URL = "/api/v1/uploads"

MOCK_RESPONSE = {
    "secure_url": "https://res.cloudinary.com/test/image/upload/v1/foodstore/productos/sample.jpg",
    "public_id": "foodstore/productos/sample",
    "width": 800,
    "height": 600,
    "format": "jpg",
    "resource_type": "image",
}

JPEG_MAGIC = b"\xff\xd8\xff" + b"\x00" * 100


def test_upload_imagen_ok(client, auth_headers):
    with patch("app.modules.uploads.service.cloudinary.uploader.upload") as mock_upload:
        mock_upload.return_value = MOCK_RESPONSE
        response = client.post(
            f"{BASE_URL}/imagen",
            data={"folder": "productos"},
            files={"file": ("test.jpg", JPEG_MAGIC, "image/jpeg")},
            headers=auth_headers,
        )
    assert response.status_code == 201
    data = response.json()
    assert data["secure_url"] == MOCK_RESPONSE["secure_url"]
    assert data["public_id"] == MOCK_RESPONSE["public_id"]
    assert data["width"] == 800
    assert data["height"] == 600
    assert data["format"] == "jpg"
    assert data["resource_type"] == "image"


def test_upload_mime_invalido(client, auth_headers):
    with patch("app.modules.uploads.service.cloudinary.uploader.upload"):
        response = client.post(
            f"{BASE_URL}/imagen",
            data={"folder": "productos"},
            files={"file": ("doc.pdf", b"%PDF-1.4", "application/pdf")},
            headers=auth_headers,
        )
    assert response.status_code == 400
    assert "no permitido" in response.json()["detail"]


def test_upload_archivo_muy_grande(client, auth_headers):
    big_file = JPEG_MAGIC + b"\x00" * (5 * 1024 * 1024 + 1)
    with patch("app.modules.uploads.service.cloudinary.uploader.upload"):
        response = client.post(
            f"{BASE_URL}/imagen",
            data={"folder": "productos"},
            files={"file": ("big.jpg", big_file, "image/jpeg")},
            headers=auth_headers,
        )
    assert response.status_code == 400
    assert "5 MB" in response.json()["detail"]


def test_upload_sin_autenticacion(client):
    response = client.post(
        f"{BASE_URL}/imagen",
        data={"folder": "productos"},
        files={"file": ("test.jpg", JPEG_MAGIC, "image/jpeg")},
    )
    assert response.status_code == 401


def test_delete_imagen_ok(client, auth_headers):
    with patch("app.modules.uploads.service.cloudinary.uploader.destroy") as mock_destroy:
        mock_destroy.return_value = {"result": "ok"}
        response = client.delete(
            f"{BASE_URL}/imagen/foodstore/productos/sample",
            headers=auth_headers,
        )
    assert response.status_code == 204
    assert response.content == b""


def test_delete_sin_autenticacion(client):
    response = client.delete(f"{BASE_URL}/imagen/foodstore/productos/sample")
    assert response.status_code == 401
