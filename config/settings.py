"""
Configuración global de la aplicación de Forecast Financiero.

Este módulo contiene todas las constantes y configuraciones utilizadas
en la aplicación para mantener la consistencia y facilitar el mantenimiento.
"""

from typing import Dict, List
from dataclasses import dataclass


@dataclass
class BusinessRules:
    """Reglas de negocio para el cálculo del forecast."""
    
    # Lead Time mínimo en semanas
    MIN_LEAD_TIME: float = 4.0
    
    # Factores de castigo financiero por probabilidad
    FINANCIAL_PENALTY_FACTOR_DEFAULT: float = 0.40  # Para probabilidades != 60%
    FINANCIAL_PENALTY_FACTOR_60_PERCENT: float = 0.60  # Para probabilidad = 60%
    
    # Días para etapas de BU no-ICT
    DR_DAYS_OFFSET: int = 30
    SAT_DAYS_OFFSET: int = 30
    
    # Porcentajes de facturación para BU no-ICT sin PIA (editables)
    INICIO_PERCENTAGE: float = 0.30
    DR_PERCENTAGE: float = 0.30
    FAT_PERCENTAGE: float = 0.30
    SAT_PERCENTAGE: float = 0.10
    
    # Porcentajes de redistribución para BU no-ICT con PIA
    DR_FAT_SPLIT_PERCENTAGE: float = 0.50
    
    # Reglas para Lead Time faltante (por monto en USD)
    LEAD_TIME_BY_AMOUNT_RANGES: dict = None
    
    def __post_init__(self):
        if self.LEAD_TIME_BY_AMOUNT_RANGES is None:
            self.LEAD_TIME_BY_AMOUNT_RANGES = {
                (0, 50000): 6,      # Proyectos pequeños: 6 semanas
                (50000, 200000): 10, # Proyectos medianos: 10 semanas
                (200000, 500000): 16, # Proyectos grandes: 16 semanas
                (500000, float('inf')): 24  # Proyectos muy grandes: 24 semanas
            }


@dataclass
class ExcelConfig:
    """Configuración para lectura del archivo Excel."""
    
    # Fila donde comienzan los headers (0-indexed)
    HEADER_ROW: int = 12
    
    # Columnas requeridas en el archivo
    REQUIRED_COLUMNS: List[str] = None
    
    def __post_init__(self):
        self.REQUIRED_COLUMNS = [
            'Opportunity Name',
            'BU',
            'Amount',
            'Close Date',
            'Lead Time',
            'Payment Terms',
            'Probability (%)  ↑',
            'Paid in Advance'
        ]


@dataclass
class AppConfig:
    """Configuración general de la aplicación."""
    
    # Título de la aplicación
    APP_TITLE: str = "Forecast Fiscal."
    
    # Descripción
    APP_DESCRIPTION: str = """
    Aplicación para generar proyecciones de ingresos por facturación basadas en 
    el pipeline de oportunidades (C&N Funnel Report).
    """
    
    # Unidades de negocio válidas
    VALID_BUS: List[str] = None
    
    # Formatos de fecha soportados
    SUPPORTED_DATE_FORMATS: List[str] = None
    
    # Tamaño máximo de archivo (MB)
    MAX_FILE_SIZE_MB: int = 50
    
    def __post_init__(self):
        self.VALID_BUS = ['ICT', 'FCT', 'IAT', 'REP', 'SWD']
        self.SUPPORTED_DATE_FORMATS = ['%d/%m/%Y', '%Y-%m-%d', '%m/%d/%Y']


# Instancias globales de configuración
BUSINESS_RULES = BusinessRules()
EXCEL_CONFIG = ExcelConfig()
APP_CONFIG = AppConfig()


# Diccionario de mensajes de error para consistencia
ERROR_MESSAGES: Dict[str, str] = {
    'file_not_found': 'Archivo no encontrado. Por favor, sube un archivo válido.',
    'invalid_format': 'Formato de archivo inválido. Solo se aceptan archivos .xlsx',
    'missing_columns': 'El archivo no contiene las columnas requeridas: {}',
    'no_valid_data': 'No se encontraron datos válidos para procesar.',
    'date_parse_error': 'Error al procesar las fechas. Verifique el formato DD/MM/YYYY',
    'calculation_error': 'Error en el cálculo del forecast. Verifique los datos de entrada.',
    'export_error': 'Error al exportar los resultados. Inténtelo nuevamente.'
}


# Diccionario de mensajes informativos
INFO_MESSAGES: Dict[str, str] = {
    'processing_start': 'Iniciando procesamiento del archivo...',
    'processing_complete': 'Procesamiento completado exitosamente.',
    'data_filtered': 'Datos filtrados: {} registros válidos de {} totales.',
    'forecast_generated': 'Forecast generado: ${:,.2f} en {} eventos de facturación.',
    'export_success': 'Archivo exportado exitosamente.'
}


# Configuración consolidada para importación fácil
SETTINGS = {
    'business_rules': BUSINESS_RULES,
    'excel_config': EXCEL_CONFIG,
    'app_config': APP_CONFIG,
    'error_messages': ERROR_MESSAGES,
    'info_messages': INFO_MESSAGES
}
