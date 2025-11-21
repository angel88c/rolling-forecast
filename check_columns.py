"""
Script para verificar qué columnas tiene el DataFrame después del parsing.
"""

import sys
sys.path.append('src')
sys.path.append('config')

from src.data_processor import DataProcessor

file_path = "data/C&NQFunnel-OpenQuotes(25-50%)-2025-06-03-14-00-13.xlsx"

processor = DataProcessor()
df_parsed, _ = processor.read_excel_file(file_path)

print("\n" + "="*80)
print("COLUMNAS DESPUÉS DEL PARSING")
print("="*80 + "\n")

for i, col in enumerate(df_parsed.columns, 1):
    print(f"{i}. '{col}'")

print(f"\n✅ Total columnas: {len(df_parsed.columns)}")

# Verificar columnas clave
print("\n" + "="*80)
print("VERIFICACIÓN DE COLUMNAS CLAVE")
print("="*80 + "\n")

key_columns = ['Close Date', 'Probability (%)', 'Probability (%)  ↑', 'close_date_parsed', 'probability_assigned']

for col in key_columns:
    exists = col in df_parsed.columns
    status = "✅" if exists else "❌"
    print(f"{status} '{col}': {'Existe' if exists else 'NO existe'}")

# Mostrar algunos valores de Close Date y Probability
print("\n" + "="*80)
print("MUESTRAS DE DATOS")
print("="*80 + "\n")

# Buscar columnas que contengan "close" o "date"
date_cols = [col for col in df_parsed.columns if 'close' in col.lower() or 'date' in col.lower()]
print(f"Columnas con 'close' o 'date': {date_cols}\n")

# Buscar columnas que contengan "prob"
prob_cols = [col for col in df_parsed.columns if 'prob' in col.lower()]
print(f"Columnas con 'prob': {prob_cols}\n")

if date_cols:
    print(f"Primeros 5 valores de '{date_cols[0]}':")
    print(df_parsed[date_cols[0]].head())

if prob_cols:
    print(f"\nPrimeros 5 valores de '{prob_cols[0]}':")
    print(df_parsed[prob_cols[0]].head())
