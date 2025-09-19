"""
Script de prueba para validar la corrección del error de DataFrame.
"""

import sys
import os
sys.path.append('src')
sys.path.append('config')

import pandas as pd
from src.grid_utils import GridResponseHandler, get_grid_stats

def test_dataframe_ambiguity():
    """Prueba la corrección del error de ambigüedad de DataFrame."""
    print("=== PRUEBA: Corrección de DataFrame Ambiguity ===")
    
    # Caso 1: grid_response con datos vacíos
    print("\n1. Probando con datos vacíos")
    grid_response_empty = {
        'data': [],
        'selected_rows': []
    }
    
    try:
        handler = GridResponseHandler(grid_response_empty)
        print(f"   ✅ has_data: {handler.has_data}")
        print(f"   ✅ data_df shape: {handler.data_df.shape}")
        print(f"   ✅ selected_df shape: {handler.selected_df.shape}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False
    
    # Caso 2: grid_response con datos válidos
    print("\n2. Probando con datos válidos")
    grid_response_with_data = {
        'data': [
            {'Proyecto': 'A', 'BU': 'FCT', 'Enero': 1000},
            {'Proyecto': 'B', 'BU': 'ICT', 'Enero': 2000}
        ],
        'selected_rows': [
            {'Proyecto': 'A', 'BU': 'FCT', 'Enero': 1000}
        ]
    }
    
    try:
        handler = GridResponseHandler(grid_response_with_data)
        print(f"   ✅ has_data: {handler.has_data}")
        print(f"   ✅ has_selection: {handler.has_selection}")
        print(f"   ✅ data_df shape: {handler.data_df.shape}")
        print(f"   ✅ selected_df shape: {handler.selected_df.shape}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False
    
    # Caso 3: grid_response = None
    print("\n3. Probando con grid_response = None")
    try:
        handler = GridResponseHandler(None)
        print(f"   ✅ has_data: {handler.has_data}")
        print(f"   ✅ data_df shape: {handler.data_df.shape}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False
    
    # Caso 4: Probar función get_grid_stats directamente
    print("\n4. Probando get_grid_stats directamente")
    try:
        stats_empty = get_grid_stats(grid_response_empty)
        print(f"   ✅ Stats vacío: has_data={stats_empty['has_data']}")
        
        stats_with_data = get_grid_stats(grid_response_with_data)
        print(f"   ✅ Stats con datos: has_data={stats_with_data['has_data']}")
        
        stats_none = get_grid_stats(None)
        print(f"   ✅ Stats None: has_data={stats_none['has_data']}")
    except Exception as e:
        print(f"   ❌ Error en get_grid_stats: {str(e)}")
        return False
    
    print(f"\n✅ Todas las pruebas de DataFrame pasaron correctamente")
    return True

def test_export_functionality():
    """Prueba la funcionalidad de exportación."""
    print("\n=== PRUEBA: Funcionalidad de Exportación ===")
    
    grid_response = {
        'data': [
            {'Proyecto': 'A', 'BU': 'FCT', 'Enero': 1000},
            {'Proyecto': 'B', 'BU': 'ICT', 'Enero': 2000}
        ],
        'selected_rows': [
            {'Proyecto': 'A', 'BU': 'FCT', 'Enero': 1000}
        ]
    }
    
    try:
        handler = GridResponseHandler(grid_response)
        
        # Probar exportación de datos
        csv_data = handler.export_data("csv")
        print(f"   ✅ CSV data exportado: {len(csv_data)} bytes")
        
        # Probar exportación de selección
        csv_selected = handler.export_selected("csv")
        print(f"   ✅ CSV selección exportado: {len(csv_selected)} bytes")
        
        return True
    except Exception as e:
        print(f"   ❌ Error en exportación: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 VALIDACIÓN DE CORRECCIÓN DATAFRAME")
    print("=" * 50)
    
    tests = [
        test_dataframe_ambiguity,
        test_export_functionality
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE RESULTADOS:")
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Pruebas pasadas: {passed}/{total}")
    
    if passed == total:
        print("🎉 CORRECCIÓN DE DATAFRAME VALIDADA")
    else:
        print("⚠️ Algunas pruebas fallaron")
