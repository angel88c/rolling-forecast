"""
Utilidades para configurar AG-Grid con estilos y funcionalidades optimizadas.
"""

from st_aggrid import GridOptionsBuilder, JsCode
import pandas as pd
from typing import Dict, List, Optional, Any


class AGGridConfigurator:
    """Configurador de AG-Grid para diferentes tipos de tablas."""
    
    # Colores corporativos
    COLORS = {
        'primary': '#2E86AB',
        'secondary': '#A23B72', 
        'success': '#28a745',
        'warning': '#ffc107',
        'danger': '#dc3545',
        'info': '#17a2b8',
        'light': '#f8f9fa',
        'dark': '#343a40',
        'turquoise': '#40E0D0'
    }
    
    @staticmethod
    def get_currency_formatter() -> JsCode:
        """Formateador de moneda para AG-Grid con 2 decimales."""
        return JsCode("""
        function(params) {
            if (params.value == null || params.value === 0) {
                return '$0.00';
            }
            return '$' + params.value.toLocaleString('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            });
        }
        """)
    
    @staticmethod
    def get_percentage_formatter() -> JsCode:
        """Formateador de porcentaje para AG-Grid."""
        return JsCode("""
        function(params) {
            if (params.value == null) {
                return '';
            }
            return (params.value * 100).toFixed(0) + '%';
        }
        """)
    
    @staticmethod
    def get_cell_style_currency() -> JsCode:
        """Estilo condicional para celdas de moneda con mejor contraste."""
        return JsCode("""
        function(params) {
            if (params.value == null || params.value === 0) {
                return {
                    'backgroundColor': '#f8f9fa',
                    'color': '#6c757d',
                    'fontStyle': 'italic',
                    'textAlign': 'right'
                };
            } else if (params.value > 0) {
                return {
                    'backgroundColor': 'rgba(64, 224, 208, 0.3)',
                    'color': '#1f4e79',
                    'fontWeight': '600',
                    'textAlign': 'right',
                    'border': '1px solid rgba(64, 224, 208, 0.5)'
                };
            }
            return {
                'textAlign': 'right'
            };
        }
        """)
    
    @staticmethod
    def get_bu_cell_renderer() -> JsCode:
        """Renderer para celdas de BU con iconos."""
        return JsCode("""
        function(params) {
            const icons = {
                'FCT': '🏭',
                'ICT': '💻',
                'IAT': '🔧',
                'REP': '🔄',
                'SWD': '💾'
            };
            const icon = icons[params.value] || '📊';
            return icon + ' ' + params.value;
        }
        """)
    
    @classmethod
    def configure_forecast_table(cls, df: pd.DataFrame) -> GridOptionsBuilder:
        """Configura AG-Grid para la tabla principal de forecast."""
        gb = GridOptionsBuilder.from_dataframe(df)
        
        # Configuración general
        gb.configure_default_column(
            filterable=True,
            sortable=True,
            resizable=True,
            minWidth=100
        )
        
        # Columnas fijas
        gb.configure_column("Proyecto", pinned="left", width=250, minWidth=200)
        gb.configure_column("BU", 
            pinned="left", 
            width=100, 
            cellRenderer=cls.get_bu_cell_renderer()
        )
        
        # Configurar columnas de meses (todas las que no sean Proyecto y BU)
        month_columns = [col for col in df.columns if col not in ['Proyecto', 'BU']]
        
        for col in month_columns:
            gb.configure_column(col,
                type=["numericColumn"],
                valueFormatter=cls.get_currency_formatter(),
                cellStyle=cls.get_cell_style_currency(),
                width=120,
                aggFunc="sum"  # Suma automática en agrupaciones
            )
        
        # Configuraciones avanzadas
        gb.configure_grid_options(
            enableRangeSelection=True,
            enableCharts=True,
            suppressMenuHide=True,
            animateRows=True,
            rowHeight=40,
            headerHeight=45
        )
        
        # Agrupación por BU
        gb.configure_column("BU", rowGroup=True, hide=False)
        gb.configure_grid_options(
            groupDefaultExpanded=1,
            suppressAggFuncInHeader=True,
            groupIncludeFooter=True
        )
        
        return gb
    
    @classmethod
    def configure_details_table(cls, df: pd.DataFrame) -> GridOptionsBuilder:
        """Configura AG-Grid para la tabla de detalles de eventos."""
        gb = GridOptionsBuilder.from_dataframe(df)
        
        # Configuración general
        gb.configure_default_column(
            filterable=True,
            sortable=True,
            resizable=True,
            minWidth=100
        )
        
        # Configuraciones específicas por columna
        gb.configure_column("Proyecto", width=200, pinned="left")
        gb.configure_column("BU", 
            width=80, 
            cellRenderer=cls.get_bu_cell_renderer()
        )
        gb.configure_column("Etapa", width=120)
        gb.configure_column("Fecha", width=120, type="dateColumn")
        gb.configure_column("Mes", width=120)
        
        # Columnas de montos
        money_columns = ['Monto Original', 'Monto Ajustado']
        for col in money_columns:
            if col in df.columns:
                gb.configure_column(col,
                    type=["numericColumn"],
                    valueFormatter=cls.get_currency_formatter(),
                    width=140
                )
        
        # Columna de probabilidad
        if 'Probabilidad' in df.columns:
            gb.configure_column("Probabilidad", 
                width=100,
                valueFormatter=cls.get_percentage_formatter()
            )
        
        # Configuraciones avanzadas
        gb.configure_grid_options(
            enableRangeSelection=True,
            suppressMenuHide=True,
            animateRows=True,
            rowHeight=35,
            headerHeight=40
        )
        
        # Selección múltiple
        gb.configure_selection(selection_mode="multiple", use_checkbox=True)
        
        return gb
    
    @classmethod
    def configure_summary_table(cls, df: pd.DataFrame) -> GridOptionsBuilder:
        """Configura AG-Grid para tablas de resumen."""
        gb = GridOptionsBuilder.from_dataframe(df)
        
        # Configuración general
        gb.configure_default_column(
            filterable=True,
            sortable=True,
            resizable=True,
            minWidth=120
        )
        
        # Configurar todas las columnas numéricas
        for col in df.columns:
            if df[col].dtype in ['int64', 'float64']:
                gb.configure_column(col,
                    type=["numericColumn"],
                    valueFormatter=cls.get_currency_formatter(),
                    cellStyle=cls.get_cell_style_currency(),
                    width=140
                )
        
        # Configuraciones avanzadas
        gb.configure_grid_options(
            suppressMenuHide=True,
            animateRows=True,
            rowHeight=35,
            headerHeight=40,
            enableRangeSelection=True
        )
        
        return gb
    
    @staticmethod
    def get_grid_theme() -> str:
        """Retorna el tema recomendado para AG-Grid."""
        return "streamlit"  # Opciones: streamlit, alpine, balham, material
    
    @staticmethod
    def get_grid_height(num_rows: int, max_height: int = 600) -> int:
        """Calcula la altura óptima para la grid basada en el número de filas."""
        row_height = 40
        header_height = 45
        calculated_height = (num_rows * row_height) + header_height + 50
        return min(calculated_height, max_height)


class AGGridExporter:
    """Utilidades para exportar datos desde AG-Grid."""
    
    @staticmethod
    def export_to_excel(grid_response, filename: str = "export.xlsx") -> bytes:
        """Exporta los datos seleccionados/filtrados a Excel."""
        if grid_response and 'data' in grid_response:
            df = pd.DataFrame(grid_response['data'])
            return df.to_excel(filename, index=False, engine='openpyxl')
        return None
    
    @staticmethod
    def get_selected_rows(grid_response) -> pd.DataFrame:
        """Obtiene las filas seleccionadas de la grid."""
        if grid_response and 'selected_rows' in grid_response:
            return pd.DataFrame(grid_response['selected_rows'])
        return pd.DataFrame()
    
    @staticmethod
    def get_filtered_data(grid_response) -> pd.DataFrame:
        """Obtiene los datos filtrados de la grid."""
        if grid_response and 'data' in grid_response:
            return pd.DataFrame(grid_response['data'])
        return pd.DataFrame()


# Configuraciones predefinidas para diferentes tipos de análisis
GRID_CONFIGS = {
    'forecast_main': {
        'theme': 'streamlit',
        'height': 500,
        'enable_enterprise_modules': False,
        'allow_unsafe_jscode': True,
        'update_mode': 'MODEL_CHANGED',
        'fit_columns_on_grid_load': True
    },
    'details': {
        'theme': 'streamlit', 
        'height': 400,
        'enable_enterprise_modules': False,
        'allow_unsafe_jscode': True,
        'update_mode': 'SELECTION_CHANGED',
        'fit_columns_on_grid_load': False
    },
    'summary': {
        'theme': 'streamlit',
        'height': 300,
        'enable_enterprise_modules': False,
        'allow_unsafe_jscode': True,
        'update_mode': 'NO_UPDATE',
        'fit_columns_on_grid_load': True
    }
}
