"""AI processing functions using Ollama."""

from __future__ import annotations

import logging
from typing import Iterable, List

from .config import OLLAMA_MODEL
from .models import Concept
from .scraper import clean_text

try:
    import ollama  # type: ignore
except ImportError:
    ollama = None


def summarize_text(text: str) -> str:
    """Summarize text using Ollama."""
    if not text:
        return "No hay contenido para resumir."

    if ollama is None:
        logging.warning("Ollama no esta disponible.")
        return "Resumen no disponible: Ollama no configurado."

    prompt = (
        "Eres un abogado tributarista. Resume el siguiente concepto de la "
        "DIAN en un maximo de 6 frases, destacando implicaciones practicas, "
        "cambios normativos, obligaciones y recomendaciones para clientes. "
        "Texto: " + text
    )

    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        return clean_text(response["message"]["content"])
    except Exception as exc:
        logging.error("Error al resumir con Ollama: %s", exc)
        return "Resumen no disponible por error en Ollama."


def complementary_analysis(summary: str, concept: Concept) -> str:
    """Generate complementary analysis using Ollama."""
    if not summary:
        return "Analisis no disponible."

    if ollama is None:
        return "Analisis no disponible: Ollama no configurado."

    prompt = (
        "Actua como consultor tributario senior. Con base en el siguiente "
        "resumen y la informacion del concepto, identifica riesgos, "
        "oportunidades, acciones sugeridas y normas relacionadas. \n"
        f"Resumen: {summary}\n"
        f"Tema: {concept.theme}\n"
        f"Descriptor: {concept.descriptor}"
    )

    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        return clean_text(response["message"]["content"])
    except Exception as exc:
        logging.error("Error en analisis complementario: %s", exc)
        return "Analisis no disponible por error en Ollama."


def process_concepts(concepts: Iterable[Concept]) -> List[Concept]:
    """Process concepts with AI summarization and analysis."""
    processed: List[Concept] = []
    for concept in concepts:
        concept.summary = summarize_text(concept.full_text[:12000])
        concept.analysis = complementary_analysis(concept.summary, concept)
        processed.append(concept)
    return processed
