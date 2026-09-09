# LD Coding — Land Record Document Intelligence

This repository contains the land-record document intelligence foundation and evidence layer.

## Phase 2 — Document Intelligence
- Scan quality assessment before restoration
- Deskew, border crop, denoise, Sauvola binarization, CLAHE
- Conditional Real-ESRGAN super-resolution
- LayoutLMv3 / Table Transformer adapter boundary
- PaddleOCR / TrOCR / Sarvam adapter boundary
- Provenance-aware land-record field extraction
- Jurisdiction-aware area normalization while preserving original values

## Phase 3 — Evidence Layer
- Evidence graph for every extracted field
- Document, page, region, and bounding-box provenance
- OCR and NER confidence
- Validation state and human verification state
- Source text and extraction model provenance
- API-ready payloads for “Show Evidence” and source highlighting

Model adapters intentionally do not fabricate OCR or layout results until real inference is configured.
