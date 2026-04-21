"""Internationalization (i18n) support for CLean-agents.

Provides multi-language support for CLI output.
Respects CLEAN_AGENTS_LANG environment variable and system locale.
"""

from __future__ import annotations

import locale
import os
from typing import Any

TRANSLATIONS = {
    "en": {
        "design.title": "Architecture Design Session",
        "design.describe": "Describe the agentic system you want to build.",
        "design.describe_hint": "Include: domain, responsibilities, scale, compliance needs, etc.",
        "design.analyzing": "Analyzing requirements...",
        "design.save_prompt": "Save blueprint?",
        "design.saved": "Blueprint saved to",
        "design.cost": "Estimated cost per request",
        "design.modules_title": "Available modules",
        "shield.title": "CLean-shield — Security Hardening Analysis",
        "shield.checks_passed": "checks passed",
        "shield.issues_found": "issues found",
        "cost.title": "Cost Simulator",
        "cost.per_request": "Per-request cost",
        "cost.monthly": "Monthly LLM cost",
        "cost.total": "Total estimated",
        "error.no_blueprint": "No blueprint found. Run 'clean-agents design' first.",
        "error.empty_desc": "Description cannot be empty",
        "common.success": "Success",
        "common.error": "Error",
        "common.warning": "Warning",
    },
    "es": {
        "design.title": "Sesión de Diseño de Arquitectura",
        "design.describe": "Describí el sistema agéntico que querés construir.",
        "design.describe_hint": "Incluí: dominio, responsabilidades, escala, compliance, etc.",
        "design.analyzing": "Analizando requisitos...",
        "design.save_prompt": "¿Guardar blueprint?",
        "design.saved": "Blueprint guardado en",
        "design.cost": "Costo estimado por request",
        "design.modules_title": "Módulos disponibles",
        "shield.title": "CLean-shield — Análisis de Endurecimiento de Seguridad",
        "shield.checks_passed": "checks pasaron",
        "shield.issues_found": "problemas encontrados",
        "cost.title": "Simulador de Costos",
        "cost.per_request": "Costo por request",
        "cost.monthly": "Costo LLM mensual",
        "cost.total": "Estimado total",
        "error.no_blueprint": "No se encontró blueprint. Ejecutá 'clean-agents design' primero.",
        "error.empty_desc": "La descripción no puede estar vacía",
        "common.success": "Éxito",
        "common.error": "Error",
        "common.warning": "Advertencia",
    },
    "pt": {
        "design.title": "Sessão de Design de Arquitetura",
        "design.describe": "Descreva o sistema agêntico que deseja construir.",
        "design.describe_hint": "Inclua: domínio, responsabilidades, escala, compliance, etc.",
        "design.analyzing": "Analisando requisitos...",
        "design.save_prompt": "Salvar blueprint?",
        "design.saved": "Blueprint salvo em",
        "design.cost": "Custo estimado por request",
        "design.modules_title": "Módulos disponíveis",
        "shield.title": "CLean-shield — Análise de Endurecimento de Segurança",
        "shield.checks_passed": "checks passaram",
        "shield.issues_found": "problemas encontrados",
        "cost.title": "Simulador de Custos",
        "cost.per_request": "Custo por request",
        "cost.monthly": "Custo de LLM mensal",
        "cost.total": "Total estimado",
        "error.no_blueprint": "Blueprint não encontrado. Execute 'clean-agents design' primeiro.",
        "error.empty_desc": "A descrição não pode estar vazia",
        "common.success": "Sucesso",
        "common.error": "Erro",
        "common.warning": "Aviso",
    },
}


class I18n:
    """Internationalization helper.

    Supports English (en), Spanish (es), and Portuguese (pt).
    Falls back to English if translation not found.
    """

    def __init__(self, lang: str = "en") -> None:
        self._lang = lang if lang in TRANSLATIONS else "en"
        self._fallback = "en"

    @classmethod
    def from_env(cls) -> I18n:
        """Load from CLEAN_AGENTS_LANG env var or system locale."""
        # Check environment variable first
        lang = os.environ.get("CLEAN_AGENTS_LANG", "").lower()
        if lang in TRANSLATIONS:
            return cls(lang=lang)

        # Try to detect from system locale
        try:
            system_locale = locale.getlocale()[0]  # e.g., 'es_ES', 'pt_BR'
            if system_locale:
                lang_code = system_locale.split("_")[0].lower()
                if lang_code in TRANSLATIONS:
                    return cls(lang=lang_code)
        except (AttributeError, IndexError, TypeError):
            pass

        # Default to English
        return cls(lang="en")

    def t(self, key: str, **kwargs: Any) -> str:
        """Translate a key. Falls back to English if not found.

        Args:
            key: Translation key (e.g., 'design.title')
            **kwargs: Format arguments for string interpolation

        Returns:
            Translated string or key if not found
        """
        text = TRANSLATIONS.get(self._lang, {}).get(key)
        if text is None:
            text = TRANSLATIONS[self._fallback].get(key, key)
        if kwargs:
            text = text.format(**kwargs)
        return text

    @property
    def lang(self) -> str:
        """Get current language code."""
        return self._lang

    @property
    def available_languages(self) -> list[str]:
        """Get list of available language codes."""
        return list(TRANSLATIONS.keys())


# Global singleton instance
_i18n_instance: I18n | None = None


def get_i18n(lang: str | None = None) -> I18n:
    """Get i18n instance, optionally override language.

    Args:
        lang: Optional language code to override the default

    Returns:
        I18n instance
    """
    global _i18n_instance
    if lang is not None:
        return I18n(lang=lang)
    if _i18n_instance is None:
        _i18n_instance = I18n.from_env()
    return _i18n_instance


def reset_i18n() -> None:
    """Reset the global i18n instance (for testing)."""
    global _i18n_instance
    _i18n_instance = None
