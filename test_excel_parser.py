"""
Script de prueba para el nuevo sistema de parsing de Excel.
"""

import sys
import os
sys.path.append('src')
sys.path.append('config')

from src.excel_parser import ExcelParser
import pandas as pd
import io

def test_column_mapping():
    """Prueba el mapeo de columnas."""
    print("=== PRUEBA: Mapeo de Columnas ===")
    
    parser = ExcelParser()
    
    # Crear DataFrame de prueba con nombres alternativos
    test_data = {
        'Nombre Proyecto': ['Proyecto A', 'Proyecto B'],
        'Unidad Negocio': ['FCT', 'ICT'],
        'Monto': [100000, 50000],
        'Fecha Cierre': ['15/01/2025', '20/02/2025'],
        'Tiempo Entrega': [8, 12],
        'Terminos Pago': ['NET 30', 'NET 45'],
        'Probabilidad': [0.5, 0.25],
        'Calculated PIA': [0.15, 0]  # Como porcentaje
    }
    
    df_test = pd.DataFrame(test_data)
    print(f"✅ Columnas originales: {list(df_test.columns)}")
    
    # Normalizar columnas
    df_normalized = parser.normalize_column_names(df_test)
    print(f"✅ Columnas normalizadas: {list(df_normalized.columns)}")
    
    # Verificar normalización de PIA
    print(f"✅ Valores PIA originales: {df_test['Calculated PIA'].tolist()}")
    if 'Paid in Advance' in df_normalized.columns:
        print(f"✅ Valores PIA normalizados: {df_normalized['Paid in Advance'].tolist()}")

def test_header_detection():
    """Prueba la detección automática de headers."""
    print("\n=== PRUEBA: Detección de Headers ===")
    
    parser = ExcelParser()
    
    # Simular archivo con headers en diferentes filas
    test_data_rows = [
        ['', '', '', ''],  # Fila 0: vacía
        ['Reporte de Oportunidades', '', '', ''],  # Fila 1: título
        ['Fecha: 2025-09-18', '', '', ''],  # Fila 2: metadata
        ['', '', '', ''],  # Fila 3: vacía
        ['Opportunity Name', 'BU', 'Amount', 'Close Date'],  # Fila 4: headers reales
        ['Proyecto A', 'FCT', 100000, '15/01/2025'],  # Fila 5: datos
        ['Proyecto B', 'ICT', 50000, '20/02/2025']   # Fila 6: datos
    ]
    
    # Crear DataFrame simulando el archivo
    df_full = pd.DataFrame(test_data_rows)
    
    # Simular detección (normalmente se haría con archivo real)
    for row_idx in range(5):
        try:
            df_test = pd.DataFrame(test_data_rows[row_idx:], 
                                 columns=test_data_rows[row_idx] if row_idx < len(test_data_rows) else None)
            score = parser._calculate_header_score(df_test.columns.tolist() if hasattr(df_test, 'columns') else [])
            print(f"✅ Fila {row_idx}: Score = {score:.2f}")
        except:
            print(f"❌ Fila {row_idx}: Error al procesar")

def test_pia_normalization():
    """Prueba la normalización de valores PIA."""
    print("\n=== PRUEBA: Normalización de PIA ===")
    
    parser = ExcelParser()
    
    # Caso 1: PIA como porcentajes (0-100)
    df_percent = pd.DataFrame({
        'Amount': [100000, 50000, 75000],
        'Paid in Advance': [15, 0, 20]  # 15%, 0%, 20%
    })
    
    print("Caso 1 - PIA como porcentajes (15, 0, 20):")
    df_norm1 = parser._normalize_pia_values(df_percent)
    print(f"✅ Valores normalizados: {df_norm1['Paid in Advance'].tolist()}")
    
    # Caso 2: PIA como decimales (0-1)
    df_decimal = pd.DataFrame({
        'Amount': [100000, 50000, 75000],
        'Paid in Advance': [0.15, 0, 0.20]  # 15%, 0%, 20%
    })
    
    print("\nCaso 2 - PIA como decimales (0.15, 0, 0.20):")
    df_norm2 = parser._normalize_pia_values(df_decimal)
    print(f"✅ Valores normalizados: {df_norm2['Paid in Advance'].tolist()}")
    
    # Caso 3: PIA ya como montos
    df_amounts = pd.DataFrame({
        'Amount': [100000, 50000, 75000],
        'Paid in Advance': [15000, 0, 15000]  # Ya en montos
    })
    
    print("\nCaso 3 - PIA como montos (15000, 0, 15000):")
    df_norm3 = parser._normalize_pia_values(df_amounts)
    print(f"✅ Valores normalizados: {df_norm3['Paid in Advance'].tolist()}")

if __name__ == "__main__":
    test_column_mapping()
    test_header_detection()
    test_pia_normalization()
    print("\n🎉 Todas las pruebas de parsing completadas!")
