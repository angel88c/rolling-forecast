"""
Script para verificar oportunidades del 100% en el archivo real.
"""

import sys
import os
sys.path.append('src')
sys.path.append('config')

from src.data_processor import DataProcessor
import pandas as pd

def check_100_percent_in_real_file():
    """Verifica si hay oportunidades del 100% en el archivo real."""
    print("=== VERIFICACIÓN: Oportunidades del 100% en Archivo Real ===")
    
    file_path = "data/C&NQFunnel-OpenQuotes(25-50%)-2025-06-03-14-00-13.xlsx"
    
    if not os.path.exists(file_path):
        print("❌ Archivo no encontrado")
        return
    
    processor = DataProcessor()
    
    try:
        # Leer archivo
        df, parsing_report = processor.read_excel_file(file_path)
        
        # Procesar probabilidades
        df_with_prob = processor._assign_probabilities(df)
        
        print(f"📊 Análisis de probabilidades:")
        print(f"   Total de registros: {len(df_with_prob)}")
        
        # Contar por probabilidad
        prob_counts = df_with_prob['probability_assigned'].value_counts().sort_index()
        
        print(f"\n📈 Distribución de probabilidades:")
        for prob, count in prob_counts.items():
            prob_pct = f"{prob:.0%}"
            print(f"   • {prob_pct}: {count} oportunidades")
        
        # Verificar si hay del 100%
        prob_100_count = (df_with_prob['probability_assigned'] == 1.0).sum()
        
        if prob_100_count > 0:
            print(f"\n⚠️ ENCONTRADAS {prob_100_count} oportunidades con probabilidad del 100%")
            
            # Mostrar algunas de las del 100%
            prob_100_projects = df_with_prob[df_with_prob['probability_assigned'] == 1.0]
            print(f"\n📋 Ejemplos de proyectos del 100%:")
            for i, row in prob_100_projects.head(5).iterrows():
                print(f"   • {row.get('Opportunity Name', 'N/A')}")
        else:
            print(f"\n✅ NO HAY oportunidades con probabilidad del 100%")
        
        # Procesar datos completos para ver el impacto del filtro
        print(f"\n🔧 Procesando datos completos...")
        df_clean = processor.clean_and_prepare_data(df)
        
        print(f"📊 Resultados después del filtrado:")
        print(f"   Registros antes del filtro: {len(df_with_prob)}")
        print(f"   Registros después del filtro: {len(df_clean)}")
        print(f"   Registros excluidos: {len(df_with_prob) - len(df_clean)}")
        
        # Generar resumen
        summary = processor.get_processing_summary(df_with_prob, df_clean)
        print(f"   Excluidos por 100%: {summary.get('excluded_100_percent', 0)}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_100_percent_in_real_file()
