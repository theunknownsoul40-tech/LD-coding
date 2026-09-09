from __future__ import annotations

from pathlib import Path

from .models import QualityAssessment


class ScanQualityAssessor:
    """Dependency-light assessment interface; image metrics can be injected."""

    def assess(self, image_path: str | Path) -> QualityAssessment:
        # Real OpenCV/scikit-image metrics belong here in deployment.
        # The default intentionally avoids inventing measurements.
        return QualityAssessment(
            blur_score=0.0,
            skew_angle=0.0,
            noise_level=0.0,
            width=0,
            height=0,
            dpi=None,
            quality="fair",
            super_resolution_required=False,
        )
