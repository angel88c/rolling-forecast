"""
Módulo de exportación para la aplicación de Forecast Financiero.

Este módulo maneja la exportación de resultados a diferentes formatos
como Excel, CSV y PDF para facilitar el análisis y distribución.
"""

import pandas as pd
from datetime import datetime
from typing import List, Dict
import io
import logging

from .models import BillingEvent, ForecastSummary
from config.settings import ERROR_MESSAGES, INFO_MESSAGES


# Configurar logging
logger = logging.getLogger(__name__)


class ForecastExporter:
    """
    Clase para exportar resultados del forecast a diferentes formatos.
    
    Esta clase proporciona métodos para exportar los datos calculados
    a formatos que faciliten el análisis y la distribución.
    """
    
    def __init__(self):
        """Inicializa el exportador."""
        pass
    
    def export_to_excel(
        self, 
        billing_events: List[BillingEvent], 
        forecast_table: Dict,
        summary: ForecastSummary,
        filename: str = None
    ) -> io.BytesIO:
        """
        Exporta el forecast completo a Excel con múltiples hojas.
        
        Args:
            billing_events: Lista de eventos de facturación
            forecast_table: Tabla de forecast en formato pivot
            summary: Resumen ejecutivo
            filename: Nombre del archivo (opcional)
            
        Returns:
            io.BytesIO: Buffer con el archivo Excel
        """
        logger.info("Iniciando exportación a Excel")
        
        try:
            # Crear buffer en memoria
            buffer = io.BytesIO()
            
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                
                # Hoja 1: Forecast (tabla pivot)
                forecast_df = pd.DataFrame(forecast_table['data'])
                if not forecast_df.empty:
                    # Formatear números como moneda
                    numeric_columns = forecast_df.select_dtypes(include=['number']).columns
                    for col in numeric_columns:
                        forecast_df[col] = forecast_df[col].round(2)
                    
                    forecast_df.to_excel(writer, sheet_name='Forecast', index=False)
                
                # Hoja 2: Detalles de eventos
                events_data = []
                for event in billing_events:
                    events_data.append({
                        'Proyecto': event.opportunity_name,
                        'BU': event.bu.value,
                        'Etapa': event.stage.value,
                        'Fecha': event.date.strftime('%d/%m/%Y'),
                        'Mes': event.month_year,
                        'Monto Original': round(event.amount, 2),
                        'Monto Ajustado': round(event.amount_adjusted, 2),
                        'Probabilidad': event.probability,
                        'Lead Time Original': event.lead_time_original,
                        'Lead Time Ajustado': event.lead_time_adjusted
                    })
                
                events_df = pd.DataFrame(events_data)
                if not events_df.empty:
                    events_df.to_excel(writer, sheet_name='Detalles_Eventos', index=False)
                
                # Hoja 3: Resumen ejecutivo
                summary_data = self._create_summary_dataframe(summary)
                summary_data.to_excel(writer, sheet_name='Resumen_Ejecutivo', index=False)
                
                # Hoja 4: Distribución mensual
                monthly_df = pd.DataFrame([
                    {'Mes': month, 'Monto': round(amount, 2)}
                    for month, amount in summary.monthly_distribution.items()
                ])
                if not monthly_df.empty:
                    monthly_df.to_excel(writer, sheet_name='Distribucion_Mensual', index=False)
                
                # Hoja 5: Distribución por BU
                bu_df = pd.DataFrame([
                    {'BU': bu, 'Monto': round(amount, 2), 'Porcentaje': round(amount/summary.total_amount*100, 1)}
                    for bu, amount in summary.bu_distribution.items()
                ])
                if not bu_df.empty:
                    bu_df.to_excel(writer, sheet_name='Distribucion_BU', index=False)
            
            buffer.seek(0)
            logger.info("Exportación a Excel completada exitosamente")
            return buffer
            
        except Exception as e:
            logger.error(f"Error en exportación a Excel: {str(e)}")
            raise Exception(ERROR_MESSAGES['export_error'])
    
    def export_forecast_table_to_csv(self, forecast_table: Dict) -> str:
        """
        Exporta solo la tabla de forecast a CSV.
        
        Args:
            forecast_table: Tabla de forecast
            
        Returns:
            str: Contenido CSV como string
        """
        logger.info("Exportando tabla de forecast a CSV")
        
        try:
            df = pd.DataFrame(forecast_table['data'])
            if df.empty:
                return "No hay datos para exportar"
            
            # Formatear números
            numeric_columns = df.select_dtypes(include=['number']).columns
            for col in numeric_columns:
                df[col] = df[col].round(2)
            
            return df.to_csv(index=False)
            
        except Exception as e:
            logger.error(f"Error en exportación a CSV: {str(e)}")
            raise Exception(ERROR_MESSAGES['export_error'])
    
    def _create_summary_dataframe(self, summary: ForecastSummary) -> pd.DataFrame:
        """
        Crea un DataFrame con el resumen ejecutivo.
        
        Args:
            summary: Resumen del forecast
            
        Returns:
            pd.DataFrame: DataFrame con el resumen
        """
        summary_data = [
            {'Métrica': 'Total del Forecast', 'Valor': f"${summary.total_amount:,.2f}"},
            {'Métrica': 'Número de Oportunidades', 'Valor': str(summary.total_opportunities)},
            {'Métrica': 'Eventos de Facturación', 'Valor': str(summary.total_events)},
            {'Métrica': 'Fecha de Inicio', 'Valor': summary.start_date.strftime('%d/%m/%Y')},
            {'Métrica': 'Fecha de Fin', 'Valor': summary.end_date.strftime('%d/%m/%Y')},
            {'Métrica': 'Duración (meses)', 'Valor': str(summary.duration_months)},
        ]
        
        return pd.DataFrame(summary_data)
    
    def create_downloadable_filename(self, prefix: str = "forecast") -> str:
        """
        Crea un nombre de archivo único para descarga.
        
        Args:
            prefix: Prefijo del nombre del archivo
            
        Returns:
            str: Nombre de archivo único
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{timestamp}.xlsx"


class ReportGenerator:
    """
    Generador de reportes adicionales y análisis.
    
    Esta clase proporciona funcionalidades adicionales para generar
    reportes específicos y análisis detallados del forecast.
    """
    
    def __init__(self):
        """Inicializa el generador de reportes."""
        pass
    
    def generate_comparison_report(
        self, 
        current_events: List[BillingEvent], 
        previous_events: List[BillingEvent] = None
    ) -> Dict:
        """
        Genera un reporte de comparación entre forecasts.
        
        Args:
            current_events: Eventos del forecast actual
            previous_events: Eventos del forecast anterior (opcional)
            
        Returns:
            Dict: Reporte de comparación
        """
        if not previous_events:
            return {'message': 'No hay forecast anterior para comparar'}
        
        # Calcular totales
        current_total = sum(event.amount_adjusted for event in current_events)
        previous_total = sum(event.amount_adjusted for event in previous_events)
        
        # Calcular diferencia
        difference = current_total - previous_total
        percentage_change = (difference / previous_total * 100) if previous_total > 0 else 0
        
        return {
            'current_total': current_total,
            'previous_total': previous_total,
            'difference': difference,
            'percentage_change': percentage_change,
            'trend': 'up' if difference > 0 else 'down' if difference < 0 else 'stable'
        }
    
    def generate_risk_analysis(self, billing_events: List[BillingEvent]) -> Dict:
        """
        Genera un análisis de riesgo del forecast.
        
        Args:
            billing_events: Lista de eventos de facturación
            
        Returns:
            Dict: Análisis de riesgo
        """
        if not billing_events:
            return {'message': 'No hay datos para análisis de riesgo'}
        
        # Análisis por probabilidad
        low_prob_events = [e for e in billing_events if e.probability < 0.3]
        medium_prob_events = [e for e in billing_events if 0.3 <= e.probability < 0.7]
        high_prob_events = [e for e in billing_events if e.probability >= 0.7]
        
        # Análisis por concentración
        bu_amounts = {}
        for event in billing_events:
            bu = event.bu.value
            bu_amounts[bu] = bu_amounts.get(bu, 0) + event.amount_adjusted
        
        total_amount = sum(bu_amounts.values())
        max_bu_concentration = max(bu_amounts.values()) / total_amount if total_amount > 0 else 0
        
        return {
            'probability_distribution': {
                'low_risk': {
                    'count': len(high_prob_events),
                    'amount': sum(e.amount_adjusted for e in high_prob_events)
                },
                'medium_risk': {
                    'count': len(medium_prob_events),
                    'amount': sum(e.amount_adjusted for e in medium_prob_events)
                },
                'high_risk': {
                    'count': len(low_prob_events),
                    'amount': sum(e.amount_adjusted for e in low_prob_events)
                }
            },
            'concentration_risk': {
                'max_bu_concentration': max_bu_concentration,
                'is_concentrated': max_bu_concentration > 0.6,
                'bu_distribution': bu_amounts
            }
        }
