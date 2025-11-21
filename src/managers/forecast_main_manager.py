"""
Manager para el forecast principal (todas las oportunidades excluyendo 100%).
"""

import streamlit as st
from typing import List, Dict
from .base_forecast_manager import BaseForecastManager
from src.ui_components import create_section_header
from src.formatters import format_currency as fmt_currency
from datetime import datetime


class ForecastMainManager(BaseForecastManager):
    """Gestiona el forecast principal con todas las oportunidades."""
    
    def __init__(self):
        """Inicializa el manager para forecast principal (oportunidades >= 60%)."""
        # Usar hoja "Forecast (Intuition) C.Quarter(" para oportunidades >= 60%
        super().__init__(sheet_name="Forecast (Intuition) C.Quarter(")
    
    def filter_opportunities(self, opportunities: List) -> List:
        """
        Retorna todas las oportunidades (ya se excluyeron las de 100% en data_processor).
        
        Args:
            opportunities: Lista de todas las oportunidades
            
        Returns:
            Lista de oportunidades (sin filtrado adicional)
        """
        return opportunities
    
    def prepare_results(self, **kwargs) -> Dict:
        """
        Prepara resultados para forecast principal.
        Genera TODOS los datos incluyendo vista <60%.
        
        Returns:
            Dict con resultados completos
        """
        billing_events = kwargs['billing_events']
        summary = kwargs['summary']
        forecast_table = kwargs['forecast_table']
        cost_of_sale_table = kwargs['cost_of_sale_table']
        processing_summary = kwargs['processing_summary']
        validation_result = kwargs['validation_result']
        parsing_report = kwargs['parsing_report']
        opportunities_all = kwargs['opportunities_all']
        
        # Generar también vista de oportunidades <60%
        opportunities_low_prob = [opp for opp in opportunities_all if opp.probability < 0.60]
        
        if opportunities_low_prob:
            billing_events_low_prob = self.calculator.calculate_forecast(opportunities_low_prob)
            summary_low_prob = self.calculator.generate_forecast_summary(billing_events_low_prob)
            forecast_table_low_prob = self.calculator.create_forecast_table(billing_events_low_prob)
            cost_of_sale_table_low_prob = self.calculator.create_cost_of_sale_table(billing_events_low_prob)
        else:
            billing_events_low_prob = []
            summary_low_prob = None
            forecast_table_low_prob = None
            cost_of_sale_table_low_prob = None
        
        return {
            'billing_events': billing_events,
            'summary': summary,
            'forecast_table': forecast_table,
            'cost_of_sale_table': cost_of_sale_table,
            'billing_events_low_prob': billing_events_low_prob,
            'summary_low_prob': summary_low_prob,
            'forecast_table_low_prob': forecast_table_low_prob,
            'cost_of_sale_table_low_prob': cost_of_sale_table_low_prob,
            'processing_summary': processing_summary,
            'validation_result': validation_result,
            'parsing_report': parsing_report
        }
    
    def render_forecast_tab(self, results: Dict, file_uploader_func):
        """
        Renderiza la pestaña completa de forecast principal.
        
        Args:
            results: Resultados del procesamiento
            file_uploader_func: Función para renderizar file uploader
        """
        # File uploader
        col_upload, col_process = st.columns([3, 1])
        with col_upload:
            uploaded_file = file_uploader_func(
                "📁 Subir archivo de Forecast de Oportunidades >= 60%",
                key="forecast_uploader",
                help_text="Archivo Excel con oportunidades del pipeline"
            )
            if uploaded_file:
                st.session_state.uploaded_file = uploaded_file
        
        with col_process:
            if st.button("🔄 Procesar", key="process_forecast", use_container_width=True):
                if hasattr(st.session_state, 'uploaded_file'):
                    results = self.process_file(st.session_state.uploaded_file)
                    if results:
                        # Hacer merge con datos existentes para preservar otras pestañas
                        st.session_state.forecast_results = self.merge_results_with_existing(results)
                else:
                    st.error("Sube un archivo primero")
        
        # Verificar si hay datos
        if not hasattr(st.session_state, 'forecast_results'):
            st.info("👆 Sube y procesa un archivo para visualizar el forecast")
            return
        
        results = st.session_state.forecast_results
        
        # Verificar si hay datos del forecast principal
        if results.get('summary') is None or len(results.get('forecast_table', {}).get('data', [])) == 0:
            st.info("ℹ️ No hay datos de forecast principal. Este archivo fue procesado solo para oportunidades < 60%.")
            st.info("👈 Para ver el forecast completo, procesa un archivo en esta pestaña o ve a la pestaña 'Forecast <60%'")
            return
        
        # Métricas principales
        self._render_key_metrics(results['summary'])
        
        st.markdown("---")
        
        # Renderizar tabla de forecast
        self.render_forecast_table(
            forecast_table=results['forecast_table'],
            summary=results['summary'],
            title="Forecast",
            key_prefix="forecast"
        )
    
    def render_cost_of_sale_tab(self, results: Dict):
        """
        Renderiza la pestaña de costo de venta.
        
        Args:
            results: Resultados del procesamiento
        """
        if not hasattr(st.session_state, 'forecast_results'):
            st.info("👈 Procesa un forecast en la pestaña 'Forecast' primero")
            return
        
        results = st.session_state.forecast_results
        
        # Verificar si hay datos
        if results.get('cost_of_sale_table') is None or len(results['cost_of_sale_table']['data']) == 0:
            st.info("ℹ️ No hay datos de costo de venta principal. Este archivo fue procesado solo para oportunidades < 60%.")
            st.info("👈 Para ver el costo de venta completo, procesa un archivo en la pestaña 'Forecast' o ve a 'Costo Venta <60%'")
            return
        
        # Renderizar tabla de costo de venta
        self.render_cost_of_sale_table(
            cost_table=results['cost_of_sale_table'],
            summary=results['summary'],
            title="",
            key_prefix="cost"
        )
    
    def _render_key_metrics(self, summary):
        """Renderiza las métricas clave del forecast."""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "💰 Total Forecast",
                fmt_currency(summary.total_amount, decimals=2),
                help="Monto total proyectado con factores de castigo aplicados"
            )
        
        with col2:
            st.metric(
                "🎯 Oportunidades",
                f"{summary.total_opportunities:,}",
                help="Número total de oportunidades activas"
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
