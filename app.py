"""
Aplicación principal de Streamlit para Forecast Financiero.

Esta aplicación proporciona una interfaz web intuitiva para generar
proyecciones de ingresos por facturación basadas en el pipeline de oportunidades.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys
import os
import logging
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

# Agregar el directorio src al path para importar módulos
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'config'))

from src.data_processor import DataProcessor
from src.forecast_calculator import ForecastCalculator
from src.validators import DataValidator
from src.exporter import ForecastExporter, ReportGenerator
from src.aggrid_utils import AGGridConfigurator, AGGridExporter, GRID_CONFIGS
from src.grid_utils import GridResponseHandler
from src.ui_styles import apply_custom_styles, create_section_header, format_currency
from src.formatters import (
    format_currency as fmt_currency, 
    format_dataframe_currency_columns,
    format_aggrid_currency_columns,
    format_business_unit_icon,
    format_compact_currency,
    create_summary_stats
)
from config.settings import *


# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ForecastApp:
    """
    Clase principal de la aplicación Streamlit.
    
    Esta clase organiza toda la lógica de la interfaz de usuario
    y coordina los diferentes módulos de la aplicación.
    """
    
    def __init__(self):
        """Inicializa la aplicación con sus componentes."""
        self.validator = DataValidator()
        self.processor = DataProcessor()
        self.calculator = ForecastCalculator()
        self.exporter = ForecastExporter()
        self.report_generator = ReportGenerator()
        
        # Configurar página
        st.set_page_config(
            page_title=APP_CONFIG.APP_TITLE,
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    
    def run(self):
        """Ejecuta la aplicación principal."""
        # Aplicar estilos personalizados
        apply_custom_styles()
        
        self._render_header()
        self._render_sidebar()
        self._render_main_content()
    
    def _render_header(self):
        """Renderiza el encabezado de la aplicación."""
        # Header principal con diseño mejorado
        st.markdown(f"""
        <div style="text-align: center; padding: 2rem 0; background: linear-gradient(135deg, #1f4e79 0%, #2E86AB 100%); 
                    margin: -1rem -1rem 2rem -1rem; border-radius: 0 0 15px 15px; color: white;">
            <h1 style="margin: 0; font-size: 2.5rem; font-weight: 700; text-shadow: 0 2px 4px rgba(0,0,0,0.3);">
                📊 {SETTINGS['app_config'].APP_TITLE}
            </h1>
            <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem; opacity: 0.9;">
                Proyecciones de ingresos por facturación basadas en pipeline de oportunidades
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Mostrar reglas de negocio en un expander
        with st.expander("📋 Reglas de Negocio Aplicadas"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Reglas Generales:**")
                st.markdown(f"- Lead Time mínimo: {BUSINESS_RULES.MIN_LEAD_TIME} semanas")
                st.markdown(f"- Factor de castigo financiero: {BUSINESS_RULES.FINANCIAL_PENALTY_FACTOR_DEFAULT*100}%")
                st.markdown(f"- Días para DR: {BUSINESS_RULES.DR_DAYS_OFFSET}")
                st.markdown(f"- Días para SAT: {BUSINESS_RULES.SAT_DAYS_OFFSET}")
            
            with col2:
                st.markdown("**Porcentajes de Facturación (sin PIA):**")
                st.markdown(f"- INICIO: {BUSINESS_RULES.INICIO_PERCENTAGE*100}%")
                st.markdown(f"- DR: {BUSINESS_RULES.DR_PERCENTAGE*100}%")
                st.markdown(f"- FAT: {BUSINESS_RULES.FAT_PERCENTAGE*100}%")
                st.markdown(f"- SAT: {BUSINESS_RULES.SAT_PERCENTAGE*100}%")
    
    def _render_sidebar(self):
        """Renderiza la barra lateral con controles."""
        
        # Logo de iBtest en la parte superior
        try:
            st.sidebar.image("logo_ibtest.png", width=200)
        except:
            st.sidebar.markdown("### iBtest")
        
        st.sidebar.header("🔧 Controles")
        
        # Upload de archivo
        uploaded_file = st.sidebar.file_uploader(
            "Subir archivo C&N Funnel",
            type=['xlsx'],
            help="Sube el archivo Excel del funnel de oportunidades"
        )
        
        # Guardar archivo en session state
        if uploaded_file is not None:
            st.session_state.uploaded_file = uploaded_file
        
        # Configuración de reglas de negocio editables
        st.sidebar.header("⚙️ Reglas de Negocio")
        
        # Factor de castigo financiero con number_input
        st.session_state.penalty_default = st.sidebar.number_input(
            "Factor Castigo (General) %",
            min_value=10, max_value=100, value=40, step=5,
            help="Factor de castigo para probabilidades diferentes a 60%"
        ) / 100.0
        
        st.session_state.penalty_60 = st.sidebar.number_input(
            "Factor Castigo (60%) %",
            min_value=10, max_value=100, value=60, step=5,
            help="Factor de castigo para probabilidad del 60%"
        ) / 100.0
        
        # Porcentajes de facturación
        with st.sidebar.expander("📊 Porcentajes de Facturación"):
            st.session_state.inicio_pct = st.slider(
                "INICIO (%)", min_value=0, max_value=100, value=30, step=5
            ) / 100
            
            st.session_state.dr_pct = st.slider(
                "DR (%)", min_value=0, max_value=100, value=30, step=5
            ) / 100
            
            st.session_state.fat_pct = st.slider(
                "FAT (%)", min_value=0, max_value=100, value=30, step=5
            ) / 100
            
            st.session_state.sat_pct = st.slider(
                "SAT (%)", min_value=0, max_value=100, value=10, step=5
            ) / 100
            
            # Validar que sumen 100%
            total_pct = (st.session_state.inicio_pct + st.session_state.dr_pct + 
                        st.session_state.fat_pct + st.session_state.sat_pct)
            
            if abs(total_pct - 1.0) > 0.01:
                st.warning(f"⚠️ Los porcentajes suman {total_pct*100:.0f}%, no 100%")
        
        # Botón de procesamiento
        if st.sidebar.button("🚀 Procesar Forecast", type="primary"):
            if hasattr(st.session_state, 'uploaded_file'):
                self._process_forecast()
            else:
                st.sidebar.error("Por favor, sube un archivo primero")
        
        # Opciones de exportación
        if hasattr(st.session_state, 'forecast_results'):
            st.sidebar.header("📥 Exportar Resultados")
            
            if st.sidebar.button("📊 Descargar Excel"):
                self._export_excel()
            
            if st.sidebar.button("📄 Descargar CSV"):
                self._export_csv()
        
        # Información de la aplicación
        st.sidebar.markdown("---")
        st.sidebar.markdown("**Versión:** 1.0.2")
        st.sidebar.markdown("**Última actualización:** " + datetime.now().strftime("%d/%m/%Y"))
    
    def _render_main_content(self):
        """Renderiza el contenido principal."""
        if not hasattr(st.session_state, 'forecast_results'):
            self._render_welcome_screen()
        else:
            self._render_forecast_results()
    
    def _render_welcome_screen(self):
        """Renderiza la pantalla de bienvenida."""
        st.markdown("## 👋 Bienvenido")
        st.markdown("""
        Para comenzar, sube tu archivo C&N Funnel en la barra lateral y haz clic en **Procesar Forecast**.
        
        ### 📋 Requisitos del archivo:
        - Formato: Excel (.xlsx)
        - Debe contener las columnas requeridas
        
        ### 🔄 Proceso:
        1. **Validación**: Se verifican los datos de entrada
        2. **Limpieza**: Se procesan y ajustan los datos
        3. **Cálculo**: Se aplican las reglas de negocio
        4. **Visualización**: Se muestran los resultados
        """)
        
        # Mostrar ejemplo de estructura de datos
        with st.expander("📊 Estructura de Datos Esperada"):
            example_data = {
                'Opportunity Name': ['Proyecto A', 'Proyecto B', 'Proyecto C'],
                'BU': ['FCT', 'ICT', 'IAT'],
                'Amount': [100000, 50000, 75000],
                'Close Date': ['30/04/2025', '15/05/2025', '01/06/2025'],
                'Lead Time': [8, 12, 6],
                'Probability (%)  ↑': [0.25, 0.5, 0.25],
                'Paid in Advance': [0, 10000, 0],
                'Payment Terms': ['NET 30', 'NET 30', 'NET 30']
            }
            
            st.dataframe(pd.DataFrame(example_data), use_container_width=True)
    
    def _process_forecast(self):
        """Procesa el forecast completo."""
        try:
            with st.spinner("Procesando forecast..."):
                # Paso 1: Validar archivo
                file_validation = self.validator.validate_file(st.session_state.uploaded_file)
                if not file_validation.is_valid:
                    st.error("❌ " + "; ".join(file_validation.errors))
                    return
                
                # Paso 2: Leer archivo con detección automática
                df, parsing_report = self.processor.read_excel_file(st.session_state.uploaded_file)
                
                # Verificar que el parsing fue exitoso
                if not parsing_report.get('parsing_success', False):
                    missing_cols = parsing_report.get('validation_result', {}).get('missing_columns', [])
                    if missing_cols:
                        st.error(f"❌ No se pudieron encontrar las siguientes columnas requeridas: {', '.join(missing_cols)}")
                        st.info("💡 Verifica que el archivo tenga las columnas necesarias con nombres similares a: Opportunity Name, BU, Amount, Close Date, Lead Time, Payment Terms, Probability, Paid in Advance")
                        return
                
                # Paso 3: Procesar datos (incluye limpieza y completado)
                df_clean = self.processor.clean_and_prepare_data(df)
                
                # Paso 4: Validar datos procesados
                data_validation = self.validator.validate_dataframe(df_clean)
                
                # Mostrar advertencias si las hay (pero no bloquear el procesamiento)
                if data_validation.warnings:
                    for warning in data_validation.warnings[:5]:  # Mostrar solo las primeras 5
                        st.warning("⚠️ " + warning)
                
                # Paso 5: Convertir a objetos Opportunity
                opportunities = self.processor.convert_to_opportunities(df_clean)
                
                # Actualizar reglas de negocio con valores editables
                if hasattr(st.session_state, 'penalty_default'):
                    BUSINESS_RULES.FINANCIAL_PENALTY_FACTOR_DEFAULT = st.session_state.penalty_default
                    BUSINESS_RULES.FINANCIAL_PENALTY_FACTOR_60_PERCENT = st.session_state.penalty_60
                    BUSINESS_RULES.INICIO_PERCENTAGE = st.session_state.inicio_pct
                    BUSINESS_RULES.DR_PERCENTAGE = st.session_state.dr_pct
                    BUSINESS_RULES.FAT_PERCENTAGE = st.session_state.fat_pct
                    BUSINESS_RULES.SAT_PERCENTAGE = st.session_state.sat_pct
                
                # Paso 6: Calcular forecast
                billing_events = self.calculator.calculate_forecast(opportunities)
                
                # Paso 7: Generar resumen y tablas
                summary = self.calculator.generate_forecast_summary(billing_events)
                forecast_table = self.calculator.create_forecast_table(billing_events)
                cost_of_sale_table = self.calculator.create_cost_of_sale_table(billing_events)
                
                # Guardar resultados en session state
                st.session_state.forecast_results = {
                    'billing_events': billing_events,
                    'summary': summary,
                    'forecast_table': forecast_table,
                    'cost_of_sale_table': cost_of_sale_table,
                    'processing_summary': self.processor.get_processing_summary(df, df_clean, parsing_report),
                    'validation_result': data_validation,
                    'parsing_report': parsing_report
                }
                
                st.success("✅ " + INFO_MESSAGES['processing_complete'])
                st.rerun()
                
        except Exception as e:
            logger.error(f"Error en procesamiento: {str(e)}")
            st.error(f"❌ Error: {str(e)}")
    
    def _render_forecast_results(self):
        """Renderiza los resultados del forecast."""
        results = st.session_state.forecast_results
        
        # Métricas principales
        self._render_key_metrics(results['summary'])
        
        # Tabs para diferentes vistas
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📊 Forecast", "💰 Costo de Venta", "📈 Gráficos", "📋 Detalles", "🎯 Análisis", "⚙️ Procesamiento"
        ])
        
        with tab1:
            self._render_forecast_table(results['forecast_table'])
        
        with tab2:
            self._render_cost_of_sale_tab(results['cost_of_sale_table'])
        
        with tab3:
            self._render_charts(results['summary'], results['billing_events'])
        
        with tab4:
            self._render_details(results['billing_events'])
        
        with tab5:
            self._render_analysis(results['billing_events'])
        
        with tab6:
            self._render_processing_info(results['processing_summary'], results['validation_result'])
    
    def _render_key_metrics(self, summary):
        """Renderiza las métricas clave."""
        create_section_header("Resumen Ejecutivo", "Métricas principales del forecast", "📊")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "💰 Total Forecast",
                fmt_currency(summary.total_amount, decimals=2),
                help="Monto total proyectado con ajustes aplicados"
            )
        
        with col2:
            st.metric(
                "🎯 Oportunidades",
                f"{summary.total_opportunities:,}",
                help="Número de oportunidades procesadas"
            )
        
        with col3:
            st.metric(
                "📅 Eventos",
                f"{summary.total_events:,}",
                help="Número total de eventos de facturación"
            )
        
        with col4:
            st.metric(
                "⏱️ Duración",
                f"{summary.duration_months} meses",
                help="Duración del forecast en meses"
            )
    
    def _render_forecast_table(self, forecast_table):
        """Renderiza la tabla principal del forecast."""
        create_section_header("Tabla de Forecast", "Distribución mensual por proyecto", "📋")
        
        if len(forecast_table['data']) == 0:
            st.warning("No hay datos para mostrar")
            return
        
        df = pd.DataFrame(forecast_table['data'])
        
        # Extraer BU de los nombres de proyecto
        #df['BU'] = df['Proyecto'].str.extract(r'\(([^)]+)\)$')[0]
        
        # Controles de la tabla
        col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
        
        with col1:
            company_options = ['Todas'] + sorted(df['Empresa'].dropna().unique().tolist())
            selected_company = st.selectbox("Filtrar por Empresa:", company_options)
        
        with col2:
            bu_options = ['Todas'] + sorted(df['BU'].dropna().unique().tolist())
            selected_bu = st.selectbox("Filtrar por BU:", bu_options)
        
        with col3:
            show_grouping = st.checkbox("Agrupar por BU", value=True)
        
        with col4:
            export_format = st.selectbox("Formato Export:", ["CSV", "Excel"])
        
        # Aplicar filtros
        df_filtered = df.copy()
        
        if selected_company != 'Todas':
            df_filtered = df_filtered[df_filtered['Empresa'] == selected_company]
        
        if selected_bu != 'Todas':
            df_filtered = df_filtered[df_filtered['BU'] == selected_bu]
        
        # Agregar fila de totales al final
        df_with_totals = self._add_totals_row(df_filtered, 'TOTAL FORECAST')
        
        # Configurar AG-Grid
        gb = AGGridConfigurator.configure_forecast_table(df_with_totals)
        
        # Estilo especial para la fila de totales
        row_style_jscode = JsCode("""
        function(params) {
            if (params.data.Proyecto === 'TOTAL FORECAST') {
                return {
                    'backgroundColor': '#E3F2FD',
                    'fontWeight': 'bold',
                    'borderTop': '2px solid #2E86AB'
                }
            }
            return null;
        }
        """)
        
        # Configuraciones específicas según filtros
        if selected_bu != 'Todas' or not show_grouping:
            # Si hay filtro específico o no se quiere agrupación, desactivar agrupación
            gb.configure_column("BU", rowGroup=False, hide=False)
            gb.configure_grid_options(groupDefaultExpanded=0, getRowStyle=row_style_jscode)
        else:
            gb.configure_grid_options(getRowStyle=row_style_jscode)
        
        # Renderizar AG-Grid
        grid_config = GRID_CONFIGS['forecast_main'].copy()
        grid_config['height'] = AGGridConfigurator.get_grid_height(len(df_with_totals), 600)
        
        st.markdown("#### 📊 Tabla Interactiva de Forecast")
        st.info("📌 La última fila muestra los **totales mensuales** (fondo azul claro)")
        
        grid_response = AgGrid(
            df_with_totals,
            gridOptions=gb.build(),
            height=grid_config['height'],
            theme=grid_config['theme'],
            allow_unsafe_jscode=grid_config['allow_unsafe_jscode'],
            update_mode=grid_config['update_mode'],
            fit_columns_on_grid_load=grid_config['fit_columns_on_grid_load'],
            enable_enterprise_modules=grid_config['enable_enterprise_modules']
        )
        
        # Mostrar estadísticas y controles adicionales usando GridResponseHandler
        grid_handler = GridResponseHandler(grid_response)
        
        if grid_handler.has_data:
            # Filtrar la fila de totales para calcular métricas
            df_forecast_metrics = grid_handler.data_df[grid_handler.data_df['Proyecto'] != 'TOTAL FORECAST'].copy()
            
            col_stats1, col_stats2, col_stats3 = st.columns(3)
            
            with col_stats1:
                st.metric("📋 Proyectos", len(df_forecast_metrics))
            
            with col_stats2:
                numeric_columns = df_forecast_metrics.select_dtypes(include=['number']).columns
                numeric_columns = [col for col in numeric_columns if col not in ['BU']]
                if len(numeric_columns) > 0:
                    total_forecast = 0
                    for col in numeric_columns:
                        total_forecast += pd.to_numeric(df_forecast_metrics[col], errors='coerce').sum()
                    st.metric("💰 Total Forecast", f"${total_forecast:,.0f}")
            
            with col_stats3:
                filters_active = []
                if selected_company != 'Todas':
                    filters_active.append(f"Empresa: {selected_company}")
                if selected_bu != 'Todas':
                    filters_active.append(f"BU: {selected_bu}")
                
                if filters_active:
                    st.info(f"🎯 Filtrado por: **{', '.join(filters_active)}**")
                else:
                    unique_bus = df_forecast_metrics['BU'].nunique()
                    st.metric("🏢 BUs Activas", unique_bus)
            
            # Controles de exportación y selección
            st.markdown("#### 🔧 Controles Avanzados")
            col_control1, col_control2, col_control3 = st.columns(3)
            
            with col_control1:
                if st.button("📥 Exportar Datos Visibles", key="export_visible"):
                    try:
                        # Excluir fila de totales de la exportación
                        df_export = df_with_totals[df_with_totals['Proyecto'] != 'TOTAL FORECAST'].copy()
                        
                        if export_format == "CSV":
                            export_data = df_export.to_csv(index=False)
                            st.download_button(
                                label="⬇️ Descargar CSV",
                                data=export_data,
                                file_name=f"forecast_{selected_bu}_{datetime.now().strftime('%Y%m%d')}.csv",
                                mime="text/csv"
                            )
                        else:
                            # Usar función con formato de moneda
                            buffer = self._export_to_excel_with_format(df_export, 'Forecast')
                            st.download_button(
                                label="⬇️ Descargar Excel",
                                data=buffer.getvalue(),
                                file_name=f"forecast_{selected_bu}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                    except Exception as e:
                        st.error(f"Error al exportar: {str(e)}")
            
            with col_control2:
                if grid_handler.has_selection:
                    st.success(f"✅ {grid_handler.selected_count} filas seleccionadas")
                    
                    if st.button("📥 Exportar Seleccionadas", key="export_selected"):
                        try:
                            selected_data = grid_handler.selected_data
                            # Excluir fila de totales si está seleccionada
                            selected_data = selected_data[selected_data['Proyecto'] != 'TOTAL FORECAST']
                            
                            if export_format == "CSV":
                                csv_data = selected_data.to_csv(index=False)
                                st.download_button(
                                    label="⬇️ Descargar Selección CSV",
                                    data=csv_data,
                                    file_name=f"forecast_seleccion_{datetime.now().strftime('%Y%m%d')}.csv",
                                    mime="text/csv"
                                )
                            else:
                                # Usar función con formato de moneda
                                buffer = self._export_to_excel_with_format(selected_data, 'Selección')
                                st.download_button(
                                    label="⬇️ Descargar Selección Excel",
                                    data=buffer.getvalue(),
                                    file_name=f"forecast_seleccion_{datetime.now().strftime('%Y%m%d')}.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                )
                        except Exception as e:
                            st.error(f"Error al exportar selección: {str(e)}")
                else:
                    st.info("💡 Selecciona filas para exportar")
            
            with col_control3:
                # Mostrar información de filtros aplicados
                filters_info = {
                    'BU': selected_bu if selected_bu != 'Todas' else None,
                    'Agrupación': 'Activa' if show_grouping else 'Desactivada'
                }
                active_filters = [f"{k}: {v}" for k, v in filters_info.items() if v]
                
                if active_filters:
                    st.info(f"🔍 {', '.join(active_filters)}")
                else:
                    st.info("📊 Vista completa")
    
    def _export_to_excel_with_format(self, df, sheet_name='Datos'):
        """
        Exporta DataFrame a Excel con formato de moneda en columnas numéricas.
        
        Args:
            df: DataFrame a exportar
            sheet_name: Nombre de la hoja
            
        Returns:
            BytesIO: Buffer con archivo Excel formateado
        """
        from io import BytesIO
        from openpyxl.styles import numbers
        
        buffer = BytesIO()
        
        # Identificar columnas numéricas (excluyendo columnas de texto)
        text_columns = ['Proyecto', 'BU', 'Empresa', 'Company']
        numeric_columns = [col for col in df.columns if col not in text_columns]
        
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name=sheet_name)
            
            # Obtener la hoja de trabajo
            worksheet = writer.sheets[sheet_name]
            
            # Aplicar formato de moneda a columnas numéricas
            for idx, col in enumerate(df.columns, start=1):
                if col in numeric_columns:
                    col_letter = worksheet.cell(row=1, column=idx).column_letter
                    
                    # Aplicar formato de moneda (ej: $1,234.56)
                    for row in range(2, len(df) + 2):  # +2 porque empezamos en row 2 (después del header)
                        cell = worksheet[f'{col_letter}{row}']
                        try:
                            if cell.value and isinstance(cell.value, (int, float)):
                                cell.number_format = '$#,##0.00'
                        except:
                            pass
            
            # Ajustar ancho de columnas
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        buffer.seek(0)
        return buffer
    
    def _add_totals_row(self, df, label='TOTAL'):
        """
        Agrega una fila de totales al final del DataFrame.
        
        Args:
            df: DataFrame al que agregar totales
            label: Etiqueta para la fila de totales
            
        Returns:
            DataFrame con fila de totales agregada
        """
        if df.empty:
            return df
        
        # Crear copia del DataFrame
        df_copy = df.copy()
        
        # Identificar columnas no numéricas (textuales)
        text_columns = ['Proyecto', 'BU', 'Empresa', 'Company']
        # Columnas que deben sumarse aunque tengan nombres específicos
        numeric_summary_columns = ['Amount Total', 'Gross Margin', 'Costo de Venta']
        
        # Crear fila de totales
        totals_row = {}
        
        # Primera columna lleva el label
        first_col = df_copy.columns[0]
        totals_row[first_col] = label
        
        # Procesar cada columna
        for col in df_copy.columns:
            if col == first_col:
                continue
            elif col in text_columns:
                # Columnas de texto quedan vacías
                totals_row[col] = ''
            else:
                # Sumar columnas numéricas (incluyendo Amount Total, Gross Margin, Costo de Venta)
                try:
                    # Asegurar que los valores sean numéricos
                    col_values = pd.to_numeric(df_copy[col], errors='coerce').fillna(0)
                    totals_row[col] = col_values.sum()
                except:
                    totals_row[col] = ''
        
        # Convertir a DataFrame y concatenar
        totals_df = pd.DataFrame([totals_row])
        result_df = pd.concat([df_copy, totals_df], ignore_index=True)
        
        return result_df
    
    def _render_forecast_monthly_totals(self, forecast_table, df_filtered):
        """Renderiza los totales mensuales de la tabla de Forecast."""
        if 'monthly_totals' not in forecast_table:
            return
        
        st.markdown("---")
        st.markdown("#### 📊 Totales Mensuales - Forecast")
        
        monthly_totals = forecast_table['monthly_totals']
        
        # Calcular totales solo de los meses que aparecen en el DataFrame filtrado
        month_columns = [col for col in df_filtered.columns if col not in ['Proyecto', 'BU', 'Empresa']]
        
        # Crear DataFrame de totales
        totals_data = []
        for month in month_columns:
            # Sumar valores del DataFrame filtrado
            month_total = df_filtered[month].sum() if month in df_filtered.columns else 0
            totals_data.append({
                'Mes': month,
                'Total': month_total
            })
        
        if totals_data:
            df_totals = pd.DataFrame(totals_data)
            
            # Crear gráfico de barras horizontal con totales
            fig_totals = px.bar(
                df_totals,
                x='Total',
                y='Mes',
                orientation='h',
                title='Totales Mensuales del Forecast',
                labels={'Total': 'Monto Total ($)', 'Mes': 'Período'},
                text='Total'
            )
            
            fig_totals.update_traces(
                texttemplate='$%{text:,.0f}',
                textposition='outside',
                marker_color='#2E86AB',
                textfont_size=10
            )
            
            fig_totals.update_layout(
                height=max(300, len(df_totals) * 35),
                title_font_size=16,
                title_font_color='#1f4e79',
                font=dict(family="Arial, sans-serif", size=11, color="#2c3e50"),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                showlegend=False,
                xaxis_title="Total Facturado ($)",
                yaxis_title="",
                yaxis={'categoryorder':'total ascending'}
            )
            
            st.plotly_chart(fig_totals, use_container_width=True)
            
            # Mostrar tabla con totales
            st.markdown("##### 📋 Tabla de Totales")
            df_totals['Total'] = df_totals['Total'].apply(lambda x: f"${x:,.2f}")
            st.dataframe(
                df_totals,
                use_container_width=True,
                hide_index=True
            )
            
            # Mostrar gran total
            grand_total = sum([item['Total'] for item in totals_data])
            st.metric("💰 Gran Total", f"${grand_total:,.2f}")
    
    def _render_cost_of_sale_tab(self, cost_table):
        """Renderiza la pestaña completa de Costo de Venta."""
        if len(cost_table['data']) == 0:
            st.warning("No hay datos de costo de venta disponibles")
            return
        
        create_section_header("Costo de Venta", "Costo de venta calculado en el último mes de facturación", "💰")
        
        df_cost = pd.DataFrame(cost_table['data'])
        
        # Controles superiores
        # Filtros de la tabla de costos
        #st.markdown("#### 🔍 Filtros")
        col_ctrl1, col_ctrl2, col_ctrl3, col_ctrl4 = st.columns([2, 2, 1, 1])
        
        with col_ctrl1:
            company_options_cost = ['Todas'] + sorted(df_cost['Empresa'].dropna().unique().tolist())
            selected_company_cost = st.selectbox("Filtrar por Empresa:", company_options_cost, key="cost_company_filter")
        
        with col_ctrl2:
            bu_options_cost = ['Todas'] + sorted(df_cost['BU'].dropna().unique().tolist())
            selected_bu_cost = st.selectbox("Filtrar por BU:", bu_options_cost, key="cost_bu_filter")
        
        with col_ctrl3:
            show_grouping_cost = st.checkbox("Agrupar por BU", value=True, key="group_by_bu_cost")
        
        with col_ctrl4:
            export_format_cost = st.selectbox(
                "Formato de Exportación",
                ["Excel", "CSV"],
                key="export_format_cost"
            )
        
        # Aplicar filtros
        df_cost_filtered = df_cost.copy()
        
        if selected_company_cost != 'Todas':
            df_cost_filtered = df_cost_filtered[df_cost_filtered['Empresa'] == selected_company_cost]
        
        if selected_bu_cost != 'Todas':
            df_cost_filtered = df_cost_filtered[df_cost_filtered['BU'] == selected_bu_cost]
        
        # Agregar fila de totales al final
        df_cost_with_totals = self._add_totals_row(df_cost_filtered, 'TOTAL COSTO')
        
        # Configurar AG-Grid con estilo especial para costo de venta
        gb_cost = AGGridConfigurator.configure_forecast_table(df_cost_with_totals)
        
        # Configuraciones específicas según agrupación
        if selected_bu_cost != 'Todas' or not show_grouping_cost:
            # Si hay filtro específico o no se quiere agrupación, desactivar agrupación
            gb_cost.configure_column("BU", rowGroup=False, hide=False)
            gb_cost.configure_grid_options(groupDefaultExpanded=0, getRowStyle=None)
        else:
            # Mantener agrupación por BU
            gb_cost.configure_grid_options(groupDefaultExpanded=1)
        
        # Aplicar color naranja #FCB72F a las columnas de meses con valores > 0
        month_columns = [col for col in df_cost_with_totals.columns if col not in ['Proyecto', 'BU', 'Empresa', 'Amount Total', 'Gross Margin', 'Costo de Venta']]
        
        for month_col in month_columns:
            # JsCode para colorear celdas con valores > 0 (excepto fila de totales)
            cell_style_jscode = JsCode("""
            function(params) {
                if (params.value > 0 && params.data.Proyecto !== 'TOTAL COSTO') {
                    return {
                        'backgroundColor': '#FCB72F',
                        'color': '#000000',
                        'fontWeight': 'bold'
                    }
                }
                return null;
            }
            """)
            
            gb_cost.configure_column(
                month_col,
                cellStyle=cell_style_jscode
            )
        
        # Estilo especial para la fila de totales
        row_style_jscode = JsCode("""
        function(params) {
            if (params.data.Proyecto === 'TOTAL COSTO') {
                return {
                    'backgroundColor': '#E8F5E9',
                    'fontWeight': 'bold',
                    'borderTop': '2px solid #2E86AB'
                }
            }
            return null;
        }
        """)
        
        # Aplicar estilo según configuración
        if selected_bu_cost != 'Todas' or not show_grouping_cost:
            gb_cost.configure_grid_options(groupDefaultExpanded=0, getRowStyle=row_style_jscode)
        else:
            gb_cost.configure_grid_options(groupDefaultExpanded=1, getRowStyle=row_style_jscode)
        
        # Renderizar AG-Grid
        grid_config_cost = GRID_CONFIGS['forecast_main'].copy()
        grid_config_cost['height'] = AGGridConfigurator.get_grid_height(len(df_cost_with_totals), 500)
        
        st.markdown("#### 💰 Tabla de Costo de Venta")
        st.info("📌 El costo de venta se muestra en el **mes del último evento** de cada proyecto (naranja). La última fila muestra los **totales mensuales** (fondo verde claro)")
        
        grid_response_cost = AgGrid(
            df_cost_with_totals,
            gridOptions=gb_cost.build(),
            height=grid_config_cost['height'],
            theme=grid_config_cost['theme'],
            allow_unsafe_jscode=grid_config_cost['allow_unsafe_jscode'],
            update_mode=grid_config_cost['update_mode'],
            fit_columns_on_grid_load=grid_config_cost['fit_columns_on_grid_load'],
            enable_enterprise_modules=grid_config_cost['enable_enterprise_modules']
        )
        
        # Estadísticas de la tabla de costos (excluyendo fila de totales)
        cost_handler = GridResponseHandler(grid_response_cost)
        
        if cost_handler.has_data:
            # Filtrar la fila de totales para calcular métricas
            df_cost_metrics = cost_handler.data_df[cost_handler.data_df['Proyecto'] != 'TOTAL COSTO'].copy()
            
            col_cost1, col_cost2, col_cost3 = st.columns(3)
            
            with col_cost1:
                st.metric("📋 Proyectos", len(df_cost_metrics))
            
            with col_cost2:
                if 'Costo de Venta' in df_cost_metrics.columns:
                    total_cost = pd.to_numeric(df_cost_metrics['Costo de Venta'], errors='coerce').sum()
                    st.metric("💰 Total Costo de Venta", f"${total_cost:,.0f}")
            
            with col_cost3:
                if 'Gross Margin' in df_cost_metrics.columns:
                    total_margin = pd.to_numeric(df_cost_metrics['Gross Margin'], errors='coerce').sum()
                    st.metric("📈 Total Gross Margin", f"${total_margin:,.0f}")
            
            # Controles de exportación
            st.markdown("#### 🔧 Controles Avanzados")
            col_control1, col_control2, col_control3 = st.columns(3)
            
            with col_control1:
                if st.button("📥 Exportar Datos Visibles", key="export_visible_cost"):
                    try:
                        # Excluir fila de totales de la exportación
                        df_export_cost = df_cost_with_totals[df_cost_with_totals['Proyecto'] != 'TOTAL COSTO'].copy()
                        
                        if export_format_cost == "CSV":
                            export_data = df_export_cost.to_csv(index=False)
                            st.download_button(
                                label="⬇️ Descargar CSV",
                                data=export_data,
                                file_name=f"costo_venta_{selected_bu_cost}_{datetime.now().strftime('%Y%m%d')}.csv",
                                mime="text/csv"
                            )
                        else:
                            # Usar función con formato de moneda
                            buffer = self._export_to_excel_with_format(df_export_cost, 'Costo de Venta')
                            st.download_button(
                                label="⬇️ Descargar Excel",
                                data=buffer.getvalue(),
                                file_name=f"costo_venta_{selected_bu_cost}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                    except Exception as e:
                        st.error(f"Error al exportar: {str(e)}")
            
            with col_control2:
                if cost_handler.has_selection:
                    st.success(f"✅ {cost_handler.selected_count} filas seleccionadas")
                    
                    if st.button("📥 Exportar Seleccionadas", key="export_selected_cost"):
                        try:
                            selected_data = cost_handler.selected_data
                            # Excluir fila de totales si está seleccionada
                            selected_data = selected_data[selected_data['Proyecto'] != 'TOTAL COSTO']
                            
                            if export_format_cost == "CSV":
                                csv_data = selected_data.to_csv(index=False)
                                st.download_button(
                                    label="⬇️ Descargar Selección CSV",
                                    data=csv_data,
                                    file_name=f"costo_venta_seleccion_{datetime.now().strftime('%Y%m%d')}.csv",
                                    mime="text/csv"
                                )
                            else:
                                # Usar función con formato de moneda
                                buffer = self._export_to_excel_with_format(selected_data, 'Selección')
                                st.download_button(
                                    label="⬇️ Descargar Selección Excel",
                                    data=buffer.getvalue(),
                                    file_name=f"costo_venta_seleccion_{datetime.now().strftime('%Y%m%d')}.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                )
                        except Exception as e:
                            st.error(f"Error al exportar selección: {str(e)}")
                else:
                    st.info("💡 Selecciona filas para exportar")
            
            with col_control3:
                # Mostrar información de filtros aplicados
                filters_info = {
                    'Empresa': selected_company_cost if selected_company_cost != 'Todas' else None,
                    'BU': selected_bu_cost if selected_bu_cost != 'Todas' else None,
                    'Agrupación': 'Activa' if show_grouping_cost else 'Desactivada'
                }
                active_filters = [f"{k}: {v}" for k, v in filters_info.items() if v]
                
                if active_filters:
                    st.info(f"🔍 {', '.join(active_filters)}")
                else:
                    st.info("📊 Vista completa")
    
    def _render_cost_monthly_totals(self, cost_table, df_cost_filtered):
        """Renderiza los totales mensuales de la tabla de Costo de Venta."""
        if 'monthly_totals' not in cost_table:
            return
        
        st.markdown("---")
        st.markdown("#### 💰 Totales Mensuales - Costo de Venta")
        
        # Calcular totales solo de los meses que aparecen en el DataFrame filtrado
        month_columns = [col for col in df_cost_filtered.columns 
                        if col not in ['Proyecto', 'BU', 'Empresa', 'Amount Total', 'Gross Margin', 'Costo de Venta']]
        
        # Crear DataFrame de totales
        totals_data = []
        for month in month_columns:
            # Sumar valores del DataFrame filtrado
            month_total = df_cost_filtered[month].sum() if month in df_cost_filtered.columns else 0
            if month_total > 0:  # Solo incluir meses con valores
                totals_data.append({
                    'Mes': month,
                    'Total': month_total
                })
        
        if totals_data:
            df_totals = pd.DataFrame(totals_data)
            
            # Crear gráfico de barras horizontal con totales
            fig_totals = px.bar(
                df_totals,
                x='Total',
                y='Mes',
                orientation='h',
                title='Totales Mensuales de Costo de Venta',
                labels={'Total': 'Costo Total ($)', 'Mes': 'Período'},
                text='Total'
            )
            
            fig_totals.update_traces(
                texttemplate='$%{text:,.0f}',
                textposition='outside',
                marker_color='#FCB72F',
                textfont_size=10
            )
            
            fig_totals.update_layout(
                height=max(300, len(df_totals) * 35),
                title_font_size=16,
                title_font_color='#1f4e79',
                font=dict(family="Arial, sans-serif", size=11, color="#2c3e50"),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                showlegend=False,
                xaxis_title="Total Costo de Venta ($)",
                yaxis_title="",
                yaxis={'categoryorder':'total ascending'}
            )
            
            st.plotly_chart(fig_totals, use_container_width=True)
            
            # Mostrar tabla con totales
            st.markdown("##### 📋 Tabla de Totales")
            df_totals['Total'] = df_totals['Total'].apply(lambda x: f"${x:,.2f}")
            st.dataframe(
                df_totals,
                use_container_width=True,
                hide_index=True
            )
            
            # Mostrar gran total
            grand_total = sum([item['Total'] for item in totals_data])
            
            col_total1, col_total2, col_total3 = st.columns(3)
            with col_total1:
                st.metric("💰 Gran Total Costo", f"${grand_total:,.2f}")
            
            with col_total2:
                if 'total_amount' in cost_table:
                    st.metric("📊 Total Amount", f"${cost_table['total_amount']:,.2f}")
            
            with col_total3:
                if 'total_gross_margin' in cost_table:
                    st.metric("📈 Total Gross Margin", f"${cost_table['total_gross_margin']:,.2f}")
    
    def _render_charts(self, summary, billing_events):
        """Renderiza los gráficos del forecast."""
        create_section_header("Visualizaciones", "Análisis gráfico del forecast", "📈")
        
        # Filtros independientes para cada visualización
        st.markdown("#### 🎯 Filtros de Visualización")
        col_filter1, col_filter2, col_filter3 = st.columns(3)
        
        with col_filter1:
            # Obtener lista de empresas disponibles
            available_companies = sorted(list(set([e.company for e in billing_events if e.company])))
            company_filter = st.selectbox(
                "Filtrar por Empresa",
                ['Todas'] + available_companies,
                key="chart_company_filter"
            )
        
        with col_filter2:
            # Obtener lista de BUs disponibles
            available_bus = list(summary.bu_distribution.keys())
            monthly_bu_filter = st.selectbox(
                "Filtrar por BU",
                ['Todas'] + available_bus,
                key="monthly_bu_filter"
            )
        
        #with col_filter2:
        #    temporal_bu_filter = st.selectbox(
        #        "Filtrar Evolución Temporal por BU",
        #        ['Todas'] + available_bus,
        #        key="temporal_bu_filter"
        #    )
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de distribución mensual con filtros independientes
            st.markdown("##### 📊 Distribución Mensual")
            
            # Aplicar filtros
            filtered_events = billing_events
            filter_labels = []
            
            if company_filter != 'Todas':
                filtered_events = [e for e in filtered_events if e.company == company_filter]
                filter_labels.append(company_filter)
            
            if monthly_bu_filter != 'Todas':
                filtered_events = [e for e in filtered_events if e.bu.value == monthly_bu_filter]
                filter_labels.append(monthly_bu_filter)
            
            if len(filter_labels) == 0:
                # Mostrar todos los datos
                monthly_data = pd.DataFrame([
                    {'Mes': month, 'Monto': amount}
                    for month, amount in summary.monthly_distribution.items()
                ])
                monthly_title_suffix = ""
            else:
                # Calcular distribución mensual filtrada
                monthly_filtered = {}
                for event in filtered_events:
                    month = event.month_year
                    monthly_filtered[month] = monthly_filtered.get(month, 0) + event.amount_adjusted
                
                monthly_data = pd.DataFrame([
                    {'Mes': month, 'Monto': amount}
                    for month, amount in monthly_filtered.items()
                ])
                monthly_title_suffix = f" - {' / '.join(filter_labels)}"
            
            if not monthly_data.empty:
                fig_monthly = px.bar(
                    monthly_data,
                    x='Mes',
                    y='Monto',
                    title=f'Ingresos por Mes{monthly_title_suffix}',
                    labels={'Monto': 'Monto ($)', 'Mes': 'Período'},
                    color='Monto',
                    color_continuous_scale=[[0, '#E3F2FD'], [0.5, '#2E86AB'], [1, '#1f4e79']]
                )
                fig_monthly.update_layout(
                    xaxis_tickangle=45,
                    showlegend=False,
                    yaxis_title="Ingresos Proyectados ($)",
                    title_font_size=16,
                    title_font_color='#1f4e79',
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(family="Arial, sans-serif", size=12, color="#2c3e50")
                )
                
                # Agregar valores en las barras
                fig_monthly.update_traces(
                    texttemplate='$%{y:,.2f}',
                    textposition='outside',
                    textfont_size=10,
                    textfont_color='#1f4e79'
                )
                
                st.plotly_chart(fig_monthly, use_container_width=True)
                
                # Mostrar total del filtro
                total_monthly = monthly_data['Monto'].sum()
                filter_text = ' / '.join(filter_labels) if filter_labels else 'Total'
                st.info(f"💰 Total {filter_text}: {fmt_currency(total_monthly, decimals=2)}")
            else:
                filter_text = ' / '.join(filter_labels) if filter_labels else 'este filtro'
                st.warning(f"No hay datos mensuales para mostrar para {filter_text}")
        
        with col2:
            # Gráfico de distribución por BU
            bu_data = pd.DataFrame([
                {'BU': bu, 'Monto': amount}
                for bu, amount in summary.bu_distribution.items()
            ])
            
            if not bu_data.empty:
                # Agregar iconos a los nombres de BU
                bu_data['BU_Display'] = bu_data['BU'].apply(
                    lambda x: f"{format_business_unit_icon(x)} {x}"
                )
                
                fig_bu = px.pie(
                    bu_data,
                    values='Monto',
                    names='BU_Display',
                    title='Distribución por Unidad de Negocio',
                    color_discrete_sequence=['#1f4e79', '#2E86AB', '#40E0D0', '#A23B72', '#28a745']
                )
                fig_bu.update_layout(
                    title_font_size=16,
                    title_font_color='#1f4e79',
                    font=dict(family="Arial, sans-serif", size=12, color="#2c3e50"),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                fig_bu.update_traces(
                    textposition='inside',
                    textinfo='percent+label',
                    hovertemplate='<b>%{label}</b><br>Monto: $%{value:,.2f}<br>Porcentaje: %{percent}<extra></extra>'
                )
                st.plotly_chart(fig_bu, use_container_width=True)
        
        # Gráfico de distribución por Empresa
        st.markdown("#### 🏢 Distribución por Empresa")
        
        # Calcular distribución por empresa
        company_distribution = {}
        for event in billing_events:
            company = event.company if event.company else 'Sin Clasificar'
            company_distribution[company] = company_distribution.get(company, 0) + event.amount_adjusted
        
        company_data = pd.DataFrame([
            {'Empresa': company, 'Monto': amount}
            for company, amount in company_distribution.items()
        ])
        
        if not company_data.empty:
            # Crear gráfico de barras para empresas
            fig_company = px.bar(
                company_data,
                x='Empresa',
                y='Monto',
                title='Distribución por Empresa (LLC, SAPI)',
                labels={'Monto': 'Monto ($)', 'Empresa': 'Tipo de Empresa'},
                color='Empresa',
                color_discrete_map={
                    'LLC': '#1f4e79',
                    'SAPI': '#2E86AB', 
                    'Sin Clasificar': '#cccccc'
                }
            )
            fig_company.update_layout(
                title_font_size=16,
                title_font_color='#1f4e79',
                font=dict(family="Arial, sans-serif", size=12, color="#2c3e50"),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                showlegend=False,
                yaxis_title="Ingresos Proyectados ($)"
            )
            fig_company.update_traces(
                texttemplate='$%{y:,.0f}',
                textposition='outside',
                textfont_size=12,
                textfont_color='#1f4e79'
            )
            st.plotly_chart(fig_company, use_container_width=True)
            
            # Mostrar métricas de distribución
            col_comp1, col_comp2, col_comp3 = st.columns(3)
            
            for idx, (company, amount) in enumerate(company_distribution.items()):
                col = [col_comp1, col_comp2, col_comp3][idx % 3]
                with col:
                    percentage = (amount / sum(company_distribution.values())) * 100
                    icon = "🏢" if company == "LLC" else "🏭" if company == "SAPI" else "⚪"
                    st.metric(
                        f"{icon} {company}",
                        f"${amount:,.0f}",
                        f"{percentage:.1f}%"
                    )
        
        # Gráfico de línea temporal
        st.markdown("#### 📅 Evolución Temporal")
        
        # Preparar datos para gráfico de línea (usando filtros aplicados)
        if len(filter_labels) == 0:
            # Usar datos completos
            temporal_monthly_distribution = summary.monthly_distribution
            temporal_title_suffix = ""
        else:
            # Usar datos filtrados (mismos filtros que distribución mensual)
            temporal_monthly_distribution = {}
            for event in filtered_events:
                month = event.month_year
                temporal_monthly_distribution[month] = temporal_monthly_distribution.get(month, 0) + event.amount_adjusted
            temporal_title_suffix = f" - {' / '.join(filter_labels)}"
        
        temporal_monthly_cumulative = []
        temporal_cumulative_amount = 0
        
        for month in sorted(temporal_monthly_distribution.keys()):
            temporal_cumulative_amount += temporal_monthly_distribution[month]
            temporal_monthly_cumulative.append({
                'Mes': month,
                'Mensual': temporal_monthly_distribution[month],
                'Acumulado': temporal_cumulative_amount
            })
        
        if temporal_monthly_cumulative:
            temporal_cumulative_df = pd.DataFrame(temporal_monthly_cumulative)
            
            fig_timeline = go.Figure()
            
            # Línea mensual
            fig_timeline.add_trace(go.Scatter(
                x=temporal_cumulative_df['Mes'],
                y=temporal_cumulative_df['Mensual'],
                mode='lines+markers',
                name='Ingresos Mensuales',
                line=dict(color='#2E86AB', width=4),
                marker=dict(size=10, color='#2E86AB'),
                fill=None
            ))
            
            # Línea acumulada (misma escala)
            fig_timeline.add_trace(go.Scatter(
                x=temporal_cumulative_df['Mes'],
                y=temporal_cumulative_df['Acumulado'],
                mode='lines+markers',
                name='Ingresos Acumulados',
                line=dict(color='#A23B72', width=4, dash='dot'),
                marker=dict(size=10, color='#A23B72')
            ))
            
            fig_timeline.update_layout(
                title=f'Evolución Temporal del Forecast{temporal_title_suffix}',
                xaxis_title='Período',
                yaxis_title='Monto ($)',
                xaxis_tickangle=45,
                hovermode='x unified',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                title_font_size=16,
                title_font_color='#1f4e79',
                font=dict(family="Arial, sans-serif", size=12, color="#2c3e50"),
                showlegend=True,
                yaxis=dict(
                    tickformat='$,.0f',
                    gridcolor='rgba(128,128,128,0.2)'
                ),
                xaxis=dict(
                    gridcolor='rgba(128,128,128,0.2)'
                )
            )
            
            st.plotly_chart(fig_timeline, use_container_width=True)
            
            # Mostrar total acumulado del filtro
            total_temporal = temporal_cumulative_df['Acumulado'].iloc[-1]
            filter_text = ' / '.join(filter_labels) if filter_labels else 'Total'
            st.info(f"💰 Total Acumulado {filter_text}: ${total_temporal:,.2f}")
        else:
            filter_text = ' / '.join(filter_labels) if filter_labels else 'este filtro'
            st.warning(f"No hay datos temporales para mostrar para {filter_text}")
    
    def _render_details(self, billing_events):
        """Renderiza los detalles de eventos de facturación."""
        st.markdown("### 📋 Detalles de Eventos de Facturación")
        
        if not billing_events:
            st.warning("No hay eventos para mostrar")
            return
        
        # Crear DataFrame con detalles
        details_data = []
        for event in billing_events:
            details_data.append({
                'Proyecto': event.opportunity_name,
                'BU': event.bu.value,
                'Empresa': event.company if event.company else 'Sin Clasificar',
                'Región': event.region if event.region else 'N/A',
                'Etapa': event.stage.value,
                'Fecha': event.date.strftime('%d/%m/%Y'),
                'Mes': event.month_year,
                'Monto Original': event.amount,
                'Monto Ajustado': event.amount_adjusted,
                'Probabilidad': event.probability,  # Mantener como decimal para AG-Grid
                'Lead Time': f"{event.lead_time_adjusted:.1f} sem"
            })
        
        details_df = pd.DataFrame(details_data)
        
        # Filtros avanzados
        st.markdown("#### 🎯 Filtros de Eventos")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            company_filter = st.selectbox(
                "Filtrar por Empresa",
                ['Todas'] + sorted(list(details_df['Empresa'].unique())),
                key="details_company_filter"
            )
        
        with col2:
            bu_filter = st.selectbox(
                "Filtrar por BU",
                ['Todas'] + sorted(list(details_df['BU'].unique())),
                key="details_bu_filter"
            )
        
        with col3:
            stage_filter = st.selectbox(
                "Filtrar por Etapa",
                ['Todas'] + sorted(list(details_df['Etapa'].unique())),
                key="details_stage_filter"
            )
        
        with col4:
            month_filter = st.selectbox(
                "Filtrar por Mes",
                ['Todos'] + sorted(list(details_df['Mes'].unique())),
                key="details_month_filter"
            )
        
        with col5:
            show_selection = st.checkbox("Mostrar solo seleccionados", key="show_selected_details")
        
        # Aplicar filtros
        filtered_df = details_df.copy()
        
        if company_filter != 'Todas':
            filtered_df = filtered_df[filtered_df['Empresa'] == company_filter]
        
        if bu_filter != 'Todas':
            filtered_df = filtered_df[filtered_df['BU'] == bu_filter]
        
        if stage_filter != 'Todas':
            filtered_df = filtered_df[filtered_df['Etapa'] == stage_filter]
        
        if month_filter != 'Todos':
            filtered_df = filtered_df[filtered_df['Mes'] == month_filter]
        
        # Configurar AG-Grid para detalles
        gb_details = AGGridConfigurator.configure_details_table(filtered_df)
        
        # Renderizar AG-Grid de detalles
        grid_config_details = GRID_CONFIGS['details'].copy()
        grid_config_details['height'] = AGGridConfigurator.get_grid_height(len(filtered_df), 500)
        
        st.markdown("#### 📋 Tabla Interactiva de Eventos de Facturación")
        
        details_grid_response = AgGrid(
            filtered_df,
            gridOptions=gb_details.build(),
            height=grid_config_details['height'],
            theme=grid_config_details['theme'],
            allow_unsafe_jscode=grid_config_details['allow_unsafe_jscode'],
            update_mode=grid_config_details['update_mode'],
            fit_columns_on_grid_load=grid_config_details['fit_columns_on_grid_load'],
            enable_enterprise_modules=grid_config_details['enable_enterprise_modules']
        )
        
        # Estadísticas de la tabla de detalles usando GridResponseHandler
        details_handler = GridResponseHandler(details_grid_response)
        
        if details_handler.has_data:
            col_det1, col_det2, col_det3, col_det4 = st.columns(4)
            
            with col_det1:
                st.metric("📊 Eventos", details_handler.total_rows)
            
            with col_det2:
                if 'Monto Ajustado' in details_handler.data_df.columns:
                    total_amount = details_handler.data_df['Monto Ajustado'].sum()
                    st.metric("💰 Total", f"${total_amount:,.0f}")
            
            with col_det3:
                st.metric("✅ Seleccionados", details_handler.selected_count)
            
            with col_det4:
                if 'Proyecto' in details_handler.data_df.columns:
                    unique_projects = details_handler.data_df['Proyecto'].nunique()
                    st.metric("🏗️ Proyectos", unique_projects)
            
            # Controles de exportación para detalles
            st.markdown("#### 🔧 Controles de Exportación")
            col_exp1, col_exp2, col_exp3 = st.columns(3)
            
            with col_exp1:
                if st.button("📥 Exportar Eventos Visibles", key="export_details_visible"):
                    try:
                        export_data = details_handler.export_data("csv")
                        st.download_button(
                            label="⬇️ Descargar CSV Eventos",
                            data=export_data,
                            file_name=f"eventos_facturacion_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv"
                        )
                    except Exception as e:
                        st.error(f"Error al exportar eventos: {str(e)}")
            
            with col_exp2:
                if details_handler.has_selection:
                    if st.button("📥 Exportar Eventos Seleccionados", key="export_details_selected"):
                        try:
                            export_data = details_handler.export_selected("csv")
                            st.download_button(
                                label="⬇️ Descargar Selección",
                                data=export_data,
                                file_name=f"eventos_seleccionados_{datetime.now().strftime('%Y%m%d')}.csv",
                                mime="text/csv"
                            )
                        except Exception as e:
                            st.error(f"Error al exportar selección: {str(e)}")
                else:
                    st.info("💡 Selecciona eventos para exportar")
            
            with col_exp3:
                # Resumen de filtros aplicados
                filters_applied = []
                if company_filter != 'Todas':
                    filters_applied.append(f"Empresa: {company_filter}")
                if bu_filter != 'Todas':
                    filters_applied.append(f"BU: {bu_filter}")
                if stage_filter != 'Todas':
                    filters_applied.append(f"Etapa: {stage_filter}")
                if month_filter != 'Todos':
                    filters_applied.append(f"Mes: {month_filter}")
                
                if filters_applied:
                    st.info(f"🔍 Filtros: {', '.join(filters_applied)}")
                else:
                    st.info("📊 Vista completa de eventos")
    
    def _render_analysis(self, billing_events):
        """Renderiza análisis adicionales."""
        st.markdown("### 🎯 Análisis de Riesgo")
        
        # Generar análisis de riesgo
        risk_analysis = self.report_generator.generate_risk_analysis(billing_events)
        
        if 'message' in risk_analysis:
            st.warning(risk_analysis['message'])
            return
        
        # Análisis por probabilidad
        st.markdown("#### 📊 Distribución por Riesgo")
        
        prob_dist = risk_analysis['probability_distribution']
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "🟢 Bajo Riesgo",
                f"${prob_dist['low_risk']['amount']:,.0f}",
                f"{prob_dist['low_risk']['count']} eventos"
            )
        
        with col2:
            st.metric(
                "🟡 Riesgo Medio",
                f"${prob_dist['medium_risk']['amount']:,.0f}",
                f"{prob_dist['medium_risk']['count']} eventos"
            )
        
        with col3:
            st.metric(
                "🔴 Alto Riesgo",
                f"${prob_dist['high_risk']['amount']:,.0f}",
                f"{prob_dist['high_risk']['count']} eventos"
            )
        
        # Análisis de concentración
        st.markdown("#### 🎯 Análisis de Concentración")
        
        conc_risk = risk_analysis['concentration_risk']
        
        if conc_risk['is_concentrated']:
            st.warning(f"⚠️ Alta concentración detectada: {conc_risk['max_bu_concentration']:.1%} en una sola BU")
        else:
            st.success(f"✅ Distribución balanceada: máxima concentración {conc_risk['max_bu_concentration']:.1%}")
        
        # Gráfico de concentración por BU
        conc_data = pd.DataFrame([
            {'BU': bu, 'Monto': amount, 'Porcentaje': amount/sum(conc_risk['bu_distribution'].values())*100}
            for bu, amount in conc_risk['bu_distribution'].items()
        ])
        
        fig_conc = px.bar(
            conc_data,
            x='BU',
            y='Porcentaje',
            title='Concentración por Unidad de Negocio (%)',
            labels={'Porcentaje': 'Porcentaje (%)', 'BU': 'Unidad de Negocio'}
        )
        
        st.plotly_chart(fig_conc, use_container_width=True)
    
    def _render_processing_info(self, processing_summary, validation_result):
        """Renderiza información del procesamiento."""
        st.markdown("### ⚙️ Información del Procesamiento")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📊 Resumen de Datos")
            st.metric("Registros Originales", processing_summary['original_records'])
            st.metric("Registros Válidos", processing_summary['valid_records'])
            excluded_100 = processing_summary.get('excluded_100_percent', 0)
            st.metric("Excluidos (100%)", excluded_100)
            st.metric("Tasa de Éxito", f"{processing_summary['success_rate']:.1%}")
            st.metric("Ajustes de Lead Time", processing_summary['lead_time_adjustments'])
        
        with col2:
            st.markdown("#### 🎯 Distribución de Datos")
            
            # Distribución por Empresa
            if 'company_distribution' in processing_summary and processing_summary['company_distribution']:
                st.markdown("**Por Empresa:**")
                for company, count in processing_summary['company_distribution'].items():
                    icon = "🏢" if company == "LLC" else "🏭" if company == "SAPI" else "⚪"
                    st.text(f"{icon} {company}: {count} oportunidades")
            
            # Distribución por BU
            st.markdown("**Por BU:**")
            for bu, count in processing_summary['bu_distribution'].items():
                st.text(f"• {bu}: {count} oportunidades")
            
            # Distribución por probabilidad
            st.markdown("**Por Probabilidad:**")
            for prob, count in processing_summary['probability_distribution'].items():
                st.text(f"• {prob:.0%}: {count} oportunidades")
        
        # Mostrar información de parsing del archivo
        if 'parsing_report' in st.session_state.forecast_results:
            parsing_info = st.session_state.forecast_results['parsing_report']
            
            st.markdown("#### 📄 Información de Parsing del Archivo")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Fila de Headers Detectada", parsing_info.get('detected_header_row', 'N/A'))
            
            with col2:
                st.metric("Columnas Originales", parsing_info.get('original_columns_count', 0))
            
            with col3:
                parsing_success = "✅ Exitoso" if parsing_info.get('parsing_success', False) else "❌ Con errores"
                st.metric("Estado del Parsing", parsing_success)
            
            # Mostrar mapeos de columnas aplicados
            if parsing_info.get('applied_mappings'):
                st.markdown("**Mapeos de Columnas Aplicados:**")
                for original, normalized in parsing_info['applied_mappings'].items():
                    st.text(f"• '{original}' → '{normalized}'")
            
            # Mostrar si se normalizó PIA
            if parsing_info.get('pia_normalization_applied'):
                st.info("💡 Se detectaron y normalizaron valores de 'Paid in Advance' desde porcentajes a montos")
        
        # Mostrar información sobre datos completados
        st.markdown("#### 🔧 Datos Completados Automáticamente")
        
        # Información sobre Lead Times completados
        if 'lead_time_source' in processing_summary:
            lead_time_stats = processing_summary.get('lead_time_completion', {})
            if lead_time_stats:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Lead Times Históricos", lead_time_stats.get('historical', 0))
                with col2:
                    st.metric("Lead Times Estimados", lead_time_stats.get('estimated', 0))
                with col3:
                    st.metric("Lead Times Originales", lead_time_stats.get('original', 0))
        
        # Información sobre Payment Terms completados
        if 'payment_terms_source' in processing_summary:
            payment_terms_stats = processing_summary.get('payment_terms_completion', {})
            if payment_terms_stats:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Payment Terms Históricos", payment_terms_stats.get('historical', 0))
                with col2:
                    st.metric("Payment Terms por Defecto", payment_terms_stats.get('default', 0))
                with col3:
                    st.metric("Payment Terms Originales", payment_terms_stats.get('original', 0))
        
        # Mostrar advertencias de validación
        if validation_result.warnings:
            st.markdown("#### ⚠️ Advertencias de Validación")
            for warning in validation_result.warnings[:10]:  # Mostrar máximo 10
                st.warning(warning)
    
    def _export_excel(self):
        """Exporta resultados a Excel."""
        try:
            results = st.session_state.forecast_results
            
            buffer = self.exporter.export_to_excel(
                results['billing_events'],
                results['forecast_table'],
                results['summary']
            )
            
            filename = self.exporter.create_downloadable_filename("forecast")
            
            st.download_button(
                label="📊 Descargar Excel",
                data=buffer.getvalue(),
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            st.success("✅ Archivo Excel preparado para descarga")
            
        except Exception as e:
            st.error(f"❌ Error al exportar Excel: {str(e)}")
    
    def _export_csv(self):
        """Exporta tabla de forecast a CSV."""
        try:
            results = st.session_state.forecast_results
            
            csv_content = self.exporter.export_forecast_table_to_csv(results['forecast_table'])
            
            filename = self.exporter.create_downloadable_filename("forecast").replace('.xlsx', '.csv')
            
            st.download_button(
                label="📄 Descargar CSV",
                data=csv_content,
                file_name=filename,
                mime="text/csv"
            )
            
            st.success("✅ Archivo CSV preparado para descarga")
            
        except Exception as e:
            st.error(f"❌ Error al exportar CSV: {str(e)}")


# Punto de entrada de la aplicación
if __name__ == "__main__":
    app = ForecastApp()
    app.run()
