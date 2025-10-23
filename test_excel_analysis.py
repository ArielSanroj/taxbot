#!/usr/bin/env python3
"""
Test script to analyze the Excel file and generate AI-powered summaries
for September conceptos as a tax lawyer and accountant.
"""

import pandas as pd
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import ollama
import re

def clean_text(value: str) -> str:
    """Clean text by removing extra whitespace and special characters."""
    if pd.isna(value) or value is None:
        return ""
    return " ".join(str(value).replace("\xa0", " ").split())

def analyze_excel_file(file_path: str) -> List[Dict[str, Any]]:
    """Analyze the Excel file and extract conceptos."""
    print(f"📊 Analyzing Excel file: {file_path}")
    
    # Read the Excel file
    df = pd.read_excel(file_path, header=None)
    print(f"📋 File shape: {df.shape}")
    
    # Extract conceptos from the data
    conceptos = []
    
    for i, row in df.iterrows():
        row_data = [clean_text(cell) for cell in row.tolist()]
        # Look for rows that contain meaningful content
        non_empty_cells = [cell for cell in row_data if cell and cell != "NaN"]
        
        if len(non_empty_cells) > 0:
            concepto = {
                'row_number': i,
                'raw_data': row_data,
                'content': ' | '.join(non_empty_cells),
                'title': non_empty_cells[0] if non_empty_cells else "",
                'description': ' | '.join(non_empty_cells[1:]) if len(non_empty_cells) > 1 else ""
            }
            conceptos.append(concepto)
    
    print(f"📝 Found {len(conceptos)} conceptos")
    return conceptos

def generate_tax_lawyer_summary(concepto: Dict[str, Any]) -> str:
    """Generate a professional tax lawyer summary using Ollama."""
    content = concepto['content']
    title = concepto['title']
    
    if not content or len(content.strip()) < 10:
        return "No hay contenido suficiente para generar un análisis."
    
    prompt = f"""
Eres un abogado tributarista y contador público experto en legislación colombiana. 
Analiza el siguiente concepto de la DIAN y proporciona un resumen profesional que incluya:

1. **RESUMEN EJECUTIVO**: Explicación clara y concisa del concepto
2. **IMPLICACIONES TRIBUTARIAS**: Impacto en obligaciones fiscales
3. **OBLIGACIONES PARA CONTRIBUYENTES**: Qué deben hacer los contribuyentes
4. **RIESGOS Y OPORTUNIDADES**: Aspectos críticos a considerar
5. **RECOMENDACIONES PRÁCTICAS**: Acciones sugeridas para implementar

CONCEPTO A ANALIZAR:
Título: {title}
Contenido: {content}

Proporciona un análisis profesional, técnico y práctico que sea útil para contadores y abogados.
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

def generate_accountant_analysis(concepto: Dict[str, Any]) -> str:
    """Generate a professional accountant analysis using Ollama."""
    content = concepto['content']
    title = concepto['title']
    
    if not content or len(content.strip()) < 10:
        return "No hay contenido suficiente para generar un análisis contable."
    
    prompt = f"""
Eres un contador público experto en normatividad contable y tributaria colombiana.
Analiza el siguiente concepto de la DIAN desde la perspectiva contable y proporciona:

1. **IMPACTO CONTABLE**: Cómo afecta los registros contables
2. **TRATAMIENTO FISCAL**: Implicaciones en declaraciones de renta e IVA
3. **CONTROLES INTERNOS**: Qué controles implementar
4. **DOCUMENTACIÓN REQUERIDA**: Qué documentos mantener
5. **FECHAS IMPORTANTES**: Plazos y vencimientos
6. **CASOS PRÁCTICOS**: Ejemplos de aplicación

CONCEPTO A ANALIZAR:
Título: {title}
Contenido: {content}

Proporciona un análisis técnico contable que sea práctico para la implementación.
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

def main():
    """Main function to test the Excel analysis."""
    print("🏛️  TAXBOT - ANÁLISIS PROFESIONAL DE CONCEPTOS DIAN")
    print("=" * 60)
    
    # File path
    excel_file = "/Users/arielsanroj/downloads/testastra2.xlsx"
    
    if not os.path.exists(excel_file):
        print(f"❌ File not found: {excel_file}")
        return
    
    # Analyze the Excel file
    conceptos = analyze_excel_file(excel_file)
    
    if not conceptos:
        print("❌ No conceptos found in the Excel file")
        return
    
    print(f"\n🔍 Processing {len(conceptos)} conceptos...")
    print("=" * 60)
    
    # Process each concepto
    for i, concepto in enumerate(conceptos, 1):
        print(f"\n📋 CONCEPTO {i}: {concepto['title']}")
        print("-" * 40)
        print(f"📄 Contenido: {concepto['content'][:200]}...")
        
        # Generate tax lawyer summary
        print("\n⚖️  ANÁLISIS COMO ABOGADO TRIBUTARISTA:")
        print("-" * 40)
        lawyer_summary = generate_tax_lawyer_summary(concepto)
        print(lawyer_summary)
        
        # Generate accountant analysis
        print("\n📊 ANÁLISIS COMO CONTADOR PÚBLICO:")
        print("-" * 40)
        accountant_analysis = generate_accountant_analysis(concepto)
        print(accountant_analysis)
        
        print("\n" + "=" * 60)
        
        # Limit to first 3 conceptos for testing
        if i >= 3:
            print(f"\n⏹️  Showing first 3 conceptos for testing. Total available: {len(conceptos)}")
            break

if __name__ == "__main__":
    main()