#!/usr/bin/env python3
"""
Comprehensive test script to analyze all September conceptos from the Excel file
and generate professional AI-powered summaries as a tax lawyer and accountant.
"""

import pandas as pd
import os
import json
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
                'description': ' | '.join(non_empty_cells[1:]) if len(non_empty_cells) > 1 else "",
                'date_processed': datetime.now().isoformat()
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
Eres un abogado tributarista experto en legislación colombiana con más de 15 años de experiencia.
Analiza el siguiente concepto de la DIAN y proporciona un resumen profesional que incluya:

1. **RESUMEN EJECUTIVO**: Explicación clara y concisa del concepto
2. **IMPLICACIONES TRIBUTARIAS**: Impacto en obligaciones fiscales y normativa aplicable
3. **OBLIGACIONES PARA CONTRIBUYENTES**: Qué deben hacer los contribuyentes específicamente
4. **RIESGOS Y OPORTUNIDADES**: Aspectos críticos a considerar
5. **RECOMENDACIONES PRÁCTICAS**: Acciones sugeridas para implementar
6. **NORMATIVA APLICABLE**: Leyes, decretos y resoluciones relacionadas

CONCEPTO A ANALIZAR:
Título: {title}
Contenido: {content}

Proporciona un análisis profesional, técnico y práctico que sea útil para contadores y abogados.
Mantén un tono profesional y técnico apropiado para el ámbito tributario colombiano.
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
Eres un contador público experto en normatividad contable y tributaria colombiana con más de 15 años de experiencia.
Analiza el siguiente concepto de la DIAN desde la perspectiva contable y proporciona:

1. **IMPACTO CONTABLE**: Cómo afecta los registros contables y estados financieros
2. **TRATAMIENTO FISCAL**: Implicaciones en declaraciones de renta, IVA y otros impuestos
3. **CONTROLES INTERNOS**: Qué controles implementar para cumplimiento
4. **DOCUMENTACIÓN REQUERIDA**: Qué documentos mantener y por cuánto tiempo
5. **FECHAS IMPORTANTES**: Plazos, vencimientos y calendario fiscal
6. **CASOS PRÁCTICOS**: Ejemplos de aplicación con cifras y asientos contables
7. **NORMATIVA CONTABLE**: Referencias a NIIF, Código de Comercio y normativa DIAN

CONCEPTO A ANALIZAR:
Título: {title}
Contenido: {content}

Proporciona un análisis técnico contable que sea práctico para la implementación.
Incluye ejemplos específicos y referencias a la normativa colombiana.
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

def save_results_to_file(conceptos_analizados: List[Dict[str, Any]], output_file: str):
    """Save the analyzed conceptos to a JSON file."""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(conceptos_analizados, f, ensure_ascii=False, indent=2)
        print(f"💾 Results saved to: {output_file}")
    except Exception as e:
        print(f"❌ Error saving results: {e}")

def main():
    """Main function to test the Excel analysis."""
    print("🏛️  TAXBOT - ANÁLISIS PROFESIONAL DE CONCEPTOS DIAN SEPTIEMBRE")
    print("=" * 70)
    
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
    print("=" * 70)
    
    # Process each concepto
    conceptos_analizados = []
    
    for i, concepto in enumerate(conceptos, 1):
        print(f"\n📋 CONCEPTO {i}: {concepto['title']}")
        print("-" * 50)
        print(f"📄 Contenido: {concepto['content'][:150]}...")
        
        # Generate tax lawyer summary
        print("\n⚖️  ANÁLISIS COMO ABOGADO TRIBUTARISTA:")
        print("-" * 50)
        lawyer_summary = generate_tax_lawyer_summary(concepto)
        print(lawyer_summary)
        
        # Generate accountant analysis
        print("\n📊 ANÁLISIS COMO CONTADOR PÚBLICO:")
        print("-" * 50)
        accountant_analysis = generate_accountant_analysis(concepto)
        print(accountant_analysis)
        
        # Store results
        concepto_analizado = {
            'concepto_number': i,
            'title': concepto['title'],
            'content': concepto['content'],
            'lawyer_analysis': lawyer_summary,
            'accountant_analysis': accountant_analysis,
            'processed_date': datetime.now().isoformat()
        }
        conceptos_analizados.append(concepto_analizado)
        
        print("\n" + "=" * 70)
        
        # Add a small delay to avoid overwhelming the API
        import time
        time.sleep(1)
    
    # Save results to file
    output_file = f"september_conceptos_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    save_results_to_file(conceptos_analizados, output_file)
    
    print(f"\n✅ Analysis completed! Processed {len(conceptos_analizados)} conceptos")
    print(f"📁 Results saved to: {output_file}")

if __name__ == "__main__":
    main()