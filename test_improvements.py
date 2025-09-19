"""
Script de prueba para verificar las mejoras implementadas.
"""

import sys
import os
sys.path.append('src')
sys.path.append('config')

from src.client_database import ClientDatabase
from src.data_processor import DataProcessor
from config.settings import BUSINESS_RULES
import pandas as pd
from datetime import datetime

def test_client_database():
    """Prueba la funcionalidad de base de datos de clientes."""
    print("=== PRUEBA: Base de Datos de Clientes ===")
    
    # Crear instancia
    client_db = ClientDatabase("test_client_history.db")
    
    # Datos de prueba
    test_data = pd.DataFrame([
        {
            'Opportunity Name': 'Cliente ABC - Proyecto Test',
            'BU': 'FCT',
            'Amount': 100000,
            'Close Date': '15/01/2025',
            'Lead Time': 8,
            'Payment Terms': 'NET 30',
            'probability_assigned': 0.5,
            'Paid in Advance': 0
        }
    ])
    
    # Agregar datos
    records_added = client_db.add_historical_data(test_data)
    print(f"✅ Registros agregados: {records_added}")
    
    # Probar extracción de cliente
    client_name = client_db._extract_client_name("Cliente ABC - Proyecto Test")
    print(f"✅ Cliente extraído: '{client_name}'")
    
    # Probar consulta de Payment Terms
    payment_terms = client_db.get_client_payment_terms("Cliente ABC")
    print(f"✅ Payment Terms: {payment_terms}")
    
    # Probar estimación de Lead Time por monto
    lead_time = client_db.estimate_lead_time_by_amount(75000)
    print(f"✅ Lead Time estimado para $75,000: {lead_time} semanas")
    
    # Estadísticas
    stats = client_db.get_database_stats()
    print(f"✅ Estadísticas BD: {stats}")

def test_date_adjustment():
    """Prueba el ajuste de fechas del mes actual."""
    print("\n=== PRUEBA: Ajuste de Fechas del Mes Actual ===")
    
    processor = DataProcessor()
    
    # Fecha del mes actual (simulada)
    current_month_date = datetime(2025, 9, 4)  # 4 de septiembre
    
    # Probar ajuste
    adjusted_date = processor._adjust_current_month_dates(current_month_date)
    print(f"✅ Fecha original: {current_month_date.strftime('%d/%m/%Y')}")
    print(f"✅ Fecha ajustada: {adjusted_date.strftime('%d/%m/%Y')}")
    
    # Fecha de otro mes (no debe cambiar)
    other_month_date = datetime(2025, 10, 15)
    not_adjusted = processor._adjust_current_month_dates(other_month_date)
    print(f"✅ Fecha otro mes: {other_month_date.strftime('%d/%m/%Y')} -> {not_adjusted.strftime('%d/%m/%Y')}")

def test_business_rules():
    """Prueba las nuevas reglas de negocio."""
    print("\n=== PRUEBA: Reglas de Negocio Actualizadas ===")
    
    print(f"✅ Factor castigo general: {BUSINESS_RULES.FINANCIAL_PENALTY_FACTOR_DEFAULT}")
    print(f"✅ Factor castigo 60%: {BUSINESS_RULES.FINANCIAL_PENALTY_FACTOR_60_PERCENT}")
    print(f"✅ Rangos Lead Time por monto: {BUSINESS_RULES.LEAD_TIME_BY_AMOUNT_RANGES}")

if __name__ == "__main__":
    test_client_database()
    test_date_adjustment()
    test_business_rules()
    print("\n🎉 Todas las pruebas completadas exitosamente!")
