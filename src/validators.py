"""
Módulo de validación de datos para la aplicación de Forecast Financiero.

Este módulo contiene todas las funciones de validación para asegurar
la integridad y calidad de los datos de entrada.
"""

import pandas as pd
from datetime import datetime
from typing import List, Optional
import logging

from .models import ValidationResult, BusinessUnit
from config.settings import EXCEL_CONFIG, APP_CONFIG, ERROR_MESSAGES


# Configurar logging
logger = logging.getLogger(__name__)


class DataValidator:
    """
    Clase principal para validación de datos del funnel.
    
    Esta clase encapsula toda la lógica de validación para mantener
    el código organizado y reutilizable.
    """
    
    def __init__(self):
        """Inicializa el validador con configuraciones por defecto."""
        self.required_columns = EXCEL_CONFIG.REQUIRED_COLUMNS
        self.valid_bus = APP_CONFIG.VALID_BUS
        self.date_formats = APP_CONFIG.SUPPORTED_DATE_FORMATS
    
    def validate_file(self, file) -> ValidationResult:
        """
        Valida el archivo subido antes del procesamiento.
        
        Args:
            file: Archivo subido por el usuario
            
        Returns:
            ValidationResult: Resultado de la validación
        """
        result = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[],
            valid_records=0,
            total_records=0
        )
        
        # Validar que el archivo existe
        if file is None:
            result.add_error(ERROR_MESSAGES['file_not_found'])
            return result
        
        # Validar extensión del archivo
        if not file.name.endswith('.xlsx'):
            result.add_error(ERROR_MESSAGES['invalid_format'])
            return result
        
        # Validar tamaño del archivo
        if hasattr(file, 'size') and file.size > APP_CONFIG.MAX_FILE_SIZE_MB * 1024 * 1024:
            result.add_error(f"El archivo es demasiado grande. Máximo permitido: {APP_CONFIG.MAX_FILE_SIZE_MB}MB")
            return result
        
        return result
    
    def validate_dataframe(self, df: pd.DataFrame) -> ValidationResult:
        """
        Valida el DataFrame después de leer el Excel.
        
        Args:
            df: DataFrame con los datos del funnel
            
        Returns:
            ValidationResult: Resultado de la validación
        """
        result = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[],
            valid_records=0,
            total_records=len(df)
        )
        
        # Validar que el DataFrame no esté vacío
        if df.empty:
            result.add_error(ERROR_MESSAGES['no_valid_data'])
            return result
        
        # Validar columnas requeridas
        missing_columns = self._validate_required_columns(df)
        if missing_columns:
            result.add_error(
                ERROR_MESSAGES['missing_columns'].format(', '.join(missing_columns))
            )
            return result
        
        # Validar datos por fila
        valid_rows = 0
        for index, row in df.iterrows():
            row_validation = self._validate_row(row, index)
            
            if row_validation.is_valid:
                valid_rows += 1
            else:
                # Agregar errores específicos de la fila
                for error in row_validation.errors:
                    result.add_warning(f"Fila {index + 1}: {error}")
        
        result.valid_records = valid_rows
        
        # Si no hay registros válidos, es un error crítico
        if valid_rows == 0:
            result.add_error(ERROR_MESSAGES['no_valid_data'])
        elif valid_rows < len(df) * 0.5:  # Menos del 50% válido
            result.add_warning(
                f"Solo {valid_rows} de {len(df)} registros son válidos ({valid_rows/len(df)*100:.1f}%)"
            )
        
        return result
    
    def _validate_required_columns(self, df: pd.DataFrame) -> List[str]:
        """
        Valida que todas las columnas requeridas estén presentes.
        
        Args:
            df: DataFrame a validar
            
        Returns:
            List[str]: Lista de columnas faltantes
        """
        missing_columns = []
        df_columns = df.columns.tolist()
        
        for required_col in self.required_columns:
            if required_col not in df_columns:
                missing_columns.append(required_col)
        
        return missing_columns
    
    def _validate_row(self, row: pd.Series, index: int) -> ValidationResult:
        """
        Valida una fila individual del DataFrame.
        
        Args:
            row: Fila a validar
            index: Índice de la fila
            
        Returns:
            ValidationResult: Resultado de la validación de la fila
        """
        result = ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[],
            valid_records=0,
            total_records=1
        )
        
        # Validar campos obligatorios para procesamiento
        required_for_processing = [
            'Opportunity Name', 'BU', 'Amount', 'Close Date', 
            'Lead Time', 'Payment Terms'
        ]
        
        for field in required_for_processing:
            if pd.isna(row.get(field)) or row.get(field) == '':
                result.add_error(f"Campo requerido '{field}' está vacío")
        
        # Validar BU
        if not pd.isna(row.get('BU')) and row.get('BU') not in self.valid_bus:
            result.add_error(f"BU inválida: '{row.get('BU')}'. Válidas: {', '.join(self.valid_bus)}")
        
        # Validar Amount
        try:
            amount = float(row.get('Amount', 0))
            if amount <= 0:
                result.add_error("Amount debe ser mayor a 0")
        except (ValueError, TypeError):
            result.add_error("Amount debe ser un número válido")
        
        # Validar Lead Time
        try:
            lead_time = float(row.get('Lead Time', 0))
            if lead_time <= 0:
                result.add_error("Lead Time debe ser mayor a 0")
        except (ValueError, TypeError):
            result.add_error("Lead Time debe ser un número válido")
        
        # Validar Close Date
        if not self._validate_date(row.get('Close Date')):
            result.add_error("Close Date debe estar en formato DD/MM/YYYY")
        
        # Validar Paid in Advance (opcional)
        pia = row.get('Paid in Advance')
        if not pd.isna(pia) and pia != '':
            try:
                pia_value = float(pia)
                if pia_value < 0:
                    result.add_error("Paid in Advance no puede ser negativo")
            except (ValueError, TypeError):
                result.add_error("Paid in Advance debe ser un número válido")
        
        if result.errors:
            result.is_valid = False
        else:
            result.valid_records = 1
        
        return result
    
    def _validate_date(self, date_value) -> bool:
        """
        Valida que una fecha esté en formato correcto.
        
        Args:
            date_value: Valor de fecha a validar
            
        Returns:
            bool: True si la fecha es válida
        """
        if pd.isna(date_value) or date_value == '':
            return False
        
        date_str = str(date_value)
        
        for date_format in self.date_formats:
            try:
                datetime.strptime(date_str, date_format)
                return True
            except ValueError:
                continue
        
        return False
    
    def get_data_quality_report(self, df: pd.DataFrame) -> dict:
        """
        Genera un reporte de calidad de datos.
        
        Args:
            df: DataFrame a analizar
            
        Returns:
            dict: Reporte de calidad de datos
        """
        report = {
            'total_records': len(df),
            'columns_analysis': {},
            'missing_data_summary': {},
            'data_types': {}
        }
        
        for column in df.columns:
            if column in self.required_columns:
                missing_count = df[column].isna().sum()
                missing_percentage = (missing_count / len(df)) * 100
                
                report['columns_analysis'][column] = {
                    'missing_count': missing_count,
                    'missing_percentage': missing_percentage,
                    'data_type': str(df[column].dtype),
                    'unique_values': df[column].nunique()
                }
        
        return report
