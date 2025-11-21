"""
Módulo de análisis y normalización de archivos Excel para la aplicación de Forecast Financiero.

Este módulo maneja la detección automática de headers y la normalización de nombres
de columnas para hacer la aplicación compatible con diferentes formatos de Excel.
"""

import pandas as pd
import re
from typing import Optional, Dict, List, Tuple
import logging

from config.settings import EXCEL_CONFIG


# Configurar logging
logger = logging.getLogger(__name__)


class ExcelParser:
    """
    Clase para análisis inteligente de archivos Excel.
    
    Esta clase detecta automáticamente la fila de headers y normaliza
    los nombres de columnas para mantener compatibilidad con diferentes formatos.
    """
    
    def __init__(self):
        """Inicializa el parser con mapeos de columnas."""
        self.column_mappings = self._create_column_mappings()
        self.required_columns_normalized = self._normalize_required_columns()
    
    def _create_column_mappings(self) -> Dict[str, List[str]]:
        """
        Crea mapeos de nombres de columnas alternativos.
        
        Returns:
            Dict[str, List[str]]: Mapeo de columna estándar a variantes
        """
        return {
            'Opportunity Name': [
                'opportunity name', 'opportunity_name', 'project name', 'project_name',
                'nombre oportunidad', 'nombre proyecto', 'oportunidad', 'proyecto'
            ],
            'Account Name': [
                'account name', 'account_name', 'client name', 'client_name',
                'customer name', 'customer_name', 'nombre cliente', 'cliente', 'customer'
            ],
            'BU': [
                'bu', 'business unit', 'business_unit', 'unidad negocio', 'unidad_negocio'
            ],
            'Amount': [
                'amount', 'monto', 'valor', 'value', 'total', 'importe', 'precio', 'price'
            ],
            'Close Date': [
                'close date', 'close_date', 'fecha cierre', 'fecha_cierre', 
                'closing date', 'closing_date', 'fecha', 'date'
            ],
            'Lead Time': [
                'lead time', 'lead_time', 'leadtime', 'tiempo entrega', 'tiempo_entrega',
                'delivery time', 'delivery_time', 'plazo', 'semanas'
            ],
            'Payment Terms': [
                'payment terms', 'payment_terms', 'terminos pago', 'terminos_pago',
                'condiciones pago', 'condiciones_pago', 'terms', 'terminos'
            ],
            'Probability (%)  ↑': [
                'probability', 'probabilidad', 'prob', 'probability (%)', 'probability%',
                'probability (%) ↑', 'probability (%)↑', 'prob %', 'prob%'
            ],
            'Paid in Advance': [
                'paid in advance', 'paid_in_advance', 'pia', 'calculated pia', 'calculated_pia',
                'pago adelantado', 'pago_adelantado', 'anticipo', 'advance payment',
                'advance_payment', 'prepago', 'prepayment'
            ],
            'Region': [
                'region', 'región', 'area', 'country', 'pais', 'país', 'location', 'ubicación', 
                'ubicacion', 'zona', 'zone', 'territorio', 'territory'
            ],
            'Gross Margin': [
                'gross margin', 'gross_margin', 'margen bruto', 'margen_bruto', 
                'margen', 'margin', 'gm'
            ]
        }
    
    def _normalize_required_columns(self) -> List[str]:
        """
        Normaliza los nombres de columnas requeridas.
        
        Returns:
            List[str]: Lista de columnas requeridas normalizadas
        """
        return [self._normalize_text(col) for col in EXCEL_CONFIG.REQUIRED_COLUMNS]
    
    def _normalize_text(self, text: str) -> str:
        """
        Normaliza texto para comparación.
        
        Args:
            text: Texto a normalizar
            
        Returns:
            str: Texto normalizado
        """
        if not text:
            return ""
        
        # Convertir a minúsculas y remover caracteres especiales
        normalized = re.sub(r'[^\w\s]', '', str(text).lower().strip())
        # Reemplazar múltiples espacios con uno solo
        normalized = re.sub(r'\s+', ' ', normalized)
        return normalized
    
    def _clean_column_headers(self, columns) -> List[str]:
        """
        Limpia los nombres de las columnas removiendo símbolos especiales como flechas.
        
        Args:
            columns: Lista o Index de nombres de columnas
            
        Returns:
            List[str]: Lista de nombres de columnas limpios
        """
        cleaned_columns = []
        
        for col in columns:
            col_str = str(col)
            
            # Remover símbolos especiales comunes: flechas
            col_str = col_str.replace('↑', '')
            col_str = col_str.replace('↓', '')
            col_str = col_str.replace('→', '')
            col_str = col_str.replace('←', '')
            col_str = col_str.replace('⬆', '')
            col_str = col_str.replace('⬇', '')
            col_str = col_str.replace('➡', '')
            col_str = col_str.replace('⬅', '')
            
            # Remover espacios al inicio y final
            col_str = col_str.strip()
            
            # Remover múltiples espacios
            col_str = re.sub(r'\s+', ' ', col_str)
            
            cleaned_columns.append(col_str)
        
        logger.debug(f"Columnas limpiadas de símbolos especiales")
        return cleaned_columns
    
    def detect_header_row(self, file_path_or_buffer, max_rows: int = 20, sheet_name: str = 0) -> Tuple[int, pd.DataFrame]:
        """
        Usa el método extract_projects_from_pipeline para detectar headers y procesar datos.
        
        Args:
            file_path_or_buffer: Ruta del archivo o buffer
            max_rows: Número máximo de filas a analizar (no usado con el nuevo método)
            sheet_name: Nombre o índice de la hoja a leer (default: 0)
            
        Returns:
            Tuple[int, pd.DataFrame]: (fila_header_detectada, dataframe_procesado)
        """
        logger.info(f"Usando extract_projects_from_pipeline para procesar archivo Excel (hoja: '{sheet_name}')")
        
        try:
            # Importar el método desde extract_projects
            from .extract_projects import extract_projects_from_pipeline
            
            # Usar el método que ya implementa toda la lógica necesaria
            df_processed = extract_projects_from_pipeline(file_path_or_buffer, sheet_name=sheet_name)
            
            # El método ya:
            # 1. Detecta automáticamente los headers
            # 2. Limpia símbolos de las columnas (flechas, etc.)
            # 3. Elimina filas de totales (Subtotal, Sum, Avg, Count)
            # 4. Aplica forward fill a Probability y BU
            
            logger.info(f"Archivo procesado exitosamente: {len(df_processed)} registros")
            
            # Retornar -1 como header_row porque el método ya procesó todo
            return -1, df_processed
            
        except Exception as e:
            logger.error(f"Error procesando con extract_projects_from_pipeline: {str(e)}")
            
            # Fallback al método original si falla
            logger.warning("Usando método de detección original como fallback")
            return self._detect_header_row_original(file_path_or_buffer, max_rows, sheet_name)
    
    def _detect_header_row_original(self, file_path_or_buffer, max_rows: int = 20, sheet_name: str = 0) -> Tuple[int, pd.DataFrame]:
        """
        Método original de detección de headers (como fallback).
        
        Args:
            file_path_or_buffer: Ruta del archivo o buffer
            max_rows: Número máximo de filas a analizar
            sheet_name: Nombre o índice de la hoja a leer
        """
        logger.info(f"Iniciando detección automática de fila de headers (método original, hoja: '{sheet_name}')")
        
        best_row = 0
        best_score = 0
        best_df = None
        
        # Probar diferentes filas como posibles headers
        for row_idx in range(max_rows):
            try:
                # Leer archivo con esta fila como header
                df = pd.read_excel(file_path_or_buffer, sheet_name=sheet_name, header=row_idx)
                
                # Calcular score de coincidencia
                score = self._calculate_header_score(df.columns.tolist())
                
                logger.debug(f"Fila {row_idx}: Score = {score}, Columnas = {len(df.columns)}")
                
                # Si encontramos un score perfecto o muy alto, usar esta fila
                if score > best_score:
                    best_score = score
                    best_row = row_idx
                    best_df = df
                
                # Si el score es muy alto, podemos parar la búsqueda
                if score >= 0.8:  # 80% de coincidencia
                    break
                    
            except Exception as e:
                logger.debug(f"Error leyendo fila {row_idx} como header: {str(e)}")
                continue
        
        if best_df is None:
            # Fallback: usar fila 0
            logger.warning("No se pudo detectar header automáticamente, usando fila 0")
            best_df = pd.read_excel(file_path_or_buffer, sheet_name=sheet_name, header=0)
            best_row = 0
        
        logger.info(f"Header detectado en fila {best_row} con score {best_score:.2f}")
        
        # Filtrar filas: tomar solo HASTA encontrar "Total" en la columna de Probability
        best_df = self._filter_rows_until_total(best_df)
        
        # Eliminar filas de resumen: Subtotal, Sum, Avg, Count
        best_df = self._remove_summary_rows(best_df)
        
        return best_row, best_df
    
    def _calculate_header_score(self, columns: List[str]) -> float:
        """
        Calcula un score de qué tan probable es que esta fila sea el header.
        
        Args:
            columns: Lista de nombres de columnas
            
        Returns:
            float: Score entre 0 y 1
        """
        if not columns:
            return 0.0
        
        matches = 0
        total_required = len(self.required_columns_normalized)
        
        # Normalizar columnas encontradas
        normalized_columns = [self._normalize_text(col) for col in columns]
        
        # Contar coincidencias con columnas requeridas
        for required_col in EXCEL_CONFIG.REQUIRED_COLUMNS:
            if self._find_matching_column(required_col, columns):
                matches += 1
        
        # Score base por coincidencias exactas
        base_score = matches / total_required
        
        # Bonus por tener un número razonable de columnas (no demasiadas ni muy pocas)
        column_count_bonus = 0
        if 5 <= len(columns) <= 20:
            column_count_bonus = 0.1
        
        # Penalty si hay muchas columnas vacías o con nombres extraños
        empty_columns = sum(1 for col in columns if pd.isna(col) or str(col).strip() == '')
        empty_penalty = (empty_columns / len(columns)) * 0.2
        
        final_score = base_score + column_count_bonus - empty_penalty
        return max(0.0, min(1.0, final_score))
    
    def normalize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normaliza los nombres de columnas del DataFrame.
        
        Args:
            df: DataFrame con columnas originales
            
        Returns:
            pd.DataFrame: DataFrame con columnas normalizadas
        """
        logger.info("Normalizando nombres de columnas")
        
        df_normalized = df.copy()
        
        # Limpiar símbolos especiales de los nombres de columnas (headers)
        df_normalized.columns = self._clean_column_headers(df_normalized.columns)
        column_mapping = {}
        
        # Para cada columna requerida, buscar coincidencia
        for required_col in EXCEL_CONFIG.REQUIRED_COLUMNS:
            matching_col = self._find_matching_column(required_col, df_normalized.columns.tolist())
            
            if matching_col:
                column_mapping[matching_col] = required_col
                logger.debug(f"Mapeo encontrado: '{matching_col}' -> '{required_col}'")
            else:
                logger.warning(f"No se encontró columna para: '{required_col}'")
        
        # Aplicar mapeo
        df_normalized = df_normalized.rename(columns=column_mapping)
        
        # Normalizar valores de PIA si es porcentaje
        df_normalized = self._normalize_pia_values(df_normalized)
        
        logger.info(f"Se normalizaron {len(column_mapping)} nombres de columnas")
        return df_normalized
    
    def _find_matching_column(self, required_col: str, available_columns: List[str]) -> Optional[str]:
        """
        Encuentra la columna que mejor coincide con la requerida.
        
        Args:
            required_col: Nombre de columna requerida
            available_columns: Lista de columnas disponibles
            
        Returns:
            Optional[str]: Nombre de columna coincidente o None
        """
        # Primero buscar coincidencia exacta (normalizada)
        required_normalized = self._normalize_text(required_col)
        
        for col in available_columns:
            if self._normalize_text(col) == required_normalized:
                return col
        
        # Buscar en mapeos alternativos
        if required_col in self.column_mappings:
            for alternative in self.column_mappings[required_col]:
                for col in available_columns:
                    if self._normalize_text(col) == self._normalize_text(alternative):
                        return col
        
        # Buscar coincidencias parciales (contiene)
        for col in available_columns:
            col_normalized = self._normalize_text(col)
            if required_normalized in col_normalized or col_normalized in required_normalized:
                # Verificar que la coincidencia sea significativa (más del 50% de la palabra)
                if len(required_normalized) > 3 and len(col_normalized) > 3:
                    return col
        
        return None
    
    def _filter_rows_until_total(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filtra las filas del DataFrame, tomando datos HASTA encontrar "Total" 
        en la columna de Probability.
        
        Args:
            df: DataFrame con datos
            
        Returns:
            pd.DataFrame: DataFrame filtrado con datos hasta "Total"
        """
        # Buscar columna de probabilidad
        prob_col = None
        for col in df.columns:
            if 'probability' in str(col).lower() or 'prob' in str(col).lower():
                prob_col = col
                break
        
        if prob_col is None:
            logger.warning("No se encontró columna de Probability, no se filtrará por 'Total'")
            return df
        
        # Buscar la fila que contiene "Total" en la columna de probabilidad
        total_row_idx = None
        for idx in range(len(df)):
            value = df.iloc[idx][prob_col]
            if pd.notna(value) and str(value).strip().upper() == 'TOTAL':
                total_row_idx = idx
                logger.info(f"Encontrada fila 'Total' en posición {idx}, tomando datos HASTA esta fila (exclusive)")
                break
        
        if total_row_idx is None:
            logger.info("No se encontró 'Total' en columna Probability, se tomarán todos los datos")
            return df
        
        # Tomar solo las filas HASTA "Total" (sin incluir la fila Total)
        df_filtered = df.iloc[:total_row_idx].copy()
        logger.info(f"Se filtraron {len(df) - len(df_filtered)} filas después de 'Total'")
        
        return df_filtered
    
    def _remove_summary_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Elimina filas que contienen palabras de resumen: Subtotal, Sum, Avg, Count.
        
        Args:
            df: DataFrame con datos
            
        Returns:
            pd.DataFrame: DataFrame sin filas de resumen
        """
        initial_count = len(df)
        
        # Palabras clave a buscar en cualquier columna
        summary_keywords = ['SUBTOTAL', 'SUM', 'AVG', 'COUNT', 'AVERAGE', 'TOTAL']
        
        # Crear máscara para identificar filas de resumen
        mask_to_keep = pd.Series([True] * len(df), index=df.index)
        
        # Revisar cada columna
        for col in df.columns:
            for keyword in summary_keywords:
                # Buscar keyword en los valores de la columna
                mask_keyword = df[col].astype(str).str.upper().str.contains(keyword, na=False)
                mask_to_keep = mask_to_keep & ~mask_keyword
        
        # Filtrar el DataFrame
        df_filtered = df[mask_to_keep].copy()
        
        removed_count = initial_count - len(df_filtered)
        if removed_count > 0:
            logger.info(f"Se eliminaron {removed_count} filas de resumen (Subtotal, Sum, Avg, Count, Total)")
        
        return df_filtered
    
    def _normalize_pia_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normaliza los valores de Paid in Advance si están en porcentaje.
        
        Args:
            df: DataFrame con datos
            
        Returns:
            pd.DataFrame: DataFrame con valores PIA normalizados
        """
        pia_column = 'Paid in Advance'
        
        if pia_column not in df.columns:
            return df
        
        df_normalized = df.copy()
        
        # Detectar si los valores están en porcentaje
        sample_values = df[pia_column].dropna().head(10)
        
        if len(sample_values) == 0:
            return df_normalized
        
        # Verificar si hay valores que parecen porcentajes (0-1 o 0-100)
        numeric_values = pd.to_numeric(sample_values, errors='coerce').dropna()
        
        if len(numeric_values) > 0:
            max_value = numeric_values.max()
            
            # Si el valor máximo está entre 0 y 1, asumir que son decimales (0.15 = 15%)
            if 0 < max_value <= 1:
                logger.info("Detectados valores PIA como decimales, convirtiendo a montos")
                # Necesitamos el Amount para calcular el monto real
                if 'Amount' in df.columns:
                    df_normalized[pia_column] = (
                        pd.to_numeric(df[pia_column], errors='coerce') * 
                        pd.to_numeric(df['Amount'], errors='coerce')
                    )
                    logger.info("Valores PIA convertidos de porcentaje decimal a monto")
            
            # Si el valor máximo está entre 1 y 100, asumir que son porcentajes (15 = 15%)
            elif 1 < max_value <= 100:
                logger.info("Detectados valores PIA como porcentajes, convirtiendo a montos")
                if 'Amount' in df.columns:
                    df_normalized[pia_column] = (
                        pd.to_numeric(df[pia_column], errors='coerce') / 100 * 
                        pd.to_numeric(df['Amount'], errors='coerce')
                    )
                    logger.info("Valores PIA convertidos de porcentaje a monto")
        
        return df_normalized
    
    def validate_normalized_data(self, df: pd.DataFrame) -> Dict[str, any]:
        """
        Valida que los datos normalizados tengan las columnas requeridas.
        
        Args:
            df: DataFrame normalizado
            
        Returns:
            Dict: Resultado de validación
        """
        missing_columns = []
        available_columns = df.columns.tolist()
        
        for required_col in EXCEL_CONFIG.REQUIRED_COLUMNS:
            if required_col not in available_columns:
                missing_columns.append(required_col)
        
        return {
            'is_valid': len(missing_columns) == 0,
            'missing_columns': missing_columns,
            'available_columns': available_columns,
            'total_columns': len(available_columns),
            'required_columns': len(EXCEL_CONFIG.REQUIRED_COLUMNS)
        }
    
    def get_parsing_report(self, original_columns: List[str], normalized_df: pd.DataFrame) -> Dict:
        """
        Genera un reporte del proceso de parsing y normalización.
        
        Args:
            original_columns: Columnas originales del archivo
            normalized_df: DataFrame después de normalización
            
        Returns:
            Dict: Reporte detallado del parsing
        """
        validation = self.validate_normalized_data(normalized_df)
        
        # Identificar mapeos aplicados
        applied_mappings = {}
        for required_col in EXCEL_CONFIG.REQUIRED_COLUMNS:
            matching_col = self._find_matching_column(required_col, original_columns)
            if matching_col and matching_col != required_col:
                applied_mappings[matching_col] = required_col
        
        return {
            'original_columns_count': len(original_columns),
            'normalized_columns_count': len(normalized_df.columns),
            'applied_mappings': applied_mappings,
            'validation_result': validation,
            'pia_normalization_applied': self._was_pia_normalized(normalized_df),
            'parsing_success': validation['is_valid']
        }
    
    def _was_pia_normalized(self, df: pd.DataFrame) -> bool:
        """
        Verifica si se aplicó normalización a los valores PIA.
        
        Args:
            df: DataFrame normalizado
            
        Returns:
            bool: True si se normalizó PIA
        """
        # Esta es una verificación simple - en una implementación más robusta
        # podríamos mantener un flag durante el proceso de normalización
        pia_column = 'Paid in Advance'
        
        if pia_column not in df.columns:
            return False
        
        # Verificar si hay valores que parecen haber sido convertidos
        sample_values = pd.to_numeric(df[pia_column], errors='coerce').dropna()
        
        if len(sample_values) == 0:
            return False
        
        # Si todos los valores son 0 o muy grandes comparados con 1, probablemente se normalizó
        return sample_values.max() > 100 or (sample_values > 0).any()
