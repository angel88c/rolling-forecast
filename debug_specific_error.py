"""
Script para simular el error específico y encontrar la línea problemática.
"""

import sys
import os
sys.path.append('src')
sys.path.append('config')

import pandas as pd
from src.grid_utils import GridResponseHandler, safe_calculate_totals

def test_specific_error():
    """Reproduce el error específico reportado."""
    print("=== REPRODUCIENDO ERROR ESPECÍFICO ===")
    
    # Simular datos que podrían causar el problema
    test_cases = [
        # Caso 1: Lista vacía
        {'data': [], 'selected_rows': []},
        
        # Caso 2: Lista con datos
        {'data': [{'A': 1, 'B': 2}], 'selected_rows': []},
        
        # Caso 3: None
        None,
        
        # Caso 4: DataFrame como data (esto podría ser el problema)
        {'data': pd.DataFrame([{'A': 1, 'B': 2}]), 'selected_rows': []},
    ]
    
    numeric_columns = ['A', 'B', 'Enero', 'Febrero']
    
    for i, grid_response in enumerate(test_cases):
        print(f"\n--- Caso {i+1}: {type(grid_response)} ---")
        
        try:
            if grid_response is None:
                print("   Grid response es None")
                handler = GridResponseHandler(None)
                totals = handler.calculate_totals(numeric_columns)
                print(f"   ✅ Totales: {totals}")
            else:
                print(f"   Data type: {type(grid_response.get('data', 'N/A'))}")
                handler = GridResponseHandler(grid_response)
                totals = handler.calculate_totals(numeric_columns)
                print(f"   ✅ Totales: {totals}")
                
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
            print(f"   Tipo de error: {type(e)}")
            
            # Si es el error que buscamos, investigar más
            if "ambiguous" in str(e):
                print("   🎯 ESTE ES EL ERROR QUE BUSCAMOS!")
                print(f"   Grid response: {grid_response}")
                if grid_response and 'data' in grid_response:
                    print(f"   Data content: {grid_response['data']}")
                    print(f"   Data type: {type(grid_response['data'])}")

def test_safe_calculate_totals_directly():
    """Prueba la función safe_calculate_totals directamente."""
    print("\n=== PROBANDO safe_calculate_totals DIRECTAMENTE ===")
    
    # Casos que podrían causar problemas
    test_responses = [
        None,
        {'data': []},
        {'data': [{'A': 1}]},
        {'data': pd.DataFrame([{'A': 1}])},  # DataFrame como data
    ]
    
    for i, response in enumerate(test_responses):
        print(f"\n--- Prueba directa {i+1} ---")
        try:
            result = safe_calculate_totals(response, ['A', 'B'])
            print(f"   ✅ Resultado: {result}")
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
            if "ambiguous" in str(e):
                print("   🎯 ENCONTRADO EL PROBLEMA!")

if __name__ == "__main__":
    test_specific_error()
    test_safe_calculate_totals_directly()
