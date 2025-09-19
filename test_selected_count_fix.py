"""
Script para validar la corrección del atributo selected_count.
"""

import sys
import os
sys.path.append('src')
sys.path.append('config')

from src.grid_utils import GridResponseHandler

def test_selected_count_attribute():
    """Prueba que el atributo selected_count funcione correctamente."""
    print("=== PRUEBA: Atributo selected_count ===")
    
    # Caso 1: Sin selección
    grid_response_no_selection = {
        'data': [{'A': 1}, {'B': 2}],
        'selected_rows': []
    }
    
    handler = GridResponseHandler(grid_response_no_selection)
    print(f"Sin selección:")
    print(f"   selected_rows_count: {handler.selected_rows_count}")
    print(f"   selected_count: {handler.selected_count}")
    print(f"   has_selection: {handler.has_selection}")
    
    # Caso 2: Con selección
    grid_response_with_selection = {
        'data': [{'A': 1}, {'B': 2}, {'C': 3}],
        'selected_rows': [{'A': 1}, {'B': 2}]
    }
    
    handler2 = GridResponseHandler(grid_response_with_selection)
    print(f"\nCon selección:")
    print(f"   selected_rows_count: {handler2.selected_rows_count}")
    print(f"   selected_count: {handler2.selected_count}")
    print(f"   has_selection: {handler2.has_selection}")
    
    # Caso 3: Grid response nulo
    handler3 = GridResponseHandler(None)
    print(f"\nGrid response nulo:")
    print(f"   selected_rows_count: {handler3.selected_rows_count}")
    print(f"   selected_count: {handler3.selected_count}")
    print(f"   has_selection: {handler3.has_selection}")
    
    # Verificar que ambos atributos retornan lo mismo
    assert handler.selected_count == handler.selected_rows_count
    assert handler2.selected_count == handler2.selected_rows_count
    assert handler3.selected_count == handler3.selected_rows_count
    
    print(f"\n✅ Todos los atributos funcionan correctamente")
    return True

if __name__ == "__main__":
    print("🧪 VALIDACIÓN DE ATRIBUTO selected_count")
    print("=" * 50)
    
    try:
        test_selected_count_attribute()
        print("\n🎉 CORRECCIÓN VALIDADA EXITOSAMENTE")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
