import os
from typing import Optional

from fastapi import HTTPException, UploadFile, status


ALLOWED_EXTENSIONS = {"docx", "pdf"}
MAX_FILE_SIZE_MB = int(os.getenv("TDB_MAX_FILE_SIZE_MB", "50"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

_MAX_FILE_SIZE_MB_BY_EXT = {
    "pdf": int(os.getenv("TDB_MAX_PDF_FILE_SIZE_MB", "25")),
}


def _ext_of(filename: Optional[str]) -> str:
    if filename and "." in filename:
        return filename.rsplit(".", 1)[-1].lower()
    return ""


def max_file_size_mb_for(ext: Optional[str]) -> int:
    return _MAX_FILE_SIZE_MB_BY_EXT.get((ext or "").lower(), MAX_FILE_SIZE_MB)


def max_file_size_bytes_for(ext: Optional[str]) -> int:
    return max_file_size_mb_for(ext) * 1024 * 1024


def validate_file_type(file: UploadFile) -> str:
    ext = _ext_of(file.filename)
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail={
                "error_code": "UNSUPPORTED_FILE_TYPE",
                "message": f"File type '.{ext}' is not supported" if ext else "File has no extension",
                "supported_types": sorted(ALLOWED_EXTENSIONS),
            },
        )
    return ext


async def validate_file_size(file: UploadFile, ext: Optional[str] = None) -> int:
    if ext is None:
        ext = _ext_of(file.filename)
    cap_mb = max_file_size_mb_for(ext)
    cap_bytes = cap_mb * 1024 * 1024

    contents = await file.read()
    file_size = len(contents)
    if file_size > cap_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "error_code": "FILE_TOO_LARGE",
                "message": (
                    f"File size ({file_size // (1024 * 1024)}MB) "
                    f"exceeds the maximum allowed size ({cap_mb}MB)"
                ),
                "max_file_size_mb": cap_mb,
            },
        )
    await file.seek(0)
    return file_size
