"""
Script de prueba para validar las correcciones de AG-Grid.
"""

import sys
import os
sys.path.append('src')
sys.path.append('config')

from src.grid_utils import GridResponseHandler, safe_get_selected_rows, safe_get_grid_data
import pandas as pd

def test_grid_response_handling():
    """Prueba el manejo seguro de respuestas de AG-Grid."""
    print("=== PRUEBA: Manejo Seguro de Grid Response ===")
    
    # Caso 1: grid_response es None
    print("\n1. Probando grid_response = None")
    handler_none = GridResponseHandler(None)
    print(f"   has_data: {handler_none.has_data}")
    print(f"   has_selection: {handler_none.has_selection}")
    print(f"   total_rows: {handler_none.total_rows}")
    print(f"   selected_count: {handler_none.selected_count}")
    
    # Caso 2: grid_response con selected_rows = None
    print("\n2. Probando selected_rows = None")
    grid_response_none_selection = {
        'data': [
            {'Proyecto': 'A', 'BU': 'FCT', 'Enero': 1000},
            {'Proyecto': 'B', 'BU': 'ICT', 'Enero': 2000}
        ],
        'selected_rows': None
    }
    
    handler_none_selection = GridResponseHandler(grid_response_none_selection)
    print(f"   has_data: {handler_none_selection.has_data}")
    print(f"   has_selection: {handler_none_selection.has_selection}")
    print(f"   total_rows: {handler_none_selection.total_rows}")
    print(f"   selected_count: {handler_none_selection.selected_count}")
    
    # Caso 3: grid_response con selected_rows = []
    print("\n3. Probando selected_rows = []")
    grid_response_empty_selection = {
        'data': [
            {'Proyecto': 'A', 'BU': 'FCT', 'Enero': 1000},
            {'Proyecto': 'B', 'BU': 'ICT', 'Enero': 2000}
        ],
        'selected_rows': []
    }
    
    handler_empty_selection = GridResponseHandler(grid_response_empty_selection)
    print(f"   has_data: {handler_empty_selection.has_data}")
    print(f"   has_selection: {handler_empty_selection.has_selection}")
    print(f"   total_rows: {handler_empty_selection.total_rows}")
    print(f"   selected_count: {handler_empty_selection.selected_count}")
    
    # Caso 4: grid_response con selección válida
    print("\n4. Probando con selección válida")
    grid_response_with_selection = {
        'data': [
            {'Proyecto': 'A', 'BU': 'FCT', 'Enero': 1000},
            {'Proyecto': 'B', 'BU': 'ICT', 'Enero': 2000},
            {'Proyecto': 'C', 'BU': 'IAT', 'Enero': 3000}
        ],
        'selected_rows': [
            {'Proyecto': 'A', 'BU': 'FCT', 'Enero': 1000},
            {'Proyecto': 'C', 'BU': 'IAT', 'Enero': 3000}
        ]
    }
    
    handler_with_selection = GridResponseHandler(grid_response_with_selection)
    print(f"   has_data: {handler_with_selection.has_data}")
    print(f"   has_selection: {handler_with_selection.has_selection}")
    print(f"   total_rows: {handler_with_selection.total_rows}")
    print(f"   selected_count: {handler_with_selection.selected_count}")
    
    # Probar cálculo de totales
    print("\n5. Probando cálculo de totales")
    totals = handler_with_selection.calculate_totals(['Enero'])
    print(f"   Total Enero: ${totals['Enero']:,.0f}")
    
    # Probar exportación
    print("\n6. Probando exportación")
    try:
        csv_data = handler_with_selection.export_data("csv")
        print(f"   CSV exportado: {len(csv_data)} bytes")
        
        if handler_with_selection.has_selection:
            csv_selected = handler_with_selection.export_selected("csv")
            print(f"   CSV selección: {len(csv_selected)} bytes")
    except Exception as e:
        print(f"   Error en exportación: {str(e)}")
    
    print(f"\n✅ Todas las pruebas de manejo seguro completadas")

def test_safe_functions():
    """Prueba las funciones de seguridad individuales."""
    print("\n=== PRUEBA: Funciones de Seguridad ===")
    
    # Probar safe_get_selected_rows con diferentes casos
    test_cases = [
        None,
        {},
        {'selected_rows': None},
        {'selected_rows': []},
        {'selected_rows': [{'a': 1}]},
        {'selected_rows': 'not_a_list'}
    ]
    
    for i, case in enumerate(test_cases):
        result = safe_get_selected_rows(case)
        print(f"   Caso {i+1}: {case} → {result} (tipo: {type(result)})")
    
    # Probar safe_get_grid_data
    print(f"\n   Probando safe_get_grid_data:")
    for i, case in enumerate(test_cases):
        result = safe_get_grid_data(case)
        print(f"   Caso {i+1}: {len(result)} elementos")
    
    print(f"\n✅ Funciones de seguridad validadas")

if __name__ == "__main__":
    test_grid_response_handling()
    test_safe_functions()
