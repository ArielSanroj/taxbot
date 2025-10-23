#!/usr/bin/env python3
"""
Script de prueba para demostrar el sistema completo de generación de reportes DIAN
"""

import sys
import os
from pathlib import Path

# Add the taxbot directory to the path
sys.path.append(str(Path(__file__).parent))

from taxbot.dian_report_generator import generate_professional_dian_report

def test_dian_report_system():
    """Test the complete DIAN report generation system."""
    print("🧪 PRUEBA DEL SISTEMA DE REPORTES DIAN")
    print("=" * 50)
    
    # Test 1: Generate report for 2025 concepts
    print("\n📋 Prueba 1: Generando reporte para conceptos 2025")
    report_file_2025 = generate_professional_dian_report(
        csv_path="taxbot/data/conceptos_dian.csv",
        max_conceptos=5,  # Small number for testing
        year_filter="2025"
    )
    
    if report_file_2025:
        print(f"✅ Reporte 2025 generado: {report_file_2025}")
        
        # Show first few lines of the report
        with open(report_file_2025, 'r', encoding='utf-8') as f:
            content = f.read()
            print("\n📄 Primeras líneas del reporte:")
            print("-" * 40)
            lines = content.split('\n')
            for i, line in enumerate(lines[:20]):
                print(f"{i+1:2d}: {line}")
            if len(lines) > 20:
                print("    ...")
    else:
        print("❌ Error generando reporte 2025")
    
    print("\n" + "=" * 50)
    print("🎯 PRUEBA COMPLETADA")
    print("=" * 50)
    
    if report_file_2025:
        print(f"✅ Sistema funcionando correctamente")
        print(f"📁 Archivo generado: {report_file_2025}")
        print("📊 El sistema puede generar reportes con:")
        print("   • Resúmenes profesionales generados por IA")
        print("   • Análisis técnicos detallados")
        print("   • Organización cronológica")
        print("   • Formato compatible con base de datos")
    else:
        print("❌ Sistema con errores")

if __name__ == "__main__":
    test_dian_report_system()