# 📊 Forecast Financiero - Aplicación Streamlit

Aplicación web para generar proyecciones de ingresos por facturación basadas en el pipeline de oportunidades (C&N Funnel Report).

## 🚀 Características Principales

- **Interfaz intuitiva**: Upload de archivos Excel con drag & drop
- **Validación automática**: Verificación de datos de entrada con reportes detallados
- **Cálculo automatizado**: Aplicación de reglas de negocio específicas por BU
- **Visualizaciones interactivas**: Gráficos y dashboards con Plotly
- **Exportación múltiple**: Excel y CSV con múltiples hojas de análisis
- **Análisis de riesgo**: Evaluación automática de concentración y probabilidades

## 🏗️ Arquitectura del Proyecto

```
forecast_app/
├── app.py                 # Aplicación principal Streamlit
├── requirements.txt       # Dependencias Python
├── README.md             # Documentación
├── config/
│   └── settings.py       # Configuraciones globales
├── src/
│   ├── models.py         # Modelos de datos y estructuras
│   ├── validators.py     # Validación de datos de entrada
│   ├── data_processor.py # Procesamiento y limpieza de datos
│   ├── forecast_calculator.py # Lógica de cálculo del forecast
│   └── exporter.py       # Exportación a diferentes formatos
├── tests/                # Tests unitarios (futuro)
├── data/                 # Datos de ejemplo (futuro)
└── docs/                 # Documentación adicional (futuro)
```

## 📋 Reglas de Negocio Implementadas

### Reglas Generales
- **Lead Time mínimo**: 4 semanas (ajuste automático)
- **Factor de castigo financiero**: 40% del monto ajustado por probabilidad
- **Probabilidades**: Lógica de agrupador (forward fill)

### Reglas por Unidad de Negocio

#### ICT
- **Sin PIA**: 1 cobro del 100% después del Lead Time
- **Con PIA**: 2 cobros (PIA al inicio + resto después del Lead Time)

#### FCT, IAT, REP, SWD
- **4 etapas**: INICIO, DR (+30 días), FAT (DR + Lead Time), SAT (FAT + 30 días)
- **Sin PIA**: 30%, 30%, 30%, 10%
- **Con PIA**: PIA reemplaza INICIO, SAT mantiene 10%, resto se divide 50/50 entre DR y FAT

## 🔧 Instalación y Configuración

### Requisitos del Sistema
- Python 3.8 o superior
- 4GB RAM mínimo
- Navegador web moderno

### Instalación

1. **Clonar o descargar el proyecto**
```bash
cd forecast_app
```

2. **Crear entorno virtual (recomendado)**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate     # Windows
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Ejecutar la aplicación**
```bash
streamlit run app.py
```

5. **Abrir en navegador**
La aplicación se abrirá automáticamente en `http://localhost:8501`

## 📊 Uso de la Aplicación

### 1. Preparar Archivo de Entrada
- **Formato**: Excel (.xlsx)
- **Estructura**: Headers en fila 12, datos desde fila 13
- **Columnas requeridas**:
  - Opportunity Name
  - BU (ICT, FCT, IAT, REP, SWD)
  - Amount
  - Close Date (DD/MM/YYYY)
  - Lead Time (semanas)
  - Payment Terms
  - Probability (%) ↑
  - Paid in Advance (opcional)

### 2. Subir y Procesar
1. Usar el botón "Subir archivo C&N Funnel" en la barra lateral
2. Hacer clic en "🚀 Procesar Forecast"
3. Revisar validaciones y advertencias

### 3. Analizar Resultados
- **Forecast**: Tabla principal con proyectos y meses
- **Gráficos**: Visualizaciones interactivas
- **Detalles**: Eventos de facturación individuales
- **Análisis**: Evaluación de riesgo y concentración
- **Procesamiento**: Información técnica del proceso

### 4. Exportar Resultados
- **Excel**: Múltiples hojas con análisis completo
- **CSV**: Tabla de forecast para análisis externo

## 🧪 Validaciones Implementadas

### Validación de Archivo
- ✅ Formato Excel válido
- ✅ Tamaño de archivo (máx. 50MB)
- ✅ Columnas requeridas presentes

### Validación de Datos
- ✅ Campos obligatorios completos
- ✅ BU válidas
- ✅ Montos positivos
- ✅ Fechas en formato correcto
- ✅ Lead Times válidos
- ✅ PIA no negativo

### Reportes de Calidad
- 📊 Tasa de éxito de validación
- ⚠️ Advertencias por fila
- 📈 Estadísticas de procesamiento

## 🔍 Análisis Avanzados

### Análisis de Riesgo
- **Por Probabilidad**: Clasificación en bajo, medio y alto riesgo
- **Por Concentración**: Detección de dependencia excesiva en una BU
- **Visualizaciones**: Gráficos de distribución de riesgo

### Métricas Clave
- 💰 Total del forecast
- 🎯 Número de oportunidades
- 📅 Eventos de facturación
- ⏱️ Duración en meses

## 🛠️ Desarrollo y Mantenimiento

### Estructura Modular
- **Separación de responsabilidades**: Cada módulo tiene una función específica
- **Configuración centralizada**: Todas las reglas en `config/settings.py`
- **Logging integrado**: Trazabilidad completa de operaciones
- **Manejo de errores**: Validaciones y mensajes de error consistentes

### Extensibilidad
- **Nuevas BU**: Agregar en `APP_CONFIG.VALID_BUS`
- **Nuevas reglas**: Modificar `BUSINESS_RULES`
- **Nuevos formatos**: Extender `ForecastExporter`
- **Nuevas validaciones**: Agregar en `DataValidator`

### Mejores Prácticas Implementadas
- ✅ **Type hints**: Documentación de tipos en todo el código
- ✅ **Docstrings**: Documentación completa de funciones y clases
- ✅ **Error handling**: Manejo robusto de excepciones
- ✅ **Logging**: Trazabilidad de operaciones
- ✅ **Configuración**: Parámetros centralizados y modificables
- ✅ **Modularidad**: Código organizado y reutilizable

## 📝 Notas Técnicas

### Performance
- **Procesamiento en memoria**: Manejo eficiente de archivos grandes
- **Caching de Streamlit**: Optimización de recálculos
- **Validación progresiva**: Detección temprana de errores

### Seguridad
- **Validación de entrada**: Verificación exhaustiva de datos
- **Límites de archivo**: Prevención de uploads excesivos
- **Manejo de errores**: No exposición de información sensible

### Compatibilidad
- **Python**: 3.8+
- **Navegadores**: Chrome, Firefox, Safari, Edge
- **Excel**: Todas las versiones modernas (.xlsx)

## 🐛 Solución de Problemas

### Errores Comunes

1. **"Columnas requeridas faltantes"**
   - Verificar que el archivo tenga todas las columnas necesarias
   - Revisar que los headers estén en la fila 12

2. **"Error al procesar fechas"**
   - Asegurar formato DD/MM/YYYY en Close Date
   - Verificar que no haya celdas vacías en fechas

3. **"No se encontraron datos válidos"**
   - Revisar que haya datos después de la fila 12
   - Verificar que Lead Time y Payment Terms no estén vacíos

### Logs y Debugging
- Los logs se muestran en la consola donde se ejecuta Streamlit
- Usar el tab "Procesamiento" para ver detalles técnicos
- Revisar advertencias de validación para identificar problemas

## 📞 Soporte

Para soporte técnico o preguntas sobre la aplicación:
1. Revisar esta documentación
2. Verificar logs de error
3. Contactar al equipo de desarrollo con detalles específicos

---

**Versión**: 1.0.0  
**Última actualización**: Septiembre 2025  
**Desarrollado con**: Python, Streamlit, Pandas, Plotly
