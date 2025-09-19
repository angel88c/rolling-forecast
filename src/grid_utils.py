"""
Utilidades para manejo seguro de respuestas de AG-Grid.

Este módulo proporciona funciones y clases para manejar de forma segura
las respuestas de AG-Grid, evitando errores comunes como evaluaciones
ambiguas de DataFrames.
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
    
    return data


def safe_get_selected_rows(grid_response: Optional[Dict[str, Any]]) -> List[Dict]:
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
    
    return selected_rows


def safe_get_filter_model(grid_response: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Obtiene el modelo de filtros de forma segura.
    
    Args:
        grid_response: Respuesta de AG-Grid que puede ser None
        
    Returns:
        Diccionario con el modelo de filtros, vacío si no hay filtros
    """
    if not grid_response:
        return {}
    
    return grid_response.get('filterModel', {})


def get_grid_stats(grid_response: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calcula estadísticas de la grid de forma segura.
    
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


class GridResponseHandler:
    """
    Manejador seguro para respuestas de AG-Grid.
    
    Esta clase encapsula el manejo de respuestas de AG-Grid,
    proporcionando acceso seguro a datos, selecciones y estadísticas.
    """
    
    def __init__(self, grid_response: Optional[Dict[str, Any]]):
        """
        Inicializa el manejador con una respuesta de grid.
        
        Args:
            grid_response: Respuesta de AG-Grid que puede ser None
        """
        self.grid_response = grid_response
        self._stats = None
    
    @property
    def stats(self) -> Dict[str, Any]:
        """Obtiene las estadísticas de la grid (lazy loading)."""
        if self._stats is None:
            self._stats = get_grid_stats(self.grid_response)
        return self._stats
    
    @property
    def has_data(self) -> bool:
        """Indica si la grid tiene datos."""
        return self.stats['has_data']
    
    @property
    def has_selection(self) -> bool:
        """Indica si hay filas seleccionadas."""
        return self.stats['has_selection']
    
    @property
    def total_rows(self) -> int:
        """Número total de filas."""
        return self.stats['total_rows']
    
    @property
    def selected_rows_count(self) -> int:
        """Número de filas seleccionadas."""
        return self.stats['selected_rows']
    
    @property
    def selected_count(self) -> int:
        """Alias para selected_rows_count (compatibilidad)."""
        return self.selected_rows_count
    
    @property
    def data_df(self) -> pd.DataFrame:
        """DataFrame con todos los datos."""
        return self.stats['data_df']
    
    @property
    def selected_df(self) -> pd.DataFrame:
        """DataFrame con las filas seleccionadas."""
        return self.stats['selected_df']
    
    def get_data(self) -> List[Dict]:
        """Obtiene los datos como lista de diccionarios."""
        return safe_get_grid_data(self.grid_response)
    
    def get_selected_rows(self) -> List[Dict]:
        """Obtiene las filas seleccionadas como lista de diccionarios."""
        return safe_get_selected_rows(self.grid_response)
    
    def calculate_totals(self, numeric_columns: List[str]) -> Dict[str, float]:
        """
        Calcula totales para las columnas numéricas especificadas.
        
        Args:
            numeric_columns: Lista de nombres de columnas numéricas
            
        Returns:
            Diccionario con los totales por columna
        """
        return safe_calculate_totals(self.grid_response, numeric_columns)
    
    def export_data(self, format_type: str = "csv") -> bytes:
        """
        Exporta todos los datos.
        
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
