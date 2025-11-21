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
            opportunity: Oportunidad a calcular
            
        Returns:
            List[BillingEvent]: Eventos de facturación para la oportunidad
        """
        # ICT y REP tienen facturación simplificada (1 o 2 eventos)
        if opportunity.bu in [BusinessUnit.ICT, BusinessUnit.REP]:
            return self._calculate_ict_billing(opportunity)
        else:
            return self._calculate_multi_stage_billing(opportunity)
    
    def _calculate_ict_billing(self, opportunity: Opportunity) -> List[BillingEvent]:
        """
        Calcula facturación simplificada para BU ICT y REP.
        
        Casos:
        - Sin PIA: 1 evento al 100% en Invoice Date (si existe) o close_date + lead_time (fallback)
        - Con PIA < 100%: 2 eventos (PIA en close_date + restante en SAT Date si existe o close_date + lead_time)
        - Con PIA = 100%: 1 evento al 100% en close_date
        
        Args:
            opportunity: Oportunidad ICT o REP
            
        Returns:
            List[BillingEvent]: Eventos de facturación (1 o 2 eventos)
        """
        events = []
        
        if opportunity.paid_in_advance and opportunity.paid_in_advance > 0:
            # Caso con PIA: uno o dos cobros
            
            # Primer cobro (INICIO/PIA) en close_date
            events.append(self._create_billing_event(
                opportunity=opportunity,
                stage=BillingStage.INICIO,
                date=opportunity.close_date,
                amount=opportunity.paid_in_advance
            ))
            
            # Segundo cobro (Restante) - solo si hay monto restante
            final_amount = opportunity.amount - opportunity.paid_in_advance
            
            if final_amount > 0:
                # Usar SAT Date si existe, sino usar close_date + lead_time
                if opportunity.sat_date:
                    final_date = opportunity.sat_date
                else:
                    final_date = self._add_weeks(opportunity.close_date, opportunity.lead_time)
                    logger.warning(f"Oportunidad '{opportunity.name}' con PIA pero sin SAT Date, usando close_date + lead_time")
                
                events.append(self._create_billing_event(
                    opportunity=opportunity,
                    stage=BillingStage.SAT,
                    date=final_date,
                    amount=final_amount
                ))
            
        else:
            # Caso sin PIA: un solo cobro
            # Usar Invoice Date si existe, sino usar close_date + lead_time
            if opportunity.invoice_date:
                final_date = opportunity.invoice_date
            else:
                final_date = self._add_weeks(opportunity.close_date, opportunity.lead_time)
                logger.warning(f"Oportunidad '{opportunity.name}' sin PIA y sin Invoice Date, usando close_date + lead_time")
            
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
        
        # Monto restante después de descontar el PIA
        remaining_amount = opportunity.amount - opportunity.paid_in_advance
        
        # Crear evento INICIO (siempre con PIA)
        events.append(
            self._create_billing_event(opportunity, BillingStage.INICIO, inicio_date, opportunity.paid_in_advance)
        )
        
        # Si hay monto restante, distribuirlo entre DR, FAT y SAT
        if remaining_amount > 0:
            # SAT es 10% del monto RESTANTE (no del total)
            # Para mantener la proporción: DR:FAT:SAT = 30:30:10 del restante
            # Normalizando: DR=30/70, FAT=30/70, SAT=10/70 del restante
            sat_amount = remaining_amount * (self.rules.SAT_PERCENTAGE / 0.70)  # 10/70 ≈ 14.3% del restante
            
            # Monto a distribuir entre DR y FAT (60% del restante)
            dr_fat_total = remaining_amount - sat_amount
            dr_amount = dr_fat_total * self.rules.DR_FAT_SPLIT_PERCENTAGE
            fat_amount = dr_fat_total * self.rules.DR_FAT_SPLIT_PERCENTAGE
            
            # Crear eventos solo si tienen monto > 0
            if dr_amount > 0:
                events.append(self._create_billing_event(opportunity, BillingStage.DR, dr_date, dr_amount))
            
            if fat_amount > 0:
                events.append(self._create_billing_event(opportunity, BillingStage.FAT, fat_date, fat_amount))
            
            if sat_amount > 0:
                events.append(self._create_billing_event(opportunity, BillingStage.SAT, sat_date, sat_amount))
        
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
            lead_time_adjusted=opportunity.lead_time,
            region=opportunity.region,
            company=opportunity.company,
            gross_margin_total=opportunity.gross_margin
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
            # Usar solo el nombre del proyecto como clave, sin BU
            project_key = event.opportunity_name
            bu_key = event.bu.value
            company_key = event.company if event.company else 'Sin Clasificar'
            month_key = event.month_year
            
            # Crear clave compuesta para identificar proyecto único con BU
            unique_key = f"{project_key}|{bu_key}"
            
            if unique_key not in forecast_data:
                forecast_data[unique_key] = {
                    'project_name': project_key,
                    'bu': bu_key,
                    'company': company_key,
                    'monthly_data': {}
                }
            
            if month_key not in forecast_data[unique_key]['monthly_data']:
                forecast_data[unique_key]['monthly_data'][month_key] = 0
            
            forecast_data[unique_key]['monthly_data'][month_key] += event.amount_adjusted
            months.add(month_key)
        
        # Ordenar meses cronológicamente
        sorted_months = self._sort_months(list(months))
        
        # Crear tabla final con columnas separadas para Proyecto, BU y Company
        table_data = []
        monthly_totals = {month: 0 for month in sorted_months}
        
        for unique_key, project_info in forecast_data.items():
            row = {
                'Proyecto': project_info['project_name'],
                'BU': project_info['bu'],
                'Empresa': project_info['company']
            }
            for month in sorted_months:
                amount = project_info['monthly_data'].get(month, 0)
                row[month] = amount
                monthly_totals[month] += amount
            table_data.append(row)
        
        return {
            'data': table_data,
            'columns': ['Proyecto', 'BU', 'Empresa'] + sorted_months,
            'monthly_totals': monthly_totals
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
    
    def create_cost_of_sale_table(self, billing_events: List[BillingEvent]) -> Dict:
        """
        Crea la tabla de Costo de Venta.
        
        Muestra el costo de venta (Amount - Gross Margin) para cada proyecto,
        colocando el valor únicamente en el mes del último evento de facturación.
        
        Args:
            billing_events: Lista de eventos de facturación
            
        Returns:
            Dict: Datos de la tabla de costo de venta
        """
        if not billing_events:
            return {'data': [], 'columns': []}
        
        # Agrupar eventos por proyecto
        project_data = {}
        months = set()
        
        for event in billing_events:
            project_key = event.opportunity_name
            bu_key = event.bu.value
            company_key = event.company if event.company else 'Sin Clasificar'
            month_key = event.month_year
            
            # Crear clave única para proyecto + BU
            unique_key = f"{project_key}|{bu_key}"
            
            if unique_key not in project_data:
                project_data[unique_key] = {
                    'project_name': project_key,
                    'bu': bu_key,
                    'company': company_key,
                    'amount_total': 0,
                    'gross_margin': event.gross_margin_total if event.gross_margin_total else 0,
                    'events': [],
                    'last_event_month': None,
                    'last_event_date': None
                }
            
            # Registrar evento
            project_data[unique_key]['events'].append({
                'date': event.date,
                'month': month_key,
                'amount': event.amount
            })
            
            # Actualizar último evento si es más reciente
            if (project_data[unique_key]['last_event_date'] is None or 
                event.date > project_data[unique_key]['last_event_date']):
                project_data[unique_key]['last_event_date'] = event.date
                project_data[unique_key]['last_event_month'] = month_key
            
            months.add(month_key)
        
        # Ordenar meses cronológicamente
        sorted_months = self._sort_months(list(months))
        
        # Crear tabla final
        table_data = []
        monthly_totals = {month: 0 for month in sorted_months}
        total_amount = 0
        total_gross_margin = 0
        total_cost_of_sale = 0
        
        for unique_key, project_info in project_data.items():
            # Calcular amount total sumando todos los eventos del proyecto
            amount_total = sum(event['amount'] for event in project_info['events'])
            gross_margin = project_info['gross_margin']
            cost_of_sale = amount_total - gross_margin if amount_total > 0 else 0
            
            # Acumular totales generales
            total_amount += amount_total
            total_gross_margin += gross_margin
            total_cost_of_sale += cost_of_sale
            
            # Crear fila con proyecto y BU
            row = {
                'Proyecto': project_info['project_name'],
                'BU': project_info['bu'],
                'Empresa': project_info['company'],
                'Amount Total': amount_total,
                'Gross Margin': gross_margin,
                'Costo de Venta': cost_of_sale
            }
            
            # Colocar el costo de venta solo en el mes del último evento
            for month in sorted_months:
                if month == project_info['last_event_month']:
                    row[month] = cost_of_sale
                    monthly_totals[month] += cost_of_sale
                else:
                    row[month] = 0
            
            table_data.append(row)
        
        return {
            'data': table_data,
            'columns': ['Proyecto', 'BU', 'Empresa', 'Amount Total', 'Gross Margin', 'Costo de Venta'] + sorted_months,
            'monthly_totals': monthly_totals,
            'total_amount': total_amount,
            'total_gross_margin': total_gross_margin,
            'total_cost_of_sale': total_cost_of_sale
        }
