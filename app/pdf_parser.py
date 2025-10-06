from __future__ import annotations

import io

from fastapi import HTTPException, status
from pypdf import PdfReader


async def extract_text_from_upload(file) -> str:
    filename = file.filename or "uploaded"
    content = await file.read()
    await file.seek(0)
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filen är tom")

    if filename.lower().endswith(".pdf"):
        return _extract_from_pdf(content)
    return content.decode("utf-8", errors="ignore")


def _extract_from_pdf(content: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(content))
    except Exception as exc:  # pragma: no cover - fallback for invalid pdf
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Kunde inte läsa PDF") from exc

    text_parts: list[str] = []
    for page in reader.pages:
        text_parts.append(page.extract_text() or "")
    combined = "\n".join(text_parts)
    if not combined.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="PDF:en saknar text")
    return combined
