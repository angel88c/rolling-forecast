"""
Módulo de formateo para números, monedas y datos.

Este módulo proporciona funciones para formatear datos de manera
consistente y profesional en toda la aplicación.
"""

import pandas as pd
from typing import Union, List, Dict, Any
import locale

# Configurar locale para formateo de números (fallback a C si no está disponible)
try:
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'C.UTF-8')
    except locale.Error:
        pass  # Usar configuración por defecto

def format_currency(value: Union[float, int], decimals: int = 2, symbol: str = "$") -> str:
    """
    Formatea un valor numérico como moneda con separadores de miles.
    
    Args:
        value: Valor numérico a formatear
        decimals: Número de decimales a mostrar (default: 2)
        symbol: Símbolo de moneda (default: "$")
        
    Returns:
        String formateado como moneda
        
    Examples:
        >>> format_currency(1234.56)
        '$1,234.56'
        >>> format_currency(1000000, decimals=0)
        '$1,000,000'
    """
    if pd.isna(value) or value is None:
        return f"{symbol}0.{'0' * decimals}"
    
    try:
        # Convertir a float para asegurar el tipo
        numeric_value = float(value)
        
        # Formatear con separadores de miles y decimales especificados
        if decimals == 0:
            formatted = f"{numeric_value:,.0f}"
        else:
            formatted = f"{numeric_value:,.{decimals}f}"
            
        return f"{symbol}{formatted}"
    
    except (ValueError, TypeError):
        return f"{symbol}0.{'0' * decimals}"

def format_percentage(value: Union[float, int], decimals: int = 1) -> str:
    """
    Formatea un valor como porcentaje.
    
    Args:
        value: Valor numérico (0-100 o 0-1)
        decimals: Número de decimales a mostrar
        
    Returns:
        String formateado como porcentaje
        
    Examples:
        >>> format_percentage(0.25)
        '25.0%'
        >>> format_percentage(75)
        '75.0%'
    """
    if pd.isna(value) or value is None:
        return "0.0%"
    
    try:
        numeric_value = float(value)
        
        # Si el valor está entre 0 y 1, asumimos que es decimal
        if 0 <= numeric_value <= 1:
            numeric_value *= 100
            
        return f"{numeric_value:.{decimals}f}%"
    
    except (ValueError, TypeError):
        return "0.0%"

def format_number(value: Union[float, int], decimals: int = 0) -> str:
    """
    Formatea un número con separadores de miles.
    
    Args:
        value: Valor numérico
        decimals: Número de decimales
        
    Returns:
        String formateado con separadores de miles
    """
    if pd.isna(value) or value is None:
        return "0"
    
    try:
        numeric_value = float(value)
        
        if decimals == 0:
            return f"{numeric_value:,.0f}"
        else:
            return f"{numeric_value:,.{decimals}f}"
    
    except (ValueError, TypeError):
        return "0"

def format_compact_currency(value: Union[float, int], decimals: int = 1) -> str:
    """
    Formatea moneda en formato compacto (K, M, B).
    
    Args:
        value: Valor numérico
        decimals: Decimales para valores compactos
        
    Returns:
        String formateado compacto
        
    Examples:
        >>> format_compact_currency(1500)
        '$1.5K'
        >>> format_compact_currency(2500000)
        '$2.5M'
    """
    if pd.isna(value) or value is None:
        return "$0"
    
    try:
        numeric_value = float(value)
        
        if abs(numeric_value) >= 1_000_000_000:
            return f"${numeric_value/1_000_000_000:.{decimals}f}B"
        elif abs(numeric_value) >= 1_000_000:
            return f"${numeric_value/1_000_000:.{decimals}f}M"
        elif abs(numeric_value) >= 1_000:
            return f"${numeric_value/1_000:.{decimals}f}K"
        else:
            return format_currency(numeric_value, decimals=0)
    
    except (ValueError, TypeError):
        return "$0"

def format_dataframe_currency_columns(df: pd.DataFrame, 
                                    currency_columns: List[str], 
                                    decimals: int = 2) -> pd.DataFrame:
    """
    Formatea columnas de moneda en un DataFrame.
    
    Args:
        df: DataFrame a formatear
        currency_columns: Lista de nombres de columnas que contienen monedas
        decimals: Número de decimales para las monedas
        
    Returns:
        DataFrame con columnas formateadas
    """
    df_formatted = df.copy()
    
    for col in currency_columns:
        if col in df_formatted.columns:
            df_formatted[col] = df_formatted[col].apply(
                lambda x: format_currency(x, decimals=decimals)
            )
    
    return df_formatted

def format_aggrid_currency_columns(column_defs: List[Dict[str, Any]], 
                                 currency_columns: List[str],
                                 decimals: int = 2) -> List[Dict[str, Any]]:
    """
    Configura el formateo de monedas para columnas de AG-Grid.
    
    Args:
        column_defs: Definiciones de columnas de AG-Grid
        currency_columns: Lista de columnas que contienen monedas
        decimals: Número de decimales
        
    Returns:
        Definiciones de columnas actualizadas con formateo
    """
    updated_defs = []
    
    for col_def in column_defs:
        updated_def = col_def.copy()
        
        if col_def.get('field') in currency_columns:
            updated_def.update({
                'type': 'numericColumn',
                'valueFormatter': {
                    'function': f'''
                    function(params) {{
                        if (params.value == null || params.value === '') return '$0.{'0' * decimals}';
                        const num = parseFloat(params.value);
                        if (isNaN(num)) return '$0.{'0' * decimals}';
                        return '$' + num.toLocaleString('en-US', {{
                            minimumFractionDigits: {decimals},
                            maximumFractionDigits: {decimals}
                        }});
                    }}
                    '''
                },
                'cellStyle': {
                    'textAlign': 'right',
                    'fontFamily': 'monospace',
                    'fontWeight': '500'
                }
            })
        
        updated_defs.append(updated_def)
    
    return updated_defs

def create_summary_stats(df: pd.DataFrame, 
                        numeric_columns: List[str],
                        currency_columns: List[str] = None) -> Dict[str, str]:
    """
    Crea estadísticas resumidas formateadas para un DataFrame.
    
    Args:
        df: DataFrame para analizar
        numeric_columns: Columnas numéricas
        currency_columns: Columnas de moneda (subset de numeric_columns)
        
    Returns:
        Diccionario con estadísticas formateadas
    """
    if currency_columns is None:
        currency_columns = []
    
    stats = {}
    
    for col in numeric_columns:
        if col in df.columns:
            total = df[col].sum()
            avg = df[col].mean()
            
            if col in currency_columns:
                stats[f"{col}_total"] = format_currency(total)
                stats[f"{col}_average"] = format_currency(avg)
            else:
                stats[f"{col}_total"] = format_number(total)
                stats[f"{col}_average"] = format_number(avg, decimals=1)
    
    return stats

def format_business_unit_icon(bu: str) -> str:
    """
    Retorna un icono apropiado para cada Business Unit.
    
    Args:
        bu: Código de Business Unit
        
    Returns:
        Emoji/icono correspondiente
    """
    icons = {
        'FCT': '🏭',  # Factory/Manufacturing
        'ICT': '💻',  # Information Technology
        'IAT': '🔧',  # Industrial Automation
        'REP': '🔄',  # Repair/Service
        'SWD': '⚙️'   # Software Development
    }
    
    return icons.get(bu.upper(), '📊')

def format_project_status(probability: float) -> tuple:
    """
    Retorna el estado y color basado en la probabilidad.
    
    Args:
        probability: Probabilidad del proyecto (0-1 o 0-100)
        
    Returns:
        Tupla (status_text, color_class)
    """
    if pd.isna(probability):
        return ("Desconocido", "secondary")
    
    # Normalizar a 0-100 si está en 0-1
    if probability <= 1:
        probability *= 100
    
    if probability >= 75:
        return ("Alta Probabilidad", "success")
    elif probability >= 50:
        return ("Probabilidad Media", "warning")
    elif probability >= 25:
        return ("Baja Probabilidad", "danger")
    else:
        return ("Muy Baja", "danger")

def format_month_name(date_str: str) -> str:
    """
    Convierte una fecha en formato YYYY-MM a nombre de mes legible.
    
    Args:
        date_str: Fecha en formato 'YYYY-MM'
        
    Returns:
        Nombre del mes en español
    """
    month_names = {
        '01': 'Enero', '02': 'Febrero', '03': 'Marzo', '04': 'Abril',
        '05': 'Mayo', '06': 'Junio', '07': 'Julio', '08': 'Agosto',
        '09': 'Septiembre', '10': 'Octubre', '11': 'Noviembre', '12': 'Diciembre'
    }
    
    try:
        year, month = date_str.split('-')
        month_name = month_names.get(month, month)
        return f"{month_name} {year}"
    except (ValueError, AttributeError):
        return str(date_str)

def get_color_scale_for_values(values: List[float], 
                              color_type: str = "turquoise") -> List[str]:
    """
    Genera una escala de colores basada en los valores.
    
    Args:
        values: Lista de valores numéricos
        color_type: Tipo de escala de color
        
    Returns:
        Lista de colores en formato hex
    """
    if not values or all(pd.isna(v) for v in values):
        return ['#ffffff'] * len(values)
    
    # Filtrar valores válidos
    valid_values = [v for v in values if not pd.isna(v) and v != 0]
    
    if not valid_values:
        return ['#ffffff'] * len(values)
    
    min_val = min(valid_values)
    max_val = max(valid_values)
    
    colors = []
    
    for value in values:
        if pd.isna(value) or value == 0:
            colors.append('#ffffff')
        else:
            # Normalizar valor entre 0 y 1
            if max_val == min_val:
                normalized = 0.5
            else:
                normalized = (value - min_val) / (max_val - min_val)
            
            if color_type == "turquoise":
                # Escala de turquesa claro a oscuro
                intensity = int(255 - (normalized * 100))  # 255 a 155
                colors.append(f'rgb(64, 224, {intensity})')
            elif color_type == "blue":
                # Escala de azul claro a oscuro
                intensity = int(255 - (normalized * 100))
                colors.append(f'rgb(64, {intensity}, 224)')
            else:
                # Escala de grises por defecto
                intensity = int(255 - (normalized * 100))
                colors.append(f'rgb({intensity}, {intensity}, {intensity})')
    
    return colors
