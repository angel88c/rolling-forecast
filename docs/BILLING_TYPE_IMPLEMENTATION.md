# Implementación de Tipos de Facturación: Contable y Financiera

## Resumen

Se implementó un selector en el sidebar para elegir entre dos métodos de facturación:
- **Contable**: Proceso actual con múltiples eventos de facturación (INICIO, DR, FAT, SAT)
- **Financiera**: Un solo evento de facturación al 100% en el mes del SAT

## Cambios Realizados

### 1. Selector en Sidebar (`app.py`)

**Ubicación:** Líneas 105-122

```python
# Selector de tipo de facturación
st.sidebar.header("💼 Tipo de Facturación")
billing_type = st.sidebar.radio(
    "Método de Facturación",
    options=["Contable", "Financiera"],
    index=0,
    help="Contable: Múltiples eventos (INICIO, DR, FAT, SAT). Financiera: Un solo evento al 100% en SAT."
)

# Guardar en session state
st.session_state.billing_type = billing_type
```

**Características:**
- Radio button con dos opciones
- Valor por defecto: "Contable"
- Muestra información contextual según la selección
- Se guarda automáticamente en `st.session_state`

---

### 2. ForecastCalculator (`src/forecast_calculator.py`)

**Cambios principales:**

#### Método `calculate_forecast()` (Líneas 33-61)
- Agregado parámetro `billing_type: str = "Contable"`
- Decisión de lógica según el tipo seleccionado

#### Nuevo método `_calculate_financial_billing()` (Líneas 63-95)
Calcula facturación financiera con las siguientes reglas:

**Para ICT/REP:**
- Usa SAT Date si existe
- Fallback: close_date + lead_time

**Para otras BUs (FCT, IAT, SWD, TRN):**
- Calcula fechas de etapas (INICIO, DR, FAT, SAT)
- Usa fecha SAT calculada

**Resultado:**
- Un solo evento al 100% del Amount en el mes del SAT
- Se aplican factores de castigo y probabilidad (como en modo Contable)

#### Formato del evento:
```python
event = self._create_billing_event(
    opportunity=opportunity,
    stage=BillingStage.SAT,
    date=sat_date,
    amount=opportunity.amount  # 100% del monto
)
```

**Factores aplicados:**
- Probabilidad del proyecto
- Factor de castigo financiero (60% para prob=60%, 40% para otras)

---

### 3. BaseForecastManager (`src/managers/base_forecast_manager.py`)

**Cambio:** Líneas 130-132

```python
# Paso 7: Calcular forecast con tipo de facturación
billing_type = getattr(st.session_state, 'billing_type', 'Contable')
billing_events = self.calculator.calculate_forecast(opportunities, billing_type=billing_type)
```

**Función:**
- Lee el tipo de facturación de `session_state`
- Lo pasa al calculador de forecast
- Valor por defecto: "Contable"

---

### 4. KPIProcessor (`src/kpi_processor.py`)

**Cambios principales:**

#### Método `process_kpi_file()` (Línea 23)
- Agregado parámetro `billing_type: str = "Contable"`

#### Método `_create_billing_table()` (Líneas 227-317)
- Agregado parámetro `billing_type`
- Lógica condicional para distribuir montos:

**Modo Contable (líneas 308-312):**
```python
# Distribuir según eventos de facturación
for _, event in project_data.iterrows():
    month = event['Mes Facturación']
    if month in row:
        row[month] += event['Monto Facturación']
```

**Modo Financiero (líneas 297-306):**
```python
# Todo el monto (100% del Total PO) en el último mes de facturación
project_data_sorted = project_data.sort_values('Probable fecha de facturación')
last_month = project_data_sorted.iloc[-1]['Mes Facturación']

# Asignar 100% del Total PO en el último mes (sin factores de castigo)
if last_month in row:
    row[last_month] = row['Total PO']
```

**Reglas para KPIs (Modo Financiero):**
- Un solo evento al 100% del Total PO
- NO se aplican factores de castigo (son datos reales, no proyecciones)
- Se coloca en el último mes con evento de facturación

---

### 5. LLCKPIProcessor (`src/llc_kpi_processor.py`)

**Cambios principales:**

#### Método `process_llc_file()` (Línea 16)
- Agregado parámetro `billing_type: str = "Contable"`

#### Método `_create_billing_table()` (Líneas 170-256)
- Agregado parámetro `billing_type`
- Lógica similar a KPIProcessor

**Modo Contable (líneas 247-251):**
```python
# Distribuir según fechas de invoice individuales
for _, event in project_data.iterrows():
    month = event['Mes Facturación']
    if month in row:
        row[month] += event['Invoice Amount']
```

**Modo Financiero (líneas 236-245):**
```python
# Todo el monto total en el último mes de facturación
project_data_sorted = project_data.sort_values('Invoice Date')
last_month = project_data_sorted.iloc[-1]['Mes Facturación']

# Asignar el total del proyecto en el último mes
if last_month in row:
    row[last_month] = row['Total PO']  # Total PO = suma de todos los invoices
```

---

### 6. Integración en app.py

**Método `_process_kpis()` (Líneas 313-338)**

```python
# Obtener tipo de facturación desde session state
billing_type = getattr(st.session_state, 'billing_type', 'Contable')

# Procesar archivo SAPI
sapi_results = self.kpi_processor.process_kpi_file(
    st.session_state.uploaded_file_kpis, 
    billing_type=billing_type
)

# Procesar archivo LLC
llc_results = self.llc_kpi_processor.process_llc_file(
    st.session_state.uploaded_file_llc,
    billing_type=billing_type
)
```

---

## Resumen de Reglas por Tipo de Facturación

### Modo CONTABLE (Proceso Actual)

**Forecast (Probabilidad >= 60% y < 60%):**
- Múltiples eventos: INICIO, DR, FAT, SAT
- Distribución según porcentajes configurables
- Factores de castigo aplicados:
  - 60% para probabilidad = 60%
  - 40% para otras probabilidades
- PIA (Paid in Advance) respetado cuando existe

**KPIs PM-008 (SAPI):**
- Múltiples eventos según "Probable fecha de facturación"
- Montos según "% Facturación"
- Sin factores de castigo (son datos reales)

**KPIs LLC (iBtest):**
- Múltiples eventos según "Invoice Date"
- Montos individuales por invoice
- Sin factores de castigo

---

### Modo FINANCIERO (Nuevo)

**Forecast (Probabilidad >= 60% y < 60%):**
- UN SOLO evento al 100% del Amount
- Fecha: Mes del SAT (calculado según BU)
- Factores de castigo aplicados:
  - 60% para probabilidad = 60%
  - 40% para otras probabilidades
- PIA ignorado (todo se factura en SAT)

**KPIs PM-008 (SAPI):**
- UN SOLO evento al 100% del Total PO
- Fecha: Último mes con evento de facturación
- SIN factores de castigo (son datos reales)

**KPIs LLC (iBtest):**
- UN SOLO evento al 100% del Total PO (suma de invoices)
- Fecha: Último mes con invoice
- SIN factores de castigo (son datos reales)

---

## Costo de Venta

### Forecast
El costo de venta se calcula y muestra siguiendo las mismas reglas que el billing:
- **Modo Contable**: Distribuido según eventos
- **Modo Financiero**: Todo en el mes del SAT

### KPIs (SAPI y LLC)
El costo de venta siempre se muestra en el último mes con facturación, independientemente del modo:
- Lógica actual en `app.py` líneas 619-627
- Encuentra el último mes con billing > 0
- Asigna el costo completo a ese mes

**Nota:** En modo Financiero, como todo el billing ya está en el último mes, el costo automáticamente queda en ese mismo mes.

---

## Validación de Integración

Todos los archivos modificados:
1. ✅ `app.py` - Selector y llamadas a procesadores
2. ✅ `src/forecast_calculator.py` - Lógica de forecast
3. ✅ `src/managers/base_forecast_manager.py` - Pase de parámetros
4. ✅ `src/kpi_processor.py` - Procesamiento KPIs SAPI
5. ✅ `src/llc_kpi_processor.py` - Procesamiento KPIs LLC

**Flujo completo:**
```
Usuario selecciona tipo → Se guarda en session_state → 
Procesadores lo leen → Aplican lógica correspondiente → 
Generan tablas con distribución correcta
```

---

## Notas Importantes

1. **Retrocompatibilidad:** Todos los métodos tienen `billing_type="Contable"` como valor por defecto
2. **Session State:** El tipo seleccionado se preserva durante toda la sesión
3. **Reporte Consolidado:** Usa los datos ya procesados, respeta el tipo usado en el procesamiento
4. **Logging:** Todos los procesadores registran el modo utilizado
5. **No afecta pestañas de <60%:** La lógica de filtrado se mantiene igual, solo cambia la distribución de eventos

---

## Pruebas Recomendadas

### Forecast
1. Procesar archivo con modo Contable → Verificar múltiples eventos
2. Cambiar a modo Financiero → Re-procesar → Verificar un solo evento en SAT
3. Verificar que factores de castigo se aplican en ambos modos

### KPIs
1. Procesar KPIs SAPI con modo Contable → Verificar distribución múltiple
2. Cambiar a modo Financiero → Re-procesar → Verificar consolidación en último mes
3. Verificar que NO se aplican factores de castigo

### LLC
1. Procesar KPIs LLC con modo Contable → Verificar invoices individuales
2. Cambiar a modo Financiero → Re-procesar → Verificar consolidación
3. Verificar que Total PO suma todos los invoices

### Costo de Venta
1. Verificar que en ambos modos el costo aparece en el mes correcto
2. Modo Contable: Costo en último mes con billing
3. Modo Financiero: Costo en mes SAT (que es el único mes con billing)

---

## Fecha de Implementación
**26 de Noviembre, 2024**
