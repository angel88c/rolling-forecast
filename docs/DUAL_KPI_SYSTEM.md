# Sistema Dual de KPIs: SAPI + LLC

## 📋 Resumen

Se implementó un sistema dual para procesar KPIs de dos fuentes diferentes:
1. **SAPI**: Archivo PM-008 (registros con Location != LLC)
2. **LLC**: Archivo iBtest LLC-Overall Results (registros con Status f/Invoice = Pending)

## 🏗️ Arquitectura

### Archivos Creados

**1. `src/llc_kpi_processor.py`**
- Nuevo procesador especializado para archivos LLC
- Clase: `LLCKPIProcessor`
- Procesa archivo "iBtest LLC-Overall Results.xlsx"

### Archivos Modificados

**1. `src/kpi_processor.py`**
- Líneas 68-74: Filtrado de registros LLC
- Excluye automáticamente registros con `Location = LLC`
- Logging detallado de exclusiones

**2. `app.py`**
- Línea 29: Importación de `LLCKPIProcessor`
- Línea 72: Inicialización de `self.llc_kpi_processor`
- Líneas 235-275: Nuevo UI con dos file uploaders
- Líneas 284-318: Procesamiento dual de archivos
- Líneas 320-392: Método de combinación de resultados

## 📊 Flujo de Procesamiento

```
┌─────────────────────────────────────────────────────┐
│                  Usuario carga archivos              │
└─────────────────────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
         ▼                               ▼
┌─────────────────┐            ┌─────────────────┐
│ Archivo PM-008  │            │ Archivo iBtest  │
│    (SAPI)       │            │     (LLC)       │
└─────────────────┘            └─────────────────┘
         │                               │
         ▼                               ▼
┌─────────────────┐            ┌─────────────────┐
│ KPIProcessor    │            │LLCKPIProcessor  │
│                 │            │                 │
│ Filtros:        │            │ Filtros:        │
│ • Status:       │            │ • Status:       │
│   Abierto/      │            │   Pending       │
│   On Hold       │            │ • Fecha válida  │
│ • Location      │            │                 │
│   != LLC        │            │                 │
└─────────────────┘            └─────────────────┘
         │                               │
         │      ┌─────────────────┐      │
         └─────>│  Combinador     │<─────┘
                │  (_combine_kpi_ │
                │   results)      │
                └─────────────────┘
                         │
                         ▼
                ┌─────────────────┐
                │ Tabla Unificada │
                │  SAPI + LLC     │
                └─────────────────┘
```

## 🔍 Detalles de Implementación

### KPIProcessor (SAPI)

**Filtros aplicados:**
```python
# 1. Status: Abierto o On Hold
valid_status = ['abierto', 'on hold']

# 2. Location != LLC (nuevo)
df = df[df['Location'].str.upper().strip() != 'LLC']
```

**Columnas procesadas:**
- `Project Name`: Nombre del proyecto
- `Status`: Estado (Abierto/On Hold)
- `Total de PO`: Monto total de la orden
- `% Facturación`: Porcentaje de facturación
- `Probable fecha de facturación`: Fecha de facturación
- `Main BU`: Business Unit
- `Customer`: Cliente
- `Location`: Ubicación (SAPI)
- `Costo de Venta`: Costo de venta

**Eventos de facturación:**
- Múltiples eventos por proyecto según `% Facturación`
- Fecha: `Probable fecha de facturación`
- Monto: `Total de PO * % Facturación`

### LLCKPIProcessor (LLC)

**Filtros aplicados:**
```python
# 1. Status f/Invoice = Pending (excluir Invoiced)
df = df[df['Status f/Invoice'].str.lower() == 'pending']

# 2. Fecha válida
df = df[df['Invoice Date'].notna()]
```

**Columnas procesadas:**
- `Project`: Nombre del proyecto
- `Status f/Invoice`: Estado del invoice (solo Pending)
- `Invoice Amount`: Monto del invoice
- `Invoice Date`: Fecha del invoice
- `Main BU`: Business Unit
- `Customer`: Cliente
- `Location`: Siempre "LLC"

**Eventos de facturación:**
- Un evento por invoice (ordenado por `Invoice Date`)
- Fecha: `Invoice Date`
- Monto: `Invoice Amount`
- % Facturación: Siempre 100% (cada invoice es completo)

## 🎨 Interfaz de Usuario

### File Uploaders

```
┌────────────────────────────────────────────────────┐
│         📋 KPIs PM-008                             │
│    Billing de proyectos SAPI + LLC                │
└────────────────────────────────────────────────────┘

┌──────────────────────┬──────────────────────────┐
│ 📄 KPIs SAPI         │ 📄 KPIs LLC             │
│ (PM-008)             │ (iBtest)                │
├──────────────────────┼──────────────────────────┤
│                      │                          │
│ [Subir archivo SAPI] │ [Subir archivo LLC]     │
│                      │                          │
│ ✅ Archivo cargado   │ ✅ Archivo cargado      │
│                      │                          │
└──────────────────────┴──────────────────────────┘

            [🔄 Procesar KPIs]
```

### Mensajes de Feedback

```
✅ SAPI: 45 proyectos procesados
✅ LLC: 23 proyectos procesados
✅ Total: 68 proyectos (SAPI: 45, LLC: 23)
```

## 📦 Estructura de Datos Combinada

```python
combined_results = {
    'data': [
        # Proyectos SAPI
        {
            'Proyecto': 'Proyecto A',
            'BU': 'FCT',
            'Location': 'SAPI',
            'Status': 'Abierto',
            'Customer': 'Cliente A',
            'Total PO': 100000,
            '% Facturación': '50%',
            'Costo de Venta': 30000,
            'January 2025': 50000,
            'February 2025': 0,
            ...
        },
        # Proyectos LLC
        {
            'Proyecto': 'Proyecto B',
            'BU': 'ICT',
            'Location': 'LLC',
            'Status': 'Pending',
            'Customer': 'Cliente B',
            'Total PO': 80000,
            '% Facturación': '100%',
            'Costo de Venta': 0,
            'January 2025': 40000,
            'February 2025': 40000,
            ...
        }
    ],
    'summary': {
        'total_projects': 68,
        'total_billing': 5000000,
        'total_po': 5000000,
        'bu_distribution': {
            'FCT': 2000000,
            'ICT': 1500000,
            'IAT': 1000000,
            ...
        },
        'monthly_distribution': {
            'January 2025': 500000,
            'February 2025': 600000,
            ...
        },
        'status_distribution': {
            'Abierto': 30,
            'On Hold': 15,
            'Pending': 23
        },
        'tbd_projects': ['Proyecto X', 'Proyecto Y']
    }
}
```

## 🎯 Ventajas del Sistema Dual

### 1. **Separación Clara de Responsabilidades**
- Cada procesador maneja su propio formato de archivo
- Lógica de negocio específica para cada fuente
- Fácil mantenimiento y debugging

### 2. **Flexibilidad**
- Se puede cargar solo SAPI, solo LLC, o ambos
- Los resultados se combinan automáticamente
- No hay dependencias entre archivos

### 3. **Trazabilidad**
- Cada registro mantiene su origen (Location)
- Logging detallado por cada procesador
- Métricas separadas por fuente

### 4. **Escalabilidad**
- Fácil agregar nuevas fuentes de datos
- Patrón replicable para otros tipos de KPIs
- Combinar datos de múltiples fuentes

## 🔧 Diferencias Clave SAPI vs LLC

| Característica | SAPI (PM-008) | LLC (iBtest) |
|----------------|---------------|--------------|
| **Archivo** | KPIs PM-008.xlsx | iBtest LLC-Overall Results.xlsx |
| **Hoja** | Billing | (default) |
| **Filtro Status** | Abierto, On Hold | Pending |
| **Fecha** | Probable fecha de facturación | Invoice Date |
| **Monto** | Total de PO * % Facturación | Invoice Amount |
| **Eventos** | Múltiples (según %) | Uno por invoice |
| **Location** | SAPI, otras | Siempre LLC |
| **Costo de Venta** | Disponible | No disponible (0) |
| **% Facturación** | Variable (ej: 30%, 70%) | Siempre 100% |

## 📝 Logging

### SAPI
```
INFO: Proyectos filtrados (Abierto/On Hold): 50
INFO: Registros LLC excluidos: 5 (se procesarán con archivo LLC separado)
INFO: Proyectos SAPI después de filtrar LLC: 45
INFO: Datos limpios: 45 registros válidos con monto total de $2,500,000.00
```

### LLC
```
INFO: Archivo LLC leído: 100 registros
INFO: Status f/Invoice únicos encontrados: ['Pending', nan]
INFO: Registros con Status f/Invoice = Pending: 23
INFO: Datos limpios: 23 registros válidos con monto total de $1,800,000.00
```

### Combinación
```
INFO: Resultados combinados: 68 proyectos totales
```

## ✅ Testing

### Casos de Prueba

1. **Solo SAPI**
   - Cargar solo archivo PM-008
   - Verificar que se excluyen registros LLC
   - Confirmar conteo correcto

2. **Solo LLC**
   - Cargar solo archivo iBtest
   - Verificar filtrado por Status = Pending
   - Confirmar Location = LLC

3. **SAPI + LLC**
   - Cargar ambos archivos
   - Verificar combinación correcta
   - Confirmar totales sumados

4. **Sin archivos**
   - No cargar archivos
   - Verificar UI de estado vacío
   - Confirmar botón deshabilitado

## 🚀 Próximos Pasos

1. ✅ Crear LLCKPIProcessor
2. ✅ Modificar KPIProcessor para filtrar LLC
3. ✅ Agregar UI dual en app.py
4. ✅ Implementar combinación de resultados
5. 🔄 Probar con archivos reales
6. 📝 Actualizar documentación de usuario
7. 🎨 Ajustar visualizaciones según feedback

## 📚 Archivos Relacionados

- `src/kpi_processor.py`: Procesador SAPI
- `src/llc_kpi_processor.py`: Procesador LLC (NUEVO)
- `app.py`: Interfaz y orquestación
- `docs/DUAL_KPI_SYSTEM.md`: Esta documentación
