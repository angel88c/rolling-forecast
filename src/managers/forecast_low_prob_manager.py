"""
Manager para forecast de oportunidades con probabilidad < 60%.
"""

import streamlit as st
from typing import List, Dict
from .base_forecast_manager import BaseForecastManager
from src.ui_components import create_section_header
from src.formatters import format_currency as fmt_currency
from datetime import datetime


class ForecastLowProbManager(BaseForecastManager):
    """Gestiona el forecast de oportunidades con probabilidad < 60%."""
    
    def __init__(self):
        """Inicializa el manager para forecast de oportunidades < 60%."""
        # Usar hoja "YTD Pipeline" para oportunidades < 60%
        super().__init__(sheet_name="YTD Pipeline")
    
    def filter_opportunities(self, opportunities: List) -> List:
        """
        Filtra solo oportunidades con probabilidad < 60%.
        
        Args:
            opportunities: Lista de todas las oportunidades
            
        Returns:
            Lista filtrada de oportunidades < 60%
        """
        return [opp for opp in opportunities if opp.probability < 0.60]
    
    def get_no_data_message(self) -> str:
        """Retorna mensaje cuando no hay oportunidades <60%."""
        return "⚠️ No se encontraron oportunidades con probabilidad menor al 60% en el archivo"
    
    def get_success_message(self, count: int) -> str:
        """Retorna mensaje de éxito."""
        return f"✅ Forecast procesado: {count} oportunidades < 60%"
    
    def show_filter_info(self, filtered_count: int, total_count: int):
        """Muestra información sobre cuántas oportunidades <60% se encontraron."""
        st.info(f"📊 Se encontraron {filtered_count} oportunidades con probabilidad < 60% de {total_count} totales")
    
    def prepare_results(self, **kwargs) -> Dict:
        """
        Prepara resultados para forecast <60%.
        Solo llena datos de oportunidades <60%, NO incluye claves principales
        para no sobrescribir datos del forecast principal.
        
        Returns:
            Dict con resultados para oportunidades <60%
        """
        billing_events = kwargs['billing_events']
        summary = kwargs['summary']
        forecast_table = kwargs['forecast_table']
        cost_of_sale_table = kwargs['cost_of_sale_table']
        processing_summary = kwargs['processing_summary']
        validation_result = kwargs['validation_result']
        parsing_report = kwargs['parsing_report']
        
        # IMPORTANTE: No incluir 'billing_events', 'summary', 'forecast_table', 'cost_of_sale_table'
        # para no sobrescribir los datos del forecast principal (>=60%)
        return {
            'billing_events_low_prob': billing_events,
            'summary_low_prob': summary,
            'forecast_table_low_prob': forecast_table,
            'cost_of_sale_table_low_prob': cost_of_sale_table,
            'processing_summary_low_prob': processing_summary,
            'validation_result_low_prob': validation_result,
            'parsing_report_low_prob': parsing_report
        }
    
    def render_forecast_tab(self, results: Dict, file_uploader_func):
        """
        Renderiza la pestaña completa de forecast <60%.
        
        Args:
            results: Resultados del procesamiento
            file_uploader_func: Función para renderizar file uploader
        """
        create_section_header("Forecast Pipeline", "Oportunidades < 60%", "📊")
        
        # File uploader
        col_upload, col_process = st.columns([3, 1])
        with col_upload:
            uploaded_file = file_uploader_func(
                "📁 Subir archivo de Forecast (Oportunidades < 60%)",
                key="forecast_low_prob_uploader",
                help_text="Archivo Excel con oportunidades del pipeline (se filtrarán automáticamente las < 60%)"
            )
            if uploaded_file:
                st.session_state.uploaded_file = uploaded_file
        
        with col_process:
            if st.button("🔄 Procesar", key="process_forecast_low_prob", use_container_width=True):
                if hasattr(st.session_state, 'uploaded_file'):
                    results = self.process_file(st.session_state.uploaded_file)
                    if results:
                        # Hacer merge con datos existentes para preservar otras pestañas
                        st.session_state.forecast_results = self.merge_results_with_existing(results)
                else:
                    st.error("Sube un archivo primero")
        
        # Verificar si hay datos
        if not hasattr(st.session_state, 'forecast_results'):
            st.info("👆 Sube y procesa un archivo para visualizar el forecast de oportunidades < 60%")
            return
        
        results = st.session_state.forecast_results
        
        # Verificar si hay datos de oportunidades < 60%
        if results.get('forecast_table_low_prob') is None:
            st.info("ℹ️ No hay oportunidades con probabilidad menor al 60% en el forecast procesado")
            return
        
        # Información sobre el filtro aplicado
        st.info("📉 Esta tabla muestra únicamente oportunidades con **probabilidad < 60%** con factores de castigo aplicados")
        
        # Métricas principales
        if results.get('summary_low_prob'):
            self._render_key_metrics(results['summary_low_prob'])
            
            # Botón de descarga de totales consolidados
            st.markdown("---")
            col_download, col_info = st.columns([1, 3])
            
            with col_download:
                if st.button("📊 Descargar Reporte Consolidado de Totales <60%", 
                           key="download_consolidated_low_prob",
                           help="Descarga Excel con totales por Empresa y BU para oportunidades <60%",
                           use_container_width=True):
                    try:
                        excel_buffer = self.generate_consolidated_totals_excel(
                            forecast_table=results['forecast_table_low_prob'],
                            cost_table=results['cost_of_sale_table_low_prob'],
                            sheet_prefix="<60%"
                        )
                        st.download_button(
                            label="⬇️ Descargar Excel Consolidado <60%",
                            data=excel_buffer.getvalue(),
                            file_name=f"reporte_consolidado_totales_low_prob_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key="download_consolidated_low_prob_btn"
                        )
                    except Exception as e:
                        st.error(f"Error al generar reporte: {str(e)}")
            
            with col_info:
                st.info("📋 Incluye: Hoja 'Totales <60%' con resumen general + Una hoja por cada BU con sus totales específicos")
        
        st.markdown("---")
        
        # Renderizar tabla de forecast
        self.render_forecast_table(
            forecast_table=results['forecast_table_low_prob'],
            summary=results.get('summary_low_prob'),
            title="Forecast <60%",
            key_prefix="forecast_low_prob"
        )
    
    def render_cost_of_sale_tab(self, results: Dict):
        """
        Renderiza la pestaña de costo de venta para oportunidades <60%.
        
        Args:
            results: Resultados del procesamiento
        """
        if not hasattr(st.session_state, 'forecast_results'):
            st.info("👈 Procesa un forecast en la pestaña 'Forecast <60%' primero")
            return
        
        results = st.session_state.forecast_results
        
        # Verificar si hay datos
        if results.get('cost_of_sale_table_low_prob') is None:
            st.info("ℹ️ No hay oportunidades con probabilidad menor al 60% en el forecast procesado")
            return
        
        # Información sobre el filtro aplicado
        st.info("💸 Esta tabla muestra el costo de venta únicamente de oportunidades con **probabilidad < 60%**")
        
        # Renderizar tabla de costo de venta
        self.render_cost_of_sale_table(
            cost_table=results['cost_of_sale_table_low_prob'],
            summary=results.get('summary_low_prob'),
            title="<60%",
            key_prefix="cost_low_prob"
        )
    
    def _render_key_metrics(self, summary):
        """Renderiza las métricas clave del forecast <60%."""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "💰 Total Forecast <60%",
                fmt_currency(summary.total_amount, decimals=2),
                help="Monto total proyectado con factores de castigo aplicados"
            )
        
        with col2:
            st.metric(
                "🎯 Oportunidades <60%",
                f"{summary.total_opportunities:,}",
                help="Número de oportunidades con probabilidad menor a 60%"
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
