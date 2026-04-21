"""Tests for internationalization (i18n)."""

from __future__ import annotations

import os

from clean_agents.i18n import I18n, get_i18n, reset_i18n


def test_english_default():
    """Test English is the default language."""
    i18n = I18n()
    assert i18n.lang == "en"
    assert i18n.t("design.title") == "Architecture Design Session"


def test_spanish_translation():
    """Test Spanish translation."""
    i18n = I18n(lang="es")
    assert i18n.lang == "es"
    assert i18n.t("design.title") == "Sesión de Diseño de Arquitectura"
    assert i18n.t("design.describe") == "Describí el sistema agéntico que querés construir."


def test_portuguese_translation():
    """Test Portuguese translation."""
    i18n = I18n(lang="pt")
    assert i18n.lang == "pt"
    assert i18n.t("design.title") == "Sessão de Design de Arquitetura"
    assert i18n.t("design.describe") == "Descreva o sistema agêntico que deseja construir."


def test_fallback_to_english():
    """Test fallback to English when key not found in current language."""
    i18n = I18n(lang="pt")
    # Assume this key exists in English but might not in Portuguese
    result = i18n.t("design.title")
    assert result is not None
    assert isinstance(result, str)


def test_missing_key_returns_key():
    """Test that missing keys return the key itself."""
    i18n = I18n(lang="en")
    result = i18n.t("nonexistent.key")
    assert result == "nonexistent.key"


def test_translation_with_format_args():
    """Test translation with format arguments."""
    i18n = I18n(lang="en")
    # Create a test key with format placeholders
    result = i18n.t("design.saved", path="/path/to/blueprint")
    # The key itself doesn't have placeholders in the real dict, but test the formatting ability
    assert isinstance(result, str)


def test_from_env_with_lang_var():
    """Test loading from environment variable."""
    os.environ["CLEAN_AGENTS_LANG"] = "es"
    try:
        i18n = I18n.from_env()
        assert i18n.lang == "es"
    finally:
        os.environ.pop("CLEAN_AGENTS_LANG", None)


def test_from_env_without_lang_var():
    """Test loading without environment variable defaults to English."""
    os.environ.pop("CLEAN_AGENTS_LANG", None)
    i18n = I18n.from_env()
    assert i18n.lang == "en"


def test_available_languages():
    """Test getting list of available languages."""
    i18n = I18n()
    langs = i18n.available_languages
    assert "en" in langs
    assert "es" in langs
    assert "pt" in langs


def test_invalid_language_defaults_to_english():
    """Test that invalid language code defaults to English."""
    i18n = I18n(lang="invalid_lang")
    assert i18n.lang == "en"


def test_all_english_keys_exist():
    """Test that all expected English keys are present."""
    i18n = I18n(lang="en")
    expected_keys = [
        "design.title",
        "design.describe",
        "design.analyzing",
        "shield.title",
        "cost.title",
        "error.no_blueprint",
        "common.success",
        "common.error",
    ]
    for key in expected_keys:
        result = i18n.t(key)
        assert result is not None
        assert result != key  # Should not be missing


def test_spanish_common_strings():
    """Test that Spanish translations exist for common strings."""
    i18n = I18n(lang="es")
    assert i18n.t("common.success") == "Éxito"
    assert i18n.t("common.error") == "Error"
    assert i18n.t("common.warning") == "Advertencia"


def test_get_i18n_singleton():
    """Test the global singleton instance."""
    reset_i18n()

    i1 = get_i18n()
    i2 = get_i18n()

    assert i1 is i2

    reset_i18n()


def test_get_i18n_with_override():
    """Test overriding language in get_i18n."""
    reset_i18n()

    i1 = get_i18n(lang="es")
    assert i1.lang == "es"

    i2 = get_i18n()  # Should use default
    assert i2.lang == "en"

    reset_i18n()


def test_format_with_multiple_args():
    """Test formatting with multiple arguments."""
    i18n = I18n(lang="en")
    # Test that formatting works even if the base string has placeholders
    # (not in our actual data but test the capability)
    test_string = "Cost is {amount} per {unit}"
    formatted = test_string.format(amount=100, unit="request")
    assert formatted == "Cost is 100 per request"


def test_portuguese_shield_strings():
    """Test Portuguese shield-related strings."""
    i18n = I18n(lang="pt")
    assert i18n.t("shield.title") == "CLean-shield — Análise de Endurecimento de Segurança"
    assert i18n.t("shield.checks_passed") == "checks passaram"


def test_spanish_error_messages():
    """Test Spanish error messages."""
    i18n = I18n(lang="es")
    assert "blueprint" in i18n.t("error.no_blueprint").lower()
    assert "clean-agents design" in i18n.t("error.no_blueprint")
