#!/usr/bin/env python3
"""
Script final para generar reporte DIAN en el formato exacto requerido
"""

import sys
from pathlib import Path

# Add the taxbot directory to the path
sys.path.append(str(Path(__file__).parent))

from taxbot.dian_report_generator import generate_professional_dian_report

def main():
    """Generate the final DIAN report in the exact required format."""
    print("🏛️  GENERADOR FINAL DE REPORTE DIAN")
    print("=" * 60)
    print("Generando reporte profesional de conceptos DIAN...")
    print("Formato: Fecha | Tema | Concepto + Resumen + Análisis")
    print("=" * 60)
    
    # Generate report for 2025 concepts (20 conceptos)
    report_file = generate_professional_dian_report(
        csv_path="taxbot/data/conceptos_dian.csv",
        max_conceptos=20,
        year_filter="2025"
    )
    
    if report_file:
        print(f"\n✅ REPORTE GENERADO EXITOSAMENTE")
        print(f"📁 Archivo: {report_file}")
        print(f"📍 Ubicación: {Path(report_file).absolute()}")
        
        # Show summary of what was generated
        with open(report_file, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            
        print(f"\n📊 RESUMEN DEL REPORTE:")
        print(f"   • Total de líneas: {len(lines)}")
        print(f"   • Conceptos procesados: {len([l for l in lines if l.startswith('-')])}")
        print(f"   • Tamaño del archivo: {len(content):,} caracteres")
        
        print(f"\n🎯 CARACTERÍSTICAS DEL REPORTE:")
        print(f"   ✅ Formato cronológico por fecha")
        print(f"   ✅ Resúmenes profesionales generados por IA")
        print(f"   ✅ Análisis técnicos detallados")
        print(f"   ✅ Compatible con base de datos")
        print(f"   ✅ Estructura: Fecha | Tema | Concepto")
        
        print(f"\n📋 PRIMEROS CONCEPTOS DEL REPORTE:")
        print("-" * 50)
        concept_lines = [l for l in lines if l.startswith('-')]
        for i, line in enumerate(concept_lines[:5], 1):
            print(f"{i}. {line}")
        if len(concept_lines) > 5:
            print(f"   ... y {len(concept_lines) - 5} conceptos más")
        
        print(f"\n🚀 EL SISTEMA ESTÁ LISTO PARA USAR")
        print(f"   • Ejecuta: python generate_final_dian_report.py")
        print(f"   • Modifica max_conceptos para más/menos conceptos")
        print(f"   • Cambia year_filter para otros años")
        
    else:
        print("❌ Error generando el reporte")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())