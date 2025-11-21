"""
Procesador de KPIs para archivos LLC (iBtest LLC-Overall Results).
"""

import pandas as pd
import logging
from typing import Dict, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class LLCKPIProcessor:
    """Procesa archivos de KPIs para LLC."""
    
    def process_llc_file(self, file_path_or_buffer) -> Dict[str, Any]:
        """
        Procesa archivo de KPIs LLC.
        
        Args:
            file_path_or_buffer: Ruta o buffer del archivo Excel
            
        Returns:
            Dict con datos procesados y resumen
        """
        try:
            logger.info("Iniciando procesamiento de archivo LLC")
            
            # Leer archivo Excel (headers en fila 3, índice 2)
            df = pd.read_excel(file_path_or_buffer, sheet_name="Data Base", header=2)
            logger.info(f"Archivo LLC leído: {len(df)} registros")
            logger.debug(f"Primeras columnas: {list(df.columns[:5])}")
            
            # Limpiar nombres de columnas
            df.columns = self._clean_column_headers(df.columns)
            logger.info(f"Columnas encontradas: {list(df.columns)}")
            
            # Renombrar columnas usando búsqueda flexible
            df = self._rename_columns_flexible(df)
            logger.info(f"Columnas después de renombrar: {list(df.columns)}")
            
            # Filtrar por Status f/Invoice = Pending
            if 'Status f/Invoice' not in df.columns:
                logger.error("Columna 'Status f/Invoice' no encontrada")
                return self._empty_result(len(df))
            
            # Normalizar status
            df['Status_normalized'] = df['Status f/Invoice'].astype(str).str.strip().str.lower()
            
            # Ver qué status únicos hay
            unique_statuses = df['Status f/Invoice'].unique()
            logger.info(f"Status f/Invoice únicos encontrados: {list(unique_statuses)}")
            
            # Filtrar solo Pending (excluir Invoiced y nan)
            df_filtered = df[df['Status_normalized'] == 'pending'].copy()
            logger.info(f"Registros con Status f/Invoice = Pending: {len(df_filtered)}")
            
            if df_filtered.empty:
                logger.warning("No hay registros con Status f/Invoice = Pending")
                return self._empty_result(len(df))
            
            # Limpiar y convertir valores
            df_filtered = self._clean_data(df_filtered)
            
            # Verificar si _clean_data devolvió DataFrame vacío
            if df_filtered.empty:
                logger.warning("No hay datos válidos después de la limpieza")
                return self._empty_result(len(df))
            
            # Crear tabla pivot estilo forecast
            billing_table = self._create_billing_table(df_filtered)
            
            return {
                'data': billing_table,
                'original_count': len(df),
                'filtered_count': len(df_filtered),
                'summary': self._create_summary(df_filtered, billing_table),
                'source': 'LLC'
            }
            
        except Exception as e:
            import traceback
            logger.error(f"Error procesando archivo LLC: {str(e)}")
            logger.error(f"Traceback completo: {traceback.format_exc()}")
            raise
    
    def _empty_result(self, original_count: int) -> Dict[str, Any]:
        """Retorna resultado vacío."""
        return {
            'data': [],
            'original_count': original_count,
            'filtered_count': 0,
            'summary': {
                'total_projects': 0,
                'total_billing': 0,
                'total_po': 0,
                'bu_distribution': {},
                'monthly_distribution': {},
                'status_distribution': {},
                'tbd_projects': []
            },
            'source': 'LLC'
        }
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Limpia y convierte los datos.
        
        Args:
            df: DataFrame a limpiar
            
        Returns:
            DataFrame limpio
        """
        df = df.copy()
        
        logger.info(f"Iniciando limpieza de {len(df)} registros LLC")
        
        # Limpiar Invoice Amount
        if 'Invoice Amount' in df.columns:
            df['Invoice Amount'] = pd.to_numeric(df['Invoice Amount'], errors='coerce').fillna(0)
            logger.info(f"Invoice Amount procesado: {df['Invoice Amount'].notna().sum()} valores válidos")
        else:
            logger.warning("Columna 'Invoice Amount' no encontrada")
            df['Invoice Amount'] = 0
        
        # Limpiar Quoted Cost (Costo de Venta)
        if 'Quoted Cost' in df.columns:
            df['Quoted Cost'] = pd.to_numeric(df['Quoted Cost'], errors='coerce').fillna(0)
            logger.info(f"Quoted Cost procesado: {df['Quoted Cost'].notna().sum()} valores válidos")
        else:
            logger.warning("Columna 'Quoted Cost' no encontrada")
            df['Quoted Cost'] = 0
        
        # Convertir Invoice Date
        if 'Invoice Date' in df.columns:
            df['Invoice Date'] = pd.to_datetime(
                df['Invoice Date'], 
                errors='coerce'
            )
            valid_dates = df['Invoice Date'].notna().sum()
            logger.info(f"Fechas válidas: {valid_dates} de {len(df)}")
        else:
            logger.error("Columna 'Invoice Date' no encontrada")
            return pd.DataFrame()
        
        # Eliminar registros sin fecha válida
        df = df[df['Invoice Date'].notna()].copy()
        
        if df.empty:
            logger.warning("No quedan registros después de filtrar fechas inválidas")
            return df
        
        # Crear columna de mes-año
        df['Mes Facturación'] = df['Invoice Date'].dt.strftime('%B %Y')
        
        # Limpiar Main BU si existe
        if 'Main BU' in df.columns:
            df['Main BU'] = df['Main BU'].fillna('').astype(str).str.strip()
            # Remover símbolos especiales
            for symbol in ['↑', '↓', '→', '←', '⬆', '⬇', '➡', '⬅']:
                df['Main BU'] = df['Main BU'].str.replace(symbol, '', regex=False)
            df['Main BU'] = df['Main BU'].str.strip()
            df['Main BU'] = df['Main BU'].replace(['', 'nan', 'None'], None)
        
        logger.info(f"Datos limpios: {len(df)} registros válidos con monto total de ${df['Invoice Amount'].sum():,.2f}")
        return df
    
    def _create_billing_table(self, df: pd.DataFrame) -> List[Dict]:
        """
        Crea tabla pivot estilo forecast.
        
        Args:
            df: DataFrame con datos limpios
            
        Returns:
            Lista de diccionarios con datos para la tabla
        """
        if df.empty:
            return []
        
        # Validar que existe la columna Project
        if 'Project' not in df.columns:
            logger.error("Columna 'Project' no encontrada en DataFrame")
            logger.error(f"Columnas disponibles: {list(df.columns)}")
            return []
        
        # Ordenar por Invoice Date
        df_sorted = df.sort_values('Invoice Date')
        unique_months = df_sorted['Mes Facturación'].unique()
        
        # Crear diccionario para cada proyecto
        projects = []
        
        for project_name in df['Project'].unique():
            project_data = df[df['Project'] == project_name]
            
            # Verificar que hay datos
            if project_data.empty:
                continue
            
            # Obtener Main BU de forma segura
            main_bu = 'N/A'
            if 'Main BU' in project_data.columns and len(project_data) > 0:
                try:
                    bu_value = project_data['Main BU'].iloc[0]
                    bu_str = str(bu_value)
                    if bu_str and bu_str.strip() and bu_str.lower().strip() not in ['nan', 'none', '']:
                        main_bu = bu_str.strip()
                        for symbol in ['↑', '↓', '→', '←', '⬆', '⬇', '➡', '⬅']:
                            main_bu = main_bu.replace(symbol, '')
                        main_bu = ' '.join(main_bu.split())
                except Exception as e:
                    logger.warning(f"Error extrayendo Main BU: {str(e)}")
                    main_bu = 'N/A'
            
            row = {
                'Proyecto': str(project_name),
                'BU': main_bu,
                'Location': 'LLC',  # Siempre LLC para estos registros
                'Status': 'Pending',  # Status f/Invoice
                'Customer': str(project_data['Customer'].iloc[0]) if 'Customer' in project_data.columns and len(project_data) > 0 else 'N/A',
                'Total PO': float(project_data['Invoice Amount'].sum()),  # Suma de todos los invoices del proyecto
                '% Facturación': '100%',  # Para LLC siempre es 100% porque son invoices individuales
                'Costo de Venta': float(project_data['Quoted Cost'].iloc[0]) if 'Quoted Cost' in project_data.columns and len(project_data) > 0 else 0
            }
            
            # Inicializar todos los meses en 0
            for month in unique_months:
                row[month] = 0
            
            # Asignar monto al mes correspondiente (ya ordenado por fecha)
            for _, event in project_data.iterrows():
                month = event['Mes Facturación']
                if month in row:
                    row[month] += event['Invoice Amount']
            
            projects.append(row)
        
        logger.info(f"Tabla de billing LLC creada: {len(projects)} proyectos")
        return projects
    
    def _create_summary(self, df: pd.DataFrame, billing_table: List[Dict]) -> Dict:
        """
        Crea resumen de los datos.
        
        Args:
            df: DataFrame original
            billing_table: Tabla de billing
            
        Returns:
            Dict con resumen
        """
        # Validar columnas requeridas
        total_projects = len(df['Project'].unique()) if 'Project' in df.columns else 0
        total_billing = df['Invoice Amount'].sum() if 'Invoice Amount' in df.columns else 0
        total_po = total_billing  # Para LLC, total PO = total billing
        
        summary = {
            'total_projects': total_projects,
            'total_billing': total_billing,
            'total_po': total_po,
            'bu_distribution': {},
            'monthly_distribution': {},
            'status_distribution': {'Pending': total_projects},
            'tbd_projects': []
        }
        
        # Distribución por BU
        if 'Main BU' in df.columns and 'Invoice Amount' in df.columns:
            try:
                df_temp = df.copy()
                df_temp['Main BU'] = df_temp['Main BU'].fillna('').astype(str).str.strip()
                
                for symbol in ['↑', '↓', '→', '←', '⬆', '⬇', '➡', '⬅']:
                    df_temp['Main BU'] = df_temp['Main BU'].str.replace(symbol, '', regex=False)
                
                df_temp['Main BU'] = df_temp['Main BU'].str.strip()
                df_with_bu = df_temp[(df_temp['Main BU'].notna()) & (df_temp['Main BU'] != '') & (df_temp['Main BU'] != 'nan')].copy()
                
                if not df_with_bu.empty:
                    bu_totals = df_with_bu.groupby('Main BU', as_index=True)['Invoice Amount'].sum()
                    summary['bu_distribution'] = bu_totals.to_dict()
                    logger.info(f"Distribución por BU (LLC) calculada: {len(bu_totals)} BUs")
            except Exception as e:
                logger.error(f"Error calculando distribución por BU (LLC): {str(e)}")
                summary['bu_distribution'] = {}
        
        # Distribución mensual
        if 'Mes Facturación' in df.columns and 'Invoice Amount' in df.columns:
            try:
                df_with_mes = df[df['Mes Facturación'].notna()].copy()
                if not df_with_mes.empty:
                    monthly_totals = df_with_mes.groupby('Mes Facturación', as_index=True)['Invoice Amount'].sum()
                    summary['monthly_distribution'] = monthly_totals.to_dict()
                    logger.info(f"Distribución mensual (LLC) calculada: {len(monthly_totals)} meses")
            except Exception as e:
                logger.error(f"Error calculando distribución mensual (LLC): {str(e)}")
                summary['monthly_distribution'] = {}
        
        return summary
    
    def _clean_column_headers(self, columns) -> list:
        """
        Limpia los nombres de las columnas removiendo símbolos especiales.
        
        Args:
            columns: Lista o Index de nombres de columnas
            
        Returns:
            list: Lista de nombres de columnas limpios
        """
        import re
        
        cleaned_columns = []
        
        for col in columns:
            col_str = str(col)
            
            # Remover símbolos especiales comunes
            col_str = col_str.replace('↑', '')
            col_str = col_str.replace('↓', '')
            col_str = col_str.replace('→', '')
            col_str = col_str.replace('←', '')
            col_str = col_str.replace('⬆', '')
            col_str = col_str.replace('⬇', '')
            col_str = col_str.replace('➡', '')
            col_str = col_str.replace('⬅', '')
            
            # Remover saltos de línea pero mantenerlos como espacio
            col_str = col_str.replace('\n', ' ')
            
            # Remover espacios al inicio y final
            col_str = col_str.strip()
            
            # Remover múltiples espacios
            col_str = re.sub(r'\s+', ' ', col_str)
            
            cleaned_columns.append(col_str)
        
        logger.debug(f"Columnas limpiadas de símbolos especiales")
        return cleaned_columns
    
    def _rename_columns_flexible(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Renombra las columnas del DataFrame buscando coincidencias flexibles.
        
        Args:
            df: DataFrame con columnas originales
            
        Returns:
            DataFrame con columnas renombradas
        """
        df = df.copy()
        rename_map = {}
        
        for col in df.columns:
            col_lower = str(col).lower().strip()
            
            # Project
            if col_lower == 'project':
                rename_map[col] = 'Project'
            
            # Status f/Invoice
            elif 'status' in col_lower and 'invoice' in col_lower:
                rename_map[col] = 'Status f/Invoice'
            
            # Invoice Amount
            elif 'invoice amount' in col_lower:
                rename_map[col] = 'Invoice Amount'
            
            # Invoice Date
            elif 'invoice date' in col_lower and 'estimated' not in col_lower:
                rename_map[col] = 'Invoice Date'
            
            # Main BU
            elif 'main bu' in col_lower or col_lower == 'bu':
                rename_map[col] = 'Main BU'
            
            # Customer
            elif col_lower == 'customer':
                rename_map[col] = 'Customer'
            
            # Location
            elif col_lower == 'location':
                rename_map[col] = 'Location'
            
            # Quoted Cost (Costo de Venta)
            elif 'quoted cost' in col_lower:
                rename_map[col] = 'Quoted Cost'
        
        if rename_map:
            logger.info(f"Mapeo de columnas LLC aplicado:")
            for old_col, new_col in rename_map.items():
                logger.info(f"  '{old_col}' -> '{new_col}'")
            df.rename(columns=rename_map, inplace=True)
            logger.info(f"Columnas renombradas exitosamente: {list(rename_map.values())}")
        else:
            logger.warning("No se encontraron columnas para renombrar")
        
        return df
