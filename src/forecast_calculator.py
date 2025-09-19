"""
Módulo de cálculo del forecast para la aplicación de Forecast Financiero.

Este módulo contiene toda la lógica de negocio para calcular las proyecciones
de ingresos basadas en las reglas específicas por unidad de negocio.
"""

import calendar
from datetime import datetime, timedelta
from typing import List, Dict
import logging

from .models import Opportunity, BillingEvent, BillingStage, BusinessUnit, ForecastSummary
from config.settings import BUSINESS_RULES


# Configurar logging
logger = logging.getLogger(__name__)


class ForecastCalculator:
    """
    Clase principal para el cálculo del forecast financiero.
    
    Esta clase implementa todas las reglas de negocio para generar
    las proyecciones de facturación por oportunidad.
    """
    
    def __init__(self):
        """Inicializa el calculador con las reglas de negocio."""
        self.rules = BUSINESS_RULES
    
    def calculate_forecast(self, opportunities: List[Opportunity]) -> List[BillingEvent]:
        """
        Calcula el forecast completo para todas las oportunidades.
        
        Args:
            opportunities: Lista de oportunidades a procesar
            
        Returns:
            List[BillingEvent]: Lista de eventos de facturación
        """
        logger.info(f"Iniciando cálculo de forecast para {len(opportunities)} oportunidades")
        
        all_billing_events = []
        
        for opportunity in opportunities:
            try:
                events = self._calculate_opportunity_billing(opportunity)
                all_billing_events.extend(events)
                
            except Exception as e:
                logger.error(f"Error calculando forecast para '{opportunity.name}': {str(e)}")
                continue
        
        logger.info(f"Forecast calculado: {len(all_billing_events)} eventos de facturación")
        return all_billing_events
    
    def _calculate_opportunity_billing(self, opportunity: Opportunity) -> List[BillingEvent]:
        """
        Calcula los eventos de facturación para una oportunidad específica.
        
        Args:
            opportunity: Oportunidad a procesar
            
        Returns:
            List[BillingEvent]: Eventos de facturación para la oportunidad
        """
        if opportunity.bu == BusinessUnit.ICT:
            return self._calculate_ict_billing(opportunity)
        else:
            return self._calculate_multi_stage_billing(opportunity)
    
    def _calculate_ict_billing(self, opportunity: Opportunity) -> List[BillingEvent]:
        """
        Calcula facturación para BU ICT (1 o 2 cobros).
        
        Args:
            opportunity: Oportunidad ICT
            
        Returns:
            List[BillingEvent]: Eventos de facturación ICT
        """
        events = []
        
        if opportunity.paid_in_advance and opportunity.paid_in_advance > 0:
            # Caso con PIA: dos cobros
            
            # Primer cobro (PIA)
            events.append(self._create_billing_event(
                opportunity=opportunity,
                stage=BillingStage.PIA,
                date=opportunity.close_date,
                amount=opportunity.paid_in_advance
            ))
            
            # Segundo cobro (Restante)
            final_date = self._add_weeks(opportunity.close_date, opportunity.lead_time)
            final_amount = opportunity.amount - opportunity.paid_in_advance
            
            events.append(self._create_billing_event(
                opportunity=opportunity,
                stage=BillingStage.FINAL,
                date=final_date,
                amount=final_amount
            ))
            
        else:
            # Caso sin PIA: un solo cobro
            final_date = self._add_weeks(opportunity.close_date, opportunity.lead_time)
            
            events.append(self._create_billing_event(
                opportunity=opportunity,
                stage=BillingStage.FINAL,
                date=final_date,
                amount=opportunity.amount
            ))
        
        return events
    
    def _calculate_multi_stage_billing(self, opportunity: Opportunity) -> List[BillingEvent]:
        """
        Calcula facturación para BU con 4 etapas (FCT, IAT, REP, SWD).
        
        Args:
            opportunity: Oportunidad multi-etapa
            
        Returns:
            List[BillingEvent]: Eventos de facturación multi-etapa
        """
        events = []
        
        # Calcular fechas de las etapas
        inicio_date = opportunity.close_date
        dr_date = self._add_days(inicio_date, self.rules.DR_DAYS_OFFSET)
        fat_date = self._add_weeks(dr_date, opportunity.lead_time)
        sat_date = self._add_days(fat_date, self.rules.SAT_DAYS_OFFSET)
        
        if opportunity.paid_in_advance and opportunity.paid_in_advance > 0:
            # Caso con PIA
            events.extend(self._calculate_multi_stage_with_pia(
                opportunity, inicio_date, dr_date, fat_date, sat_date
            ))
        else:
            # Caso sin PIA
            events.extend(self._calculate_multi_stage_without_pia(
                opportunity, inicio_date, dr_date, fat_date, sat_date
            ))
        
        return events
    
    def _calculate_multi_stage_with_pia(
        self, 
        opportunity: Opportunity, 
        inicio_date: datetime, 
        dr_date: datetime, 
        fat_date: datetime, 
        sat_date: datetime
    ) -> List[BillingEvent]:
        """
        Calcula facturación multi-etapa con PIA.
        
        Args:
            opportunity: Oportunidad
            inicio_date: Fecha de inicio
            dr_date: Fecha DR
            fat_date: Fecha FAT
            sat_date: Fecha SAT
            
        Returns:
            List[BillingEvent]: Eventos de facturación
        """
        events = []
        
        # SAT siempre es 10% del total
        sat_amount = opportunity.amount * self.rules.SAT_PERCENTAGE
        
        # Monto restante a distribuir entre DR y FAT
        remaining_amount = opportunity.amount - opportunity.paid_in_advance - sat_amount
        dr_amount = remaining_amount * self.rules.DR_FAT_SPLIT_PERCENTAGE
        fat_amount = remaining_amount * self.rules.DR_FAT_SPLIT_PERCENTAGE
        
        # Crear eventos
        events.extend([
            self._create_billing_event(opportunity, BillingStage.INICIO, inicio_date, opportunity.paid_in_advance),
            self._create_billing_event(opportunity, BillingStage.DR, dr_date, dr_amount),
            self._create_billing_event(opportunity, BillingStage.FAT, fat_date, fat_amount),
            self._create_billing_event(opportunity, BillingStage.SAT, sat_date, sat_amount)
        ])
        
        return events
    
    def _calculate_multi_stage_without_pia(
        self, 
        opportunity: Opportunity, 
        inicio_date: datetime, 
        dr_date: datetime, 
        fat_date: datetime, 
        sat_date: datetime
    ) -> List[BillingEvent]:
        """
        Calcula facturación multi-etapa sin PIA.
        
        Args:
            opportunity: Oportunidad
            inicio_date: Fecha de inicio
            dr_date: Fecha DR
            fat_date: Fecha FAT
            sat_date: Fecha SAT
            
        Returns:
            List[BillingEvent]: Eventos de facturación
        """
        events = []
        
        # Distribución estándar de porcentajes
        inicio_amount = opportunity.amount * self.rules.INICIO_PERCENTAGE
        dr_amount = opportunity.amount * self.rules.DR_PERCENTAGE
        fat_amount = opportunity.amount * self.rules.FAT_PERCENTAGE
        sat_amount = opportunity.amount * self.rules.SAT_PERCENTAGE
        
        # Crear eventos
        events.extend([
            self._create_billing_event(opportunity, BillingStage.INICIO, inicio_date, inicio_amount),
            self._create_billing_event(opportunity, BillingStage.DR, dr_date, dr_amount),
            self._create_billing_event(opportunity, BillingStage.FAT, fat_date, fat_amount),
            self._create_billing_event(opportunity, BillingStage.SAT, sat_date, sat_amount)
        ])
        
        return events
    
    def _create_billing_event(
        self, 
        opportunity: Opportunity, 
        stage: BillingStage, 
        date: datetime, 
        amount: float
    ) -> BillingEvent:
        """
        Crea un evento de facturación con ajustes aplicados.
        
        Args:
            opportunity: Oportunidad
            stage: Etapa de facturación
            date: Fecha del evento
            amount: Monto original
            
        Returns:
            BillingEvent: Evento de facturación creado
        """
        # Aplicar ajustes: probabilidad × castigo financiero (diferente para 60%)
        if abs(opportunity.probability - 0.6) < 0.01:  # Probabilidad = 60%
            penalty_factor = self.rules.FINANCIAL_PENALTY_FACTOR_60_PERCENT
        else:
            penalty_factor = self.rules.FINANCIAL_PENALTY_FACTOR_DEFAULT
        
        amount_adjusted = amount * opportunity.probability * penalty_factor
        
        return BillingEvent(
            opportunity_name=opportunity.name,
            bu=opportunity.bu,
            stage=stage,
            date=date,
            amount=amount,
            amount_adjusted=amount_adjusted,
            probability=opportunity.probability,
            lead_time_original=getattr(opportunity, 'lead_time_original', opportunity.lead_time),
            lead_time_adjusted=opportunity.lead_time
        )
    
    def _add_weeks(self, date: datetime, weeks: float) -> datetime:
        """
        Añade semanas a una fecha.
        
        Args:
            date: Fecha base
            weeks: Número de semanas a añadir
            
        Returns:
            datetime: Fecha resultante
        """
        return date + timedelta(weeks=weeks)
    
    def _add_days(self, date: datetime, days: int) -> datetime:
        """
        Añade días a una fecha.
        
        Args:
            date: Fecha base
            days: Número de días a añadir
            
        Returns:
            datetime: Fecha resultante
        """
        return date + timedelta(days=days)
    
    def generate_forecast_summary(self, billing_events: List[BillingEvent]) -> ForecastSummary:
        """
        Genera un resumen ejecutivo del forecast.
        
        Args:
            billing_events: Lista de eventos de facturación
            
        Returns:
            ForecastSummary: Resumen del forecast
        """
        if not billing_events:
            return ForecastSummary(
                total_amount=0.0,
                total_opportunities=0,
                total_events=0,
                date_range=(datetime.now(), datetime.now()),
                bu_distribution={},
                monthly_distribution={}
            )
        
        # Calcular métricas básicas
        total_amount = sum(event.amount_adjusted for event in billing_events)
        total_opportunities = len(set(event.opportunity_name for event in billing_events))
        total_events = len(billing_events)
        
        # Calcular rango de fechas
        dates = [event.date for event in billing_events]
        date_range = (min(dates), max(dates))
        
        # Distribución por BU
        bu_distribution = {}
        for event in billing_events:
            bu_name = event.bu.value
            bu_distribution[bu_name] = bu_distribution.get(bu_name, 0) + event.amount_adjusted
        
        # Distribución mensual
        monthly_distribution = {}
        for event in billing_events:
            month_key = event.month_year
            monthly_distribution[month_key] = monthly_distribution.get(month_key, 0) + event.amount_adjusted
        
        return ForecastSummary(
            total_amount=total_amount,
            total_opportunities=total_opportunities,
            total_events=total_events,
            date_range=date_range,
            bu_distribution=bu_distribution,
            monthly_distribution=monthly_distribution
        )
    
    def create_forecast_table(self, billing_events: List[BillingEvent]) -> Dict:
        """
        Crea la tabla de forecast en formato pivot.
        
        Args:
            billing_events: Lista de eventos de facturación
            
        Returns:
            Dict: Datos de la tabla de forecast
        """
        if not billing_events:
            return {'data': [], 'columns': []}
        
        # Crear estructura de datos para la tabla
        forecast_data = {}
        months = set()
        
        for event in billing_events:
            project_key = f"{event.opportunity_name} ({event.bu.value})"
            month_key = event.month_year
            
            if project_key not in forecast_data:
                forecast_data[project_key] = {}
            
            if month_key not in forecast_data[project_key]:
                forecast_data[project_key][month_key] = 0
            
            forecast_data[project_key][month_key] += event.amount_adjusted
            months.add(month_key)
        
        # Ordenar meses cronológicamente
        sorted_months = self._sort_months(list(months))
        
        # Crear tabla final
        table_data = []
        for project, monthly_data in forecast_data.items():
            row = {'Proyecto': project}
            for month in sorted_months:
                row[month] = monthly_data.get(month, 0)
            table_data.append(row)
        
        return {
            'data': table_data,
            'columns': ['Proyecto'] + sorted_months
        }
    
    def _sort_months(self, months: List[str]) -> List[str]:
        """
        Ordena una lista de meses en formato 'Month YYYY'.
        
        Args:
            months: Lista de meses a ordenar
            
        Returns:
            List[str]: Meses ordenados cronológicamente
        """
        month_dates = []
        
        for month_str in months:
            try:
                month_name, year = month_str.split(' ')
                month_num = list(calendar.month_name).index(month_name)
                month_dates.append((datetime(int(year), month_num, 1), month_str))
            except (ValueError, IndexError):
                # Si no se puede parsear, ponerlo al final
                month_dates.append((datetime(2099, 12, 31), month_str))
        
        # Ordenar por fecha y retornar solo los nombres
        month_dates.sort(key=lambda x: x[0])
        return [month_str for _, month_str in month_dates]
