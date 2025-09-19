"""
Script de prueba para validar las correcciones finales.
"""

import sys
import os
sys.path.append('src')
sys.path.append('config')

def test_settings_import():
    """Prueba la importación de SETTINGS."""
    print("=== PRUEBA: Importación de SETTINGS ===")
    
    try:
        from config.settings import SETTINGS
        print("✅ SETTINGS importado correctamente")
        
        # Verificar estructura
        expected_keys = ['business_rules', 'excel_config', 'app_config', 'error_messages', 'info_messages']
        for key in expected_keys:
            if key in SETTINGS:
                print(f"✅ {key}: OK")
            else:
                print(f"❌ {key}: FALTANTE")
        
        # Verificar valores específicos
        br = SETTINGS['business_rules']
        print(f"✅ Factor castigo default: {br.FINANCIAL_PENALTY_FACTOR_DEFAULT}")
        print(f"✅ Factor castigo 60%: {br.FINANCIAL_PENALTY_FACTOR_60_PERCENT}")
        
    except ImportError as e:
        print(f"❌ Error al importar SETTINGS: {str(e)}")
        return False
    
    return True

def test_logo_exists():
    """Verifica que el logo existe."""
    print("\n=== PRUEBA: Logo iBtest ===")
    
    logo_path = "logo_ibtest.png"
    if os.path.exists(logo_path):
        print(f"✅ Logo encontrado: {logo_path}")
        
        # Verificar tamaño del archivo
        size = os.path.getsize(logo_path)
        print(f"✅ Tamaño del logo: {size:,} bytes")
        
        return True
    else:
        print(f"❌ Logo no encontrado: {logo_path}")
        return False

def test_grid_utils_import():
    """Prueba la importación de grid_utils."""
    print("\n=== PRUEBA: Grid Utils ===")
    
    try:
        from src.grid_utils import GridResponseHandler, safe_get_selected_rows
        print("✅ GridResponseHandler importado correctamente")
        
        # Prueba básica
        handler = GridResponseHandler(None)
        print(f"✅ Handler con None: has_data={handler.has_data}")
        
        # Prueba función segura
        result = safe_get_selected_rows(None)
        print(f"✅ safe_get_selected_rows(None): {result}")
        
        return True
    except ImportError as e:
        print(f"❌ Error al importar grid_utils: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 VALIDACIÓN FINAL DE CORRECCIONES")
    print("=" * 50)
    
    tests = [
        test_settings_import,
        test_logo_exists,
        test_grid_utils_import
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
        print("🎉 TODAS LAS CORRECCIONES VALIDADAS")
    else:
        print("⚠️ Algunas correcciones necesitan atención")
