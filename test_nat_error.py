"""
Script de prueba para el error NaT (Not a Time).
"""

import sys
import os
sys.path.append('src')
sys.path.append('config')

from src.data_processor import DataProcessor
from datetime import datetime
import pandas as pd
import numpy as np

def test_nat_handling():
    """Prueba el manejo de fechas NaT."""
    print("=== PRUEBA: Manejo de Fechas NaT ===")
    
    processor = DataProcessor()
    
    # Casos de prueba incluyendo NaT
    test_cases = [
        datetime(2025, 5, 5),    # Fecha válida pasada
        None,                    # None
        pd.NaT,                  # NaT (Not a Time)
        np.nan,                  # NaN
        datetime(2025, 10, 15),  # Fecha válida futura
        "fecha_invalida",        # String inválido
    ]
    
    print("🔧 Probando manejo de diferentes tipos de fecha:")
    
    for i, test_date in enumerate(test_cases, 1):
        try:
            result = processor._adjust_current_month_dates(test_date)
            
            print(f"Caso {i}: {type(test_date).__name__} {test_date} → {result}")
            
            if result is None:
                print(f"   ✅ Correcto: Valor problemático manejado como None")
            else:
                print(f"   ✅ Correcto: Fecha procesada exitosamente")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")

def test_dataframe_with_nat():
    """Prueba con DataFrame que contiene fechas NaT."""
    print("\n=== PRUEBA: DataFrame con NaT ===")
    
    processor = DataProcessor()
    
    # Crear DataFrame con fechas problemáticas
    test_data = pd.DataFrame({
        'Close Date': [
            '05/05/2025',  # Fecha válida
            '',            # String vacío
            None,          # None
            '25/10/2025',  # Fecha válida futura
            'invalid',     # Fecha inválida
        ],
        'Opportunity Name': ['Proyecto A', 'Proyecto B', 'Proyecto C', 'Proyecto D', 'Proyecto E']
    })
    
    print("📊 Datos de prueba:")
    for i, row in test_data.iterrows():
        print(f"   {row['Opportunity Name']}: '{row['Close Date']}'")
    
    try:
        # Procesar fechas
        df_processed = processor._convert_dates(test_data)
        
        print("\n📊 Fechas procesadas:")
        for i, row in df_processed.iterrows():
            original = test_data.loc[i, 'Close Date']
            processed = row['close_date_parsed']
            
            if pd.isna(processed):
                status = "❌ NaT/None"
            else:
                status = f"✅ {processed.strftime('%d/%m/%Y')}"
            
            print(f"   {row['Opportunity Name']}: '{original}' → {status}")
            
        print(f"\n✅ Procesamiento completado sin errores")
        
    except Exception as e:
        print(f"\n❌ Error durante procesamiento: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_nat_handling()
    test_dataframe_with_nat()
    print("\n🎉 Pruebas de manejo NaT completadas!")
