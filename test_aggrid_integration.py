"""
Script de prueba para validar la integración de AG-Grid.
"""

import sys
import os
sys.path.append('src')
sys.path.append('config')

from src.aggrid_utils import AGGridConfigurator, GRID_CONFIGS
import pandas as pd

def test_aggrid_configuration():
    """Prueba las configuraciones de AG-Grid."""
    print("=== PRUEBA: Configuración AG-Grid ===")
    
    # Crear datos de prueba para forecast
    forecast_data = pd.DataFrame({
        'Proyecto': ['Proyecto A (FCT)', 'Proyecto B (ICT)', 'Proyecto C (IAT)'],
        'BU': ['FCT', 'ICT', 'IAT'],
        'Enero 2025': [10000, 0, 5000],
        'Febrero 2025': [0, 15000, 0],
        'Marzo 2025': [5000, 0, 8000]
    })
    
    print(f"📊 Datos de prueba forecast:")
    print(f"   Filas: {len(forecast_data)}")
    print(f"   Columnas: {list(forecast_data.columns)}")
    
    # Configurar AG-Grid para forecast
    gb_forecast = AGGridConfigurator.configure_forecast_table(forecast_data)
    
    print(f"✅ Configuración forecast creada exitosamente")
    
    # Crear datos de prueba para detalles
    details_data = pd.DataFrame({
        'Proyecto': ['Proyecto A', 'Proyecto A', 'Proyecto B'],
        'BU': ['FCT', 'FCT', 'ICT'],
        'Etapa': ['INICIO', 'DR', 'INICIO'],
        'Fecha': ['15/01/2025', '15/02/2025', '20/02/2025'],
        'Mes': ['Enero 2025', 'Febrero 2025', 'Febrero 2025'],
        'Monto Original': [30000, 30000, 50000],
        'Monto Ajustado': [3000, 3000, 10000],
        'Probabilidad': [0.25, 0.25, 0.50],
        'Lead Time': '8.0 sem'
    })
    
    print(f"\n📋 Datos de prueba detalles:")
    print(f"   Filas: {len(details_data)}")
    print(f"   Columnas: {list(details_data.columns)}")
    
    # Configurar AG-Grid para detalles
    gb_details = AGGridConfigurator.configure_details_table(details_data)
    
    print(f"✅ Configuración detalles creada exitosamente")
    
    # Probar configuraciones predefinidas
    print(f"\n🔧 Configuraciones predefinidas:")
    for config_name, config in GRID_CONFIGS.items():
        print(f"   {config_name}: {config['theme']}, altura={config['height']}")
    
    # Probar cálculo de altura
    height_small = AGGridConfigurator.get_grid_height(5)
    height_large = AGGridConfigurator.get_grid_height(100)
    
    print(f"\n📏 Cálculo de alturas:")
    print(f"   5 filas: {height_small}px")
    print(f"   100 filas: {height_large}px")
    
    print(f"\n✅ Todas las configuraciones AG-Grid funcionan correctamente")

if __name__ == "__main__":
    test_aggrid_configuration()
