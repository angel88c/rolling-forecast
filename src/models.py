"""
Modelos de datos para la aplicación de Forecast Financiero.

Este módulo define las estructuras de datos utilizadas en toda la aplicación,
proporcionando validación de tipos y documentación clara de los datos.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from enum import Enum


class BusinessUnit(Enum):
    """Enumeración de unidades de negocio válidas."""
    
    ICT = "ICT"
    FCT = "FCT"
    IAT = "IAT"
    REP = "REP"
    SWD = "SWD"


class BillingStage(Enum):
    """Etapas de facturación para proyectos."""
    
    # Para ICT
    PIA = "PIA"  # Paid in Advance
    FINAL = "Final"  # Cobro final ICT
    
    # Para otras BU
    INICIO = "INICIO"
    DR = "DR"  # Design Review
    FAT = "FAT"  # Factory Acceptance Test
    SAT = "SAT"  # Site Acceptance Test


@dataclass
class Opportunity:
    """
    Representa una oportunidad de negocio del funnel.
    
    Attributes:
        name: Nombre de la oportunidad
        bu: Unidad de negocio
        amount: Monto total de la oportunidad
        close_date: Fecha de cierre
        lead_time: Tiempo de entrega en semanas
        probability: Probabilidad de éxito (0-1)
        paid_in_advance: Monto pagado por adelantado (opcional)
        payment_terms: Términos de pago
        region: Código de región (US, MX, etc.)
        company: Clasificación de empresa (LLC, SAPI)
        gross_margin: Margen bruto (valor absoluto)
    """
    
    name: str
    bu: BusinessUnit
    amount: float
    close_date: datetime
    lead_time: float
    probability: float
    paid_in_advance: Optional[float] = None
    payment_terms: Optional[str] = None
    region: Optional[str] = None
    company: Optional[str] = None
    gross_margin: Optional[float] = None
    
    def __post_init__(self):
        """Validaciones post-inicialización."""
        if self.amount <= 0:
            raise ValueError("El monto debe ser mayor a 0")
        
        if not (0 <= self.probability <= 1):
            raise ValueError("La probabilidad debe estar entre 0 y 1")
        
        if self.lead_time <= 0:
            raise ValueError("El Lead Time debe ser mayor a 0")
        
        if self.paid_in_advance and self.paid_in_advance < 0:
            raise ValueError("El monto PIA no puede ser negativo")


@dataclass
class BillingEvent:
    """
    Representa un evento de facturación calculado.
    
    Attributes:
        opportunity_name: Nombre de la oportunidad
        bu: Unidad de negocio
        stage: Etapa de facturación
        date: Fecha del evento
        amount: Monto original
        amount_adjusted: Monto ajustado (probabilidad + castigo financiero)
        probability: Probabilidad aplicada
        lead_time_original: Lead time original
        lead_time_adjusted: Lead time ajustado
        region: Código de región
        company: Clasificación de empresa
        gross_margin_total: Margen bruto total del proyecto
    """
    
    opportunity_name: str
    bu: BusinessUnit
    stage: BillingStage
    date: datetime
    amount: float
    amount_adjusted: float
    probability: float
    lead_time_original: float
    lead_time_adjusted: float
    region: Optional[str] = None
    company: Optional[str] = None
    gross_margin_total: Optional[float] = None
    
    @property
    def month_year(self) -> str:
        """Retorna el mes y año en formato legible."""
        return f"{self.date.strftime('%B')} {self.date.year}"
    
    def __post_init__(self):
        """Validaciones post-inicialización."""
        if self.amount <= 0:
            raise ValueError("El monto debe ser mayor a 0")
        
        if self.amount_adjusted < 0:
            raise ValueError("El monto ajustado no puede ser negativo")


@dataclass
class ForecastSummary:
    """
    Resumen ejecutivo del forecast generado.
    
    Attributes:
        total_amount: Monto total del forecast
        total_opportunities: Número de oportunidades procesadas
        total_events: Número de eventos de facturación
        date_range: Rango de fechas del forecast
        bu_distribution: Distribución por unidad de negocio
        monthly_distribution: Distribución mensual
    """
    
    total_amount: float
    total_opportunities: int
    total_events: int
    date_range: tuple[datetime, datetime]
    bu_distribution: dict[str, float]
    monthly_distribution: dict[str, float]
    
    @property
    def start_date(self) -> datetime:
        """Fecha de inicio del forecast."""
        return self.date_range[0]
    
    @property
    def end_date(self) -> datetime:
        """Fecha de fin del forecast."""
        return self.date_range[1]
    
    @property
    def duration_months(self) -> int:
        """Duración del forecast en meses."""
        return (self.end_date.year - self.start_date.year) * 12 + \
               (self.end_date.month - self.start_date.month) + 1


@dataclass
class ValidationResult:
    """
    Resultado de validación de datos.
    
    Attributes:
        is_valid: Si los datos son válidos
        errors: Lista de errores encontrados
        warnings: Lista de advertencias
        valid_records: Número de registros válidos
        total_records: Número total de registros
    """
    
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    valid_records: int
    total_records: int
    
    @property
    def success_rate(self) -> float:
        """Tasa de éxito de validación."""
        if self.total_records == 0:
            return 0.0
        return self.valid_records / self.total_records
    
    def add_error(self, error: str) -> None:
        """Agrega un error a la lista."""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str) -> None:
        """Agrega una advertencia a la lista."""
        self.warnings.append(warning)
