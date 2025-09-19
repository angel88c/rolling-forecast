"""
Utilidades para manejo seguro de respuestas de AG-Grid.
"""

from typing import Dict, List, Any, Optional
import pandas as pd


def safe_get_grid_data(grid_response: Optional[Dict[str, Any]]) -> List[Dict]:
    """
    Obtiene los datos de la grid de forma segura.
    
    Args:
        grid_response: Respuesta de AG-Grid que puede ser None
        
    Returns:
        Lista de diccionarios con los datos, vacía si no hay datos
    """
    if not grid_response:
        return []
    
    data = grid_response.get('data', [])
    
    # Si data es un DataFrame, convertirlo a lista de diccionarios
    if hasattr(data, 'to_dict'):
        return data.to_dict('records')
    
    # Si data no es una lista, convertirlo a lista vacía
    if not isinstance(data, list):
        return []
    
    return dadef safe_get_selected_rows(grid_response: Optional[Dict[str, Any]]) -> List[Dict]:
    """
    Obtiene las filas seleccionadas de forma segura.
    
    Args:
        grid_response: Respuesta de AG-Grid que puede ser None
        
    Returns:
        Lista de diccionarios con las filas seleccionadas, vacía si no hay selección
    """
    if not grid_response:
        return []
    
    selected_rows = grid_response.get('selected_rows', [])
    
    if selected_rows is None:
        return []
    
    # Si selected_rows es un DataFrame, convertirlo a lista de diccionarios
    if hasattr(selected_rows, 'to_dict'):
        return selected_rows.to_dict('records')
    
    if not isinstance(selected_rows, list):
        return []
    
    return selected_rows if not isinstance(selected_rows, list):
        return []
    
    return selected_rows


def safe_get_filter_model(grid_response: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Obtiene el modelo de filtros de forma segura.
    
    Args:
        grid_response: Respuesta de AG-Grid que puede ser None
        
    Returns:
        Diccionario con los filtros aplicados, vacío si no hay filtros
    """
    if not grid_response:
        return {}
    
    return grid_response.get('filterModel', {})


def get_grid_stats(grid_response: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Obtiene estadísticas de la grid de forma segura.
    
    Args:
        grid_response: Respuesta de AG-Grid que puede ser None
        
    Returns:
        Diccionario con estadísticas de la grid
    """
    data = safe_get_grid_data(grid_response)
    selected_rows = safe_get_selected_rows(grid_response)
    
    stats = {
        'total_rows': len(data),
        'selected_rows': len(selected_rows),
        'has_data': len(data) > 0,
        'has_selection': len(selected_rows) > 0,
        'data_df': pd.DataFrame(data) if len(data) > 0 else pd.DataFrame(),
        'selected_df': pd.DataFrame(selected_rows) if len(selected_rows) > 0 else pd.DataFrame()
    }
    
    return stats


def safe_calculate_totals(grid_response: Optional[Dict[str, Any]], 
                         numeric_columns: List[str]) -> Dict[str, float]:
    """
    Calcula totales de columnas numéricas de forma segura.
    
    Args:
        grid_response: Respuesta de AG-Grid que puede ser None
        numeric_columns: Lista de nombres de columnas numéricas
        
    Returns:
        Diccionario con los totales por columna
    """
    data = safe_get_grid_data(grid_response)
    
    if len(data) == 0:
        return {col: 0.0 for col in numeric_columns}
    
    df = pd.DataFrame(data)
    totals = {}
    
    for col in numeric_columns:
        if col in df.columns:
            try:
                # Convertir a numérico, manejando errores
                numeric_series = pd.to_numeric(df[col], errors='coerce')
                totals[col] = numeric_series.sum()
            except Exception:
                totals[col] = 0.0
        else:
            totals[col] = 0.0
    
    return totals


def format_grid_export_filename(base_name: str, 
                               filters: Dict[str, str] = None,
                               extension: str = "csv") -> str:
    """
    Genera un nombre de archivo para exportación con filtros aplicados.
    
    Args:
        base_name: Nombre base del archivo
        filters: Diccionario con filtros aplicados
        extension: Extensión del archivo (csv, xlsx)
        
    Returns:
        Nombre de archivo formateado
    """
    from datetime import datetime
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    filename_parts = [base_name]
    
    if filters:
        filter_parts = []
        for key, value in filters.items():
            if value and value != 'Todas' and value != 'Todos':
                # Limpiar el valor para uso en nombre de archivo
                clean_value = str(value).replace(' ', '_').replace('/', '_')
                filter_parts.append(f"{key}_{clean_value}")
        
        if filter_parts:
            filename_parts.extend(filter_parts)
    
    filename_parts.append(timestamp)
    
    return f"{'_'.join(filename_parts)}.{extension}"


class GridResponseHandler:
    """
    Manejador centralizado para respuestas de AG-Grid.
    """
    
    def __init__(self, grid_response: Optional[Dict[str, Any]]):
        self.grid_response = grid_response
        self._stats = None
    
    @property
    def stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas calculadas una sola vez."""
        if self._stats is None:
            self._stats = get_grid_stats(self.grid_response)
        return self._stats
    
    @property
    def data(self) -> List[Dict]:
        """Obtiene los datos de forma segura."""
        return safe_get_grid_data(self.grid_response)
    
    @property
    def selected_rows(self) -> List[Dict]:
        """Obtiene las filas seleccionadas de forma segura."""
        return safe_get_selected_rows(self.grid_response)
    
    @property
    def data_df(self) -> pd.DataFrame:
        """Obtiene los datos como DataFrame."""
        return self.stats['data_df']
    
    @property
    def selected_df(self) -> pd.DataFrame:
        """Obtiene las filas seleccionadas como DataFrame."""
        return self.stats['selected_df']
    
    @property
    def has_data(self) -> bool:
        """Verifica si hay datos."""
        return self.stats['has_data']
    
    @property
    def has_selection(self) -> bool:
        """Verifica si hay filas seleccionadas."""
        return self.stats['has_selection']
    
    @property
    def total_rows(self) -> int:
        """Obtiene el número total de filas."""
        return self.stats['total_rows']
    
    @property
    def selected_count(self) -> int:
        """Obtiene el número de filas seleccionadas."""
        return self.stats['selected_rows']
    
    def calculate_totals(self, numeric_columns: List[str]) -> Dict[str, float]:
        """Calcula totales de columnas numéricas."""
        return safe_calculate_totals(self.grid_response, numeric_columns)
    
    def export_data(self, format_type: str = "csv") -> bytes:
        """
        Exporta los datos visibles.
        
        Args:
            format_type: Tipo de formato ('csv' o 'excel')
            
        Returns:
            Datos exportados como bytes
        """
        if not self.has_data:
            return b""
        
        if format_type.lower() == "csv":
            return self.data_df.to_csv(index=False).encode('utf-8')
        elif format_type.lower() == "excel":
            from io import BytesIO
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                self.data_df.to_excel(writer, index=False, sheet_name='Data')
            return buffer.getvalue()
        else:
            raise ValueError(f"Formato no soportado: {format_type}")
    
    def export_selected(self, format_type: str = "csv") -> bytes:
        """
        Exporta las filas seleccionadas.
        
        Args:
            format_type: Tipo de formato ('csv' o 'excel')
            
        Returns:
            Datos exportados como bytes
        """
        if not self.has_selection:
            return b""
        
        if format_type.lower() == "csv":
            return self.selected_df.to_csv(index=False).encode('utf-8')
        elif format_type.lower() == "excel":
            from io import BytesIO
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                self.selected_df.to_excel(writer, index=False, sheet_name='Selected')
            return buffer.getvalue()
        else:
            raise ValueError(f"Formato no soportado: {format_type}")
