"""
Módulo de procesamiento de datos para la aplicación de Forecast Financiero.

Este módulo contiene toda la lógica de transformación y limpieza de datos,
separando claramente las responsabilidades de procesamiento.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Dict
import logging

from .models import Opportunity, BusinessUnit, ValidationResult
from .client_database import ClientDatabase
from .excel_parser import ExcelParser
from config.settings import EXCEL_CONFIG, BUSINESS_RULES, ERROR_MESSAGES


# Configurar logging
logger = logging.getLogger(__name__)


class DataProcessor:
    """
    Clase principal para procesamiento de datos del funnel.
    
    Esta clase maneja la lectura, limpieza y transformación de los datos
    de entrada para prepararlos para el cálculo del forecast.
    """
    
    def __init__(self):
        """Inicializa el procesador con configuraciones por defecto."""
        self.header_row = EXCEL_CONFIG.HEADER_ROW
        self.min_lead_time = BUSINESS_RULES.MIN_LEAD_TIME
        self.client_db = ClientDatabase()
        self.excel_parser = ExcelParser()
    
    def read_excel_file(self, file) -> Tuple[pd.DataFrame, Dict]:
        """
        Lee el archivo Excel del funnel con detección automática de headers.
        
        Args:
            file: Archivo Excel subido
            
        Returns:
            Tuple[pd.DataFrame, Dict]: (DataFrame con datos, reporte de parsing)
            
        Raises:
            Exception: Si hay error al leer el archivo
        """
        try:
            logger.info("Iniciando lectura del archivo Excel con detección automática")
            
            # Detectar automáticamente la fila de headers
            header_row, df_raw = self.excel_parser.detect_header_row(file)
            
            # Guardar columnas originales para el reporte
            original_columns = df_raw.columns.tolist()
            
            # Normalizar nombres de columnas
            df_normalized = self.excel_parser.normalize_column_names(df_raw)
            
            # Limpiar filas completamente vacías
            df_clean = df_normalized.dropna(how='all').reset_index(drop=True)
            
            # Generar reporte de parsing
            parsing_report = self.excel_parser.get_parsing_report(original_columns, df_clean)
            parsing_report['detected_header_row'] = header_row
            
            logger.info(f"Archivo leído exitosamente: {len(df_clean)} registros, header en fila {header_row}")
            
            return df_clean, parsing_report
            
        except Exception as e:
            logger.error(f"Error al leer archivo Excel: {str(e)}")
            raise Exception(f"Error al leer el archivo: {str(e)}")
    
    def clean_and_prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Limpia y prepara los datos para el procesamiento.
        
        Args:
            df: DataFrame con datos crudos
            
        Returns:
            pd.DataFrame: DataFrame limpio y preparado
        """
        logger.info("Iniciando limpieza de datos")
        
        df_clean = df.copy()
        
        # Asignar probabilidades usando lógica de agrupador
        df_clean = self._assign_probabilities(df_clean)
        
        # Ajustar Lead Times
        df_clean = self._adjust_lead_times(df_clean)
        
        # Convertir fechas
        df_clean = self._convert_dates(df_clean)
        
        # Limpiar valores numéricos
        df_clean = self._clean_numeric_values(df_clean)
        
        # Detectar región y clasificar empresa
        df_clean = self._detect_region_and_classify_company(df_clean)
        
        # Completar datos faltantes usando base de datos histórica
        df_clean = self._complete_missing_data(df_clean)
        
        # Filtrar solo registros válidos para procesamiento
        df_clean = self._filter_valid_records(df_clean)
        
        # Actualizar base de datos histórica con nuevos datos
        self.client_db.add_historical_data(df_clean)
        
        logger.info(f"Datos limpiados: {len(df_clean)} registros válidos")
        return df_clean
    
    def _assign_probabilities(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Asigna probabilidades usando la lógica de agrupador.
        
        La columna de probabilidad funciona como un agrupador donde el valor
        se aplica a todos los proyectos siguientes hasta que aparece un nuevo valor.
        
        Args:
            df: DataFrame con datos
            
        Returns:
            pd.DataFrame: DataFrame con probabilidades asignadas
        """
        logger.debug("Asignando probabilidades con lógica de agrupador")
        
        df = df.copy()
        prob_col = 'Probability (%)  ↑'
        
        # Convertir a numérico, manteniendo NaN
        df[prob_col] = pd.to_numeric(df[prob_col], errors='coerce')
        
        # Forward fill: propagar el último valor válido hacia adelante
        df['probability_assigned'] = df[prob_col].ffill()
        
        # Si los primeros registros no tienen probabilidad, usar valor por defecto
        if pd.isna(df['probability_assigned'].iloc[0]):
            df['probability_assigned'] = df['probability_assigned'].fillna(0.25)
        
        return df
    
    def _adjust_lead_times(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ajusta Lead Times al mínimo establecido.
        
        Args:
            df: DataFrame con datos
            
        Returns:
            pd.DataFrame: DataFrame con Lead Times ajustados
        """
        logger.debug(f"Ajustando Lead Times al mínimo de {self.min_lead_time} semanas")
        
        df = df.copy()
        
        # Guardar Lead Time original
        df['lead_time_original'] = df['Lead Time'].copy()
        
        # Ajustar Lead Time
        df['Lead Time'] = df['Lead Time'].apply(
            lambda x: max(x, self.min_lead_time) if pd.notna(x) else x
        )
        
        # Contar cuántos fueron ajustados
        adjusted_count = (df['lead_time_original'] < self.min_lead_time).sum()
        if adjusted_count > 0:
            logger.info(f"Se ajustaron {adjusted_count} Lead Times al mínimo de {self.min_lead_time} semanas")
        
        return df
    
    def _convert_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convierte las fechas a formato datetime y ajusta fechas pasadas al mes actual.
        
        Args:
            df: DataFrame con datos
            
        Returns:
            pd.DataFrame: DataFrame con fechas convertidas
        """
        logger.debug("Convirtiendo fechas a formato datetime")
        
        df = df.copy()
        
        # Convertir Close Date
        df['close_date_parsed'] = df['Close Date'].apply(self._parse_date)
        
        # Ajustar fechas pasadas al último día del mes actual
        df['close_date_parsed'] = df['close_date_parsed'].apply(self._adjust_current_month_dates)
        
        return df
    
    def _parse_date(self, date_value) -> Optional[datetime]:
        """
        Parsea una fecha desde diferentes formatos.
        
        Args:
            date_value: Valor de fecha a parsear
            
        Returns:
            Optional[datetime]: Fecha parseada o None si no es válida
        """
        if pd.isna(date_value) or date_value == '':
            return None
        
        date_str = str(date_value)
        
        # Intentar diferentes formatos
        date_formats = ['%d/%m/%Y', '%Y-%m-%d', '%m/%d/%Y']
        
        for date_format in date_formats:
            try:
                return datetime.strptime(date_str, date_format)
            except ValueError:
                continue
        
        logger.warning(f"No se pudo parsear la fecha: {date_value}")
        return None
    
    def _adjust_current_month_dates(self, date_value: Optional[datetime]) -> Optional[datetime]:
        """
        Ajusta fechas pasadas (anteriores a hoy) al último día del mes actual.
        
        Args:
            date_value: Fecha a ajustar
            
        Returns:
            Optional[datetime]: Fecha ajustada o None
        """
        if date_value is None:
            return None
        
        # Verificar si es NaT (Not a Time) o fecha inválida
        if pd.isna(date_value):
            logger.warning("Fecha NaT encontrada, se omite el ajuste")
            return None
        
        try:
            current_date = datetime.now()
            
            # Si la fecha es anterior a la fecha actual (incluyendo mes y año)
            if date_value.date() < current_date.date():
                
                # Calcular último día del mes actual
                import calendar
                last_day = calendar.monthrange(current_date.year, current_date.month)[1]
                
                # Ajustar al último día del mes actual
                adjusted_date = current_date.replace(day=last_day)
                
                logger.info(f"Fecha pasada ajustada: {date_value.strftime('%d/%m/%Y')} -> {adjusted_date.strftime('%d/%m/%Y')}")
                return adjusted_date
            
            return date_value
            
        except (AttributeError, TypeError, ValueError) as e:
            logger.warning(f"Error al procesar fecha {date_value}: {str(e)}")
            return None
    
    def _clean_numeric_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Limpia y valida valores numéricos.
        
        Args:
            df: DataFrame con datos
            
        Returns:
            pd.DataFrame: DataFrame con valores numéricos limpios
        """
        logger.debug("Limpiando valores numéricos")
        
        df = df.copy()
        
        # Limpiar Amount
        df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
        
        # Limpiar Lead Time
        df['Lead Time'] = pd.to_numeric(df['Lead Time'], errors='coerce')
        
        # Limpiar Paid in Advance
        df['Paid in Advance'] = pd.to_numeric(df['Paid in Advance'], errors='coerce')
        df['Paid in Advance'] = df['Paid in Advance'].fillna(0)
        
        # Limpiar Gross Margin (si existe)
        if 'Gross Margin' in df.columns:
            df['Gross Margin'] = pd.to_numeric(df['Gross Margin'], errors='coerce')
            df['Gross Margin'] = df['Gross Margin'].fillna(0)
        else:
            df['Gross Margin'] = 0
        
        return df
    
    def _detect_region_and_classify_company(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detecta la región y clasifica la empresa (LLC o SAPI).
        
        La región se obtiene ÚNICAMENTE de la columna 'Region' en el archivo Excel.
        
        Clasificación de empresa:
        - LLC: Regiones que comienzan con US
        - SAPI: Regiones que comienzan con MX
        - Sin Clasificar: Otras regiones o sin región definida
        
        Args:
            df: DataFrame con datos
            
        Returns:
            pd.DataFrame: DataFrame con región y empresa clasificada
        """
        logger.debug("Detectando región y clasificando empresa desde columna Region")
        
        df = df.copy()
        
        # Detectar región SOLO desde columna Region
        if 'Region' in df.columns:
            # Usar columna Region del Excel
            df['region_detected'] = df['Region'].fillna('').astype(str).str.strip()
            logger.info("Región detectada desde columna 'Region' del archivo Excel")
        else:
            # Si no existe la columna, marcar como vacío
            df['region_detected'] = ''
            logger.warning("No se encontró columna 'Region' en el archivo Excel. Todos los registros se clasificarán como 'Sin Clasificar'")
        
        # Clasificar empresa basándose en región
        df['Company'] = df['region_detected'].apply(self._classify_company)
        
        # Contar clasificaciones
        company_counts = df['Company'].value_counts().to_dict()
        logger.info(f"Clasificación de empresas: {company_counts}")
        
        return df
    
    def _classify_company(self, region: str) -> str:
        """
        Clasifica la empresa basándose en la región.
        
        Args:
            region: Código de región
            
        Returns:
            str: Clasificación de empresa (LLC, SAPI, o Sin Clasificar)
        """
        if not region or region == '':
            return 'Sin Clasificar'
        
        region_upper = str(region).upper().strip()
        
        # Regiones que comienzan con US son LLC
        if region_upper.startswith('US'):
            return 'LLC'
        
        # Regiones que comienzan con MX son SAPI
        if region_upper.startswith('MX'):
            return 'SAPI'
        
        # Otras regiones
        return 'Sin Clasificar'
    
    def _complete_missing_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Completa datos faltantes usando la base de datos histórica.
        
        Args:
            df: DataFrame con datos
            
        Returns:
            pd.DataFrame: DataFrame con datos completados
        """
        logger.debug("Completando datos faltantes con información histórica")
        
        df = df.copy()
        lead_time_completed = 0
        payment_terms_completed = 0
        
        for index, row in df.iterrows():
            client_name = self.client_db._extract_client_name(row.get('Opportunity Name', ''))
            
            # Completar Lead Time faltante
            if pd.isna(row.get('Lead Time')) or row.get('Lead Time') == '':
                # Intentar obtener de base de datos histórica
                historical_lead_time = self.client_db.get_client_lead_time(
                    client_name, 
                    row.get('Amount')
                )
                
                if historical_lead_time:
                    df.at[index, 'Lead Time'] = historical_lead_time
                    df.at[index, 'lead_time_source'] = 'historical'
                    lead_time_completed += 1
                else:
                    # Estimar basado en monto
                    estimated_lead_time = self.client_db.estimate_lead_time_by_amount(
                        row.get('Amount', 0)
                    )
                    df.at[index, 'Lead Time'] = estimated_lead_time
                    df.at[index, 'lead_time_source'] = 'estimated'
                    lead_time_completed += 1
            else:
                df.at[index, 'lead_time_source'] = 'original'
            
            # Completar Payment Terms faltante
            if pd.isna(row.get('Payment Terms')) or row.get('Payment Terms') == '':
                # Intentar obtener de base de datos histórica
                historical_payment_terms = self.client_db.get_client_payment_terms(client_name)
                
                if historical_payment_terms:
                    df.at[index, 'Payment Terms'] = historical_payment_terms
                    df.at[index, 'payment_terms_source'] = 'historical'
                    payment_terms_completed += 1
                else:
                    # Valor por defecto
                    df.at[index, 'Payment Terms'] = 'NET 30'
                    df.at[index, 'payment_terms_source'] = 'default'
                    payment_terms_completed += 1
            else:
                df.at[index, 'payment_terms_source'] = 'original'
        
        if lead_time_completed > 0:
            logger.info(f"Se completaron {lead_time_completed} Lead Times faltantes")
        
        if payment_terms_completed > 0:
            logger.info(f"Se completaron {payment_terms_completed} Payment Terms faltantes")
        
        return df
    
    def _filter_valid_records(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filtra solo los registros válidos para procesamiento.
        
        Args:
            df: DataFrame con datos
            
        Returns:
            pd.DataFrame: DataFrame filtrado
        """
        logger.debug("Filtrando registros válidos")
        
        # Condiciones para registros válidos (ahora incluye datos completados)
        conditions = [
            df['Lead Time'].notna(),
            df['Payment Terms'].notna(),
            df['Opportunity Name'].notna(),
            df['Amount'].notna(),
            df['Amount'] > 0,
            df['BU'].notna(),
            df['close_date_parsed'].notna(),
            df['probability_assigned'].notna(),
            df['probability_assigned'] < 1.0  # Excluir probabilidades del 100%
        ]
        
        # Aplicar todas las condiciones
        valid_mask = pd.concat(conditions, axis=1).all(axis=1)
        df_filtered = df[valid_mask].copy()
        
        # Contar exclusiones por probabilidad 100%
        prob_100_count = (df['probability_assigned'] == 1.0).sum()
        
        logger.info(f"Registros filtrados: {len(df_filtered)} válidos de {len(df)} totales")
        if prob_100_count > 0:
            logger.info(f"Se excluyeron {prob_100_count} oportunidades con probabilidad del 100%")
        
        return df_filtered
    
    def convert_to_opportunities(self, df: pd.DataFrame) -> List[Opportunity]:
        """
        Convierte el DataFrame a lista de objetos Opportunity.
        
        Args:
            df: DataFrame con datos limpios
            
        Returns:
            List[Opportunity]: Lista de oportunidades
        """
        logger.info("Convirtiendo datos a objetos Opportunity")
        
        opportunities = []
        
        for _, row in df.iterrows():
            try:
                # Crear objeto Opportunity
                opportunity = Opportunity(
                    name=str(row['Opportunity Name']),
                    bu=BusinessUnit(row['BU']),
                    amount=float(row['Amount']),
                    close_date=row['close_date_parsed'],
                    lead_time=float(row['Lead Time']),
                    probability=float(row['probability_assigned']),
                    paid_in_advance=float(row['Paid in Advance']) if row['Paid in Advance'] > 0 else None,
                    payment_terms=str(row['Payment Terms']) if pd.notna(row['Payment Terms']) else None,
                    region=str(row['region_detected']) if pd.notna(row.get('region_detected')) else None,
                    company=str(row['Company']) if pd.notna(row.get('Company')) else None,
                    gross_margin=float(row['Gross Margin']) if pd.notna(row.get('Gross Margin')) and row['Gross Margin'] > 0 else None
                )
                
                opportunities.append(opportunity)
                
            except Exception as e:
                logger.warning(f"Error al crear oportunidad para '{row.get('Opportunity Name', 'N/A')}': {str(e)}")
                continue
        
        logger.info(f"Se crearon {len(opportunities)} objetos Opportunity")
        return opportunities
    
    def get_processing_summary(self, original_df: pd.DataFrame, clean_df: pd.DataFrame, parsing_report: Dict = None) -> dict:
        """
        Genera un resumen del procesamiento de datos.
        
        Args:
            original_df: DataFrame original
            clean_df: DataFrame limpio
            parsing_report: Reporte de parsing (opcional)
            
        Returns:
            dict: Resumen del procesamiento
        """
        # Calcular exclusiones por probabilidad 100%
        prob_100_excluded = 0
        if 'probability_assigned' in original_df.columns:
            prob_100_excluded = (original_df['probability_assigned'] == 1.0).sum()
        
        summary = {
            'original_records': len(original_df),
            'valid_records': len(clean_df),
            'excluded_100_percent': prob_100_excluded,
            'success_rate': len(clean_df) / len(original_df) if len(original_df) > 0 else 0,
            'bu_distribution': clean_df['BU'].value_counts().to_dict(),
            'company_distribution': clean_df['Company'].value_counts().to_dict() if 'Company' in clean_df.columns else {},
            'probability_distribution': clean_df['probability_assigned'].value_counts().to_dict(),
            'lead_time_adjustments': (clean_df['lead_time_original'] < self.min_lead_time).sum(),
            'date_range': {
                'start': clean_df['close_date_parsed'].min(),
                'end': clean_df['close_date_parsed'].max()
            }
        }
        
        # Agregar información de parsing si está disponible
        if parsing_report:
            summary['parsing_info'] = parsing_report
        
        # Agregar estadísticas de completado de datos
        if 'lead_time_source' in clean_df.columns:
            summary['lead_time_completion'] = clean_df['lead_time_source'].value_counts().to_dict()
        
        if 'payment_terms_source' in clean_df.columns:
            summary['payment_terms_completion'] = clean_df['payment_terms_source'].value_counts().to_dict()
        
        return summary
