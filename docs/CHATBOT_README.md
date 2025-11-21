# 🤖 Asistente de Forecast con IA

## Descripción

El Chatbot Asistente de Forecast es un asistente inteligente potenciado por IA (GPT-4o-mini/GPT-4o de OpenAI) que te permite analizar y consultar tus datos de forecast de manera conversacional.

## 🚀 Características

- **Análisis Conversacional**: Pregunta en lenguaje natural y obtén respuestas precisas
- **Acceso Completo a Datos**: El chatbot tiene acceso a todos tus datos cargados
- **Funciones Especializadas**:
  - Resumen ejecutivo del forecast
  - Análisis mensual detallado
  - Análisis por Business Unit (BU)
  - Top proyectos
  - Distribución por empresa (LLC/SAPI)
  - Análisis de costo de venta y márgenes
  - Búsqueda de proyectos

## 📋 Requisitos

### 1. API Key de OpenAI

Necesitas una API key de OpenAI para usar el chatbot:

1. Ve a [platform.openai.com](https://platform.openai.com)
2. Crea una cuenta o inicia sesión
3. Ve a "API Keys" en tu perfil
4. Crea una nueva API key
5. Copia la key y guárdala de forma segura

### 2. Instalación de Dependencias

El chatbot requiere la librería `openai`:

```bash
pip install -r requirements.txt
```

O específicamente:

```bash
pip install openai>=1.0.0
```

## 🎯 Uso

### Configuración Inicial

1. **Abre la pestaña "🤖 Chatbot"** en la aplicación
2. **Ingresa tu API Key** en el campo de la barra lateral
3. **Selecciona el modelo** (recomendado: gpt-4o-mini por su bajo costo)
4. ¡Listo! Ya puedes comenzar a hacer preguntas

### Modelos Disponibles

- **gpt-4o-mini**: Más rápido y económico (~$0.15 por 1M tokens de entrada)
- **gpt-4o**: Más potente y preciso (~$2.50 por 1M tokens de entrada)
- **gpt-3.5-turbo**: Económico pero menos capaz (~$0.50 por 1M tokens de entrada)

## 💡 Ejemplos de Preguntas

### Análisis General
```
- ¿Cuál es el total del forecast?
- Dame un resumen ejecutivo de los datos
- ¿Cuántos proyectos tenemos?
```

### Análisis por BU
```
- Analiza la BU de FCT
- ¿Cuál es el forecast de ICT?
- Compara las BUs FCT e ICT
```

### Proyectos
```
- Muéstrame los top 10 proyectos
- Busca proyectos de "Microsoft"
- ¿Cuál es el proyecto más grande?
```

### Análisis Temporal
```
- ¿Cuál es el forecast para los próximos 3 meses?
- Muéstrame la distribución mensual
- ¿Qué mes tiene el mayor forecast?
```

### Análisis Financiero
```
- ¿Cómo se distribuye por empresa?
- Analiza el costo de venta
- ¿Cuál es el margen bruto total?
- Compara LLC vs SAPI
```

## 🔒 Seguridad y Privacidad

### API Key
- Tu API key se almacena **solo en la sesión actual** de Streamlit
- **No se guarda permanentemente** en el servidor
- Se transmite de forma segura a OpenAI mediante HTTPS

### Datos del Forecast
- Tus datos se envían a OpenAI **solo para el contexto de la conversación**
- OpenAI **no entrena modelos** con datos enviados vía API (según sus políticas)
- Las conversaciones no se almacenan después de cerrar la sesión

### Recomendaciones
- No compartas tu API key con nadie
- Considera usar límites de gasto en tu cuenta de OpenAI
- Revisa periódicamente el uso en tu dashboard de OpenAI

## 💰 Costos

El chatbot usa la API de OpenAI que tiene costos asociados:

### Estimación de Costos (gpt-4o-mini)
- Conversación típica: $0.001 - $0.01 USD
- 100 preguntas: ~$0.50 - $1.00 USD
- Muy económico para uso regular

### Control de Costos
- Usa gpt-4o-mini para análisis rutinarios
- Usa gpt-4o solo cuando necesites análisis más profundos
- Limpia el historial regularmente para reducir el contexto
- Configura límites de gasto en OpenAI

## 🛠️ Funciones Disponibles

El chatbot puede ejecutar las siguientes funciones automáticamente:

| Función | Descripción |
|---------|-------------|
| `get_forecast_summary` | Resumen ejecutivo con totales y distribuciones |
| `get_monthly_forecast` | Forecast detallado mes a mes |
| `get_bu_analysis` | Análisis por Business Unit |
| `get_top_projects` | Proyectos principales ordenados por monto |
| `get_company_analysis` | Distribución por empresa (LLC/SAPI) |
| `get_cost_of_sale_analysis` | Análisis de costos y márgenes |
| `search_projects` | Búsqueda de proyectos por nombre |

## 🔧 Solución de Problemas

### "El chatbot no está configurado"
- Asegúrate de ingresar tu API key en la barra lateral
- Verifica que la key sea válida
- Intenta refrescar la página

### "Error al procesar tu mensaje"
- Verifica tu conexión a internet
- Revisa que tengas créditos en tu cuenta de OpenAI
- Intenta con un mensaje más simple

### "No hay datos disponibles"
- Asegúrate de haber cargado un archivo Excel primero
- Ve a la pestaña principal y carga tu archivo
- El chatbot solo funciona con datos cargados

## 📚 Recursos Adicionales

- [Documentación de OpenAI](https://platform.openai.com/docs)
- [Precios de OpenAI](https://openai.com/pricing)
- [Políticas de Uso de Datos](https://openai.com/policies/usage-policies)

## 🆘 Soporte

Si tienes problemas:
1. Revisa esta documentación
2. Verifica los logs en la consola
3. Contacta al administrador del sistema

---

**Nota**: El chatbot es una herramienta de análisis asistido. Siempre verifica la información crítica con los datos originales.
