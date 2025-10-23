"""Text processing utilities for concept analysis."""

from __future__ import annotations

import re
from typing import List, Optional


class TextProcessor:
    """Text processing utilities for concept analysis."""

    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove non-printable characters except newlines and tabs
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        return text

    @staticmethod
    def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
        """Extract keywords from text."""
        if not text:
            return []
        
        # Simple keyword extraction (can be enhanced with NLP libraries)
        words = re.findall(r'\b[a-zA-ZáéíóúñüÁÉÍÓÚÑÜ]{3,}\b', text.lower())
        
        # Remove common stop words
        stop_words = {
            'que', 'con', 'para', 'por', 'del', 'las', 'los', 'una', 'uno', 'son',
            'como', 'más', 'pero', 'sus', 'le', 'la', 'el', 'de', 'en', 'y', 'a',
            'es', 'se', 'no', 'te', 'lo', 'le', 'da', 'su', 'si', 'ya', 'me',
            'mi', 'tu', 'ti', 'nos', 'os', 'ellos', 'ellas', 'nosotros', 'nosotras'
        }
        
        # Count word frequency
        word_count = {}
        for word in words:
            if word not in stop_words and len(word) > 3:
                word_count[word] = word_count.get(word, 0) + 1
        
        # Sort by frequency and return top keywords
        sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
        return [word for word, _ in sorted_words[:max_keywords]]

    @staticmethod
    def extract_summary(text: str, max_sentences: int = 3) -> str:
        """Extract a simple summary from text."""
        if not text:
            return ""
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return ""
        
        # Simple heuristic: return first few sentences
        summary_sentences = sentences[:max_sentences]
        return '. '.join(summary_sentences) + '.'

    @staticmethod
    def extract_entities(text: str) -> List[str]:
        """Extract potential entities from text."""
        if not text:
            return []
        
        # Look for common legal/tax entities
        entity_patterns = [
            r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',  # Proper nouns
            r'\b(?:DIAN|IVA|GMF|Renta|Timbre|Aduanas)\b',  # Tax terms
            r'\b(?:Ley|Decreto|Resolución|Circular)\s+\d+',  # Legal documents
            r'\b(?:Artículo|Art\.)\s+\d+',  # Articles
        ]
        
        entities = []
        for pattern in entity_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities.extend(matches)
        
        return list(set(entities))

    @staticmethod
    def calculate_complexity_score(text: str) -> float:
        """Calculate text complexity score (0-1)."""
        if not text:
            return 0.0
        
        # Simple complexity metrics
        sentences = len(re.split(r'[.!?]+', text))
        words = len(text.split())
        avg_sentence_length = words / sentences if sentences > 0 else 0
        
        # Complex words (more than 3 syllables approximation)
        complex_words = len([w for w in text.split() if len(w) > 8])
        complex_word_ratio = complex_words / words if words > 0 else 0
        
        # Normalize to 0-1 scale
        complexity = (avg_sentence_length / 20) + (complex_word_ratio * 2)
        return min(complexity, 1.0)

    @staticmethod
    def extract_dates(text: str) -> List[str]:
        """Extract dates from text."""
        if not text:
            return []
        
        # Date patterns
        date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b',  # DD/MM/YYYY or DD-MM-YYYY
            r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',  # YYYY/MM/DD or YYYY-MM-DD
            r'\b\d{1,2}\s+de\s+\w+\s+de\s+\d{4}\b',  # Spanish dates
        ]
        
        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dates.extend(matches)
        
        return list(set(dates))

    @staticmethod
    def extract_amounts(text: str) -> List[str]:
        """Extract monetary amounts from text."""
        if not text:
            return []
        
        # Amount patterns
        amount_patterns = [
            r'\$\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?',  # $1,000.00
            r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*(?:pesos|dólares)',  # 1,000 pesos
            r'\d+(?:\.\d{2})?\s*(?:pesos|dólares)',  # 1000 pesos
        ]
        
        amounts = []
        for pattern in amount_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            amounts.extend(matches)
        
        return list(set(amounts))

    @staticmethod
    def is_legal_document(text: str) -> bool:
        """Check if text appears to be a legal document."""
        if not text:
            return False
        
        legal_indicators = [
            r'\b(?:concepto|oficio|resolución|decreto|ley|circular)\b',
            r'\b(?:artículo|art\.)\s*\d+',
            r'\b(?:DIAN|impuesto|tributario|fiscal)\b',
            r'\b(?:obligación|derecho|deber|procedimiento)\b',
        ]
        
        text_lower = text.lower()
        matches = sum(1 for pattern in legal_indicators if re.search(pattern, text_lower))
        
        return matches >= 2

    @staticmethod
    def extract_tax_topics(text: str) -> List[str]:
        """Extract tax-related topics from text."""
        if not text:
            return []
        
        tax_topics = {
            'IVA': r'\b(?:IVA|impuesto\s+sobre\s+las\s+ventas)\b',
            'Renta': r'\b(?:impuesto\s+de\s+renta|renta)\b',
            'GMF': r'\b(?:GMF|gravamen\s+a\s+los\s+movimientos\s+financieros)\b',
            'Timbre': r'\b(?:impuesto\s+de\s+timbre|timbre)\b',
            'Aduanas': r'\b(?:aduana|importación|exportación)\b',
            'Retención': r'\b(?:retención\s+en\s+la\s+fuente|rete)\b',
            'Facturación': r'\b(?:factura\s+electrónica|facturación)\b',
            'Declaración': r'\b(?:declaración\s+tributaria|declaración)\b',
        }
        
        topics = []
        text_lower = text.lower()
        
        for topic, pattern in tax_topics.items():
            if re.search(pattern, text_lower):
                topics.append(topic)
        
        return topics
