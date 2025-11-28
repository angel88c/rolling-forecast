"""
Procesador de archivo de KPIs PM-008.

Este módulo procesa el archivo de KPIs y genera una tabla de billing
similar a la tabla de forecast.
"""

import pandas as pd
import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class KPIProcessor:
    """Procesa datos del archivo de KPIs PM-008."""
    
    def __init__(self):
        """Inicializa el procesador de KPIs."""
        pass
    
    def process_kpi_file(self, file_path_or_buffer, billing_type: str = "Contable") -> Dict:
        """
        Procesa el archivo de KPIs PM-008.
        
        Args:
            file_path_or_buffer: Ruta o buffer del archivo Excel
            billing_type: Tipo de facturación ("Contable" o "Financiera")
            
        Returns:
            Dict con los datos procesados
        """
        try:
            logger.info("Iniciando procesamiento de archivo de KPIs")
            
            # Leer hoja Billing
            df = pd.read_excel(file_path_or_buffer, sheet_name='Billing')
            logger.info(f"Archivo leído: {len(df)} registros")
            
            # Limpiar nombres de columnas (remover símbolos especiales y espacios)
            df.columns = self._clean_column_headers(df.columns)
            logger.info(f"Columnas encontradas: {list(df.columns)}")
            
            # Renombrar columnas usando búsqueda flexible
            df = self._rename_columns_flexible(df)
            logger.info(f"Columnas después de renombrar: {list(df.columns)}")
            
            # Filtrar por status (hacer case-insensitive y flexible)
            if 'Status' not in df.columns:
                logger.error("Columna 'Status' no encontrada en el archivo")
                return {
                    'data': [],
                    'original_count': len(df),
                    'filtered_count': 0
                }
            
            # Normalizar status para comparación
            df['Status_normalized'] = df['Status'].astype(str).str.strip().str.lower()
            
            # Ver qué status únicos hay
            unique_statuses = df['Status'].unique()
            logger.info(f"Status únicos encontrados: {list(unique_statuses)}")
            
            valid_status_normalized = ['abierto', 'on hold']
            df_filtered = df[df['Status_normalized'].isin(valid_status_normalized)].copy()
            logger.info(f"Proyectos filtrados (Abierto/On Hold): {len(df_filtered)}")
            
            # Filtrar Location != LLC y Location != 0 (esos se procesan por separado o se excluyen)
            if 'Location' in df_filtered.columns:
                initial_count = len(df_filtered)
                
                # Normalizar Location para análisis
                location_normalized = df_filtered['Location'].astype(str).str.upper().str.strip()
                
                # Contar cuántos de cada tipo hay antes de excluir
                llc_count = (location_normalized == 'LLC').sum()
                zero_count = (location_normalized == '0').sum()
                
                # Excluir LLC y 0
                excluded_values = ['LLC', '0']
                df_filtered = df_filtered[~location_normalized.isin(excluded_values)].copy()
                
                excluded_count = initial_count - len(df_filtered)
                logger.info(f"Registros excluidos por Location: {excluded_count} (LLC: {llc_count}, 0: {zero_count})")
                logger.info(f"Proyectos SAPI válidos después de filtrar: {len(df_filtered)}")
            
            # Filtrar Project Name != "Not Found" (excluir proyectos sin identificar)
            if 'Project Name' in df_filtered.columns:
                initial_count = len(df_filtered)
                
                # Normalizar Project Name para análisis
                project_normalized = df_filtered['Project Name'].astype(str).str.strip()
                
                # Contar cuántos tienen "Not Found"
                not_found_count = (project_normalized.str.upper() == 'NOT FOUND').sum()
                
                # Excluir "Not Found" (case-insensitive)
                df_filtered = df_filtered[project_normalized.str.upper() != 'NOT FOUND'].copy()
                
                if not_found_count > 0:
                    logger.info(f"Registros excluidos con Project Name 'Not Found': {not_found_count}")
                    logger.info(f"Proyectos válidos después de filtrar 'Not Found': {len(df_filtered)}")
            
            if df_filtered.empty:
                logger.warning("No hay proyectos con status Abierto u On Hold")
                return {
                    'data': [],
                    'original_count': len(df),
                    'filtered_count': 0
                }
            
            # Limpiar y convertir valores
            df_filtered = self._clean_data(df_filtered)
            
            # Verificar si _clean_data devolvió DataFrame vacío
            if df_filtered.empty:
                logger.warning("No hay datos válidos después de la limpieza")
                return {
                    'data': [],
                    'original_count': len(df),
                    'filtered_count': 0,
                    'summary': {
                        'total_projects': 0,
                        'total_billing': 0,
                        'total_po': 0,
                        'bu_distribution': {},
                        'monthly_distribution': {},
                        'status_distribution': {},
                        'tbd_projects': []
                    }
                }
            
            # Crear tabla pivot estilo forecast
            billing_table = self._create_billing_table(df_filtered, billing_type=billing_type)
            
            return {
                'data': billing_table,
                'original_count': len(df),
                'filtered_count': len(df_filtered),
                'summary': self._create_summary(df_filtered, billing_table)
            }
            
        except Exception as e:
            import traceback
            logger.error(f"Error procesando archivo de KPIs: {str(e)}")
            logger.error(f"Traceback completo: {traceback.format_exc()}")
            raise
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Limpia y convierte los datos.
        
        Args:
            df: DataFrame a limpiar
            
        Returns:
            DataFrame limpio
        """
        df = df.copy()
        
        logger.info(f"Iniciando limpieza de {len(df)} registros")
        
        # Limpiar Total de PO
        if 'Total de PO' in df.columns:
            df['Total de PO'] = pd.to_numeric(df['Total de PO'], errors='coerce').fillna(0)
            logger.info(f"Total de PO procesado: {df['Total de PO'].notna().sum()} valores válidos")
        else:
            logger.warning("Columna 'Total de PO' no encontrada")
            df['Total de PO'] = 0
        
        # Identificar proyectos con Costo de Venta TBD
        df['Costo_TBD'] = False
        if 'Costo de Venta' in df.columns:
            # Detectar valores TBD (como string)
            tbd_mask = df['Costo de Venta'].astype(str).str.upper().str.strip() == 'TBD'
            df.loc[tbd_mask, 'Costo_TBD'] = True
            
            # Convertir a numérico (TBD se convierte en NaN)
            df['Costo de Venta'] = pd.to_numeric(df['Costo de Venta'], errors='coerce').fillna(0)
            logger.info(f"Costo de Venta procesado: {tbd_mask.sum()} proyectos con TBD")
        else:
            logger.warning("Columna 'Costo de Venta' no encontrada")
            df['Costo de Venta'] = 0
        
        # Limpiar % Facturación (convertir de porcentaje a decimal)
        if '% Facturación' in df.columns:
            df['% Facturación'] = pd.to_numeric(df['% Facturación'], errors='coerce').fillna(0)
            # Si está en formato porcentaje (>1), convertir a decimal
            mask_percentage = df['% Facturación'] > 1
            if mask_percentage.any():
                df.loc[mask_percentage, '% Facturación'] = df.loc[mask_percentage, '% Facturación'] / 100
                logger.info(f"Convertidos {mask_percentage.sum()} valores de porcentaje a decimal")
        else:
            logger.warning("Columna '% Facturación' no encontrada")
            df['% Facturación'] = 0
        
        # Convertir fecha
        if 'Probable fecha de facturación' in df.columns:
            df['Probable fecha de facturación'] = pd.to_datetime(
                df['Probable fecha de facturación'], 
                errors='coerce',
                dayfirst=True  # Formato DD/MM/AAAA
            )
            valid_dates = df['Probable fecha de facturación'].notna().sum()
            logger.info(f"Fechas válidas: {valid_dates} de {len(df)}")
        else:
            logger.error("Columna 'Probable fecha de facturación' no encontrada")
            return pd.DataFrame()  # Retornar DataFrame vacío si no hay fechas
        
        # Eliminar registros sin fecha válida
        df = df[df['Probable fecha de facturación'].notna()].copy()
        
        if df.empty:
            logger.warning("No quedan registros después de filtrar fechas inválidas")
            return df
        
        # Calcular monto de facturación
        df['Monto Facturación'] = df['Total de PO'] * df['% Facturación']
        
        # Crear columna de mes-año
        df['Mes Facturación'] = df['Probable fecha de facturación'].dt.strftime('%B %Y')
        
        logger.info(f"Datos limpios: {len(df)} registros válidos con monto total de ${df['Monto Facturación'].sum():,.2f}")
        return df
    
    def _create_billing_table(self, df: pd.DataFrame, billing_type: str = "Contable") -> List[Dict]:
        """
        Crea tabla pivot estilo forecast.
        
        Args:
            df: DataFrame con datos limpios
            billing_type: Tipo de facturación ("Contable" o "Financiera")
            
        Returns:
            Lista de diccionarios con datos para la tabla
        """
        logger.info(f"Creando tabla de billing en modo: {billing_type}")
        if df.empty:
            return []
        
        # Validar que existe la columna Project Name
        if 'Project Name' not in df.columns:
            logger.error("Columna 'Project Name' no encontrada en DataFrame")
            logger.error(f"Columnas disponibles: {list(df.columns)}")
            return []
        
        # Obtener lista única de meses ordenados
        df_sorted = df.sort_values('Probable fecha de facturación')
        unique_months = df_sorted['Mes Facturación'].unique()
        
        # Crear diccionario para cada proyecto
        projects = []
        
        for project_name in df['Project Name'].unique():
            project_data = df[df['Project Name'] == project_name]
            
            # Verificar que hay datos
            if project_data.empty:
                continue
            
            # Información base del proyecto
            # Obtener Main BU de forma completamente segura
            main_bu = 'N/A'
            if 'Main BU' in project_data.columns and len(project_data) > 0:
                try:
                    bu_value = project_data['Main BU'].iloc[0]
                    # Forzar conversión a string sin importar el tipo
                    bu_str = str(bu_value)
                    # Validar que no sea un valor nulo representado como string
                    if bu_str and bu_str.strip() and bu_str.lower().strip() not in ['nan', 'none', '']:
                        main_bu = bu_str.strip()
                        # Limpiar símbolos especiales si existen
                        for symbol in ['↑', '↓', '→', '←', '⬆', '⬇', '➡', '⬅']:
                            main_bu = main_bu.replace(symbol, '')
                        main_bu = ' '.join(main_bu.split())  # Limpiar espacios múltiples
                except Exception as e:
                    logger.warning(f"Error extrayendo Main BU: {str(e)}")
                    main_bu = 'N/A'
            
            row = {
                'Proyecto': str(project_name),
                'BU': main_bu,
                'Location': str(project_data['Location'].iloc[0]) if 'Location' in project_data.columns and len(project_data) > 0 else 'N/A',
                'Status': str(project_data['Status'].iloc[0]) if len(project_data) > 0 else 'N/A',
                'Customer': str(project_data['Customer'].iloc[0]) if 'Customer' in project_data.columns and len(project_data) > 0 else 'N/A',
                'Total PO': float(project_data['Total de PO'].iloc[0]) if len(project_data) > 0 else 0,
                '% Facturación': f"{float(project_data['% Facturación'].iloc[0])*100:.0f}%" if len(project_data) > 0 else "0%",
                'Costo de Venta': float(project_data['Costo de Venta'].iloc[0]) if 'Costo de Venta' in project_data.columns and len(project_data) > 0 else 0
            }
            
            # Inicializar todos los meses en 0
            for month in unique_months:
                row[month] = 0
            
            # Asignar montos según tipo de facturación
            if billing_type == "Financiera":
                # Modo Financiero: Todo el monto (100% del Total PO) en el último mes de facturación
                # Ordenar por fecha para encontrar el último evento
                project_data_sorted = project_data.sort_values('Probable fecha de facturación')
                last_month = project_data_sorted.iloc[-1]['Mes Facturación']
                
                # Asignar 100% del Total PO en el último mes (sin factores de castigo)
                if last_month in row:
                    row[last_month] = row['Total PO']
                    logger.debug(f"Proyecto '{project_name}' - Modo Financiero: ${row['Total PO']:,.2f} en {last_month}")
            else:
                # Modo Contable: Distribuir según eventos de facturación
                for _, event in project_data.iterrows():
                    month = event['Mes Facturación']
                    if month in row:
                        row[month] += event['Monto Facturación']
            
            projects.append(row)
        
        logger.info(f"Tabla de billing creada: {len(projects)} proyectos")
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
        total_projects = len(df['Project Name'].unique()) if 'Project Name' in df.columns else 0
        total_billing = df['Monto Facturación'].sum() if 'Monto Facturación' in df.columns else 0
        total_po = df['Total de PO'].sum() if 'Total de PO' in df.columns else 0
        
        summary = {
            'total_projects': total_projects,
            'total_billing': total_billing,
            'total_po': total_po,
            'bu_distribution': {},
            'monthly_distribution': {},
            'status_distribution': df['Status'].value_counts().to_dict() if 'Status' in df.columns else {},
            'tbd_projects': []
        }
        
        # Distribución por BU
        if 'Main BU' in df.columns and 'Monto Facturación' in df.columns:
            try:
                # Limpiar Main BU para groupby
                df_temp = df.copy()
                df_temp['Main BU'] = df_temp['Main BU'].fillna('').astype(str).str.strip()
                
                # Remover símbolos especiales
                for symbol in ['↑', '↓', '→', '←', '⬆', '⬇', '➡', '⬅']:
                    df_temp['Main BU'] = df_temp['Main BU'].str.replace(symbol, '', regex=False)
                
                df_temp['Main BU'] = df_temp['Main BU'].str.strip()
                
                # Filtrar valores nulos y vacíos
                df_with_bu = df_temp[(df_temp['Main BU'].notna()) & (df_temp['Main BU'] != '') & (df_temp['Main BU'] != 'nan')].copy()
                
                if not df_with_bu.empty:
                    bu_totals = df_with_bu.groupby('Main BU', as_index=True)['Monto Facturación'].sum()
                    summary['bu_distribution'] = bu_totals.to_dict()
                    logger.info(f"Distribución por BU calculada: {len(bu_totals)} BUs")
            except Exception as e:
                logger.error(f"Error calculando distribución por BU: {str(e)}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                summary['bu_distribution'] = {}
        
        # Distribución mensual
        if 'Mes Facturación' in df.columns and 'Monto Facturación' in df.columns:
            try:
                # Filtrar valores nulos antes de agrupar
                df_with_mes = df[df['Mes Facturación'].notna()].copy()
                if not df_with_mes.empty:
                    monthly_totals = df_with_mes.groupby('Mes Facturación', as_index=True)['Monto Facturación'].sum()
                    summary['monthly_distribution'] = monthly_totals.to_dict()
                    logger.info(f"Distribución mensual calculada: {len(monthly_totals)} meses")
            except Exception as e:
                logger.error(f"Error calculando distribución mensual: {str(e)}")
                summary['monthly_distribution'] = {}
        
        # Proyectos con Costo de Venta TBD
        if 'Costo_TBD' in df.columns and 'Project Name' in df.columns:
            tbd_projects = df[df['Costo_TBD'] == True]['Project Name'].unique().tolist()
            summary['tbd_projects'] = tbd_projects
            logger.info(f"Proyectos con Costo de Venta TBD: {len(tbd_projects)}")
        
        return summary
    
    def _clean_column_headers(self, columns) -> list:
        """
        Limpia los nombres de las columnas removiendo símbolos especiales como flechas.
        
        Args:
            columns: Lista o Index de nombres de columnas
            
        Returns:
            list: Lista de nombres de columnas limpios
        """
        import re
        
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
    
    def _rename_columns_flexible(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Renombra las columnas del DataFrame buscando coincidencias flexibles.
        
        Args:
            df: DataFrame con columnas originales
            
        Returns:
            DataFrame con columnas renombradas
        """
        import re
        
        df = df.copy()
        rename_map = {}
        
        for col in df.columns:
            col_lower = str(col).lower().strip()
            
            # Project Name (priorizar 'Project Name' sobre 'Registro de proyecto')
            if col_lower == 'project name':
                rename_map[col] = 'Project Name'
            elif 'registro de proyecto' in col_lower and 'project name' not in [c.lower() for c in df.columns]:
                # Solo usar 'Registro de proyecto' si no existe 'Project Name'
                rename_map[col] = 'Project Name'
            
            # Status
            elif col_lower == 'status':
                rename_map[col] = 'Status'
            
            # Total de PO
            elif 'total' in col_lower and 'po' in col_lower:
                rename_map[col] = 'Total de PO'
            
            # % Facturación
            elif 'facturaci' in col_lower and '%' in col_lower:
                rename_map[col] = '% Facturación'
            
            # Probable fecha de facturación (con variaciones)
            # Prioridad a las columnas con "probable"
            elif col_lower.startswith('probable fecha'):
                rename_map[col] = 'Probable fecha de facturación'
            elif 'probable' in col_lower and 'fecha' in col_lower and 'facturaci' in col_lower:
                rename_map[col] = 'Probable fecha de facturación'
            
            # Main BU
            elif ('main bu' in col_lower or col_lower == 'bu') and not 'main bu2' in col_lower:
                rename_map[col] = 'Main BU'
            
            # Customer
            elif col_lower == 'customer':
                rename_map[col] = 'Customer'
            
            # Location
            elif col_lower in ['location', 'location ']:
                rename_map[col] = 'Location'
            
            # Costo de Venta
            elif 'costo' in col_lower and 'venta' in col_lower:
                rename_map[col] = 'Costo de Venta'
        
        if rename_map:
            logger.info(f"Mapeo de columnas aplicado:")
            for old_col, new_col in rename_map.items():
                logger.info(f"  '{old_col}' -> '{new_col}'")
            df.rename(columns=rename_map, inplace=True)
            logger.info(f"Columnas renombradas exitosamente: {list(rename_map.values())}")
        else:
            logger.warning("No se encontraron columnas para renombrar")
        
        return df
