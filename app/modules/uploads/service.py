import cloudinary.uploader

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


def upload_image(file_bytes: bytes, content_type: str, folder: str) -> dict:
    if content_type not in ALLOWED_MIME_TYPES:
        raise ValueError(f"Tipo de archivo no permitido: {content_type}")
    if len(file_bytes) > MAX_SIZE_BYTES:
        raise ValueError("El archivo supera el tamaño máximo de 5 MB")
    return cloudinary.uploader.upload(
        file_bytes,
        folder=f"foodstore/{folder}",
        overwrite=False,
        unique_filename=True,
        resource_type="image",
    )


def delete_image(public_id: str) -> None:
    cloudinary.uploader.destroy(public_id)
