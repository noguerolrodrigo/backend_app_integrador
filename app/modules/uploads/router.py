from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.core.deps import require_role
from app.modules.usuario.models import Usuario
from app.modules.uploads import service
from app.modules.uploads.schema import CloudinaryResponse

router = APIRouter(prefix="/api/v1/uploads", tags=["Uploads"])


@router.post("/imagen", response_model=CloudinaryResponse, status_code=status.HTTP_201_CREATED)
async def upload_imagen(
    file: UploadFile = File(...),
    folder: str = Form(...),
    _: Usuario = Depends(require_role(["ADMIN"])),
):
    content_type = file.content_type or ""
    file_bytes = await file.read()
    try:
        result = service.upload_image(file_bytes, content_type, folder)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return CloudinaryResponse(**result)


@router.delete("/imagen/{public_id:path}", status_code=status.HTTP_204_NO_CONTENT)
def delete_imagen(
    public_id: str,
    _: Usuario = Depends(require_role(["ADMIN"])),
):
    service.delete_image(public_id)
