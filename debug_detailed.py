"""
Script para hacer debug detallado del procesamiento paso a paso.
"""

import sys
sys.path.append('src')
sys.path.append('config')

from src.data_processor import DataProcessor
import pandas as pd

file_path = "data/C&NQFunnel-OpenQuotes(25-50%)-2025-06-03-14-00-13.xlsx"

print("\n" + "="*80)
print("DEBUG DETALLADO DEL PROCESAMIENTO")
print("="*80 + "\n")

processor = DataProcessor()

# Paso 1: Leer archivo
print("📖 PASO 1: Leyendo archivo...")
df_parsed, _ = processor.read_excel_file(file_path)
print(f"✅ Registros leídos: {len(df_parsed)}")
print(f"✅ Columnas: {list(df_parsed.columns)[:5]}...")

# Paso 2: Limpiar BU
print("\n🧹 PASO 2: Limpiando columna BU...")
df_bu = processor._clean_bu_column(df_parsed)
print(f"✅ Registros después de limpiar BU: {len(df_bu)}")

# Paso 3: Asignar probabilidades
print("\n🎲 PASO 3: Asignando probabilidades...")
df_prob = processor._assign_probabilities(df_bu)
print(f"✅ Registros después de asignar prob: {len(df_prob)}")
if 'probability_assigned' in df_prob.columns:
    print(f"✅ probability_assigned creada")
    print(f"   - Con valores: {df_prob['probability_assigned'].notna().sum()}")
    print(f"   - Valores únicos: {df_prob['probability_assigned'].unique()[:5]}")
else:
    print(f"❌ probability_assigned NO fue creada")

# Paso 4: Convertir fechas
print("\n📅 PASO 4: Convirtiendo fechas...")
print(f"   - Columna 'Close Date' existe: {'Close Date' in df_prob.columns}")
if 'Close Date' in df_prob.columns:
    print(f"   - Valores no nulos en Close Date: {df_prob['Close Date'].notna().sum()}")
    print(f"   - Ejemplo de Close Date: {df_prob['Close Date'].iloc[0]}")

df_dates = processor._convert_dates(df_prob)
print(f"✅ Registros después de convertir fechas: {len(df_dates)}")
if 'close_date_parsed' in df_dates.columns:
    print(f"✅ close_date_parsed creada")
    print(f"   - Con valores: {df_dates['close_date_parsed'].notna().sum()}")
    if df_dates['close_date_parsed'].notna().sum() > 0:
        print(f"   - Ejemplo: {df_dates['close_date_parsed'].iloc[0]}")
else:
    print(f"❌ close_date_parsed NO fue creada")

# Paso 5: Limpiar valores numéricos
print("\n🔢 PASO 5: Limpiando valores numéricos...")
df_numeric = processor._clean_numeric_values(df_dates)
print(f"✅ Registros después de limpiar numéricos: {len(df_numeric)}")

# Paso 6: Detectar región y clasificar empresa
print("\n🌎 PASO 6: Detectando región y clasificando empresa...")
df_region = processor._detect_region_and_classify_company(df_numeric)
print(f"✅ Registros después de detectar región: {len(df_region)}")

# Paso 7: Completar datos faltantes
print("\n🔧 PASO 7: Completando datos faltantes...")
df_completed = processor._complete_missing_data(df_region)
print(f"✅ Registros después de completar datos: {len(df_completed)}")

# Verificación final antes del filtro
print("\n" + "="*80)
print("VERIFICACIÓN ANTES DEL FILTRO")
print("="*80 + "\n")

print(f"✓ Columna 'probability_assigned' existe: {'probability_assigned' in df_completed.columns}")
if 'probability_assigned' in df_completed.columns:
    print(f"  - Con valores: {df_completed['probability_assigned'].notna().sum()} de {len(df_completed)}")
    print(f"  - Sin valores: {df_completed['probability_assigned'].isna().sum()}")

print(f"✓ Columna 'close_date_parsed' existe: {'close_date_parsed' in df_completed.columns}")
if 'close_date_parsed' in df_completed.columns:
    print(f"  - Con valores: {df_completed['close_date_parsed'].notna().sum()} de {len(df_completed)}")
    print(f"  - Sin valores: {df_completed['close_date_parsed'].isna().sum()}")

# Paso 8: Filtrar registros válidos
print("\n🔍 PASO 8: Filtrando registros válidos...")
df_filtered = processor._filter_valid_records(df_completed)
print(f"✅ Registros válidos finales: {len(df_filtered)}")
print(f"❌ Registros excluidos: {len(df_completed) - len(df_filtered)}")
