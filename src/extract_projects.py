import pandas as pd
import re
from typing import Optional

def extract_projects_from_pipeline(file_path: str, sheet_name: str = 'YTD Pipeline') -> pd.DataFrame:
    """
    Extrae el listado de proyectos con sus probabilidades desde un archivo Excel de pipeline.
    
    Esta función:
    - Detecta automáticamente la fila de headers (buscando 'Probability' y 'Account Name')
    - Limpia los nombres de columnas removiendo símbolos como flechas (↑, ↓)
    - Remueve filas de totales (Subtotal, Sum, Avg, Count)
    - Retorna solo las filas de proyectos individuales
    
    Parameters:
    -----------
    file_path : str
        Ruta al archivo Excel
    sheet_name : str, optional
        Nombre de la hoja a leer (default: 'YTD Pipeline')
    
    Returns:
    --------
    pd.DataFrame
        DataFrame con el listado de proyectos limpio
    
    Example:
    --------
    >>> df_projects = extract_projects_from_pipeline('YTDPipeline-2025-10-28-14-00-02.xlsx')
    >>> print(df_projects.head())
    """
    
    # Leer el archivo sin headers para detectar la estructura
    df_raw = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
    print(df_raw.head(50).to_csv("OutCSV.csv"))
    # Buscar la fila de headers
    header_row = None
    for idx in range(min(20, len(df_raw))):  # Buscar en las primeras 20 filas
        row_values = df_raw.iloc[idx].astype(str).tolist()
        # Buscar indicadores de que esta es la fila de headers
        if any('Probability' in str(val) for val in row_values) and \
           any('Account Name' in str(val) or 'Opportunity' in str(val) for val in row_values):
            header_row = idx
            break
    
    if header_row is None:
        raise ValueError("No se pudo encontrar la fila de headers en el archivo")
    
    # Extraer los headers y limpiarlos
    headers = df_raw.iloc[header_row].tolist()
    cleaned_headers = []
    
    for i, header in enumerate(headers):
        if pd.isna(header):
            # Si el header es NaN, usar un nombre genérico
            cleaned_headers.append(f'Column_{i}')
        else:
            # Limpiar símbolos como flechas y espacios extras
            clean_header = str(header)
            # Remover flechas y otros símbolos especiales
            clean_header = re.sub(r'[↑↓→←▲▼►◄]', '', clean_header)
            # Limpiar espacios múltiples
            clean_header = re.sub(r'\s+', ' ', clean_header).strip()
            cleaned_headers.append(clean_header)
    
    # Leer el dataframe desde la fila siguiente a los headers
    df = pd.read_excel(file_path, sheet_name=sheet_name, header=header_row)
    
    # Aplicar los headers limpios
    df.columns = cleaned_headers[:len(df.columns)]
    
    # Identificar columnas clave para filtrado
    # Buscar la columna de BU (Business Unit) o similar
    bu_col = None
    for col in df.columns:
        if 'BU' in str(col).upper() or 'Business Unit' in str(col):
            bu_col = col
            break
    
    # Buscar columna de Account Name
    account_col = None
    for col in df.columns:
        if 'Account Name' in str(col) or 'Account' in str(col):
            account_col = col
            break
    
    # Palabras clave que indican filas de totales o agregaciones
    total_keywords = ['Subtotal', 'Sum', 'Avg', 'Count', 'Total', 'Grand Total', 'Average']
    
    # Crear máscara para filtrar filas de totales
    mask = pd.Series([True] * len(df), index=df.index)
    
    # Filtrar por columna BU
    if bu_col:
        mask &= ~df[bu_col].astype(str).str.contains('|'.join(total_keywords), case=False, na=False)
    
    # Filtrar por primera columna (Probability)
    first_col = df.columns[0]
    if first_col:
        mask &= ~df[first_col].astype(str).str.contains('|'.join(total_keywords), case=False, na=False)
    
    # Filtrar por Account Name - remover filas donde Account Name es un número (indicador de Count)
    if account_col:
        # Remover filas donde Account Name está vacío
        mask &= df[account_col].notna()
        # Remover filas donde Account Name es solo un número (como "4", "1", "9")
        mask &= ~df[account_col].astype(str).str.match(r'^\d+$')
    
    # Aplicar el filtro
    df = df[mask]
    
    # Remover filas completamente vacías
    df = df.dropna(how='all')
    
    # Reset del índice
    df = df.reset_index(drop=True)
    
    # Remover columnas completamente vacías
    df = df.dropna(axis=1, how='all')
    
    # Propagar la probabilidad agrupada a todos los proyectos del grupo
    # La probabilidad está en la primera columna y se agrupa en celdas
    # Buscar la columna de Probability
    prob_col = None
    for col in df.columns:
        if 'Probability' in str(col).upper() or 'Probability' in str(col):
            prob_col = col
            break
   
    #prob_col = df.columns[0]     
    # Aplicar forward fill preliminar para ayudar con la lectura del Excel
    # El forward fill definitivo se aplicará en data_processor.py después de la conversión numérica
    df[prob_col] = df[prob_col].ffill()
    
    if bu_col:
        df[bu_col] = df[bu_col].ffill()
    
    # También propagar Account Name si está vacío en algunas filas
    #if account_col:
    #    df[account_col] = df[account_col].ffill()
    
    return df


# Función auxiliar para obtener solo columnas específicas
def extract_projects_summary(file_path: str, 
                             columns: Optional[list] = None,
                             sheet_name: str = 'YTD Pipeline') -> pd.DataFrame:
    """
    Extrae un resumen de proyectos con columnas específicas.
    
    Parameters:
    -----------
    file_path : str
        Ruta al archivo Excel
    columns : list, optional
        Lista de nombres de columnas a incluir. Si es None, incluye todas.
        Ejemplos: ['Probability (%)', 'Account Name', 'Opportunity Name', 'Amount']
    sheet_name : str, optional
        Nombre de la hoja a leer (default: 'YTD Pipeline')
    
    Returns:
    --------
    pd.DataFrame
        DataFrame con las columnas seleccionadas
    """
    
    df = extract_projects_from_pipeline(file_path, sheet_name)
    
    if columns:
        # Buscar las columnas que coincidan (ignorando mayúsculas/minúsculas y espacios)
        available_cols = []
        for col_name in columns:
            for df_col in df.columns:
                if col_name.lower().strip() in df_col.lower().strip() or \
                   df_col.lower().strip() in col_name.lower().strip():
                    available_cols.append(df_col)
                    break
        
        if available_cols:
            df = df[available_cols]
    
    return df


if __name__ == "__main__":
    # Ejemplo de uso
    file_path = 'data/YTD Pipeline-2025-10-28-14-00-02.xlsx'
    file_path = 'data/Forecast (Intuition) C.Quarter(Opp =60%)-2025-11-11-13-00-06.xlsx'
    # file_path = 'data/YTD Pipeline-2025-11-11-14-00-01.xlsx'
    
    print("=" * 80)
    print("EXTRAYENDO TODOS LOS PROYECTOS")
    print("=" * 80)
    df_projects = extract_projects_from_pipeline(file_path, sheet_name="Forecast (Intuition) C.Quarter(")
    print(f"\nTotal de proyectos encontrados: {len(df_projects)}")
    print(f"\nColumnas disponibles: {list(df_projects.columns)}")
    print(f"\nPrimeros 10 proyectos:")
    print(df_projects.head(10).to_string())
    
    print("\n" + "=" * 80)
    print("RESUMEN CON COLUMNAS ESPECÍFICAS")
    print("=" * 80)
    df_summary = extract_projects_summary(
        file_path,
        columns=['Probability (%)', 'BU', 'Account Name', 'Opportunity Name', 'Amount', 'Stage'],
        sheet_name="Forecast (Intuition) C.Quarter(")
    print(f"\nPrimeros 20 proyectos (resumen):")
    print(df_summary.head(20).to_string())
    
    # Guardar a CSV para verificación
    output_path = '/users/c_angel/downloads/projects_extracted_mayores_60.csv'
    df_projects.to_csv(output_path, index=False)
    print(f"\n\nDataFrame completo guardado en: {output_path}")
    print(f"Total de proyectos en el archivo: {len(df_projects)}")
