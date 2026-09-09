from __future__ import annotations

from pathlib import Path

from .adapters import LandRecordExtractor, LayoutDetector, OCRBackend
from .models import DocumentResult
from .normalization import normalize_area
from .quality import ScanQualityAssessor
from .restoration import ImageRestorationPipeline


class DocumentIntelligencePipeline:
    """Orchestrates quality gating, restoration, layout, OCR/HTR and extraction."""

    def __init__(self, *, quality=None, restoration=None, layout=None, ocr=None, extractor=None):
        self.quality = quality or ScanQualityAssessor()
        self.restoration = restoration or ImageRestorationPipeline()
        self.layout = layout or LayoutDetector()
        self.ocr = ocr or OCRBackend()
        self.extractor = extractor or LandRecordExtractor()

    def process(
        self,
        image_path: str | Path,
        *,
        page: int = 1,
        jurisdiction: str | None = None,
        super_resolution: bool | None = None,
    ) -> DocumentResult:
        assessment = self.quality.assess(image_path)
        use_sr = assessment.super_resolution_required if super_resolution is None else super_resolution
        cleaned = self.restoration.restore(
            image_path,
            super_resolution_required=use_sr,
        )
        regions = self.layout.detect(cleaned, page=page)
        provenance = self.ocr.extract(cleaned, page=page)
        entities = [p.to_dict() for p in provenance]
        fields = self.extractor.extract(entities)

        normalized = None
        for f in fields:
            if f.name == "area" and f.value is not None:
                payload = normalize_area(str(f.value), jurisdiction)
                normalized = type("NormalizedAreaAdapter", (), {})
                from .models import NormalizedArea
                normalized = NormalizedArea(**payload)
                break

        return DocumentResult(
            quality=assessment,
            regions=regions,
            fields=fields,
            normalized_area=normalized,
            artifacts={"clean_image": str(cleaned)},
        )
