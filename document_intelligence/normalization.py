from __future__ import annotations

import re

CONVERSIONS = {
    "maharashtra": {
        "guntha": (0.0101171411, "hectare", "Maharashtra_guntha_v1"),
        "acre": (0.4046856422, "hectare", "international_acre_v1"),
        "hectare": (1.0, "hectare", "si_hectare_v1"),
        "sq metre": (0.0001, "hectare", "si_square_metre_v1"),
        "square metre": (0.0001, "hectare", "si_square_metre_v1"),
        "cent": (0.0040468564, "hectare", "international_cent_v1"),
    }
}


def _canonical_unit(unit: str) -> str:
    aliases = {
        "gunthas": "guntha",
        "guntha": "guntha",
        "acre": "acre",
        "acres": "acre",
        "hectare": "hectare",
        "hectares": "hectare",
        "ha": "hectare",
        "sq m": "sq metre",
        "sqm": "sq metre",
        "sq metre": "sq metre",
        "square metre": "square metre",
        "square meters": "sq metre",
        "cent": "cent",
        "cents": "cent",
    }
    return aliases.get(unit.strip().lower(), unit.strip().lower())


def normalize_area(text: str, jurisdiction: str | None = None) -> dict:
    match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*([A-Za-z ]+)", text)
    if not match:
        return {
            "original_text": text,
            "standard_area": None,
            "standard_area_unit": "hectare",
            "conversion_rule": None,
            "conversion_confidence": 0.0,
            "requires_review": True,
        }

    value = float(match.group(1))
    original_unit = _canonical_unit(match.group(2))
    rules = CONVERSIONS.get((jurisdiction or "").strip().lower(), {})
    rule = rules.get(original_unit)
    if not rule:
        return {
            "original_value": value,
            "original_unit": original_unit,
            "original_text": text,
            "standard_area": None,
            "standard_area_unit": "hectare",
            "conversion_rule": None,
            "conversion_confidence": 0.0,
            "requires_review": True,
        }

    factor, standard_unit, rule_id = rule
    return {
        "original_value": value,
        "original_unit": original_unit,
        "original_text": text,
        "standard_area": round(value * factor, 10),
        "standard_area_unit": standard_unit,
        "conversion_rule": rule_id,
        "conversion_confidence": 1.0,
        "requires_review": False,
    }
