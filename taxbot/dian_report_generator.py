#!/usr/bin/env python3
"""
Generador de reportes profesionales de conceptos DIAN
Integrado con el sistema principal del taxbot
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import ollama
import pandas as pd
import re

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
Contenido: {content[:2000]}

Proporciona un resumen ejecutivo de máximo 2 párrafos que incluya:
1. El tema principal y las implicaciones tributarias clave
2. Las obligaciones específicas para contribuyentes

Mantén un tono profesional y técnico. NO uses viñetas ni formato especial.
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
Genera un análisis técnico detallado del siguiente concepto de la DIAN.

CONCEPTO:
Título: {title}
Tema: {theme}
Descriptor: {descriptor}
Contenido: {content[:2000]}

Proporciona un análisis técnico que incluya:
1. IMPLICACIONES TRIBUTARIAS: Impacto en obligaciones fiscales
2. OBLIGACIONES PARA CONTRIBUYENTES: Qué deben hacer específicamente
3. RIESGOS Y OPORTUNIDADES: Aspectos críticos a considerar
4. RECOMENDACIONES PRÁCTICAS: Acciones sugeridas para implementar
5. NORMATIVA APLICABLE: Referencias legales relevantes

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

def extract_concept_number(title: str) -> str:
    """Extract concept number from title."""
    # Look for patterns like "Concepto 1234" or "Concepto 1234(567890)"
    match = re.search(r'Concepto\s+(\d+(?:\(\d+\))?)', title)
    if match:
        return match.group(1)
    return ""

def load_conceptos_from_csv(csv_path: str) -> List[Dict[str, Any]]:
    """Load conceptos from the CSV file."""
    if not os.path.exists(csv_path):
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

def generate_professional_dian_report(
    csv_path: str = "taxbot/data/conceptos_dian.csv",
    max_conceptos: int = 20,
    year_filter: str = "2025"
) -> str:
    """Generate the professional DIAN report in the exact required format."""
    print("🏛️  GENERADOR DE REPORTE PROFESIONAL DIAN")
    print("=" * 70)
    
    # Load conceptos from CSV
    conceptos = load_conceptos_from_csv(csv_path)
    
    if not conceptos:
        print("❌ No se encontraron conceptos para procesar")
        return ""
    
    # Filter conceptos by year
    filtered_conceptos = []
    for concepto in conceptos:
        date_str = concepto.get('date', '')
        if year_filter in date_str:
            filtered_conceptos.append(concepto)
    
    if not filtered_conceptos:
        print(f"❌ No se encontraron conceptos de {year_filter}")
        return ""
    
    print(f"📅 Encontrados {len(filtered_conceptos)} conceptos de {year_filter}")
    
    # Sort by date (most recent first)
    filtered_conceptos.sort(key=lambda x: x.get('date', ''), reverse=True)
    
    # Take specified number of conceptos for the report
    selected_conceptos = filtered_conceptos[:max_conceptos]
    
    # Generate report
    report_lines = []
    report_lines.append(f"Test ejecutado: {datetime.now().isoformat()} UTC")
    report_lines.append(f"Fuente: https://cijuf.org.co/normatividad/conceptos-y-oficios-dian/{year_filter}")
    report_lines.append(f"Conceptos encontrados: {len(selected_conceptos)}")
    report_lines.append("")
    
    for i, concepto in enumerate(selected_conceptos, 1):
        print(f"📋 Procesando concepto {i}/{len(selected_conceptos)}: {concepto.get('title', '')[:50]}...")
        
        # Extract components
        date_str = concepto.get('date', '')
        theme = concepto.get('theme', 'Sin tema')
        title = concepto.get('title', 'Sin título')
        concept_number = extract_concept_number(title)
        
        # Generate professional summary
        summary = generate_professional_summary(concepto)
        
        # Generate detailed analysis
        analysis = generate_detailed_analysis(concepto)
        
        # Format the entry exactly as required
        if concept_number:
            report_lines.append(f"- {date_str} | {theme} | Concepto {concept_number}")
        else:
            report_lines.append(f"- {date_str} | {theme} | {title}")
        
        report_lines.append(f"  Resumen:")
        report_lines.append(f"{summary}")
        report_lines.append(f"  Análisis:")
        report_lines.append(f"{analysis}")
        report_lines.append("")
        
        # Add delay to avoid overwhelming the API
        import time
        time.sleep(1)
    
    # Save report
    report_content = "\n".join(report_lines)
    report_file = f"dian_conceptos_profesional_{year_filter}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"✅ Reporte profesional generado: {report_file}")
    print(f"📄 Contenido del reporte:")
    print("=" * 70)
    print(report_content[:2000] + "..." if len(report_content) > 2000 else report_content)
    
    return report_file

def main():
    """Main function to generate DIAN report."""
    # Generate report for 2025 concepts
    report_file = generate_professional_dian_report(
        csv_path="taxbot/data/conceptos_dian.csv",
        max_conceptos=20,
        year_filter="2025"
    )
    
    if report_file:
        print(f"\n🎯 Reporte generado exitosamente: {report_file}")
        print("📁 El archivo está listo para usar y contiene:")
        print("   • Resúmenes profesionales de cada concepto")
        print("   • Análisis técnicos detallados")
        print("   • Organización cronológica por fecha")
        print("   • Formato compatible con base de datos")

if __name__ == "__main__":
    main()