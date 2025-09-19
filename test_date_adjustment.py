"""
Script de prueba para validar el nuevo ajuste de fechas pasadas.
"""

import sys
import os
sys.path.append('src')
sys.path.append('config')

from src.data_processor import DataProcessor
from datetime import datetime
import pandas as pd

def test_date_adjustment():
    """Prueba el ajuste de fechas pasadas."""
    print("=== PRUEBA: Ajuste de Fechas Pasadas ===")
    
    processor = DataProcessor()
    
    # Simular fecha actual: 18 de septiembre de 2025
    current_date = datetime.now()
    print(f"📅 Fecha actual simulada: {current_date.strftime('%d/%m/%Y')}")
    
    # Casos de prueba
    test_cases = [
        datetime(2025, 5, 5),    # 05/05/2025 - Fecha pasada (mayo)
        datetime(2025, 9, 16),   # 16/09/2025 - Fecha pasada (mismo mes)
        datetime(2025, 9, 18),   # 18/09/2025 - Fecha actual
        datetime(2025, 10, 15),  # 15/10/2025 - Fecha futura
        datetime(2024, 12, 20),  # 20/12/2024 - Fecha pasada (año anterior)
    ]
    
    print("\n🔧 Probando ajustes de fechas:")
    
    for i, test_date in enumerate(test_cases, 1):
        adjusted_date = processor._adjust_current_month_dates(test_date)
        
        status = "📅 AJUSTADA" if adjusted_date != test_date else "✅ SIN CAMBIO"
        
        print(f"Caso {i}: {test_date.strftime('%d/%m/%Y')} → {adjusted_date.strftime('%d/%m/%Y')} {status}")
        
        # Validar lógica
        if test_date.date() < current_date.date():
            # Debe ajustarse al último día del mes actual
            import calendar
            last_day = calendar.monthrange(current_date.year, current_date.month)[1]
            expected_date = current_date.replace(day=last_day)
            
            if adjusted_date.date() == expected_date.date():
                print(f"   ✅ Correcto: Fecha pasada ajustada al último día del mes actual")
            else:
                print(f"   ❌ Error: Esperado {expected_date.strftime('%d/%m/%Y')}, obtenido {adjusted_date.strftime('%d/%m/%Y')}")
        else:
            # No debe cambiar
            if adjusted_date == test_date:
                print(f"   ✅ Correcto: Fecha futura/actual sin cambios")
            else:
                print(f"   ❌ Error: Fecha futura no debería cambiar")

def test_with_dataframe():
    """Prueba con un DataFrame completo."""
    print("\n=== PRUEBA: DataFrame Completo ===")
    
    processor = DataProcessor()
    
    # Crear DataFrame de prueba
    test_data = pd.DataFrame({
        'Close Date': [
            '05/05/2025',  # Fecha pasada
            '16/09/2025',  # Fecha pasada (mismo mes)
            '25/10/2025',  # Fecha futura
            '20/12/2024'   # Fecha pasada (año anterior)
        ],
        'Opportunity Name': ['Proyecto A', 'Proyecto B', 'Proyecto C', 'Proyecto D']
    })
    
    print("📊 Datos originales:")
    for i, row in test_data.iterrows():
        print(f"   {row['Opportunity Name']}: {row['Close Date']}")
    
    # Procesar fechas
    df_processed = processor._convert_dates(test_data)
    
    print("\n📊 Fechas procesadas:")
    for i, row in df_processed.iterrows():
        original = test_data.loc[i, 'Close Date']
        processed = row['close_date_parsed'].strftime('%d/%m/%Y')
        status = "📅 AJUSTADA" if original != processed else "✅ SIN CAMBIO"
        print(f"   {row['Opportunity Name']}: {original} → {processed} {status}")

if __name__ == "__main__":
    test_date_adjustment()
    test_with_dataframe()
    print("\n🎉 Pruebas de ajuste de fechas completadas!")
