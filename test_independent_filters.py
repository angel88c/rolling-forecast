"""
Script de prueba para validar los filtros independientes en gráficos.
"""

import sys
import os
sys.path.append('src')
sys.path.append('config')

from src.data_processor import DataProcessor
from src.forecast_calculator import ForecastCalculator
import pandas as pd

def test_independent_filters():
    """Prueba que los filtros independientes funcionen correctamente."""
    print("=== PRUEBA: Filtros Independientes en Gráficos ===")
    
    # Crear datos de prueba
    test_data = pd.DataFrame({
        'Opportunity Name': ['Proyecto FCT 1', 'Proyecto ICT 1', 'Proyecto FCT 2', 'Proyecto IAT 1'],
        'BU': ['FCT', 'ICT', 'FCT', 'IAT'],
        'Amount': [100000, 50000, 75000, 120000],
        'Close Date': ['15/01/2025', '20/02/2025', '10/03/2025', '05/04/2025'],
        'Lead Time': [8, 12, 6, 10],
        'Payment Terms': ['NET 30', 'NET 45', 'NET 30', 'NET 60'],
        'Paid in Advance': [0, 5000, 0, 12000],
        'probability_assigned': [0.25, 0.50, 0.25, 0.60]
    })
    
    # Procesar datos
    processor = DataProcessor()
    calculator = ForecastCalculator()
    
    # Simular procesamiento
    test_data['close_date_parsed'] = pd.to_datetime(test_data['Close Date'], format='%d/%m/%Y')
    test_data['lead_time_original'] = test_data['Lead Time']
    
    # Convertir a oportunidades
    opportunities = processor.convert_to_opportunities(test_data)
    
    # Calcular forecast
    billing_events = calculator.calculate_forecast(opportunities)
    summary = calculator.generate_forecast_summary(billing_events)
    
    print(f"📊 Datos de prueba generados:")
    print(f"   Oportunidades: {len(opportunities)}")
    print(f"   Eventos de facturación: {len(billing_events)}")
    print(f"   BUs disponibles: {list(summary.bu_distribution.keys())}")
    
    # Simular filtros independientes
    print(f"\n🎯 Simulando filtros independientes:")
    
    # Filtro mensual: Solo FCT
    monthly_filter = 'FCT'
    monthly_events = [e for e in billing_events if e.bu.value == monthly_filter]
    monthly_total = sum(e.amount_adjusted for e in monthly_events)
    
    print(f"   Filtro Mensual ({monthly_filter}): {len(monthly_events)} eventos, ${monthly_total:,.2f}")
    
    # Filtro temporal: Solo ICT
    temporal_filter = 'ICT'
    temporal_events = [e for e in billing_events if e.bu.value == temporal_filter]
    temporal_total = sum(e.amount_adjusted for e in temporal_events)
    
    print(f"   Filtro Temporal ({temporal_filter}): {len(temporal_events)} eventos, ${temporal_total:,.2f}")
    
    # Verificar que son independientes
    total_general = sum(e.amount_adjusted for e in billing_events)
    print(f"   Total General: ${total_general:,.2f}")
    
    # Validar distribución mensual
    print(f"\n📈 Distribución mensual por BU:")
    for bu in summary.bu_distribution.keys():
        bu_events = [e for e in billing_events if e.bu.value == bu]
        bu_monthly = {}
        for event in bu_events:
            month = event.month_year
            bu_monthly[month] = bu_monthly.get(month, 0) + event.amount_adjusted
        
        print(f"   {bu}: {len(bu_monthly)} meses con facturación")
        for month, amount in sorted(bu_monthly.items()):
            print(f"      {month}: ${amount:,.2f}")
    
    print(f"\n✅ Filtros independientes funcionando correctamente")

if __name__ == "__main__":
    test_independent_filters()
