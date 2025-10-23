#!/usr/bin/env python3
"""
Script para generar reporte de conceptos DIAN en el formato requerido
con resúmenes profesionales y análisis detallados.
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import ollama

def clean_text(value: str) -> str:
    """Clean text by removing extra whitespace and special characters."""
    if not value or value is None:
        return ""
    return " ".join(str(value).replace("\xa0", " ").split())

def generate_professional_summary(concepto: Dict[str, Any]) -> str:
    """Generate a professional summary using Ollama."""
    content = concepto.get('full_text', '')
    title = concepto.get('title', '')
    theme = concepto.get('theme', '')
    descriptor = concepto.get('descriptor', '')
    
    if not content or len(content.strip()) < 50:
        return "No hay contenido suficiente para generar un resumen profesional."
    
    prompt = f"""
Eres un abogado tributarista experto en legislación colombiana. 
Genera un resumen profesional y conciso del siguiente concepto de la DIAN.

CONCEPTO:
Título: {title}
Tema: {theme}
Descriptor: {descriptor}
Contenido: {content[:3000]}

Proporciona un resumen ejecutivo de máximo 3 párrafos que incluya:
1. El tema principal del concepto
2. Las implicaciones tributarias clave
3. Las obligaciones o recomendaciones principales

Mantén un tono profesional y técnico apropiado para abogados y contadores.
"""
    
    try:
        response = ollama.chat(
            model="llama3", 
            messages=[{"role": "user", "content": prompt}]
        )
        return clean_text(response["message"]["content"])
    except Exception as e:
        print(f"❌ Error generating summary: {e}")
        return f"Error al generar resumen: {str(e)}"

def generate_detailed_analysis(concepto: Dict[str, Any]) -> str:
    """Generate a detailed analysis using Ollama."""
    content = concepto.get('full_text', '')
    title = concepto.get('title', '')
    theme = concepto.get('theme', '')
    descriptor = concepto.get('descriptor', '')
    
    if not content or len(content.strip()) < 50:
        return "No hay contenido suficiente para generar un análisis detallado."
    
    prompt = f"""
Eres un contador público y abogado tributarista experto en normatividad colombiana.
Genera un análisis detallado del siguiente concepto de la DIAN.

CONCEPTO:
Título: {title}
Tema: {theme}
Descriptor: {descriptor}
Contenido: {content[:3000]}

Proporciona un análisis técnico que incluya:
1. **IMPLICACIONES TRIBUTARIAS**: Impacto en obligaciones fiscales
2. **OBLIGACIONES PARA CONTRIBUYENTES**: Qué deben hacer específicamente
3. **RIESGOS Y OPORTUNIDADES**: Aspectos críticos a considerar
4. **RECOMENDACIONES PRÁCTICAS**: Acciones sugeridas para implementar
5. **NORMATIVA APLICABLE**: Referencias legales relevantes

Mantén un tono profesional y técnico con ejemplos prácticos cuando sea posible.
"""
    
    try:
        response = ollama.chat(
            model="llama3", 
            messages=[{"role": "user", "content": prompt}]
        )
        return clean_text(response["message"]["content"])
    except Exception as e:
        print(f"❌ Error generating analysis: {e}")
        return f"Error al generar análisis: {str(e)}"

def load_conceptos_from_csv() -> List[Dict[str, Any]]:
    """Load conceptos from the CSV file."""
    import pandas as pd
    
    csv_path = Path("taxbot/data/conceptos_dian.csv")
    if not csv_path.exists():
        print(f"❌ No se encontró el archivo: {csv_path}")
        return []
    
    try:
        df = pd.read_csv(csv_path)
        conceptos = []
        
        for _, row in df.iterrows():
            concepto = {
                'title': str(row.get('title', '')),
                'date': str(row.get('date', '')),
                'theme': str(row.get('theme', '')),
                'descriptor': str(row.get('descriptor', '')),
                'link': str(row.get('link', '')),
                'summary': str(row.get('summary', '')),
                'analysis': str(row.get('analysis', '')),
                'full_text': str(row.get('summary', '')) + ' ' + str(row.get('analysis', ''))
            }
            conceptos.append(concepto)
        
        print(f"📊 Cargados {len(conceptos)} conceptos del CSV")
        return conceptos
        
    except Exception as e:
        print(f"❌ Error cargando CSV: {e}")
        return []

def generate_dian_report():
    """Generate the DIAN report in the required format."""
    print("🏛️  GENERADOR DE REPORTE DIAN - CONCEPTOS SEPTIEMBRE 2024")
    print("=" * 70)
    
    # Load conceptos from CSV
    conceptos = load_conceptos_from_csv()
    
    if not conceptos:
        print("❌ No se encontraron conceptos para procesar")
        return
    
    # Filter conceptos from recent months (2025)
    recent_conceptos = []
    for concepto in conceptos:
        date_str = concepto.get('date', '')
        if '2025' in date_str:
            recent_conceptos.append(concepto)
    
    if not recent_conceptos:
        print("❌ No se encontraron conceptos recientes")
        return
    
    print(f"📅 Encontrados {len(recent_conceptos)} conceptos de 2025")
    
    # Sort by date
    recent_conceptos.sort(key=lambda x: x.get('date', ''), reverse=True)
    
    # Take first 20 conceptos for the report
    selected_conceptos = recent_conceptos[:20]
    
    # Generate report
    report_lines = []
    report_lines.append(f"Test ejecutado: {datetime.now().isoformat()} UTC")
    report_lines.append("Fuente: https://cijuf.org.co/normatividad/conceptos-y-oficios-dian/2025")
    report_lines.append(f"Conceptos encontrados: {len(selected_conceptos)}")
    report_lines.append("")
    
    for i, concepto in enumerate(selected_conceptos, 1):
        print(f"📋 Procesando concepto {i}/{len(selected_conceptos)}: {concepto.get('title', '')[:50]}...")
        
        # Extract date components
        date_str = concepto.get('date', '')
        theme = concepto.get('theme', 'Sin tema')
        title = concepto.get('title', 'Sin título')
        
        # Generate professional summary
        summary = generate_professional_summary(concepto)
        
        # Generate detailed analysis
        analysis = generate_detailed_analysis(concepto)
        
        # Format the entry
        report_lines.append(f"- {date_str} | {theme} | {title}")
        report_lines.append(f"  Resumen:")
        report_lines.append(f"{summary}")
        report_lines.append(f"  Análisis:")
        report_lines.append(f"{analysis}")
        report_lines.append("")
        
        # Add delay to avoid overwhelming the API
        import time
        time.sleep(2)
    
    # Save report
    report_content = "\n".join(report_lines)
    report_file = f"dian_conceptos_2025_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"✅ Reporte generado: {report_file}")
    print(f"📄 Contenido del reporte:")
    print("=" * 70)
    print(report_content[:2000] + "..." if len(report_content) > 2000 else report_content)

if __name__ == "__main__":
    generate_dian_report()