"""
Módulo de base de datos histórica de clientes para la aplicación de Forecast Financiero.

Este módulo maneja la información histórica de clientes para inferir Payment Terms
y Lead Times basados en proyectos anteriores.
"""

import pandas as pd
import sqlite3
import os
from datetime import datetime
from typing import Optional, Dict, List, Tuple
import logging
from dataclasses import dataclass

from config.settings import BUSINESS_RULES


# Configurar logging
logger = logging.getLogger(__name__)


@dataclass
class ClientHistoricalData:
    """Datos históricos de un cliente."""
    
    client_name: str
    most_common_payment_terms: str
    average_lead_time: float
    project_count: int
    last_project_date: datetime
    average_amount: float


class ClientDatabase:
    """
    Clase para manejar la base de datos histórica de clientes.
    
    Esta clase proporciona funcionalidades para almacenar y consultar
    información histórica de clientes para inferir datos faltantes.
    """
    
    def __init__(self, db_path: str = "data/client_history.db"):
        """
        Inicializa la base de datos de clientes.
        
        Args:
            db_path: Ruta al archivo de base de datos SQLite
        """
        self.db_path = db_path
        self._ensure_db_directory()
        self._initialize_database()
    
    def _ensure_db_directory(self):
        """Asegura que el directorio de la base de datos exista."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
    
    def _initialize_database(self):
        """Inicializa las tablas de la base de datos."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Tabla de proyectos históricos
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS historical_projects (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        client_name TEXT NOT NULL,
                        project_name TEXT,
                        bu TEXT,
                        amount REAL,
                        close_date TEXT,
                        lead_time REAL,
                        payment_terms TEXT,
                        probability REAL,
                        paid_in_advance REAL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(client_name, project_name, close_date)
                    )
                """)
                
                # Tabla de configuración de clientes
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS client_config (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        client_name TEXT UNIQUE NOT NULL,
                        default_payment_terms TEXT,
                        default_lead_time REAL,
                        notes TEXT,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Índices para mejorar performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_client_name ON historical_projects(client_name)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_close_date ON historical_projects(close_date)")
                
                conn.commit()
                logger.info("Base de datos de clientes inicializada correctamente")
                
        except Exception as e:
            logger.error(f"Error inicializando base de datos: {str(e)}")
            raise
    
    def add_historical_data(self, df: pd.DataFrame) -> int:
        """
        Agrega datos históricos desde un DataFrame.
        
        Args:
            df: DataFrame con datos de proyectos
            
        Returns:
            int: Número de registros agregados
        """
        try:
            records_added = 0
            
            with sqlite3.connect(self.db_path) as conn:
                for _, row in df.iterrows():
                    # Extraer nombre del cliente del nombre del proyecto
                    client_name = self._extract_client_name(row.get('Opportunity Name', ''))
                    
                    if not client_name:
                        continue
                    
                    # Preparar datos
                    project_data = {
                        'client_name': client_name,
                        'project_name': str(row.get('Opportunity Name', '')),
                        'bu': str(row.get('BU', '')),
                        'amount': float(row.get('Amount', 0)) if pd.notna(row.get('Amount')) else None,
                        'close_date': str(row.get('Close Date', '')),
                        'lead_time': float(row.get('Lead Time', 0)) if pd.notna(row.get('Lead Time')) else None,
                        'payment_terms': str(row.get('Payment Terms', '')) if pd.notna(row.get('Payment Terms')) else None,
                        'probability': float(row.get('probability_assigned', 0)) if pd.notna(row.get('probability_assigned')) else None,
                        'paid_in_advance': float(row.get('Paid in Advance', 0)) if pd.notna(row.get('Paid in Advance')) else None
                    }
                    
                    # Insertar o actualizar
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT OR REPLACE INTO historical_projects 
                        (client_name, project_name, bu, amount, close_date, lead_time, 
                         payment_terms, probability, paid_in_advance)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        project_data['client_name'],
                        project_data['project_name'],
                        project_data['bu'],
                        project_data['amount'],
                        project_data['close_date'],
                        project_data['lead_time'],
                        project_data['payment_terms'],
                        project_data['probability'],
                        project_data['paid_in_advance']
                    ))
                    
                    records_added += 1
                
                conn.commit()
                logger.info(f"Se agregaron {records_added} registros históricos")
                return records_added
                
        except Exception as e:
            logger.error(f"Error agregando datos históricos: {str(e)}")
            return 0
    
    def get_client_payment_terms(self, client_name: str) -> Optional[str]:
        """
        Obtiene los Payment Terms más comunes para un cliente.
        
        Args:
            client_name: Nombre del cliente
            
        Returns:
            Optional[str]: Payment Terms más común o None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Buscar Payment Terms más común
                cursor.execute("""
                    SELECT payment_terms, COUNT(*) as count
                    FROM historical_projects 
                    WHERE client_name = ? AND payment_terms IS NOT NULL AND payment_terms != ''
                    GROUP BY payment_terms
                    ORDER BY count DESC, MAX(close_date) DESC
                    LIMIT 1
                """, (client_name,))
                
                result = cursor.fetchone()
                return result[0] if result else None
                
        except Exception as e:
            logger.error(f"Error obteniendo Payment Terms para {client_name}: {str(e)}")
            return None
    
    def get_client_lead_time(self, client_name: str, amount: float = None) -> Optional[float]:
        """
        Obtiene el Lead Time promedio para un cliente.
        
        Args:
            client_name: Nombre del cliente
            amount: Monto del proyecto (para filtrar proyectos similares)
            
        Returns:
            Optional[float]: Lead Time promedio o None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if amount:
                    # Buscar proyectos con montos similares (±50%)
                    min_amount = amount * 0.5
                    max_amount = amount * 1.5
                    
                    cursor.execute("""
                        SELECT AVG(lead_time) as avg_lead_time
                        FROM historical_projects 
                        WHERE client_name = ? 
                        AND lead_time IS NOT NULL 
                        AND amount BETWEEN ? AND ?
                    """, (client_name, min_amount, max_amount))
                else:
                    # Buscar promedio general del cliente
                    cursor.execute("""
                        SELECT AVG(lead_time) as avg_lead_time
                        FROM historical_projects 
                        WHERE client_name = ? AND lead_time IS NOT NULL
                    """, (client_name,))
                
                result = cursor.fetchone()
                return result[0] if result and result[0] else None
                
        except Exception as e:
            logger.error(f"Error obteniendo Lead Time para {client_name}: {str(e)}")
            return None
    
    def get_client_historical_data(self, client_name: str) -> Optional[ClientHistoricalData]:
        """
        Obtiene un resumen completo de datos históricos de un cliente.
        
        Args:
            client_name: Nombre del cliente
            
        Returns:
            Optional[ClientHistoricalData]: Datos históricos del cliente
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Obtener estadísticas del cliente
                cursor.execute("""
                    SELECT 
                        COUNT(*) as project_count,
                        AVG(lead_time) as avg_lead_time,
                        AVG(amount) as avg_amount,
                        MAX(close_date) as last_project_date
                    FROM historical_projects 
                    WHERE client_name = ?
                """, (client_name,))
                
                stats = cursor.fetchone()
                
                if not stats or stats[0] == 0:
                    return None
                
                # Obtener Payment Terms más común
                payment_terms = self.get_client_payment_terms(client_name)
                
                return ClientHistoricalData(
                    client_name=client_name,
                    most_common_payment_terms=payment_terms or "NET 30",
                    average_lead_time=stats[1] or 8.0,
                    project_count=stats[0],
                    last_project_date=datetime.strptime(stats[3], '%d/%m/%Y') if stats[3] else datetime.now(),
                    average_amount=stats[2] or 0.0
                )
                
        except Exception as e:
            logger.error(f"Error obteniendo datos históricos para {client_name}: {str(e)}")
            return None
    
    def _extract_client_name(self, project_name: str) -> str:
        """
        Extrae el nombre del cliente del nombre del proyecto.
        
        Args:
            project_name: Nombre completo del proyecto
            
        Returns:
            str: Nombre del cliente extraído
        """
        if not project_name or pd.isna(project_name):
            return "Unknown Client"
        
        clean_name = str(project_name).strip()
        
        # Patrones comunes para extraer cliente
        # Ejemplo: "Cliente ABC - Proyecto XYZ" -> "Cliente ABC"
        if " - " in clean_name:
            return clean_name.split(" - ")[0].strip()
        
        # Ejemplo: "Proyecto para Cliente ABC" -> "Cliente ABC"
        if " para " in clean_name.lower():
            parts = clean_name.lower().split(" para ")
            if len(parts) > 1:
                return parts[1].strip().title()
        
        # Ejemplo: "ABC Corp Project" -> "ABC Corp"
        words = clean_name.split()
        if len(words) > 1:
            # Tomar las primeras 2-3 palabras como cliente
            if "project" in words[-1].lower() or "proyecto" in words[-1].lower():
                return " ".join(words[:-1])
            else:
                return " ".join(words[:2])
        
        return clean_name
    
    def estimate_lead_time_by_amount(self, amount: float) -> float:
        """
        Estima Lead Time basado en el monto del proyecto.
        
        Args:
            amount: Monto del proyecto
            
        Returns:
            float: Lead Time estimado en semanas
        """
        rules = BUSINESS_RULES.LEAD_TIME_BY_AMOUNT_RANGES
        
        for (min_amount, max_amount), lead_time in rules.items():
            if min_amount <= amount < max_amount:
                return float(lead_time)
        
        # Valor por defecto si no coincide con ningún rango
        return 8.0
    
    def get_database_stats(self) -> Dict:
        """
        Obtiene estadísticas de la base de datos.
        
        Returns:
            Dict: Estadísticas de la base de datos
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Estadísticas generales
                cursor.execute("SELECT COUNT(*) FROM historical_projects")
                total_projects = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(DISTINCT client_name) FROM historical_projects")
                unique_clients = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT COUNT(*) FROM historical_projects 
                    WHERE payment_terms IS NOT NULL AND payment_terms != ''
                """)
                projects_with_payment_terms = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT COUNT(*) FROM historical_projects 
                    WHERE lead_time IS NOT NULL
                """)
                projects_with_lead_time = cursor.fetchone()[0]
                
                return {
                    'total_projects': total_projects,
                    'unique_clients': unique_clients,
                    'projects_with_payment_terms': projects_with_payment_terms,
                    'projects_with_lead_time': projects_with_lead_time,
                    'payment_terms_coverage': projects_with_payment_terms / total_projects if total_projects > 0 else 0,
                    'lead_time_coverage': projects_with_lead_time / total_projects if total_projects > 0 else 0
                }
                
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de BD: {str(e)}")
            return {}
