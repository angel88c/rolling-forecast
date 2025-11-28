"""
Aplicación principal de Streamlit para Forecast Financiero - REFACTORIZADA.

Esta aplicación proporciona una interfaz web intuitiva para generar
proyecciones de ingresos por facturación basadas en el pipeline de oportunidades.

Versión refactorizada usando arquitectura modular con Managers.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from typing import Dict, Any
import sys
import os
import logging

# Agregar el directorio src al path para importar módulos
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'config'))

# Managers
from src.managers import ForecastMainManager, ForecastLowProbManager

# Otros componentes
from src.kpi_processor import KPIProcessor
from src.llc_kpi_processor import LLCKPIProcessor
from src.exporter import ForecastExporter, ReportGenerator
from src.consolidated_report_generator import ConsolidatedReportGenerator
from src.ui_components import (
    render_file_uploader,
    render_filters_row,
    render_totals_panel,
    render_export_buttons,
    export_to_excel_with_format,
    AGGridConfigurator,
    AGGridExporter,
    GRID_CONFIGS,
    GridResponseHandler,
    create_section_header
)
from src.ui_styles import apply_custom_styles, format_currency
from src.formatters import (
    format_currency as fmt_currency, 
    format_dataframe_currency_columns,
    format_aggrid_currency_columns,
    format_business_unit_icon,
    format_compact_currency,
    create_summary_stats
)
from config.settings import *
from st_aggrid import AgGrid

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ForecastApp:
    """
    Clase principal de la aplicación Streamlit - Versión Refactorizada.
    
    Usa arquitectura modular con Managers para separar responsabilidades.
    """
    
    def __init__(self):
        """Inicializa la aplicación y sus componentes."""
        self.forecast_main_manager = ForecastMainManager()
        self.forecast_low_prob_manager = ForecastLowProbManager()
        self.kpi_processor = KPIProcessor()
        self.llc_kpi_processor = LLCKPIProcessor()
        self.exporter = ForecastExporter()
        
        # Configurar página
        st.set_page_config(
            page_title="iBtest - Forecast Manager",
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Aplicar estilos personalizados
        apply_custom_styles()
    
    def run(self):
        """Ejecuta la aplicación principal."""
        self._render_sidebar()
        self._render_main_content()
    
    def _render_sidebar(self):
        """Renderiza la barra lateral simplificada."""
        
        # Logo de iBtest en la parte superior
        try:
            st.sidebar.image("logo_ibtest.png", width=200)
        except:
            st.sidebar.markdown("### iBtest")
        
        st.sidebar.markdown("---")
        st.sidebar.markdown("**📊 Forecast & KPI Manager**")
        st.sidebar.caption("v3.0 - Gestión de Proyectos")
        
        # Selector de tipo de facturación
        st.sidebar.header("💼 Tipo de Facturación")
        
        # Inicializar billing_type en session_state si no existe
        if 'billing_type' not in st.session_state:
            st.session_state.billing_type = 'Contable'
        
        # Variable de control para detectar cambios (separada del valor actual)
        if 'billing_type_control' not in st.session_state:
            st.session_state.billing_type_control = st.session_state.billing_type
        
        # Callback que se ejecuta cuando cambia el selectbox
        def on_billing_type_change():
            new_value = st.session_state.billing_type_selector
            old_value = st.session_state.billing_type_control
            
            # Solo limpiar si realmente cambió
            if new_value != old_value:
                # Limpiar resultados de forecast
                if 'forecast_results' in st.session_state:
                    del st.session_state.forecast_results
                
                # Limpiar resultados de KPIs
                if 'kpi_results' in st.session_state:
                    del st.session_state.kpi_results
                
                # Actualizar valor de control
                st.session_state.billing_type_control = new_value
                st.session_state.billing_type = new_value
                
                # Marcar que hubo cambio para mostrar mensajes
                st.session_state.billing_type_just_changed = True
        
        # Selectbox con callback
        st.sidebar.selectbox(
            "Método de Facturación",
            options=["Contable", "Financiera"],
            index=0 if st.session_state.billing_type == "Contable" else 1,
            help="Contable: Múltiples eventos (INICIO, DR, FAT, SAT). Financiera: Un solo evento al 100% en SAT.",
            key="billing_type_selector",
            on_change=on_billing_type_change
        )
        
        # Mostrar mensajes si acabó de cambiar
        if st.session_state.get('billing_type_just_changed', False):
            st.sidebar.warning(f"⚠️ Tipo de facturación cambiado a: **{st.session_state.billing_type}**")
            st.sidebar.info("📝 Las tablas se han limpiado. Por favor, vuelve a procesar los archivos.")
            # Limpiar flag después de mostrar
            st.session_state.billing_type_just_changed = False
        
        # Mostrar información sobre el tipo seleccionado
        if st.session_state.billing_type == "Financiera":
            st.sidebar.info("📌 Modo Financiero: Un solo evento de facturación al 100% en el mes del SAT")
        else:
            st.sidebar.info("📌 Modo Contable: Múltiples eventos según reglas de negocio")
        
        st.sidebar.markdown("---")
        
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
        
        # Opciones de exportación
        if hasattr(st.session_state, 'forecast_results'):
            st.sidebar.header("📥 Exportar Resultados")
            
            if st.sidebar.button("📊 Descargar Excel"):
                self._export_excel()
            
            if st.sidebar.button("📄 Descargar CSV"):
                self._export_csv()
            
            st.sidebar.markdown("---")
            
            # Reporte consolidado
            if st.sidebar.button("📋 Generar Reporte Consolidado", 
                                help="Genera reporte completo con Forecast, Costo de Venta y KPIs usando el template",
                                type="primary"):
                self._generate_consolidated_report()
        
        # Información sobre reglas de negocio
        with st.sidebar.expander("ℹ️ Información de Reglas"):
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
    
    def _render_main_content(self):
        """Renderiza el contenido principal con pestañas."""
        # Mostrar título grande con el tipo de facturación actual
        billing_type = st.session_state.get('billing_type', 'Contable')
        if billing_type == "Financiera":
            st.title("📊 MODO FINANCIERO - Facturación Consolidada en SAT")
            st.caption("Un solo evento de facturación al 100% en el mes del SAT para todos los proyectos")
        else:
            st.title("📊 MODO CONTABLE - Facturación por Eventos")
            st.caption("Múltiples eventos de facturación según reglas de negocio (INICIO, DR, FAT, SAT)")
        
        st.markdown("---")
        
        tabs = st.tabs([
            "📊 Forecast", 
            "💰 Costo de Venta",
            "📉 Forecast <60%",
            "💸 Costo Venta <60%",
            "📋 KPIs PM-008", 
            "💵 Costo Venta KPIs"
        ])
        
        with tabs[0]:
            self._render_forecast_tab()
        
        with tabs[1]:
            self._render_cost_of_sale_tab()
        
        with tabs[2]:
            self._render_forecast_low_prob_tab()
        
        with tabs[3]:
            self._render_cost_of_sale_low_prob_tab()
        
        with tabs[4]:
            self._render_kpi_billing_tab()
        
        with tabs[5]:
            self._render_kpi_cost_tab()
    
    # ========== FORECAST PRINCIPAL ==========
    
    def _render_forecast_tab(self):
        """Pestaña de Forecast Pipeline - Usa ForecastMainManager."""
        results = st.session_state.get('forecast_results')
        self.forecast_main_manager.render_forecast_tab(results, render_file_uploader)
    
    def _render_cost_of_sale_tab(self):
        """Pestaña de Costo de Venta - Usa ForecastMainManager."""
        results = st.session_state.get('forecast_results')
        self.forecast_main_manager.render_cost_of_sale_tab(results)
    
    # ========== FORECAST <60% ==========
    
    def _render_forecast_low_prob_tab(self):
        """Pestaña de Forecast <60% - Usa ForecastLowProbManager."""
        results = st.session_state.get('forecast_results')
        self.forecast_low_prob_manager.render_forecast_tab(results, render_file_uploader)
    
    def _render_cost_of_sale_low_prob_tab(self):
        """Pestaña de Costo de Venta <60% - Usa ForecastLowProbManager."""
        results = st.session_state.get('forecast_results')
        self.forecast_low_prob_manager.render_cost_of_sale_tab(results)
    
    # ========== KPIs ==========
    
    def _render_kpi_billing_tab(self):
        """Pestaña de KPIs Billing."""
        if hasattr(st.session_state, 'kpi_results'):
            self._render_kpi_billing_table()
        else:
            self._render_kpi_empty_state()
    
    def _render_kpi_empty_state(self):
        """Estado vacío para pestaña de KPIs."""
        create_section_header("KPIs PM-008", "Billing de proyectos SAPI + LLC", "📋")
        
        # File uploaders en dos columnas
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📄 KPIs SAPI (PM-008)")
            uploaded_file_kpi = render_file_uploader(
                "📁 Subir archivo KPIs PM-008 (SAPI)",
                key="kpi_uploader_sapi",
                help_text="Archivo Excel con KPIs PM-008 - Solo registros SAPI"
            )
            if uploaded_file_kpi:
                st.session_state.uploaded_file_kpis = uploaded_file_kpi
                st.success("✅ Archivo SAPI cargado")
        
        with col2:
            st.markdown("### 📄 KPIs LLC (iBtest)")
            uploaded_file_llc = render_file_uploader(
                "📁 Subir archivo iBtest LLC-Overall Results",
                key="kpi_uploader_llc",
                help_text="Archivo Excel con KPIs LLC - Registros con Status f/Invoice = Pending"
            )
            if uploaded_file_llc:
                st.session_state.uploaded_file_llc = uploaded_file_llc
                st.success("✅ Archivo LLC cargado")
        
        # Botón de procesamiento centrado
        col_empty1, col_process, col_empty2 = st.columns([1, 2, 1])
        with col_process:
            files_uploaded = (
                hasattr(st.session_state, 'uploaded_file_kpis') or 
                hasattr(st.session_state, 'uploaded_file_llc')
            )
            
            if st.button("🔄 Procesar KPIs", key="process_kpi_empty", use_container_width=True, disabled=not files_uploaded):
                self._process_kpis()
        
        st.info("👆 Sube al menos un archivo y procésalo. Se pueden procesar ambos archivos simultáneamente.")
    
    def _render_kpi_cost_tab(self):
        """Pestaña de Costo de Venta KPIs."""
        if hasattr(st.session_state, 'kpi_results'):
            self._render_kpi_cost_of_sale_table()
        else:
            st.info("👈 Procesa KPIs en la pestaña 'KPIs PM-008' primero")
    
    def _process_kpis(self):
        """Procesa los archivos de KPIs SAPI y LLC, combinando los resultados."""
        try:
            sapi_results = None
            llc_results = None
            
            # Obtener tipo de facturación desde session state
            billing_type = getattr(st.session_state, 'billing_type', 'Contable')
            
            # Procesar archivo SAPI si está disponible
            if hasattr(st.session_state, 'uploaded_file_kpis'):
                with st.spinner("Procesando KPIs SAPI (PM-008)..."):
                    sapi_results = self.kpi_processor.process_kpi_file(
                        st.session_state.uploaded_file_kpis, 
                        billing_type=billing_type
                    )
                    st.success(f"✅ SAPI: {sapi_results['filtered_count']} proyectos procesados")
            
            # Procesar archivo LLC si está disponible
            if hasattr(st.session_state, 'uploaded_file_llc'):
                with st.spinner("Procesando KPIs LLC (iBtest)..."):
                    llc_results = self.llc_kpi_processor.process_llc_file(
                        st.session_state.uploaded_file_llc,
                        billing_type=billing_type
                    )
                    st.success(f"✅ LLC: {llc_results['filtered_count']} proyectos procesados")
            
            # Combinar resultados
            if sapi_results or llc_results:
                combined_results = self._combine_kpi_results(sapi_results, llc_results)
                # Guardar en session_state separado (no sobrescribe forecast_results)
                st.session_state.kpi_results = combined_results
                
                total_projects = combined_results['filtered_count']
                sapi_count = sapi_results['filtered_count'] if sapi_results else 0
                llc_count = llc_results['filtered_count'] if llc_results else 0
                
                st.success(f"✅ Total: {total_projects} proyectos (SAPI: {sapi_count}, LLC: {llc_count})")
                # Nota: st.rerun() preserva session_state
                st.rerun()
            else:
                st.error("❌ No se pudo procesar ningún archivo")
                
        except Exception as e:
            logger.error(f"Error procesando KPIs: {str(e)}")
            st.error(f"❌ Error procesando KPIs: {str(e)}")
    
    def _combine_kpi_results(self, sapi_results, llc_results):
        """
        Combina los resultados de SAPI y LLC en una estructura unificada.
        
        Args:
            sapi_results: Resultados del procesador SAPI
            llc_results: Resultados del procesador LLC
            
        Returns:
            Dict con resultados combinados
        """
        # Inicializar estructura combinada
        combined = {
            'data': [],
            'original_count': 0,
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
        
        # Combinar datos SAPI
        if sapi_results:
            combined['data'].extend(sapi_results['data'])
            combined['original_count'] += sapi_results['original_count']
            combined['filtered_count'] += sapi_results['filtered_count']
            
            # Combinar summary
            combined['summary']['total_projects'] += sapi_results['summary']['total_projects']
            combined['summary']['total_billing'] += sapi_results['summary']['total_billing']
            combined['summary']['total_po'] += sapi_results['summary']['total_po']
            combined['summary']['tbd_projects'].extend(sapi_results['summary']['tbd_projects'])
            
            # Combinar distribuciones
            for bu, amount in sapi_results['summary']['bu_distribution'].items():
                combined['summary']['bu_distribution'][bu] = combined['summary']['bu_distribution'].get(bu, 0) + amount
            
            for month, amount in sapi_results['summary']['monthly_distribution'].items():
                combined['summary']['monthly_distribution'][month] = combined['summary']['monthly_distribution'].get(month, 0) + amount
            
            for status, count in sapi_results['summary']['status_distribution'].items():
                combined['summary']['status_distribution'][status] = combined['summary']['status_distribution'].get(status, 0) + count
        
        # Combinar datos LLC
        if llc_results:
            combined['data'].extend(llc_results['data'])
            combined['original_count'] += llc_results['original_count']
            combined['filtered_count'] += llc_results['filtered_count']
            
            # Combinar summary
            combined['summary']['total_projects'] += llc_results['summary']['total_projects']
            combined['summary']['total_billing'] += llc_results['summary']['total_billing']
            combined['summary']['total_po'] += llc_results['summary']['total_po']
            combined['summary']['tbd_projects'].extend(llc_results['summary']['tbd_projects'])
            
            # Combinar distribuciones
            for bu, amount in llc_results['summary']['bu_distribution'].items():
                combined['summary']['bu_distribution'][bu] = combined['summary']['bu_distribution'].get(bu, 0) + amount
            
            for month, amount in llc_results['summary']['monthly_distribution'].items():
                combined['summary']['monthly_distribution'][month] = combined['summary']['monthly_distribution'].get(month, 0) + amount
            
            for status, count in llc_results['summary']['status_distribution'].items():
                combined['summary']['status_distribution'][status] = combined['summary']['status_distribution'].get(status, 0) + count
        
        logger.info(f"Resultados combinados: {combined['filtered_count']} proyectos totales")
        return combined
    
    def _render_kpi_billing_table(self):
        """Renderiza la tabla de KPIs PM-008."""
        if not hasattr(st.session_state, 'kpi_results'):
            st.warning("⚠️ No hay datos de KPIs disponibles. Por favor, carga y procesa el archivo de KPIs PM-008.")
            
            with st.expander("📖 ¿Cómo usar esta función?"):
                st.markdown("""
                ### Pasos para cargar KPIs PM-008:
                
                1. **Sube el archivo**: Usa el file uploader arriba
                2. **Procesa los datos**: Haz clic en "Procesar"
                3. **Visualiza**: La tabla aparecerá aquí automáticamente
                
                ### Información que se mostrará:
                - Proyectos con status "Abierto" y "On Hold"
                - Montos de facturación por mes
                - Calculados como: Total de PO × % Facturación
                - Ubicados en el mes de probable facturación
                """)
            return
        
        kpi_results = st.session_state.kpi_results
        
        if not kpi_results['data']:
            st.info("ℹ️ No hay proyectos con status 'Abierto' u 'On Hold' en el archivo de KPIs.")
            return
        
        create_section_header("KPIs PM-008 - Billing", "Proyectos activos con facturación probable", "📋")
        
        # Mostrar resumen
        summary = kpi_results['summary']
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📋 Proyectos Activos", summary['total_projects'])
        
        with col2:
            st.metric("💰 Total Billing", f"${summary['total_billing']:,.2f}")
        
        with col3:
            st.metric("📊 Total PO", f"${summary['total_po']:,.2f}")
        
        with col4:
            if summary['status_distribution']:
                abierto = summary['status_distribution'].get('Abierto', 0)
                on_hold = summary['status_distribution'].get('On Hold', 0)
                st.metric("🚦 Abierto / On Hold", f"{abierto} / {on_hold}")
        
        # Convertir a DataFrame
        df_kpis = pd.DataFrame(kpi_results['data'])
        
        # Mostrar warning si hay proyectos con Costo de Venta TBD
        if summary.get('tbd_projects') and len(summary['tbd_projects']) > 0:
            st.warning(f"⚠️ **{len(summary['tbd_projects'])} proyectos con Costo de Venta TBD (pendiente por definir):**")
            
            # Mostrar lista de proyectos
            tbd_list = "\n".join([f"- {project}" for project in summary['tbd_projects']])
            with st.expander(f"📋 Ver {len(summary['tbd_projects'])} proyectos con costo TBD"):
                st.markdown(tbd_list)
                st.info("💡 Estos proyectos se muestran con Costo de Venta = $0.00 hasta que se defina el valor.")
        
        # Filtros
        st.markdown("#### 🔍 Filtros")
        col_filter1, col_filter2, col_filter3, col_filter4 = st.columns(4)
        
        with col_filter1:
            location_options = ['Todas'] + sorted(df_kpis['Location'].dropna().unique().tolist())
            selected_location = st.selectbox("Filtrar por Location:", location_options, key="kpi_location_filter")
        
        with col_filter2:
            bu_options = ['Todas'] + sorted(df_kpis['BU'].dropna().unique().tolist())
            selected_bu = st.selectbox("Filtrar por BU:", bu_options, key="kpi_bu_filter")
        
        with col_filter3:
            status_options = ['Todos'] + sorted(df_kpis['Status'].dropna().unique().tolist())
            selected_status = st.selectbox("Filtrar por Status:", status_options, key="kpi_status_filter")
        
        with col_filter4:
            show_grouping = st.checkbox("Agrupar por BU", value=False, key="kpi_group_by_bu")
        
        # Aplicar filtros
        df_filtered = df_kpis.copy()
        
        if selected_location != 'Todas':
            df_filtered = df_filtered[df_filtered['Location'] == selected_location]
        
        if selected_bu != 'Todas':
            df_filtered = df_filtered[df_filtered['BU'] == selected_bu]
        
        if selected_status != 'Todos':
            df_filtered = df_filtered[df_filtered['Status'] == selected_status]
        
        # Mostrar panel de totales
        render_totals_panel(df_filtered, "TOTALES KPIs BILLING")
        
        # Configurar AG-Grid
        gb = AGGridConfigurator.configure_forecast_table(df_filtered)
        
        # Configurar agrupación
        if selected_bu != 'Todas' or not show_grouping:
            gb.configure_column("BU", rowGroup=False, hide=False)
            gb.configure_grid_options(groupDefaultExpanded=0)
        else:
            gb.configure_grid_options(groupDefaultExpanded=1)
        
        # Renderizar tabla
        grid_config = GRID_CONFIGS['forecast_main'].copy()
        grid_config['height'] = AGGridConfigurator.get_grid_height(len(df_filtered), 600)
        
        st.markdown("#### 📋 Tabla de Billing KPIs")
        st.info("💡 Los montos se muestran en el mes de **probable fecha de facturación**.")
        
        AgGrid(
            df_filtered,
            gridOptions=gb.build(),
            height=grid_config['height'],
            theme=grid_config['theme'],
            allow_unsafe_jscode=grid_config['allow_unsafe_jscode'],
            update_mode=grid_config['update_mode'],
            fit_columns_on_grid_load=grid_config['fit_columns_on_grid_load'],
            enable_enterprise_modules=grid_config['enable_enterprise_modules']
        )
        
        # Exportación
        #st.markdown("#### 📥 Exportar Datos")
        #render_export_buttons(df_filtered, 'kpis_pm008', 'export_kpi')
    
    def _render_kpi_cost_of_sale_table(self):
        """Renderiza la tabla de Costo de Venta de KPIs PM-008."""
        if not hasattr(st.session_state, 'kpi_results'):
            st.warning("⚠️ No hay datos de KPIs disponibles.")
            return
        
        kpi_results = st.session_state.kpi_results
        
        if not kpi_results['data']:
            st.info("ℹ️ No hay proyectos con costo de venta.")
            return
        
        create_section_header("KPIs PM-008 - Costo de Venta", "Costo de venta de proyectos activos", "💵")
        
        # Convertir a DataFrame
        df_kpis = pd.DataFrame(kpi_results['data'])
        
        # Filtros
        st.markdown("#### 🔍 Filtros")
        col_filter1, col_filter2, col_filter3, col_filter4 = st.columns(4)
        
        with col_filter1:
            location_options = ['Todas'] + sorted(df_kpis['Location'].dropna().unique().tolist())
            selected_location_cost = st.selectbox("Filtrar por Location:", location_options, key="kpi_cost_location_filter")
        
        with col_filter2:
            bu_options = ['Todas'] + sorted(df_kpis['BU'].dropna().unique().tolist())
            selected_bu_cost = st.selectbox("Filtrar por BU:", bu_options, key="kpi_cost_bu_filter")
        
        with col_filter3:
            status_options = ['Todos'] + sorted(df_kpis['Status'].dropna().unique().tolist())
            selected_status_cost = st.selectbox("Filtrar por Status:", status_options, key="kpi_cost_status_filter")
        
        with col_filter4:
            show_grouping_cost = st.checkbox("Agrupar por BU", value=False, key="kpi_cost_group_by_bu")
        
        # Aplicar filtros
        df_filtered = df_kpis.copy()
        
        if selected_location_cost != 'Todas':
            df_filtered = df_filtered[df_filtered['Location'] == selected_location_cost]
        
        if selected_bu_cost != 'Todas':
            df_filtered = df_filtered[df_filtered['BU'] == selected_bu_cost]
        
        if selected_status_cost != 'Todos':
            df_filtered = df_filtered[df_filtered['Status'] == selected_status_cost]
        
        # Crear tabla con costo de venta
        month_cols = [col for col in df_filtered.columns 
                     if col not in ['Proyecto', 'BU', 'Location', 'Status', 'Customer', 'Total PO', '% Facturación', 'Costo de Venta']]
        
        df_cost = df_filtered[['Proyecto', 'BU', 'Location', 'Status', 'Customer', 'Costo de Venta']].copy()
        
        # Agregar columnas de meses con costo de venta
        for month in month_cols:
            df_cost[month] = 0
        
        # Para cada proyecto, encontrar el último mes con facturación
        for idx in df_filtered.index:
            last_billing_month = None
            for month in month_cols:
                if df_filtered.loc[idx, month] > 0:
                    last_billing_month = month
            
            if last_billing_month:
                df_cost.loc[idx, last_billing_month] = df_filtered.loc[idx, 'Costo de Venta']
        
        # Mostrar panel de totales
        render_totals_panel(df_cost, "TOTALES COSTO VENTA KPIs")
        
        # Configurar AG-Grid
        gb = AGGridConfigurator.configure_forecast_table(df_cost)
        
        if selected_bu_cost != 'Todas' or not show_grouping_cost:
            gb.configure_column("BU", rowGroup=False, hide=False)
            gb.configure_grid_options(groupDefaultExpanded=0)
        else:
            gb.configure_grid_options(groupDefaultExpanded=1)
        
        # Estilo para celdas con costo
        from st_aggrid import JsCode
        cell_style_jscode = JsCode("""
        function(params) {
            if (params.value && params.value > 0) {
                return {
                    'backgroundColor': '#FCB72F',
                    'color': '#000000',
                    'fontWeight': 'bold'
                }
            }
            return null;
        }
        """)
        
        for month in month_cols:
            gb.configure_column(month, cellStyle=cell_style_jscode)
        
        # Renderizar tabla
        grid_config = GRID_CONFIGS['forecast_main'].copy()
        grid_config['height'] = AGGridConfigurator.get_grid_height(len(df_cost), 600)
        
        st.markdown("#### 💵 Tabla de Costo de Venta KPIs")
        st.info("💡 El costo se muestra **SOLO en el último mes de facturación** del proyecto. Celdas resaltadas en naranja.")
        
        AgGrid(
            df_cost,
            gridOptions=gb.build(),
            height=grid_config['height'],
            theme=grid_config['theme'],
            allow_unsafe_jscode=grid_config['allow_unsafe_jscode'],
            update_mode=grid_config['update_mode'],
            fit_columns_on_grid_load=grid_config['fit_columns_on_grid_load'],
            enable_enterprise_modules=grid_config['enable_enterprise_modules']
        )
        
        # Exportación
        #st.markdown("#### 📥 Exportar Datos")
        #render_export_buttons(df_cost, 'costo_venta_kpis_pm008', 'export_kpi_cost')
    
    # ========== EXPORTACIÓN ==========
    
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
    
    def _generate_consolidated_report(self):
        """Genera reporte consolidado completo usando el template."""
        try:
            with st.spinner("Generando reporte consolidado..."):
                # Inicializar generador
                generator = ConsolidatedReportGenerator()
                
                # Obtener datos de forecast (ambos tipos)
                forecast_results = None
                if hasattr(st.session_state, 'forecast_results'):
                    forecast_results = st.session_state.forecast_results
                
                # Obtener datos de KPIs
                kpi_results = None
                if hasattr(st.session_state, 'kpi_results'):
                    kpi_results = st.session_state.kpi_results
                
                # Validar que hay datos disponibles
                if not forecast_results and not kpi_results:
                    st.warning("⚠️ No hay datos procesados. Procesa al menos un Forecast o KPIs primero.")
                    return
                
                # Generar reporte
                excel_buffer = generator.generate_report(
                    forecast_results=forecast_results,
                    kpi_results=kpi_results
                )
                
                # Crear nombre de archivo
                timestamp = datetime.now().strftime("%Y%m%d_%H%M")
                filename = f"reporte_consolidado_{timestamp}.xlsx"
                
                # Botón de descarga
                st.download_button(
                    label="⬇️ Descargar Reporte Consolidado",
                    data=excel_buffer.getvalue(),
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_consolidated"
                )
                
                st.success("✅ Reporte consolidado generado exitosamente")
                
                # Información sobre el reporte
                st.info("📊 El reporte incluye:")
                
                included = []
                if forecast_results:
                    if 'forecast_table' in forecast_results and forecast_results['forecast_table'].get('data'):
                        included.append("✓ Facturación por Forecast >= 60%")
                        included.append("✓ Costo de venta por Forecast >= 60%")
                    if 'forecast_table_low_prob' in forecast_results and forecast_results['forecast_table_low_prob'].get('data'):
                        included.append("✓ Facturación por Forecast < 60%")
                        included.append("✓ Costo de venta por Forecast < 60%")
                
                if kpi_results:
                    if 'billing_table' in kpi_results:
                        included.append("✓ Facturación por Backlog PM (KPIs)")
                    if 'cost_table' in kpi_results:
                        included.append("✓ Costo de venta por Backlog PM (KPIs)")
                
                if included:
                    for item in included:
                        st.markdown(f"  {item}")
                
        except FileNotFoundError as e:
            st.error("❌ No se encontró el archivo Template.xlsx. Asegúrate de que existe en la carpeta 'data/'")
            logger.error(f"Template no encontrado: {str(e)}")
        except Exception as e:
            st.error(f"❌ Error al generar reporte consolidado: {str(e)}")
            logger.error(f"Error en reporte consolidado: {str(e)}", exc_info=True)


# Punto de entrada de la aplicación
if __name__ == "__main__":
    app = ForecastApp()
    app.run()
