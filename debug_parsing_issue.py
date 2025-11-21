"""
Script de diagnóstico detallado para identificar proyectos excluidos.

Analiza cada condición de filtrado y muestra qué proyectos no cumplen.
"""

import sys
import os
sys.path.append('src')
sys.path.append('config')

from src.data_processor import DataProcessor
from src.extract_projects import extract_projects_from_pipeline
import pandas as pd
import logging

# Configurar logging silencioso
logging.basicConfig(level=logging.WARNING)

def analyze_exclusions(file_path: str):
    """
    Analiza detalladamente qué proyectos se excluyen y por qué.
    """
    print("\n" + "="*80)
    print("ANÁLISIS DETALLADO DE PROYECTOS EXCLUIDOS")
    print("="*80 + "\n")
    
    if not os.path.exists(file_path):
        print(f"❌ Error: No se encontró el archivo: {file_path}")
        return
    
    try:
        # Leer datos sin procesar
        print("📖 Leyendo Excel...")
        processor = DataProcessor()
        df_parsed, _ = processor.read_excel_file(file_path)
        
        print(f"✅ Total registros leídos del Excel: {len(df_parsed)}\n")
        
        # Completar datos faltantes
        df_completed = processor._complete_missing_data(df_parsed)
        
        # Crear DataFrame con análisis de cada condición
        exclusions = []
        
        for idx, row in df_completed.iterrows():
            project_name = row.get('Opportunity Name', 'N/A')
            reasons = []
            
            # Verificar cada condición
            if pd.isna(row.get('Lead Time')):
                reasons.append("Lead Time faltante")
            
            if pd.isna(row.get('Payment Terms')):
                reasons.append("Payment Terms faltante")
            
            if pd.isna(row.get('Opportunity Name')):
                reasons.append("Nombre de proyecto faltante")
            
            if pd.isna(row.get('Amount')) or row.get('Amount', 0) <= 0:
                reasons.append("Amount inválido o ≤ 0")
            
            bu_value = row.get('BU')
            if pd.isna(bu_value) or str(bu_value).strip() == '' or str(bu_value).upper() == 'NAN':
                reasons.append(f"BU inválido: '{bu_value}'")
            
            if pd.isna(row.get('close_date_parsed')):
                reasons.append("Close Date inválida")
            
            if pd.isna(row.get('probability_assigned')):
                reasons.append("Probabilidad no asignada")
            
            if row.get('probability_assigned', 0) >= 1.0:
                reasons.append("Probabilidad = 100% (ya ganado)")
            
            if reasons:
                exclusions.append({
                    'Proyecto': project_name,
                    'BU': bu_value,
                    'Amount': row.get('Amount', 0),
                    'Razones': ' | '.join(reasons)
                })
        
        # Mostrar resumen
        print(f"📊 RESUMEN:")
        print(f"   • Total proyectos en Excel: {len(df_completed)}")
        print(f"   • Proyectos excluidos: {len(exclusions)}")
        print(f"   • Proyectos que pasarán el filtro: {len(df_completed) - len(exclusions)}\n")
        
        if exclusions:
            print("="*80)
            print("PROYECTOS EXCLUIDOS (con razones)")
            print("="*80 + "\n")
            
            # Agrupar por razón
            reason_counts = {}
            for exc in exclusions:
                for reason in exc['Razones'].split(' | '):
                    reason_counts[reason] = reason_counts.get(reason, 0) + 1
            
            print("📋 Razones de exclusión (pueden haber múltiples por proyecto):")
            for reason, count in sorted(reason_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"   • {reason}: {count} proyectos")
            
            print(f"\n{'='*80}")
            print("LISTA DETALLADA DE PROYECTOS EXCLUIDOS")
            print(f"{'='*80}\n")
            
            for i, exc in enumerate(exclusions, 1):
                print(f"{i}. {exc['Proyecto']}")
                print(f"   BU: {exc['BU']}")
                print(f"   Amount: ${exc['Amount']:,.2f}" if isinstance(exc['Amount'], (int, float)) else f"   Amount: {exc['Amount']}")
                print(f"   ❌ Razones: {exc['Razones']}")
                print()
        else:
            print("✅ No hay proyectos excluidos. Todos cumplen las condiciones.\n")
        
    except Exception as e:
        print(f"❌ Error durante el procesamiento: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import glob
    
    # Buscar archivos Excel en la carpeta data
    excel_files = glob.glob("data/*.xlsx")
    
    if not excel_files:
        print("❌ No se encontraron archivos Excel en la carpeta 'data/'")
        sys.exit(1)
    
    # Usar el primer archivo que NO sea de KPIs
    file_path = None
    for f in excel_files:
        if 'KPI' not in f and 'kpi' not in f.lower():
            file_path = f
            break
    
    if not file_path:
        file_path = excel_files[0]
    
    print(f"\n📁 Archivo: {file_path}")
    analyze_exclusions(file_path)
