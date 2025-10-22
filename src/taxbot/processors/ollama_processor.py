"""Ollama AI processor for concept analysis."""

from __future__ import annotations

import json
from typing import List, Optional

try:
    import ollama
except ImportError:
    ollama = None

from ..core.config import get_settings
from ..core.logging import get_scraper_logger
from ..models.concept import Concept


class OllamaProcessor:
    """Ollama AI processor for concept analysis."""

    def __init__(self):
        """Initialize Ollama processor."""
        self.settings = get_settings()
        self.logger = get_scraper_logger()
        self._client = None

    def _get_client(self):
        """Get or create Ollama client."""
        if ollama is None:
            raise ImportError("Ollama package not available")
        
        if self._client is None:
            self._client = ollama.Client(host=self.settings.ollama_base_url)
        
        return self._client

    def is_available(self) -> bool:
        """Check if Ollama is available."""
        try:
            if ollama is None:
                return False
            
            client = self._get_client()
            # Test connection by listing models
            client.list()
            return True
        except Exception as e:
            self.logger.warning(f"Ollama not available: {e}")
            return False

    def summarize_concept(self, concept: Concept) -> str:
        """Generate AI summary for a concept."""
        if not concept.full_text:
            return "No hay contenido para resumir."
        
        if not self.is_available():
            return "Resumen no disponible: Ollama no configurado."

        prompt = self._build_summary_prompt(concept)
        
        try:
            client = self._get_client()
            response = client.chat(
                model=self.settings.ollama_model,
                messages=[{"role": "user", "content": prompt}],
                options={
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "max_tokens": 500,
                }
            )
            
            summary = response["message"]["content"].strip()
            self.logger.debug(f"Generated summary for concept: {concept.title}")
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating summary: {e}")
            return "Resumen no disponible por error en Ollama."

    def analyze_concept(self, concept: Concept, summary: str) -> str:
        """Generate AI analysis for a concept."""
        if not summary:
            return "Análisis no disponible."
        
        if not self.is_available():
            return "Análisis no disponible: Ollama no configurado."

        prompt = self._build_analysis_prompt(concept, summary)
        
        try:
            client = self._get_client()
            response = client.chat(
                model=self.settings.ollama_model,
                messages=[{"role": "user", "content": prompt}],
                options={
                    "temperature": 0.4,
                    "top_p": 0.9,
                    "max_tokens": 800,
                }
            )
            
            analysis = response["message"]["content"].strip()
            self.logger.debug(f"Generated analysis for concept: {concept.title}")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error generating analysis: {e}")
            return "Análisis no disponible por error en Ollama."

    def process_concepts_batch(self, concepts: List[Concept]) -> List[Concept]:
        """Process multiple concepts in batch."""
        if not concepts:
            return concepts
        
        if not self.is_available():
            self.logger.warning("Ollama not available, skipping AI processing")
            return concepts
        
        processed = []
        for concept in concepts:
            try:
                # Generate summary
                concept.summary = self.summarize_concept(concept)
                
                # Generate analysis
                concept.analysis = self.analyze_concept(concept, concept.summary)
                
                processed.append(concept)
                
            except Exception as e:
                self.logger.error(f"Error processing concept {concept.title}: {e}")
                processed.append(concept)  # Add without AI processing
        
        return processed

    def _build_summary_prompt(self, concept: Concept) -> str:
        """Build prompt for concept summarization."""
        # Truncate text if too long
        text = concept.full_text[:self.settings.scraper_max_text_length]
        
        prompt = f"""Eres un abogado tributarista experto. Resume el siguiente concepto de la DIAN en un máximo de 6 frases, destacando:

1. Implicaciones prácticas para contribuyentes
2. Cambios normativos relevantes
3. Obligaciones y responsabilidades
4. Recomendaciones para clientes

Información del concepto:
- Título: {concept.title}
- Tema: {concept.theme}
- Descriptor: {concept.descriptor}

Texto completo:
{text}

Resumen:"""
        
        return prompt

    def _build_analysis_prompt(self, concept: Concept, summary: str) -> str:
        """Build prompt for concept analysis."""
        prompt = f"""Actúa como consultor tributario sénior. Con base en el siguiente resumen y la información del concepto, proporciona un análisis detallado que incluya:

1. RIESGOS IDENTIFICADOS: Principales riesgos para contribuyentes
2. OPORTUNIDADES: Beneficios o ventajas tributarias
3. ACCIONES SUGERIDAS: Pasos específicos a seguir
4. NORMAS RELACIONADAS: Referencias legales relevantes
5. IMPACTO EMPRESARIAL: Efectos en diferentes tipos de empresas

Información del concepto:
- Título: {concept.title}
- Tema: {concept.theme}
- Descriptor: {concept.descriptor}
- Fecha: {concept.date.strftime('%Y-%m-%d')}

Resumen:
{summary}

Análisis:"""
        
        return prompt

    def get_model_info(self) -> dict:
        """Get information about the current model."""
        if not self.is_available():
            return {"available": False, "error": "Ollama not available"}
        
        try:
            client = self._get_client()
            models = client.list()
            current_model = self.settings.ollama_model
            
            model_info = {
                "available": True,
                "current_model": current_model,
                "models": [model["name"] for model in models.get("models", [])],
            }
            
            # Check if current model is available
            model_names = [model["name"] for model in models.get("models", [])]
            model_info["model_available"] = current_model in model_names
            
            return model_info
            
        except Exception as e:
            return {"available": False, "error": str(e)}

    def test_connection(self) -> dict:
        """Test Ollama connection and return status."""
        try:
            if not self.is_available():
                return {
                    "status": "error",
                    "message": "Ollama not available",
                    "details": "Ollama package not installed or service not running"
                }
            
            client = self._get_client()
            models = client.list()
            
            return {
                "status": "success",
                "message": "Ollama connection successful",
                "details": f"Found {len(models.get('models', []))} models available"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": "Ollama connection failed",
                "details": str(e)
            }
