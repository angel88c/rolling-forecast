"""
Script para debuggear el problema de parsing con el archivo real.
"""

import sys
import os
sys.path.append('src')
sys.path.append('config')

from src.data_processor import DataProcessor
from src.validators import DataValidator
import pandas as pd

def test_with_real_file():
    """Prueba con el archivo real para identificar el problema."""
    print("=== DEBUG: Problema de Parsing ===")
    
    file_path = "data/C&NQFunnel-OpenQuotes(25-50%)-2025-06-03-14-00-13.xlsx"
    
    if not os.path.exists(file_path):
        print("❌ Archivo no encontrado")
        return
    
    # Crear instancias
    processor = DataProcessor()
    validator = DataValidator()
    
    try:
        # Paso 1: Leer archivo con detección automática
        print("📖 Leyendo archivo con detección automática...")
        df, parsing_report = processor.read_excel_file(file_path)
        
        print(f"✅ Archivo leído: {len(df)} registros")
        print(f"✅ Columnas encontradas: {list(df.columns)}")
        print(f"✅ Fila de header detectada: {parsing_report.get('detected_header_row', 'N/A')}")
        print(f"✅ Parsing exitoso: {parsing_report.get('parsing_success', False)}")
        
        # Mostrar mapeos aplicados
        if parsing_report.get('applied_mappings'):
            print("✅ Mapeos aplicados:")
            for orig, norm in parsing_report['applied_mappings'].items():
                print(f"   '{orig}' → '{norm}'")
        
        # Mostrar columnas faltantes si las hay
        validation_result = parsing_report.get('validation_result', {})
        if validation_result.get('missing_columns'):
            print("❌ Columnas faltantes:")
            for col in validation_result['missing_columns']:
                print(f"   - {col}")
        
        # Paso 2: Procesar datos
        print("\n🔧 Procesando datos...")
        df_clean = processor.clean_and_prepare_data(df)
        print(f"✅ Datos procesados: {len(df_clean)} registros válidos")
        
        # Paso 3: Validar datos procesados
        print("\n✅ Validando datos procesados...")
        data_validation = validator.validate_dataframe(df_clean)
        print(f"✅ Validación exitosa: {data_validation.is_valid}")
        print(f"✅ Registros válidos: {data_validation.valid_records}")
        
        if data_validation.errors:
            print("❌ Errores encontrados:")
            for error in data_validation.errors:
                print(f"   - {error}")
        
        if data_validation.warnings:
            print("⚠️ Advertencias:")
            for warning in data_validation.warnings[:5]:
                print(f"   - {warning}")
        
    except Exception as e:
        print(f"❌ Error durante el procesamiento: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_with_real_file()
