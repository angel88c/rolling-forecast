# Plan de Refactorización del Proyecto

## Objetivo
Modular el proyecto para que cada tipo de Forecast tenga su propia clase y procesamiento, reutilizando código de manera eficiente.

## Cambios Realizados

### 1. Organización de Archivos ✅
- Movidos todos los archivos markdown (excepto README.md) a `docs/`
- Creada estructura `src/managers/` para clases de gestión de forecast

### 2. Estructura de Managers Creada ✅

#### `src/managers/base_forecast_manager.py`
Clase base con lógica común:
- `process_file()`: Procesa archivo Excel
- `filter_opportunities()`: Método abstracto para filtrar oportunidades
- `prepare_results()`: Método abstracto para preparar resultados
- `render_forecast_table()`: Renderiza tabla de forecast con filtros
- `render_cost_of_sale_table()`: Renderiza tabla de costo de venta
- `generate_consolidated_totals_excel()`: Genera reporte consolidado en Excel

#### `src/managers/forecast_main_manager.py`
Manager para forecast principal:
- Procesa TODAS las oportunidades (excluyendo 100%)
- Genera vista adicional de oportunidades <60%
- `render_forecast_tab()`: Renderiza pestaña completa de forecast
- `render_cost_of_sale_tab()`: Renderiza pestaña de costo de venta

#### `src/managers/forecast_low_prob_manager.py`
Manager para oportunidades <60%:
- Filtra SOLO oportunidades con probabilidad < 60%
- Muestra información de cuántas oportunidades encontró
- `render_forecast_tab()`: Renderiza pestaña completa con file uploader propio
- `render_cost_of_sale_tab()`: Renderiza costo de venta filtrado
- Genera reporte consolidado específico para <60%

### 3. Pendientes

#### Crear `src/ui_components.py`
Mover funciones reutilizables de UI desde app.py:
- `render_filters_row()`: Renderiza filtros
- `render_totals_panel()`: Panel de totales
- `render_export_buttons()`: Botones de exportación
- `render_file_uploader()`: File uploader consistente
- Importar y re-exportar componentes de aggrid_utils

#### Refactorizar `app.py`
- Eliminar código duplicado de procesamiento
- Usar `ForecastMainManager` para pestaña principal
- Usar `ForecastLowProbManager` para pestaña <60%
- Eliminar métricas redundantes después de las tablas
- Simplificar métodos de renderizado

#### Limpieza
- Eliminar archivos de debug en raíz:
  - `check_100_percent_real.py`
  - `check_columns.py`
  - `debug_*.py`
  - `find_dataframe_issues.py`
  - `test_*.py` (mover a `tests/`)
  - `df_clean.xlsx`
  - `OutCSV.csv`

## Beneficios de la Refactorización

1. **Modularidad**: Cada tipo de forecast tiene su propia clase
2. **Reutilización**: Código común en clase base
3. **Mantenibilidad**: Más fácil de entender y modificar
4. **Escalabilidad**: Fácil agregar nuevos tipos de forecast
5. **Organización**: Archivos en carpetas apropiadas
6. **Limpieza**: Menos código duplicado

## Próximos Pasos

1. Crear `src/ui_components.py` con funciones de UI
2. Refactorizar `app.py` para usar managers
3. Eliminar métricas redundantes
4. Limpiar archivos innecesarios
5. Probar funcionamiento completo
6. Actualizar documentación

## Compatibilidad

La refactorización mantiene compatibilidad con:
- Session state existente
- Estructura de datos actual
- Flujo de trabajo del usuario
- Funcionalidades de exportación
- KPIs y otras pestañas
