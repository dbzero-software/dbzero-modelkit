"""Tests for multi-language string support."""

from __future__ import annotations

import dbzero_modelkit

from dbzero_modelkit.language import LanguageCode, ML_String


def test_language_code_enum_values(db0_fixture):
    assert hasattr(LanguageCode, "LEN")
    assert hasattr(LanguageCode, "LPL")
    assert hasattr(LanguageCode, "LGER")
    assert hasattr(LanguageCode, "LFR")
    assert hasattr(LanguageCode, "LESP")


def test_language_code_enum_access(db0_fixture):
    assert LanguageCode.LEN is not None
    assert LanguageCode.LPL is not None
    assert LanguageCode.LGER is not None
    assert LanguageCode.LFR is not None
    assert LanguageCode.LESP is not None


def test_language_code_enum_equality(db0_fixture):
    assert LanguageCode.LEN == LanguageCode.LEN
    assert LanguageCode.LPL == LanguageCode.LPL
    assert LanguageCode.LEN != LanguageCode.LPL


def test_language_code_enum_string_representation(db0_fixture):
    assert str(LanguageCode.LEN) == "LEN"
    assert str(LanguageCode.LPL) == "LPL"
    assert str(LanguageCode.LGER) == "LGER"
    assert str(LanguageCode.LFR) == "LFR"
    assert str(LanguageCode.LESP) == "LESP"


def test_ml_string_str_returns_primary_value(db0_fixture):
    text = ML_String("Dieta standardowa", LanguageCode.LPL)

    assert str(text) == "Dieta standardowa"


def test_ml_string_get_without_language_returns_primary_value(db0_fixture):
    text = ML_String("Dieta standardowa", LanguageCode.LPL, {LanguageCode.LEN: "Standard Diet"})

    assert text.get() == "Dieta standardowa"


def test_ml_string_get_returns_requested_translation(db0_fixture):
    text = ML_String("Dieta standardowa", LanguageCode.LPL, {LanguageCode.LEN: "Standard Diet"})

    assert text.get(LanguageCode.LEN) == "Standard Diet"


def test_ml_string_get_uses_fallback_codes(db0_fixture):
    text = ML_String("Dieta standardowa", LanguageCode.LPL, {LanguageCode.LEN: "Standard Diet"})

    assert text.get(LanguageCode.LFR, [LanguageCode.LEN]) == "Standard Diet"


def test_ml_string_get_returns_default_when_no_language_matches(db0_fixture):
    text = ML_String("Dieta standardowa", LanguageCode.LPL, {LanguageCode.LEN: "Standard Diet"})

    assert text.get(LanguageCode.LFR, [LanguageCode.LESP], "") == ""


def test_ml_string_get_returns_none_when_no_language_matches(db0_fixture):
    text = ML_String(
        "Mufinka czekoladowa",
        LanguageCode.LPL,
        {LanguageCode.LEN: "Chocolate muffin"},
    )

    assert text.get(LanguageCode.LFR, [LanguageCode.LESP]) is None


def test_ml_string_get_can_fallback_to_primary_value(db0_fixture):
    text = ML_String("Dieta standardowa", LanguageCode.LPL)

    assert text.get(LanguageCode.LFR, [LanguageCode.LPL]) == "Dieta standardowa"


def test_ml_string_load_returns_requested_or_polish_fallback(db0_fixture):
    text = ML_String("Dieta standardowa", LanguageCode.LPL, {LanguageCode.LEN: "Standard Diet"})

    assert text.__load__(LanguageCode.LEN) == "Standard Diet"
    assert text.__load__(LanguageCode.LFR) == "Dieta standardowa"


def test_package_exports_language_public_names():
    assert dbzero_modelkit.LanguageCode is not None
    assert dbzero_modelkit.ML_String is not None
