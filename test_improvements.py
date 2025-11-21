"""
Script de prueba para verificar que Account Name se lee correctamente del Excel.

Verifica que:
1. La columna Account Name se lee del Excel
2. Se usa Account Name en lugar de extraer del nombre del proyecto
3. El cliente correcto se asigna a cada proyecto
"""

import sys
import os
sys.path.append('src')
sys.path.append('config')

import pandas as pd
from src.data_processor import DataProcessor
from src.extract_projects import extract_projects_from_pipeline
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

def test_account_name_reading(file_path: str):
    """
    Prueba que Account Name se lea correctamente del Excel.
    
    Args:
        file_path: Ruta al archivo Excel a probar
    """
    print("\n" + "="*80)
    print("PRUEBA DE LECTURA DE ACCOUNT NAME")
    print("="*80 + "\n")
    
    if not os.path.exists(file_path):
        print(f"❌ Error: No se encontró el archivo: {file_path}")
        return
    
    try:
        # PASO 1: Leer Excel directamente
        print("📖 Paso 1: Leyendo Excel directamente...")
        df_raw = extract_projects_from_pipeline(file_path, sheet_name=0)
        
        # Verificar si existe columna Account Name
        account_col = None
        for col in df_raw.columns:
            if 'account' in col.lower() and 'name' in col.lower():
                account_col = col
                break
        
        if account_col:
            print(f"   ✅ Columna '{account_col}' encontrada en el Excel")
            print(f"   ✅ Total de clientes únicos: {df_raw[account_col].nunique()}")
            
            # Buscar el proyecto específico
            search_term = "Heating Cycle Optimization"
            matching_rows = df_raw[df_raw.apply(lambda row: search_term.lower() in str(row).lower(), axis=1)]
            
            if len(matching_rows) > 0:
                print(f"\n🔍 Proyecto encontrado: '{search_term}'")
                for idx, row in matching_rows.iterrows():
                    opp_col = None
                    for col in df_raw.columns:
                        if 'opportunity' in col.lower() or 'project' in col.lower():
                            opp_col = col
                            break
                    
                    if opp_col:
                        print(f"   • Nombre: {row[opp_col]}")
                        print(f"   • Cliente (Account Name): {row[account_col]}")
            else:
                print(f"\n⚠️ No se encontró el proyecto '{search_term}' en el Excel")
        else:
            print("   ⚠️ No se encontró columna Account Name en el Excel")
            print(f"   Columnas disponibles: {list(df_raw.columns)}")
        
        # PASO 2: Procesar con DataProcessor
        print("\n🔧 Paso 2: Procesando con DataProcessor...")
        processor = DataProcessor()
        df_parsed, parsing_report = processor.read_excel_file(file_path)
        
        # Verificar si Account Name se normalizó correctamente
        if 'Account Name' in df_parsed.columns:
            print("   ✅ 'Account Name' normalizada correctamente")
        else:
            print("   ⚠️ 'Account Name' NO fue normalizada")
            print(f"   Columnas disponibles después de parsing: {list(df_parsed.columns)}")
        
        # PASO 3: Limpiar y preparar datos
        print("\n🧹 Paso 3: Limpiando datos...")
        df_clean = processor.clean_and_prepare_data(df_parsed)
        
        # Buscar el proyecto específico en datos limpios
        if len(df_clean) > 0:
            search_rows = df_clean[df_clean['Opportunity Name'].str.contains("Heating Cycle", case=False, na=False)]
            
            if len(search_rows) > 0:
                print(f"\n🎯 Proyecto 'Heating Cycle Optimization' después del procesamiento:")
                for idx, row in search_rows.iterrows():
                    print(f"   • Nombre: {row['Opportunity Name']}")
                    if 'Account Name' in df_clean.columns:
                        print(f"   • Cliente (Account Name del Excel): {row['Account Name']}")
                    else:
                        print(f"   ⚠️ Account Name no disponible en datos procesados")
                    print(f"   • BU: {row['BU']}")
                    print(f"   • Amount: ${row['Amount']:,.2f}")
            else:
                print("\n⚠️ Proyecto 'Heating Cycle Optimization' no encontrado en datos procesados")
        
        # PASO 4: Convertir a Opportunities
        print("\n📦 Paso 4: Convirtiendo a objetos Opportunity...")
        opportunities = processor.convert_to_opportunities(df_clean)
        
        # Buscar el proyecto específico en opportunities
        matching_opps = [opp for opp in opportunities if "Heating Cycle" in opp.name]
        
        if matching_opps:
            print(f"\n✅ Proyecto encontrado en objetos Opportunity:")
            for opp in matching_opps:
                print(f"   • Nombre: {opp.name}")
                print(f"   • Cliente (account_name): {opp.account_name}")
                print(f"   • BU: {opp.bu.value}")
                print(f"   • Amount: ${opp.amount:,.2f}")
                print(f"   • Company: {opp.company}")
        else:
            print("\n⚠️ Proyecto 'Heating Cycle Optimization' no encontrado en objetos Opportunity")
        
        # RESUMEN
        print(f"\n" + "="*80)
        print("RESUMEN")
        print("="*80)
        print(f"   • Total registros procesados: {len(df_clean)}")
        print(f"   • Total opportunities creadas: {len(opportunities)}")
        
        if 'Account Name' in df_clean.columns:
            print(f"   ✅ Account Name está disponible en el procesamiento")
            with_account = df_clean['Account Name'].notna().sum()
            print(f"   • Proyectos con Account Name: {with_account} de {len(df_clean)}")
        else:
            print(f"   ❌ Account Name NO está disponible en el procesamiento")
            print(f"   ⚠️ Los clientes se están extrayendo del nombre del proyecto (puede ser inexacto)")
        
    except Exception as e:
        print(f"\n❌ Error durante la prueba: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import glob
    
    # Buscar archivos Excel en la carpeta data
    excel_files = glob.glob("data/*.xlsx")
    
    if not excel_files:
        print("❌ No se encontraron archivos Excel en la carpeta 'data/'")
        print("\n💡 Uso: python test_improvements.py <ruta_archivo>")
        sys.exit(1)
    
    # Usar el primer archivo encontrado o el especificado en argumentos
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = excel_files[0]
        print(f"\n📁 Usando archivo: {file_path}")
    
    test_account_name_reading(file_path)
