"""
Componentes reutilizables de UI para la aplicación de Forecast.
Funciones extraídas de app.py para mejorar modularidad.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from openpyxl.styles import numbers

# Re-exportar componentes de otros módulos para facilitar imports
from src.aggrid_utils import AGGridConfigurator, AGGridExporter, GRID_CONFIGS
from src.grid_utils import GridResponseHandler
from src.ui_styles import create_section_header


def render_file_uploader(label: str, key: str, file_types: list = None, help_text: str = None):
    """
    Componente reutilizable para subir archivos.
    
    Args:
        label: Etiqueta del uploader
        key: Key único para el componente
        file_types: Lista de extensiones aceptadas
        help_text: Texto de ayuda
        
    Returns:
        Archivo subido o None
    """
    if file_types is None:
        file_types = ['xlsx']
        
    uploaded_file = st.file_uploader(
        label,
        type=file_types,
        help=help_text,
        key=key
    )
    return uploaded_file


def render_filters_row(df: pd.DataFrame, filter_configs: list) -> dict:
    """
    Componente reutilizable para renderizar fila de filtros.
    
    Args:
        df: DataFrame con los datos
        filter_configs: Lista de dicts con configuración de filtros
            [{'column': 'Empresa', 'label': '🏢 Empresa', 'key': 'filter_empresa', 'default': 'Todas'}]
    
    Returns:
        dict: Diccionario con los valores seleccionados {column: valor}
    """
    cols = st.columns(len(filter_configs))
    selected_values = {}
    
    for idx, (col, config) in enumerate(zip(cols, filter_configs)):
        with col:
            column = config['column']
            default_option = config.get('default', 'Todas')
            options = [default_option] + sorted(df[column].dropna().unique().tolist())
            selected = st.selectbox(
                config['label'],
                options,
                key=config['key']
            )
            selected_values[column] = selected
    
    return selected_values


def render_totals_panel(df: pd.DataFrame, label: str, color: str = '#E3F2FD') -> dict:
    """
    Renderiza un panel de totales separado que siempre es visible.
    
    Args:
        df: DataFrame con los datos
        label: Etiqueta del panel
        color: Color de fondo (no usado actualmente)
        
    Returns:
        dict: Diccionario con los totales calculados
    """
    # Calcular totales solo de columnas numéricas
    text_columns = ['Proyecto', 'BU', 'Empresa', 'Company', 'Location', 'Status', 'Customer', '% Facturación']
    
    totals = {}
    for col in df.columns:
        if col not in text_columns:
            try:
                total = pd.to_numeric(df[col], errors='coerce').sum()
                if total != 0:  # Solo mostrar si hay valor
                    totals[col] = total
            except:
                pass
    
    # Mostrar panel de totales
    st.markdown(f"### 🧮 {label}")
    
    # Crear DataFrame con los totales en formato tabla
    if totals:
        # Crear DataFrame con una fila de totales
        totals_df = pd.DataFrame([totals])
        
        # Formatear valores como moneda para visualización
        totals_df_formatted = totals_df.copy()
        for col in totals_df_formatted.columns:
            totals_df_formatted[col] = totals_df_formatted[col].apply(lambda x: f"${x:,.2f}")
        
        # Mostrar tabla con st.data_editor
        st.data_editor(
            totals_df_formatted,
            use_container_width=True,
            hide_index=True,
            disabled=True,  # Solo lectura
            column_config={
                col: st.column_config.TextColumn(
                    col,
                    width="medium",
                ) for col in totals_df_formatted.columns
            }
        )
    else:
        st.info("No hay totales para mostrar")
    
    # Mostrar totales agrupados por BU
    if 'BU' in df.columns and totals:
        st.markdown("#### 📊 Totales por Grupo de BU")
        
        # Mapeo de BUs a grupos
        bu_groups = {
            'TESTING': ['ICT', 'FCT'],
            'AUTOMATION': ['IAT'],
            'REP & TRN': ['REP', 'TRN']
        }
        
        # Crear función para asignar grupo
        def assign_group(bu):
            bu_upper = str(bu).upper().strip()
            for group_name, bus in bu_groups.items():
                if bu_upper in bus:
                    return group_name
            return 'OTROS'
        
        # Asignar grupo a cada registro
        df_with_group = df.copy()
        df_with_group['Grupo'] = df_with_group['BU'].apply(assign_group)
        
        # Calcular totales por grupo
        group_totals = []
        for group_name in ['TESTING', 'AUTOMATION', 'REP & TRN', 'OTROS']:
            group_df = df_with_group[df_with_group['Grupo'] == group_name]
            if not group_df.empty:
                group_row = {'Grupo': group_name}
                for col in df.columns:
                    if col not in text_columns:
                        try:
                            total = pd.to_numeric(group_df[col], errors='coerce').sum()
                            # Siempre agregar la columna, incluso si es 0 (para mantener consistencia con tabla general)
                            group_row[col] = total
                        except:
                            pass
                if len(group_row) > 1:  # Si tiene más que solo 'Grupo'
                    group_totals.append(group_row)
                
                # Si es TESTING, agregar ICT y FCT por separado
                if group_name == 'TESTING':
                    for bu_name in ['ICT', 'FCT']:
                        bu_df = df_with_group[df_with_group['BU'].astype(str).str.upper().str.strip() == bu_name]
                        if not bu_df.empty:
                            bu_row = {'Grupo': f'  └─ {bu_name}'}
                            for col in df.columns:
                                if col not in text_columns:
                                    try:
                                        total = pd.to_numeric(bu_df[col], errors='coerce').sum()
                                        # Siempre agregar la columna, incluso si es 0
                                        bu_row[col] = total
                                    except:
                                        pass
                            if len(bu_row) > 1:
                                group_totals.append(bu_row)
        
        if group_totals:
            # Crear DataFrame con totales por grupo
            group_df = pd.DataFrame(group_totals)
            
            # Formatear valores como moneda
            group_df_formatted = group_df.copy()
            for col in group_df_formatted.columns:
                if col != 'Grupo':
                    group_df_formatted[col] = group_df_formatted[col].apply(lambda x: f"${x:,.2f}" if pd.notna(x) else "$0.00")
            
            # Mostrar tabla
            st.data_editor(
                group_df_formatted,
                use_container_width=True,
                hide_index=True,
                disabled=True,
                column_config={
                    'Grupo': st.column_config.TextColumn(
                        'Grupo BU',
                        width="medium",
                    ),
                    **{
                        col: st.column_config.TextColumn(
                            col,
                            width="medium",
                        ) for col in group_df_formatted.columns if col != 'Grupo'
                    }
                }
            )
        else:
            st.info("No hay datos de BU para agrupar")
    
    st.markdown("---")
    return totals


def export_to_excel_with_format(df: pd.DataFrame, sheet_name: str = 'Datos') -> BytesIO:
    """
    Exporta DataFrame a Excel con formato de moneda en columnas numéricas.
    
    Args:
        df: DataFrame a exportar
        sheet_name: Nombre de la hoja
        
    Returns:
        BytesIO: Buffer con archivo Excel formateado
    """
    buffer = BytesIO()
    
    # Identificar columnas numéricas (excluyendo columnas de texto)
    text_columns = ['Proyecto', 'BU', 'Empresa', 'Company', 'Location', 'Status', 'Customer', '% Facturación']
    numeric_columns = [col for col in df.columns if col not in text_columns]
    
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
        
        # Obtener la hoja de trabajo
        worksheet = writer.sheets[sheet_name]
        
        # Aplicar formato de moneda a columnas numéricas
        for idx, col in enumerate(df.columns, start=1):
            if col in numeric_columns:
                col_letter = worksheet.cell(row=1, column=idx).column_letter
                
                # Aplicar formato de moneda (ej: $1,234.56)
                for row in range(2, len(df) + 2):  # +2 porque empezamos en row 2 (después del header)
                    cell = worksheet[f'{col_letter}{row}']
                    try:
                        if cell.value and isinstance(cell.value, (int, float)):
                            cell.number_format = '$#,##0.00'
                    except:
                        pass
        
        # Ajustar ancho de columnas
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    buffer.seek(0)
    return buffer


def render_export_buttons(df: pd.DataFrame, filename_prefix: str, key_prefix: str):
    """
    Componente reutilizable para botones de exportación.
    
    Args:
        df: DataFrame a exportar
        filename_prefix: Prefijo para el nombre del archivo
        key_prefix: Prefijo para keys de componentes
    """
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Exportar Excel", key=f"{key_prefix}_excel"):
            buffer = export_to_excel_with_format(df, filename_prefix)
            st.download_button(
                label="⬇️ Descargar Excel",
                data=buffer.getvalue(),
                file_name=f"{filename_prefix}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"{key_prefix}_download_excel"
            )
    
    with col2:
        if st.button("📥 Exportar CSV", key=f"{key_prefix}_csv"):
            csv_data = df.to_csv(index=False)
            st.download_button(
                label="⬇️ Descargar CSV",
                data=csv_data,
                file_name=f"{filename_prefix}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                key=f"{key_prefix}_download_csv"
            )


# Re-exportar todo para facilitar imports
__all__ = [
    'render_file_uploader',
    'render_filters_row',
    'render_totals_panel',
    'export_to_excel_with_format',
    'render_export_buttons',
    'AGGridConfigurator',
    'AGGridExporter',
    'GRID_CONFIGS',
    'GridResponseHandler',
    'create_section_header'
]
