# Land Record Document Intelligence

## Phase 2 — Document Intelligence

Pipeline:

`Original Scan → Deskew → Crop borders → Noise removal → Sauvola binarization → CLAHE contrast enhancement → Super-resolution if required → Clean image`

Quality is assessed first. Real-ESRGAN is conditional rather than blindly applied.

Layout is model-driven rather than fixed-coordinate based, with adapters for LayoutLMv3 and Table Transformer. OCR/HTR adapters support PaddleOCR, TrOCR, and Sarvam integration.

Structured extraction preserves provenance for owner, survey number, khata number, area, unit, village, tehsil, district, land class, and mutation ID.

Area normalization is jurisdiction-aware. Original values and units are preserved; unsupported or ambiguous conversions are marked for review.

## Phase 3 — Evidence Layer

Every extracted field can have an EvidenceNode containing:

- document ID/name
- page
- region ID
- bounding box
- OCR confidence
- NER confidence
- validation state
- human verification state
- source text
- extraction model
- stable evidence ID and timestamp

The `evidence_api.py` helpers return the payload needed for a UI “Show Evidence” action to open the original page and highlight the exact bounding box.

## Production wiring

Model adapters intentionally return empty results until real inference services/weights are configured. This prevents placeholder output from becoming land-record evidence.
