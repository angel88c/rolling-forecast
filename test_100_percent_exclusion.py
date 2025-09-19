"""
Script de prueba para validar la exclusión de oportunidades con probabilidad del 100%.
"""

import sys
import os
sys.path.append('src')
sys.path.append('config')

from src.data_processor import DataProcessor
import pandas as pd

def test_100_percent_exclusion():
    """Prueba la exclusión de oportunidades con probabilidad del 100%."""
    print("=== PRUEBA: Exclusión de Probabilidades del 100% ===")
    
    processor = DataProcessor()
    
    # Crear DataFrame de prueba con diferentes probabilidades
    test_data = pd.DataFrame({
        'Opportunity Name': ['Proyecto A', 'Proyecto B', 'Proyecto C', 'Proyecto D', 'Proyecto E'],
        'BU': ['FCT', 'ICT', 'FCT', 'IAT', 'FCT'],
        'Amount': [100000, 50000, 75000, 120000, 80000],
        'Close Date': ['15/01/2025', '20/02/2025', '10/03/2025', '05/04/2025', '25/05/2025'],
        'Lead Time': [8, 12, 6, 10, 14],
        'Payment Terms': ['NET 30', 'NET 45', 'NET 30', 'NET 60', 'NET 30'],
        'Paid in Advance': [0, 5000, 0, 12000, 0],
        'probability_assigned': [0.25, 0.50, 1.00, 0.60, 1.00]  # Dos con 100%
    })
    
    print("📊 Datos de prueba:")
    for i, row in test_data.iterrows():
        prob_str = f"{row['probability_assigned']:.0%}"
        status = "❌ EXCLUIR" if row['probability_assigned'] == 1.0 else "✅ INCLUIR"
        print(f"   {row['Opportunity Name']}: {prob_str} - {status}")
    
    # Simular el procesamiento completo
    print("\n🔧 Procesando datos...")
    
    # Agregar fechas parseadas (simulando el procesamiento real)
    test_data['close_date_parsed'] = pd.to_datetime(test_data['Close Date'], format='%d/%m/%Y')
    test_data['lead_time_original'] = test_data['Lead Time']
    
    # Aplicar filtro
    df_filtered = processor._filter_valid_records(test_data)
    
    print(f"\n📊 Resultados del filtrado:")
    print(f"   Registros originales: {len(test_data)}")
    print(f"   Registros válidos: {len(df_filtered)}")
    print(f"   Registros excluidos: {len(test_data) - len(df_filtered)}")
    
    # Verificar que se excluyeron las probabilidades del 100%
    excluded_100_percent = test_data[test_data['probability_assigned'] == 1.0]
    included_projects = df_filtered['Opportunity Name'].tolist()
    
    print(f"\n✅ Proyectos incluidos en el forecast:")
    for project in included_projects:
        prob = test_data[test_data['Opportunity Name'] == project]['probability_assigned'].iloc[0]
        print(f"   • {project}: {prob:.0%}")
    
    print(f"\n❌ Proyectos excluidos (100%):")
    for i, row in excluded_100_percent.iterrows():
        print(f"   • {row['Opportunity Name']}: {row['probability_assigned']:.0%}")
    
    # Validar que la lógica es correcta
    expected_excluded = len(excluded_100_percent)
    actual_excluded = len(test_data) - len(df_filtered)
    
    if expected_excluded == actual_excluded:
        print(f"\n✅ PRUEBA EXITOSA: Se excluyeron correctamente {expected_excluded} oportunidades con 100%")
    else:
        print(f"\n❌ ERROR: Esperado {expected_excluded} exclusiones, obtenido {actual_excluded}")

def test_processing_summary():
    """Prueba que el resumen incluya las estadísticas de exclusión."""
    print("\n=== PRUEBA: Resumen de Procesamiento ===")
    
    processor = DataProcessor()
    
    # Datos originales con probabilidades del 100%
    original_data = pd.DataFrame({
        'Opportunity Name': ['A', 'B', 'C', 'D'],
        'probability_assigned': [0.25, 1.00, 0.50, 1.00]
    })
    
    # Datos procesados (sin las del 100%)
    clean_data = pd.DataFrame({
        'Opportunity Name': ['A', 'C'],
        'probability_assigned': [0.25, 0.50],
        'BU': ['FCT', 'ICT'],
        'close_date_parsed': [pd.Timestamp('2025-01-15'), pd.Timestamp('2025-02-20')],
        'lead_time_original': [8, 6]
    })
    
    # Generar resumen
    summary = processor.get_processing_summary(original_data, clean_data)
    
    print(f"📊 Resumen generado:")
    print(f"   Registros originales: {summary['original_records']}")
    print(f"   Registros válidos: {summary['valid_records']}")
    print(f"   Excluidos (100%): {summary['excluded_100_percent']}")
    print(f"   Tasa de éxito: {summary['success_rate']:.1%}")
    
    # Validar
    if summary['excluded_100_percent'] == 2:
        print(f"\n✅ RESUMEN CORRECTO: Se reportaron correctamente 2 exclusiones por 100%")
    else:
        print(f"\n❌ ERROR EN RESUMEN: Esperado 2 exclusiones, reportado {summary['excluded_100_percent']}")

if __name__ == "__main__":
    test_100_percent_exclusion()
    test_processing_summary()
    print("\n🎉 Pruebas de exclusión del 100% completadas!")
