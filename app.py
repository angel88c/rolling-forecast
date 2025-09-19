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
                
                # Paso 7: Generar resumen y tabla
                summary = self.calculator.generate_forecast_summary(billing_events)
                forecast_table = self.calculator.create_forecast_table(billing_events)
                
                # Guardar resultados en session state
                st.session_state.forecast_results = {
                    'billing_events': billing_events,
                    'summary': summary,
                    'forecast_table': forecast_table,
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
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Forecast", "📈 Gráficos", "📋 Detalles", "🎯 Análisis", "⚙️ Procesamiento"
        ])
        
        with tab1:
            self._render_forecast_table(results['forecast_table'])
        
        with tab2:
            self._render_charts(results['summary'], results['billing_events'])
        
        with tab3:
            self._render_details(results['billing_events'])
        
        with tab4:
            self._render_analysis(results['billing_events'])
        
        with tab5:
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
        df['BU'] = df['Proyecto'].str.extract(r'\(([^)]+)\)$')[0]
        
        # Controles de la tabla
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            bu_options = ['Todas'] + sorted(df['BU'].dropna().unique().tolist())
            selected_bu = st.selectbox("Filtrar por BU:", bu_options)
        
        with col2:
            show_grouping = st.checkbox("Agrupar por BU", value=True)
        
        with col3:
            export_format = st.selectbox("Formato Export:", ["CSV", "Excel"])
        
        # Aplicar filtro
        if selected_bu != 'Todas':
            df_filtered = df[df['BU'] == selected_bu].copy()
        else:
            df_filtered = df.copy()
        
        # Configurar AG-Grid
        gb = AGGridConfigurator.configure_forecast_table(df_filtered)
        
        # Configuraciones específicas según filtros
        if selected_bu != 'Todas' or not show_grouping:
            # Si hay filtro específico o no se quiere agrupación, desactivar agrupación
            gb.configure_column("BU", rowGroup=False, hide=False)
            gb.configure_grid_options(groupDefaultExpanded=0)
        
        # Renderizar AG-Grid
        grid_config = GRID_CONFIGS['forecast_main'].copy()
        grid_config['height'] = AGGridConfigurator.get_grid_height(len(df_filtered), 600)
        
        st.markdown("#### 📊 Tabla Interactiva de Forecast")
        
        grid_response = AgGrid(
            df_filtered,
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
            col_stats1, col_stats2, col_stats3 = st.columns(3)
            
            with col_stats1:
                st.metric("📋 Proyectos", grid_handler.total_rows)
            
            with col_stats2:
                numeric_columns = grid_handler.data_df.select_dtypes(include=['number']).columns
                numeric_columns = [col for col in numeric_columns if col not in ['BU']]
                if len(numeric_columns) > 0:
                    totals = grid_handler.calculate_totals(numeric_columns)
                    total_forecast = sum(totals.values())
                    st.metric("💰 Total Forecast", f"${total_forecast:,.0f}")
            
            with col_stats3:
                if selected_bu != 'Todas':
                    st.info(f"🎯 Filtrado por: **{selected_bu}**")
                else:
                    unique_bus = df_filtered['BU'].nunique()
                    st.metric("🏢 BUs Activas", unique_bus)
            
            # Controles de exportación y selección
            st.markdown("#### 🔧 Controles Avanzados")
            col_control1, col_control2, col_control3 = st.columns(3)
            
            with col_control1:
                if st.button("📥 Exportar Datos Visibles", key="export_visible"):
                    try:
                        if export_format == "CSV":
                            export_data = grid_handler.export_data("csv")
                            st.download_button(
                                label="⬇️ Descargar CSV",
                                data=export_data,
                                file_name=f"forecast_{selected_bu}_{datetime.now().strftime('%Y%m%d')}.csv",
                                mime="text/csv"
                            )
                        else:
                            export_data = grid_handler.export_data("excel")
                            st.download_button(
                                label="⬇️ Descargar Excel",
                                data=export_data,
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
                            export_data = grid_handler.export_selected("csv")
                            st.download_button(
                                label="⬇️ Descargar Selección",
                                data=export_data,
                                file_name=f"forecast_seleccion_{datetime.now().strftime('%Y%m%d')}.csv",
                                mime="text/csv"
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
    
    def _render_charts(self, summary, billing_events):
        """Renderiza los gráficos del forecast."""
        create_section_header("Visualizaciones", "Análisis gráfico del forecast", "📈")
        
        # Filtros independientes para cada visualización
        st.markdown("#### 🎯 Filtros de Visualización")
        col_filter1, col_filter2 = st.columns(2)
        
        with col_filter1:
            # Obtener lista de BUs disponibles
            available_bus = list(summary.bu_distribution.keys())
            monthly_bu_filter = st.selectbox(
                "Filtrar Distribución Mensual por BU",
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
            # Gráfico de distribución mensual con filtro independiente
            st.markdown("##### 📊 Distribución Mensual")
            
            if monthly_bu_filter == 'Todas':
                # Mostrar todos los datos
                monthly_data = pd.DataFrame([
                    {'Mes': month, 'Monto': amount}
                    for month, amount in summary.monthly_distribution.items()
                ])
                monthly_title_suffix = ""
            else:
                # Filtrar eventos por BU seleccionada
                monthly_filtered_events = [e for e in billing_events if e.bu.value == monthly_bu_filter]
                
                # Calcular distribución mensual filtrada
                monthly_filtered = {}
                for event in monthly_filtered_events:
                    month = event.month_year
                    monthly_filtered[month] = monthly_filtered.get(month, 0) + event.amount_adjusted
                
                monthly_data = pd.DataFrame([
                    {'Mes': month, 'Monto': amount}
                    for month, amount in monthly_filtered.items()
                ])
                monthly_title_suffix = f" - {monthly_bu_filter}"
            
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
                st.info(f"💰 Total {monthly_bu_filter}: {fmt_currency(total_monthly, decimals=2)}")
            else:
                st.warning(f"No hay datos mensuales para mostrar para {monthly_bu_filter}")
        
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
        
        # Gráfico de línea temporal
        st.markdown("#### 📅 Evolución Temporal")
        
        # Preparar datos para gráfico de línea (usando filtro independiente)
        #if temporal_bu_filter == 'Todas':
        if monthly_bu_filter == 'Todas':
            # Usar datos completos
            temporal_monthly_distribution = summary.monthly_distribution
            temporal_title_suffix = ""
        else:
            # Usar datos filtrados por BU temporal
            temporal_filtered_events = [e for e in billing_events if e.bu.value == monthly_bu_filter]
            temporal_monthly_distribution = {}
            for event in temporal_filtered_events:
                month = event.month_year
                temporal_monthly_distribution[month] = temporal_monthly_distribution.get(month, 0) + event.amount_adjusted
            temporal_title_suffix = f" - {monthly_bu_filter}"
        
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
            st.info(f"💰 Total Acumulado {monthly_bu_filter}: ${total_temporal:,.2f}")
        else:
            st.warning(f"No hay datos temporales para mostrar para {monthly_bu_filter}")
    
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
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            bu_filter = st.selectbox(
                "Filtrar por BU",
                ['Todas'] + sorted(list(details_df['BU'].unique())),
                key="details_bu_filter"
            )
        
        with col2:
            stage_filter = st.selectbox(
                "Filtrar por Etapa",
                ['Todas'] + sorted(list(details_df['Etapa'].unique())),
                key="details_stage_filter"
            )
        
        with col3:
            month_filter = st.selectbox(
                "Filtrar por Mes",
                ['Todos'] + sorted(list(details_df['Mes'].unique())),
                key="details_month_filter"
            )
        
        with col4:
            show_selection = st.checkbox("Mostrar solo seleccionados", key="show_selected_details")
        
        # Aplicar filtros
        filtered_df = details_df.copy()
        
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
