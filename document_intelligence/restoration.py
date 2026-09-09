from __future__ import annotations

from pathlib import Path
from typing import Any


class ImageRestorationPipeline:
    """OpenCV/scikit-image restoration boundary with conditional SR."""

    steps = (
        "deskew",
        "crop_borders",
        "noise_removal",
        "sauvola_binarization",
        "clahe_contrast",
        "super_resolution_if_required",
    )

    def __init__(self, super_resolution_backend: Any | None = None) -> None:
        self.super_resolution_backend = super_resolution_backend

    def restore(
        self,
        image_path: str | Path,
        *,
        super_resolution_required: bool = False,
        output_path: str | Path | None = None,
    ) -> str:
        source = str(image_path)
        # Production implementation should apply OpenCV/scikit-image transforms.
        # We keep this adapter non-destructive and explicit until those libraries
        # and deployment weights are configured.
        if super_resolution_required and self.super_resolution_backend is not None:
            source = str(self.super_resolution_backend.upscale(source))
        return str(output_path) if output_path else source
