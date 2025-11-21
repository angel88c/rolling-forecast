"""
Módulo de Chatbot Asistente de Forecast.

Este módulo implementa un chatbot con capacidades de análisis de datos
que puede responder preguntas sobre el forecast y realizar análisis.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)


class ForecastChatbot:
    """
    Chatbot asistente para análisis de forecast.
    Utiliza LLM con acceso a funciones de análisis de datos.
    """
    
    def __init__(self):
        """Inicializa el chatbot."""
        self.api_key = None
        self.model = "gpt-4o-mini"  # Modelo más económico
        self.conversation_history = []
        
    def set_api_key(self, api_key: str):
        """
        Configura la API key de OpenAI.
        
        Args:
            api_key: API key de OpenAI
        """
        self.api_key = api_key
        
    def is_configured(self) -> bool:
        """
        Verifica si el chatbot está configurado.
        
        Returns:
            bool: True si está configurado
        """
        return self.api_key is not None and len(self.api_key) > 0
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """
        Define las herramientas/funciones disponibles para el chatbot.
        
        Returns:
            List[Dict]: Lista de definiciones de herramientas
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_forecast_summary",
                    "description": "Obtiene el resumen ejecutivo del forecast actual con totales, proyectos, eventos y distribución por BU",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_monthly_forecast",
                    "description": "Obtiene el forecast detallado mes a mes con los montos proyectados",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "num_months": {
                                "type": "integer",
                                "description": "Número de meses a mostrar (por defecto todos)"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_bu_analysis",
                    "description": "Analiza la distribución y proyección por Business Unit (BU)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "bu": {
                                "type": "string",
                                "description": "Business Unit específica (FCT, ICT, IAT, REP, SWD) o 'todas'"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_top_projects",
                    "description": "Obtiene los proyectos principales ordenados por monto",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "limit": {
                                "type": "integer",
                                "description": "Número de proyectos a retornar (por defecto 10)"
                            },
                            "bu": {
                                "type": "string",
                                "description": "Filtrar por BU específica (opcional)"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_company_analysis",
                    "description": "Analiza la distribución por empresa (LLC vs SAPI)",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_cost_of_sale_analysis",
                    "description": "Analiza el costo de venta y márgenes brutos",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_projects",
                    "description": "Busca proyectos por nombre o características",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Término de búsqueda en el nombre del proyecto"
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ]
    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any], 
                    forecast_data: Dict[str, Any]) -> str:
        """
        Ejecuta una herramienta/función específica.
        
        Args:
            tool_name: Nombre de la herramienta
            arguments: Argumentos de la herramienta
            forecast_data: Datos del forecast
            
        Returns:
            str: Resultado de la ejecución
        """
        try:
            if tool_name == "get_forecast_summary":
                return self._get_forecast_summary(forecast_data)
            elif tool_name == "get_monthly_forecast":
                num_months = arguments.get("num_months")
                return self._get_monthly_forecast(forecast_data, num_months)
            elif tool_name == "get_bu_analysis":
                bu = arguments.get("bu", "todas")
                return self._get_bu_analysis(forecast_data, bu)
            elif tool_name == "get_top_projects":
                limit = arguments.get("limit", 10)
                bu = arguments.get("bu")
                return self._get_top_projects(forecast_data, limit, bu)
            elif tool_name == "get_company_analysis":
                return self._get_company_analysis(forecast_data)
            elif tool_name == "get_cost_of_sale_analysis":
                return self._get_cost_of_sale_analysis(forecast_data)
            elif tool_name == "search_projects":
                query = arguments.get("query", "")
                return self._search_projects(forecast_data, query)
            else:
                return f"Herramienta no reconocida: {tool_name}"
        except Exception as e:
            logger.error(f"Error ejecutando herramienta {tool_name}: {str(e)}")
            return f"Error al ejecutar {tool_name}: {str(e)}"
    
    def _get_forecast_summary(self, forecast_data: Dict[str, Any]) -> str:
        """Obtiene resumen ejecutivo del forecast."""
        summary = forecast_data.get('summary')
        if not summary:
            return "No hay datos de resumen disponibles."
        
        result = f"""
📊 RESUMEN EJECUTIVO DEL FORECAST

💰 Total Forecast: ${summary.total_amount:,.2f}
🎯 Oportunidades: {summary.total_opportunities}
📅 Eventos de Facturación: {summary.total_events}

📈 Distribución por BU:
"""
        for bu, amount in sorted(summary.bu_distribution.items(), key=lambda x: x[1], reverse=True):
            percentage = (amount / summary.total_amount * 100) if summary.total_amount > 0 else 0
            result += f"  • {bu}: ${amount:,.2f} ({percentage:.1f}%)\n"
        
        result += f"\n📅 Distribución Mensual (Top 5):\n"
        sorted_months = sorted(summary.monthly_distribution.items(), key=lambda x: x[1], reverse=True)[:5]
        for month, amount in sorted_months:
            result += f"  • {month}: ${amount:,.2f}\n"
        
        return result
    
    def _get_monthly_forecast(self, forecast_data: Dict[str, Any], num_months: Optional[int] = None) -> str:
        """Obtiene forecast mensual."""
        summary = forecast_data.get('summary')
        if not summary or not summary.monthly_distribution:
            return "No hay datos mensuales disponibles."
        
        sorted_months = sorted(summary.monthly_distribution.items(), 
                             key=lambda x: datetime.strptime(x[0], '%B %Y'))
        
        if num_months:
            sorted_months = sorted_months[:num_months]
        
        result = "📅 FORECAST MENSUAL:\n\n"
        total = 0
        for month, amount in sorted_months:
            result += f"{month}: ${amount:,.2f}\n"
            total += amount
        
        result += f"\n💰 Total: ${total:,.2f}"
        return result
    
    def _get_bu_analysis(self, forecast_data: Dict[str, Any], bu: str) -> str:
        """Analiza una BU específica o todas."""
        summary = forecast_data.get('summary')
        billing_events = forecast_data.get('billing_events', [])
        
        if not summary:
            return "No hay datos disponibles."
        
        if bu.lower() == "todas":
            result = "📊 ANÁLISIS POR BUSINESS UNIT:\n\n"
            for bu_name, amount in sorted(summary.bu_distribution.items(), key=lambda x: x[1], reverse=True):
                percentage = (amount / summary.total_amount * 100) if summary.total_amount > 0 else 0
                
                # Contar proyectos y eventos de esta BU
                bu_events = [e for e in billing_events if e.bu.value == bu_name]
                projects = len(set(e.opportunity_name for e in bu_events))
                
                result += f"🏢 {bu_name}:\n"
                result += f"  • Monto: ${amount:,.2f} ({percentage:.1f}%)\n"
                result += f"  • Proyectos: {projects}\n"
                result += f"  • Eventos: {len(bu_events)}\n\n"
        else:
            bu_upper = bu.upper()
            amount = summary.bu_distribution.get(bu_upper, 0)
            percentage = (amount / summary.total_amount * 100) if summary.total_amount > 0 else 0
            
            bu_events = [e for e in billing_events if e.bu.value == bu_upper]
            projects = len(set(e.opportunity_name for e in bu_events))
            
            result = f"🏢 ANÁLISIS DE {bu_upper}:\n\n"
            result += f"💰 Monto Total: ${amount:,.2f} ({percentage:.1f}% del total)\n"
            result += f"🎯 Proyectos: {projects}\n"
            result += f"📅 Eventos: {len(bu_events)}\n"
        
        return result
    
    def _get_top_projects(self, forecast_data: Dict[str, Any], limit: int = 10, bu: Optional[str] = None) -> str:
        """Obtiene los proyectos principales."""
        forecast_table = forecast_data.get('forecast_table', {})
        df = pd.DataFrame(forecast_table.get('data', []))
        
        if df.empty:
            return "No hay datos de proyectos disponibles."
        
        # Filtrar por BU si se especifica
        if bu:
            df = df[df['BU'] == bu.upper()]
        
        # Calcular total por proyecto
        numeric_cols = [col for col in df.columns if col not in ['Proyecto', 'BU', 'Empresa']]
        df['Total'] = df[numeric_cols].sum(axis=1)
        
        # Ordenar y limitar
        top_projects = df.nlargest(limit, 'Total')
        
        result = f"🏆 TOP {limit} PROYECTOS"
        if bu:
            result += f" (BU: {bu.upper()})"
        result += ":\n\n"
        
        for idx, row in top_projects.iterrows():
            result += f"{idx + 1}. {row['Proyecto']}\n"
            result += f"   BU: {row['BU']} | Empresa: {row.get('Empresa', 'N/A')}\n"
            result += f"   Monto: ${row['Total']:,.2f}\n\n"
        
        return result
    
    def _get_company_analysis(self, forecast_data: Dict[str, Any]) -> str:
        """Analiza distribución por empresa."""
        forecast_table = forecast_data.get('forecast_table', {})
        df = pd.DataFrame(forecast_table.get('data', []))
        
        if df.empty or 'Empresa' not in df.columns:
            return "No hay datos de empresa disponibles."
        
        numeric_cols = [col for col in df.columns if col not in ['Proyecto', 'BU', 'Empresa']]
        df['Total'] = df[numeric_cols].sum(axis=1)
        
        company_totals = df.groupby('Empresa')['Total'].sum().sort_values(ascending=False)
        total = company_totals.sum()
        
        result = "🏢 ANÁLISIS POR EMPRESA:\n\n"
        for company, amount in company_totals.items():
            percentage = (amount / total * 100) if total > 0 else 0
            projects = len(df[df['Empresa'] == company])
            result += f"📊 {company}:\n"
            result += f"  • Monto: ${amount:,.2f} ({percentage:.1f}%)\n"
            result += f"  • Proyectos: {projects}\n\n"
        
        return result
    
    def _get_cost_of_sale_analysis(self, forecast_data: Dict[str, Any]) -> str:
        """Analiza costo de venta y márgenes."""
        cost_table = forecast_data.get('cost_of_sale_table', {})
        df = pd.DataFrame(cost_table.get('data', []))
        
        if df.empty:
            return "No hay datos de costo de venta disponibles."
        
        # Calcular totales
        total_amount = df['Amount Total'].sum() if 'Amount Total' in df.columns else 0
        total_margin = df['Gross Margin'].sum() if 'Gross Margin' in df.columns else 0
        total_cost = df['Costo de Venta'].sum() if 'Costo de Venta' in df.columns else 0
        
        margin_percentage = (total_margin / total_amount * 100) if total_amount > 0 else 0
        
        result = "💰 ANÁLISIS DE COSTO DE VENTA:\n\n"
        result += f"📊 Amount Total: ${total_amount:,.2f}\n"
        result += f"📈 Gross Margin: ${total_margin:,.2f} ({margin_percentage:.1f}%)\n"
        result += f"💵 Costo de Venta: ${total_cost:,.2f}\n\n"
        
        # Análisis por BU
        if 'BU' in df.columns:
            result += "📊 Por Business Unit:\n"
            bu_analysis = df.groupby('BU').agg({
                'Amount Total': 'sum',
                'Gross Margin': 'sum',
                'Costo de Venta': 'sum'
            })
            
            for bu, row in bu_analysis.iterrows():
                margin_pct = (row['Gross Margin'] / row['Amount Total'] * 100) if row['Amount Total'] > 0 else 0
                result += f"\n🏢 {bu}:\n"
                result += f"  • Amount: ${row['Amount Total']:,.2f}\n"
                result += f"  • Margin: ${row['Gross Margin']:,.2f} ({margin_pct:.1f}%)\n"
                result += f"  • Costo: ${row['Costo de Venta']:,.2f}\n"
        
        return result
    
    def _search_projects(self, forecast_data: Dict[str, Any], query: str) -> str:
        """Busca proyectos por nombre."""
        forecast_table = forecast_data.get('forecast_table', {})
        df = pd.DataFrame(forecast_table.get('data', []))
        
        if df.empty:
            return "No hay datos de proyectos disponibles."
        
        # Buscar (case insensitive)
        mask = df['Proyecto'].str.contains(query, case=False, na=False)
        results = df[mask]
        
        if results.empty:
            return f"No se encontraron proyectos que coincidan con '{query}'."
        
        numeric_cols = [col for col in df.columns if col not in ['Proyecto', 'BU', 'Empresa']]
        results['Total'] = results[numeric_cols].sum(axis=1)
        
        result = f"🔍 RESULTADOS DE BÚSQUEDA: '{query}'\n"
        result += f"Se encontraron {len(results)} proyecto(s):\n\n"
        
        for idx, row in results.iterrows():
            result += f"• {row['Proyecto']}\n"
            result += f"  BU: {row['BU']} | Empresa: {row.get('Empresa', 'N/A')}\n"
            result += f"  Monto: ${row['Total']:,.2f}\n\n"
        
        return result
    
    def chat(self, user_message: str, forecast_data: Dict[str, Any]) -> str:
        """
        Procesa un mensaje del usuario y genera una respuesta.
        
        Args:
            user_message: Mensaje del usuario
            forecast_data: Datos del forecast disponibles
            
        Returns:
            str: Respuesta del chatbot
        """
        if not self.is_configured():
            return "⚠️ El chatbot no está configurado. Por favor, ingresa tu API key de OpenAI en la configuración."
        
        try:
            import openai
            
            # Configurar cliente de OpenAI
            client = openai.OpenAI(api_key=self.api_key)
            
            # Mensaje de sistema con contexto
            system_message = {
                "role": "system",
                "content": """Eres un asistente experto en análisis de forecast y proyecciones financieras. 
Tienes acceso a herramientas para consultar datos del forecast actual.
Responde de manera clara, concisa y profesional. Usa emojis cuando sea apropiado para hacer las respuestas más visuales.
Cuando uses números, formatéalos correctamente con separadores de miles y símbolos de moneda.
Si el usuario pregunta por información específica, usa las herramientas disponibles para obtener datos precisos."""
            }
            
            # Agregar mensaje del usuario
            self.conversation_history.append({
                "role": "user",
                "content": user_message
            })
            
            # Preparar mensajes
            messages = [system_message] + self.conversation_history
            
            # Primera llamada al LLM
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.get_available_tools(),
                tool_choice="auto"
            )
            
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls
            
            # Si el modelo quiere usar herramientas
            if tool_calls:
                # Agregar respuesta del asistente al historial
                self.conversation_history.append(response_message)
                
                # Ejecutar cada herramienta
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    # Ejecutar herramienta
                    function_response = self.execute_tool(
                        function_name,
                        function_args,
                        forecast_data
                    )
                    
                    # Agregar resultado al historial
                    self.conversation_history.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": function_response
                    })
                
                # Segunda llamada para obtener respuesta final
                second_response = client.chat.completions.create(
                    model=self.model,
                    messages=[system_message] + self.conversation_history
                )
                
                final_message = second_response.choices[0].message.content
            else:
                # Respuesta directa sin herramientas
                final_message = response_message.content
            
            # Agregar respuesta final al historial
            self.conversation_history.append({
                "role": "assistant",
                "content": final_message
            })
            
            return final_message
            
        except Exception as e:
            logger.error(f"Error en chat: {str(e)}")
            return f"❌ Error al procesar tu mensaje: {str(e)}"
    
    def clear_history(self):
        """Limpia el historial de conversación."""
        self.conversation_history = []
