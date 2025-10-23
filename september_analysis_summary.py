#!/usr/bin/env python3
"""
Generate a summary report of the September conceptos analysis
"""

import json
import os
from datetime import datetime
from pathlib import Path

def generate_summary_report(json_file: str):
    """Generate a summary report from the analysis results."""
    
    # Load the analysis results
    with open(json_file, 'r', encoding='utf-8') as f:
        conceptos = json.load(f)
    
    print("🏛️  TAXBOT - RESUMEN DE ANÁLISIS DE CONCEPTOS DIAN SEPTIEMBRE")
    print("=" * 70)
    print(f"📅 Fecha de análisis: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 Total de conceptos analizados: {len(conceptos)}")
    print("=" * 70)
    
    # Summary by category
    categories = {}
    for concepto in conceptos:
        title = concepto['title']
        if 'estados financieros' in title.lower() or 'declaración' in title.lower():
            categories['Estados Financieros y Declaraciones'] = categories.get('Estados Financieros y Declaraciones', 0) + 1
        elif 'datos generales' in title.lower():
            categories['Datos Generales'] = categories.get('Datos Generales', 0) + 1
        elif 'audit' in title.lower() or 'auditoría' in title.lower():
            categories['Auditoría y Controles'] = categories.get('Auditoría y Controles', 0) + 1
        else:
            categories['Otros'] = categories.get('Otros', 0) + 1
    
    print("\n📋 DISTRIBUCIÓN POR CATEGORÍAS:")
    print("-" * 40)
    for category, count in categories.items():
        print(f"• {category}: {count} conceptos")
    
    # Key insights
    print("\n🔍 INSIGHTS PRINCIPALES:")
    print("-" * 40)
    
    # Count conceptos with substantial content
    substantial_conceptos = [c for c in conceptos if len(c['content']) > 50]
    print(f"• Conceptos con contenido sustancial: {len(substantial_conceptos)}")
    
    # Count conceptos with AI analysis
    ai_analyzed = [c for c in conceptos if 'Error al generar' not in c['lawyer_analysis']]
    print(f"• Conceptos con análisis AI exitoso: {len(ai_analyzed)}")
    
    # Average analysis length
    avg_lawyer_length = sum(len(c['lawyer_analysis']) for c in conceptos) / len(conceptos)
    avg_accountant_length = sum(len(c['accountant_analysis']) for c in conceptos) / len(conceptos)
    
    print(f"• Longitud promedio análisis legal: {avg_lawyer_length:.0f} caracteres")
    print(f"• Longitud promedio análisis contable: {avg_accountant_length:.0f} caracteres")
    
    # Top conceptos by content length
    print("\n📈 CONCEPTOS MÁS DETALLADOS:")
    print("-" * 40)
    sorted_conceptos = sorted(conceptos, key=lambda x: len(x['content']), reverse=True)
    for i, concepto in enumerate(sorted_conceptos[:5], 1):
        print(f"{i}. {concepto['title'][:60]}... ({len(concepto['content'])} chars)")
    
    # Sample analysis excerpts
    print("\n📝 MUESTRAS DE ANÁLISIS:")
    print("-" * 40)
    
    for i, concepto in enumerate(conceptos[:3], 1):
        print(f"\n{i}. {concepto['title']}")
        print("   Análisis Legal (extracto):")
        lawyer_preview = concepto['lawyer_analysis'][:200] + "..." if len(concepto['lawyer_analysis']) > 200 else concepto['lawyer_analysis']
        print(f"   {lawyer_preview}")
        print("   Análisis Contable (extracto):")
        accountant_preview = concepto['accountant_analysis'][:200] + "..." if len(concepto['accountant_analysis']) > 200 else concepto['accountant_analysis']
        print(f"   {accountant_preview}")
    
    print("\n" + "=" * 70)
    print("✅ Análisis completado exitosamente")
    print(f"📁 Archivo de resultados: {json_file}")
    print("=" * 70)

def main():
    """Main function to generate summary report."""
    # Find the most recent analysis file
    analysis_files = list(Path('.').glob('september_conceptos_analysis_*.json'))
    
    if not analysis_files:
        print("❌ No se encontraron archivos de análisis")
        return
    
    # Get the most recent file
    latest_file = max(analysis_files, key=os.path.getctime)
    print(f"📁 Procesando archivo: {latest_file}")
    
    generate_summary_report(str(latest_file))

if __name__ == "__main__":
    main()