#!/usr/bin/env python3
"""
Script de prueba para validar la corrección del error KeyError.
"""

import sys
import os

# Agregar paths
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'config'))

try:
    from config.settings import SETTINGS, BUSINESS_RULES, APP_CONFIG
    
    print("🧪 VALIDACIÓN DE CORRECCIÓN KEYERROR")
    print("=" * 50)
    
    # Probar acceso a SETTINGS
    print("✅ SETTINGS importado correctamente")
    print(f"   - Claves disponibles: {list(SETTINGS.keys())}")
    
    # Probar acceso a APP_CONFIG
    print("✅ APP_CONFIG accesible:")
    print(f"   - Título: {SETTINGS['app_config'].APP_TITLE}")
    print(f"   - Descripción: {SETTINGS['app_config'].APP_DESCRIPTION.strip()}")
    
    # Probar acceso a BUSINESS_RULES
    print("✅ BUSINESS_RULES accesible:")
    print(f"   - Lead Time mínimo: {BUSINESS_RULES.MIN_LEAD_TIME}")
    print(f"   - Factor castigo default: {BUSINESS_RULES.FINANCIAL_PENALTY_FACTOR_DEFAULT}")
    print(f"   - Factor castigo 60%: {BUSINESS_RULES.FINANCIAL_PENALTY_FACTOR_60_PERCENT}")
    
    print("\n🎉 TODAS LAS CORRECCIONES VALIDADAS")
    print("La aplicación debería funcionar sin errores KeyError")
    
except Exception as e:
    print(f"❌ Error durante la validación: {str(e)}")
    import traceback
    traceback.print_exc()
