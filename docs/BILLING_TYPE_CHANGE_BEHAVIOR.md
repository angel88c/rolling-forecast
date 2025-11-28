# Comportamiento al Cambiar Tipo de Facturación

## Resumen

Cuando el usuario cambia entre los tipos de facturación **Contable** y **Financiera**, el sistema limpia automáticamente las tablas procesadas y solicita al usuario que vuelva a procesar los archivos.

## Fecha de Implementación
**27 de Noviembre, 2024**

---

## Funcionamiento

### 1. Detección de Cambio con Callback

El sistema usa un **callback** que se ejecuta inmediatamente cuando el usuario cambia el tipo de facturación:

```python
# Inicializar valores en session_state
if 'billing_type' not in st.session_state:
    st.session_state.billing_type = 'Contable'

# Variable de control separada para detectar cambios
if 'billing_type_control' not in st.session_state:
    st.session_state.billing_type_control = st.session_state.billing_type

# Callback que se ejecuta cuando cambia el selectbox
def on_billing_type_change():
    new_value = st.session_state.billing_type_selector
    old_value = st.session_state.billing_type_control
    
    # Solo limpiar si realmente cambió
    if new_value != old_value:
        # Limpiar resultados
        if 'forecast_results' in st.session_state:
            del st.session_state.forecast_results
        if 'kpi_results' in st.session_state:
            del st.session_state.kpi_results
        
        # Actualizar valores
        st.session_state.billing_type_control = new_value
        st.session_state.billing_type = new_value
        st.session_state.billing_type_just_changed = True

# Selectbox con callback
st.sidebar.selectbox(
    "Método de Facturación",
    options=["Contable", "Financiera"],
    index=0 if st.session_state.billing_type == "Contable" else 1,
    key="billing_type_selector",
    on_change=on_billing_type_change
)
```

**Ventajas del Callback:**
- ✅ Se ejecuta **inmediatamente** al cambiar, antes del rerun
- ✅ Evita ciclos de renders
- ✅ Detección precisa con variable de control separada
- ✅ Cambio se aplica al primer intento

**Variables de Estado Utilizadas:**
- `billing_type` - Valor actual del tipo de facturación
- `billing_type_control` - Valor de control para detectar cambios
- `billing_type_selector` - Key del widget selectbox
- `billing_type_just_changed` - Flag temporal para mostrar mensajes

### 2. Limpieza Automática de Tablas

Cuando se detecta un cambio, el sistema:

**✅ ELIMINA (se requiere reprocesar):**
- `forecast_results` - Todos los datos de forecast (≥60% y <60%)
- `kpi_results` - Todos los datos de KPIs (SAPI + LLC)

**✅ MANTIENE (no se borran):**
- `uploaded_file` - Archivo de forecast cargado
- `uploaded_file_kpis` - Archivo de KPIs SAPI cargado
- `uploaded_file_llc` - Archivo de KPIs LLC cargado
- `billing_type` - Nuevo tipo seleccionado
- Todas las configuraciones de reglas de negocio

### Session State Management

**Variables para Control de Tipo de Facturación:**
- `billing_type`: Tipo actual de facturación (el que usa el resto de la app)
- `billing_type_control`: Valor de control para detectar cambios (comparación)
- `billing_type_selector`: Key del widget (valor directo del selectbox)
- `billing_type_just_changed`: Flag temporal para mostrar mensajes una sola vez

**Variables de Archivos Cargados:**
- `uploaded_file`: Archivo de Forecast cargado
- `uploaded_file_kpis`: Archivo KPIs SAPI cargado
- `uploaded_file_llc`: Archivo KPIs LLC cargado

**Variables de Resultados Procesados:**
- `forecast_results`: Resultados de Forecast (con subkeys: `forecast_table`, `forecast_table_low_prob`)
- `kpi_results`: Resultados de KPIs combinados

### Prevención de Loops Infinitos

**Enfoque con Callback:**
1. El callback se ejecuta **una sola vez** cuando cambia el selectbox
2. Actualiza `billing_type_control` al nuevo valor
3. En el rerun, `new_value == old_value`, por lo que el callback no hace nada
4. No hay ciclo infinito porque la comparación usa la variable de control

**Flujo de Estados:**
```
Estado Inicial:
  billing_type = "Contable"
  billing_type_control = "Contable"

Usuario cambia a "Financiera":
  1. Callback detecta: "Financiera" != "Contable" → Limpia tablas
  2. Actualiza: billing_type_control = "Financiera"
  3. Rerun ocurre
  4. Nuevo render: "Financiera" == "Financiera" → No hace nada

Usuario cambia de vuelta a "Contable":
  1. Callback detecta: "Contable" != "Financiera" → Limpia tablas
  2. Actualiza: billing_type_control = "Contable"
  3. Ciclo se repite sin loops
```

### 3. Mensajes al Usuario

**En el sidebar se muestran dos mensajes:**

```
⚠️ Tipo de facturación cambiado a: Financiera

📝 Las tablas se han limpiado. Por favor, vuelve a procesar los archivos.
```

### 4. Título del Modo Activo

En la parte superior de la aplicación aparece un título grande indicando el modo actual:

**Modo Contable:**
```
📊 MODO CONTABLE - Facturación por Eventos
Múltiples eventos de facturación según reglas de negocio (INICIO, DR, FAT, SAT)
```

**Modo Financiero:**
```
📊 MODO FINANCIERO - Facturación Consolidada en SAT
Un solo evento de facturación al 100% en el mes del SAT para todos los proyectos
```

---

## Flujo Completo

```
1. Usuario carga archivos (Forecast, KPIs)
   ↓
2. Usuario procesa archivos en modo "Contable"
   ↓
3. Se generan tablas con múltiples eventos
   ↓
4. Usuario cambia a modo "Financiera"
   ↓
5. Sistema detecta el cambio
   ├─ Elimina forecast_results
   ├─ Elimina kpi_results
   ├─ Mantiene archivos cargados
   └─ Muestra mensajes de advertencia
   ↓
6. Usuario ve pestañas vacías con mensaje de estado vacío
   ↓
7. Usuario hace click en "🔄 Procesar" en cada pestaña
   ↓
8. Se generan nuevas tablas con el nuevo tipo de facturación
   ├─ Forecast: Evento único al 100% en SAT
   └─ KPIs: Consolidación en último mes
```

---

## Ventajas de este Enfoque

### ✅ Simplicidad
- Comportamiento claro y predecible
- El usuario tiene control total del reprocesamiento
- No hay automatismos que puedan confundir

### ✅ Claridad
- Mensajes explícitos sobre qué pasó
- El usuario sabe exactamente qué hacer
- Título grande siempre visible con el modo activo

### ✅ Seguridad
- Los archivos no se pierden
- El usuario decide cuándo reprocesar
- No hay riesgo de procesar con configuraciones incorrectas

### ✅ Eficiencia
- No reprocesa automáticamente todo
- El usuario solo reprocesa lo que necesita
- No hay procesamiento innecesario en segundo plano

---

## Implementación Técnica

### Ubicación del Código

**Archivo:** `app.py`

**Método:** `_render_sidebar()` (Líneas 105-159)

**Enfoque con Callback:**
```python
# Callback que se ejecuta ANTES del rerun
def on_billing_type_change():
    new_value = st.session_state.billing_type_selector
    old_value = st.session_state.billing_type_control
    
    if new_value != old_value:
        # Limpiar tablas
        if 'forecast_results' in st.session_state:
            del st.session_state.forecast_results
        if 'kpi_results' in st.session_state:
            del st.session_state.kpi_results
        
        # Actualizar estado
        st.session_state.billing_type_control = new_value
        st.session_state.billing_type = new_value
        st.session_state.billing_type_just_changed = True

# Selectbox con callback
st.sidebar.selectbox(
    "Método de Facturación",
    options=["Contable", "Financiera"],
    index=0 if st.session_state.billing_type == "Contable" else 1,
    key="billing_type_selector",
    on_change=on_billing_type_change  # ← Ejecuta ANTES del rerun
)
```

**Orden de Ejecución:**
1. Usuario cambia selectbox
2. **Callback se ejecuta primero** (limpia tablas, actualiza estado)
3. Streamlit hace rerun
4. En el rerun, el nuevo valor ya está guardado y las tablas ya están limpias

**Método:** `_render_main_content()` (Líneas 222-233)

```python
# Mostrar título grande con el tipo de facturación actual
billing_type = st.session_state.get('billing_type', 'Contable')
if billing_type == "Financiera":
    st.title("📊 MODO FINANCIERO - Facturación Consolidada en SAT")
    st.caption("Un solo evento de facturación al 100% en el mes del SAT para todos los proyectos")
else:
    st.title("📊 MODO CONTABLE - Facturación por Eventos")
    st.caption("Múltiples eventos de facturación según reglas de negocio (INICIO, DR, FAT, SAT)")

st.markdown("---")
```

---

## Estados de la Aplicación

### Estado 1: Sin datos procesados
```
[Selector: Contable]  →  Sin cambios detectados
- Tablas vacías con mensaje de estado vacío
- Archivos pueden estar cargados o no
```

### Estado 2: Datos procesados en modo actual
```
[Selector: Contable]  →  Sin cambios
- Tablas visibles con datos
- Archivos cargados
- Todo funcionando normal
```

### Estado 3: Cambio detectado
```
[Selector: Contable → Financiera]  →  Cambio detectado
- Mensaje: "⚠️ Tipo de facturación cambiado a: Financiera"
- Mensaje: "📝 Las tablas se han limpiado..."
- Tablas vacías
- Archivos TODAVÍA cargados (no se borran)
```

### Estado 4: Después de reprocesar
```
[Selector: Financiera]  →  Sin cambios (ya procesado en nuevo modo)
- Tablas visibles con nuevos datos
- Eventos consolidados en SAT
- Archivos cargados
```

---

## Testing Manual

### Test 1: Cambio básico
1. Cargar archivo de Forecast
2. Procesar en modo Contable
3. Verificar múltiples eventos en tabla
4. Cambiar a Financiera
5. ✅ Verificar que tabla se limpia y aparecen mensajes
6. Click en "Procesar"
7. ✅ Verificar evento único en SAT

### Test 2: Con KPIs
1. Cargar KPIs SAPI + LLC
2. Procesar en modo Contable
3. Verificar múltiples distribuciones
4. Cambiar a Financiera
5. ✅ Verificar limpieza de tablas KPIs
6. Reprocesar
7. ✅ Verificar consolidación en último mes

### Test 3: Archivos se mantienen
1. Cargar archivos
2. Procesar
3. Cambiar tipo
4. ✅ Verificar que archivos siguen mostrando "✅ Archivo cargado"
5. Click en Procesar (debe funcionar sin volver a subir)

### Test 4: Cambio sin procesar
1. Cargar archivos pero NO procesar
2. Cambiar tipo de facturación
3. ✅ No debe mostrar mensajes de limpieza (no hay nada que limpiar)
4. Procesar con el nuevo tipo
5. ✅ Debe generar datos con el tipo seleccionado

---

## Diferencias con el Enfoque Anterior

| Aspecto | Auto-Reprocesar (❌) | Limpiar Tablas (✅) |
|---------|---------------------|-------------------|
| Complejidad | Alta - múltiples spinners | Baja - solo detección |
| Control usuario | Bajo - automático | Alto - manual |
| Feedback | Múltiples mensajes | 2 mensajes claros |
| Riesgo bugs | Alto - procesos concurrentes | Bajo - solo limpieza |
| Performance | Procesa todo siempre | Solo cuando usuario quiere |
| Claridad | Puede confundir | Muy claro |

---

## Casos Edge Cubiertos

### ✅ Usuario cambia varias veces seguidas
- Solo se limpian tablas una vez al detectar el cambio
- No hay mensajes duplicados
- Comportamiento consistente

### ✅ Usuario cambia sin tener datos
- No muestra mensajes de limpieza (no hay nada que limpiar)
- No causa errores
- Comportamiento silencioso

### ✅ Usuario cierra y reabre navegador
- Se mantiene el último tipo seleccionado (session_state)
- Archivos se pierden (comportamiento normal de Streamlit)
- No hay inconsistencias

### ✅ Usuario cambia de vuelta al modo original
- Limpia tablas igual que cambio inicial
- Puede reprocesar con modo original
- Sin efectos secundarios

---

## Conclusión

Esta implementación proporciona una experiencia de usuario simple y predecible:
1. **Cambias el tipo** → Se limpian las tablas
2. **Mensajes claros** → Sabes qué pasó y qué hacer
3. **Título grande** → Siempre sabes en qué modo estás
4. **Archivos preservados** → No necesitas volver a subirlos
5. **Control total** → Tú decides cuándo reprocesar

Es una solución robusta que evita automatismos complejos y da al usuario el control completo del flujo de trabajo.
