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
    
    def read_excel_file(self, file, sheet_name: str = 0) -> Tuple[pd.DataFrame, Dict]:
        """
        Lee el archivo Excel del funnel con detección automática de headers.
        
        Args:
            file: Archivo Excel subido
            sheet_name: Nombre o índice de la hoja a leer (default: 0)
            
        Returns:
            Tuple[pd.DataFrame, Dict]: (DataFrame con datos, reporte de parsing)
            
        Raises:
            Exception: Si hay error al leer el archivo
        """
        try:
            logger.info(f"Iniciando lectura del archivo Excel (hoja: '{sheet_name}') con detección automática")
            
            # Detectar automáticamente la fila de headers
            header_row, df_raw = self.excel_parser.detect_header_row(file, sheet_name=sheet_name)
            
            # Guardar columnas originales para el reporte
            original_columns = df_raw.columns.tolist()
            
            # Normalizar nombres de columnas
            df_normalized = self.excel_parser.normalize_column_names(df_raw)
            
            # Limpiar filas completamente vacías
            df_clean = df_normalized.dropna(how='all').reset_index(drop=True)
            
            # Generar reporte de parsing
            parsing_report = self.excel_parser.get_parsing_report(original_columns, df_clean)
            parsing_report['detected_header_row'] = header_row
            parsing_report['sheet_name'] = sheet_name
            
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
        
        # Limpiar columna BU de símbolos especiales
        df_clean = self._clean_bu_column(df_clean)
        
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
    
    def _clean_bu_column(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Limpia la columna BU removiendo símbolos especiales como flechas (↑).
        
        Args:
            df: DataFrame con datos
            
        Returns:
            pd.DataFrame: DataFrame con columna BU limpia
        """
        if 'BU' not in df.columns:
            return df
        
        df = df.copy()
        
        # Remover símbolos especiales comunes: flechas, espacios extra, etc.
        df['BU'] = df['BU'].astype(str).str.replace('↑', '', regex=False)
        df['BU'] = df['BU'].astype(str).str.replace('↓', '', regex=False)
        df['BU'] = df['BU'].astype(str).str.replace('→', '', regex=False)
        df['BU'] = df['BU'].astype(str).str.replace('←', '', regex=False)
        
        # Remover espacios al inicio y final
        df['BU'] = df['BU'].str.strip()
        
        # Remover espacios múltiples
        df['BU'] = df['BU'].str.replace(r'\s+', ' ', regex=True)
        
        logger.debug("Columna BU limpiada de símbolos especiales")
        return df
    
    def _assign_probabilities(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normaliza columnas de probabilidad y BU ya procesadas por extract_projects_from_pipeline.
        
        El método extract_projects_from_pipeline ya aplicó forward fill a las columnas
        Probability y BU, por lo que aquí solo normalizamos los nombres y creamos 
        la columna probability_assigned.
        
        Args:
            df: DataFrame con datos ya procesados
            
        Returns:
            pd.DataFrame: DataFrame con columnas normalizadas
        """
        logger.debug("Normalizando columnas de probabilidad y BU (ya procesadas por extract_projects_from_pipeline)")
        
        df = df.copy()
        
        # Buscar columna de probabilidad (puede tener diferentes nombres)
        prob_col = None
        for col in df.columns:
            if 'probability' in str(col).lower() or 'prob' in str(col).lower():
                prob_col = col
                break
        
        if prob_col is None:
            logger.warning("No se encontró columna de Probability")
            df['probability_assigned'] = 0  # Valor por defecto
        else:
            logger.info(f"Columna de probabilidad encontrada: '{prob_col}'")
            logger.info(f"Primeras 20 filas de {prob_col} ANTES de conversión:")
            logger.info(f"\n{df[prob_col].head(20)}")
            
            # Crear columna probability_assigned desde la columna de probabilidad
            df['probability_assigned'] = pd.to_numeric(df[prob_col], errors='coerce')
            
            logger.info(f"Primeras 20 filas de probability_assigned DESPUÉS de conversión (antes de ffill):")
            logger.info(f"\n{df['probability_assigned'].head(20)}")
            
            # Contar NaN antes del forward fill
            nan_before = df['probability_assigned'].isna().sum()
            
            # APLICAR FORWARD FILL: Propagar la última probabilidad válida hacia abajo
            # Ejemplo: 0.5, NaN, NaN → 0.5, 0.5, 0.5
            df['probability_assigned'] = df['probability_assigned'].ffill()
            
            # Contar NaN después del forward fill
            nan_after = df['probability_assigned'].isna().sum()
            
            logger.info(f"\n{'='*80}")
            logger.info(f"FORWARD FILL DE PROBABILIDADES:")
            logger.info(f"  - Valores NaN ANTES del ffill: {nan_before}")
            logger.info(f"  - Valores NaN DESPUÉS del ffill: {nan_after}")
            logger.info(f"  - Registros completados con ffill: {nan_before - nan_after}")
            logger.info(f"{'='*80}")
            
            logger.info(f"\nPrimeras 20 filas de probability_assigned DESPUÉS de forward fill:")
            logger.info(f"\n{df['probability_assigned'].head(20)}")
            
            # Si aún quedan NaN después del forward fill (solo las primeras filas sin valor previo)
            if nan_after > 0:
                logger.warning(f"⚠️ {nan_after} registros sin probabilidad después del forward fill (filas iniciales sin valor previo)")
                logger.warning(f"Estos registros serán EXCLUIDOS en el filtrado posterior")
                # NO asignar valor por defecto - estos registros deben ser excluidos
        
        # Verificar y aplicar forward fill a columna BU
        bu_col = 'BU'
        if bu_col in df.columns:
            logger.info(f"\nPrimeras 20 filas de BU ANTES de forward fill:")
            logger.info(f"\n{df[bu_col].head(20)}")
            
            # Contar vacíos antes del forward fill
            mask_no_bu_before = df[bu_col].isna() | (df[bu_col].astype(str).str.strip() == '')
            no_bu_before = mask_no_bu_before.sum()
            
            # APLICAR FORWARD FILL: Propagar la última BU válida hacia abajo
            df[bu_col] = df[bu_col].ffill()
            
            # Contar vacíos después del forward fill
            mask_no_bu_after = df[bu_col].isna() | (df[bu_col].astype(str).str.strip() == '')
            no_bu_after = mask_no_bu_after.sum()
            
            logger.info(f"\n{'='*80}")
            logger.info(f"FORWARD FILL DE BU:")
            logger.info(f"  - Registros sin BU ANTES del ffill: {no_bu_before}")
            logger.info(f"  - Registros sin BU DESPUÉS del ffill: {no_bu_after}")
            logger.info(f"  - Registros completados con ffill: {no_bu_before - no_bu_after}")
            logger.info(f"{'='*80}")
            
            logger.info(f"\nPrimeras 20 filas de BU DESPUÉS de forward fill:")
            logger.info(f"\n{df[bu_col].head(20)}")
            
            if no_bu_after > 0:
                logger.warning(f"⚠️ {no_bu_after} registros sin BU después del forward fill (filas iniciales sin valor previo)")
                logger.warning(f"Estos registros serán EXCLUIDOS en el filtrado posterior")
        else:
            logger.warning("No se encontró columna BU")
        
        # Estadísticas
        prob_counts = df['probability_assigned'].value_counts().to_dict()
        bu_counts = df[bu_col].value_counts().to_dict() if bu_col in df.columns else {}
        
        logger.info(f"Columnas normalizadas:")
        logger.info(f"  - Probabilidades: {prob_counts}")
        logger.info(f"  - BUs: {bu_counts}")
        logger.info(f"  - Total registros: {len(df)}")
        
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
        
        # Convertir Invoice Date si existe (para ICT, REP, Otros sin PIA)
        if 'Invoice Date' in df.columns:
            df['invoice_date_parsed'] = df['Invoice Date'].apply(self._parse_date)
            df['invoice_date_parsed'] = df['invoice_date_parsed'].apply(self._adjust_current_month_dates)
        else:
            df['invoice_date_parsed'] = None
        
        # Convertir SAT Date si existe (para ICT, REP, Otros con PIA)
        if 'SAT Date' in df.columns:
            df['sat_date_parsed'] = df['SAT Date'].apply(self._parse_date)
            df['sat_date_parsed'] = df['sat_date_parsed'].apply(self._adjust_current_month_dates)
        else:
            df['sat_date_parsed'] = None
        
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
        
        # Si ya es un objeto datetime, retornarlo directamente
        if isinstance(date_value, datetime):
            return date_value
        
        # Si es un Timestamp de pandas, convertir a datetime
        if isinstance(date_value, pd.Timestamp):
            return date_value.to_pydatetime()
        
        # Si no, intentar parsear como string
        date_str = str(date_value)
        
        # Intentar diferentes formatos
        date_formats = ['%d/%m/%Y', '%Y-%m-%d', '%m/%d/%Y', '%Y-%m-%d %H:%M:%S']
        
        for date_format in date_formats:
            try:
                return datetime.strptime(date_str, date_format)
            except ValueError:
                continue
        
        logger.warning(f"No se pudo parsear la fecha: {date_value} (tipo: {type(date_value)})")
        return None
    
    def _adjust_current_month_dates(self, date_value: Optional[datetime]) -> Optional[datetime]:
        """
        Ajusta fechas de meses pasados al último día del mes actual.
        NO ajusta fechas dentro del mes actual, solo meses anteriores.
        
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
            
            # Solo ajustar si la fecha es de un MES ANTERIOR (no solo día anterior)
            # Comparar año y mes, no día
            is_past_month = (date_value.year < current_date.year) or \
                           (date_value.year == current_date.year and date_value.month < current_date.month)
            
            if is_past_month:
                # Calcular último día del mes actual
                import calendar
                last_day = calendar.monthrange(current_date.year, current_date.month)[1]
                
                # Ajustar al último día del mes actual
                adjusted_date = current_date.replace(day=last_day)
                
                logger.info(f"Fecha de mes pasado ajustada: {date_value.strftime('%d/%m/%Y')} -> {adjusted_date.strftime('%d/%m/%Y')}")
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
        
        initial_count = len(df)
        
        # Nota: Las filas de resumen (Subtotal, Sum, Avg, Count) ya fueron eliminadas en excel_parser.py
        logger.debug("Las filas de resumen ya fueron eliminadas en el paso de parsing del Excel")
        
        # Contar registros que no cumplen cada condición
        logger.info("Validando condiciones:")
        logger.info(f"  - Lead Time: {df['Lead Time'].notna().sum()} de {len(df)} tienen valor")
        logger.info(f"  - Payment Terms: {df['Payment Terms'].notna().sum()} de {len(df)} tienen valor")
        logger.info(f"  - Opportunity Name: {df['Opportunity Name'].notna().sum()} de {len(df)} tienen valor")
        logger.info(f"  - Amount: {(df['Amount'].notna() & (df['Amount'] > 0)).sum()} de {len(df)} tienen valor > 0")
        
        # Validación más estricta de BU
        bu_valid = df['BU'].notna() & (df['BU'].astype(str).str.strip() != '') & (df['BU'].astype(str).str.upper() != 'NAN')
        logger.info(f"  - BU: {bu_valid.sum()} de {len(df)} tienen BU válido")
        if bu_valid.sum() < len(df):
            invalid_bu_count = len(df) - bu_valid.sum()
            logger.warning(f"    ⚠️ {invalid_bu_count} registros tienen BU inválido (NaN, vacío o 'nan')")
        
        logger.info(f"  - Close Date: {df['close_date_parsed'].notna().sum()} de {len(df)} tienen fecha válida")
        logger.info(f"  - Probability: {df['probability_assigned'].notna().sum()} de {len(df)} tienen probabilidad asignada")
        
        prob_100_count = (df['probability_assigned'] == 1.0).sum()
        if prob_100_count > 0:
            logger.info(f"  - Probabilidad < 100%: {prob_100_count} registros tienen probabilidad 100% (se excluirán)")
        
        # Condiciones para registros válidos (ahora incluye datos completados)
        # Validación más estricta de BU: no puede ser NaN, vacío o 'nan'
        bu_valid_condition = df['BU'].notna() & (df['BU'].astype(str).str.strip() != '') & (df['BU'].astype(str).str.upper() != 'NAN')
        
        conditions = [
            df['Lead Time'].notna(),
            #df['Payment Terms'].notna(),
            df['Opportunity Name'].notna(),
            df['Amount'].notna(),
            df['Amount'] > 0,
            bu_valid_condition,  # Validación estricta de BU
            df['close_date_parsed'].notna(),
            df['probability_assigned'].notna(),
            df['probability_assigned'] < 1.0  # Excluir probabilidades del 100%
        ]
        
        # Aplicar todas las condiciones
        valid_mask = pd.concat(conditions, axis=1).all(axis=1)
        df_filtered = df[valid_mask].copy()
        
        logger.info(f"\nResumen de filtrado:")
        logger.info(f"  - Registros iniciales: {initial_count}")
        logger.info(f"  - Registros válidos finales: {len(df_filtered)}")
        logger.info(f"  - Registros descartados: {initial_count - len(df_filtered)}")
        
        # Mostrar distribución por BU de los registros válidos
        if 'BU' in df_filtered.columns and len(df_filtered) > 0:
            bu_counts = df_filtered['BU'].value_counts().to_dict()
            logger.info(f"  - Distribución por BU: {bu_counts}")
        
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
        errors = 0
        
        for idx, row in df.iterrows():
            try:
                # Validar que BU no sea NaN antes de crear el objeto
                bu_value = row['BU']
                if pd.isna(bu_value) or str(bu_value).strip() == '' or str(bu_value).upper() == 'NAN':
                    logger.error(f"Registro {idx} '{row.get('Opportunity Name', 'N/A')}' tiene BU inválido: '{bu_value}' - Se salta")
                    errors += 1
                    continue
                
                # Crear objeto Opportunity
                opportunity = Opportunity(
                    name=str(row['Opportunity Name']),
                    bu=BusinessUnit(str(bu_value).strip()),
                    amount=float(row['Amount']),
                    close_date=row['close_date_parsed'],
                    lead_time=float(row['Lead Time']),
                    probability=float(row['probability_assigned']),
                    paid_in_advance=float(row['Paid in Advance']) if row['Paid in Advance'] > 0 else None,
                    payment_terms=str(row['Payment Terms']) if pd.notna(row['Payment Terms']) else None,
                    region=str(row['region_detected']) if pd.notna(row.get('region_detected')) else None,
                    company=str(row['Company']) if pd.notna(row.get('Company')) else None,
                    gross_margin=float(row['Gross Margin']) if pd.notna(row.get('Gross Margin')) and row['Gross Margin'] > 0 else None,
                    account_name=str(row['Account Name']).strip() if 'Account Name' in df.columns and pd.notna(row.get('Account Name')) else None,
                    invoice_date=row.get('invoice_date_parsed') if pd.notna(row.get('invoice_date_parsed')) else None,
                    sat_date=row.get('sat_date_parsed') if pd.notna(row.get('sat_date_parsed')) else None
                )
                
                opportunities.append(opportunity)
                
            except Exception as e:
                logger.error(f"Error al crear oportunidad para '{row.get('Opportunity Name', 'N/A')}': {str(e)} - BU='{row.get('BU', 'N/A')}'")
                errors += 1
                continue
        
        logger.info(f"Se crearon {len(opportunities)} objetos Opportunity ({errors} errores)")
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
