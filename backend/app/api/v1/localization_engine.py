"""API endpoints for Localization Engine."""


import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.v1.deps import DB
from app.services.localization_engine import LocalizationEngineService


logger = structlog.get_logger()
router = APIRouter()


# --- Schemas ---


class ExportBundleRequest(BaseModel):
    format: str = Field(default="json", description="Export format (json, csv, xliff)")


class TranslationSchema(BaseModel):
    key: str
    value: str
    language: str
    updated_at: str | None


class LanguageSchema(BaseModel):
    code: str
    name: str
    total_keys: int
    translated_keys: int
    completion_percentage: float


class MissingTranslationSchema(BaseModel):
    key: str
    default_value: str
    source_language: str


class LocalizationStatsSchema(BaseModel):
    total_languages: int
    total_keys: int
    total_translated: int
    overall_completion: float


# --- Endpoints ---


@router.get("/translations/{language}", response_model=list[TranslationSchema], summary="Get translations")
async def get_translations(language: str, db: DB) -> list[TranslationSchema]:
    service = LocalizationEngineService(db=db)
    translations = await service.get_translations(language=language)
    return [
        TranslationSchema(
            key=t.key, value=t.value, language=t.language,
            updated_at=t.updated_at.isoformat() if t.updated_at else None,
        )
        for t in translations
    ]


@router.get("/languages", response_model=list[LanguageSchema], summary="List languages")
async def list_languages(db: DB) -> list[LanguageSchema]:
    service = LocalizationEngineService(db=db)
    languages = await service.list_languages()
    return [
        LanguageSchema(
            code=lang.code, name=lang.name, total_keys=lang.total_keys,
            translated_keys=lang.translated_keys, completion_percentage=lang.completion_percentage,
        )
        for lang in languages
    ]


@router.get("/missing/{language}", response_model=list[MissingTranslationSchema], summary="Get missing translations")
async def get_missing_translations(language: str, db: DB) -> list[MissingTranslationSchema]:
    service = LocalizationEngineService(db=db)
    missing = await service.get_missing_translations(language=language)
    return [
        MissingTranslationSchema(
            key=m.key, default_value=m.default_value, source_language=m.source_language,
        )
        for m in missing
    ]


@router.post("/export/{language}", summary="Export translation bundle")
async def export_bundle(language: str, request: ExportBundleRequest, db: DB) -> dict:
    service = LocalizationEngineService(db=db)
    result = await service.export_bundle(language=language, format=request.format)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Language not found")
    logger.info("bundle_exported", language=language, format=request.format)
    return {"language": language, "format": request.format, "download_url": result}


@router.get("/stats", response_model=LocalizationStatsSchema, summary="Get localization stats")
async def get_stats(db: DB) -> LocalizationStatsSchema:
    service = LocalizationEngineService(db=db)
    s = await service.get_stats()
    return LocalizationStatsSchema(
        total_languages=s.total_languages,
        total_keys=s.total_keys,
        total_translated=s.total_translated,
        overall_completion=s.overall_completion,
    )
