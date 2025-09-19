"""
Estilos CSS personalizados para mejorar la interfaz de usuario.

Este módulo contiene estilos CSS profesionales para transformar
la apariencia de la aplicación Streamlit.
"""

import streamlit as st

def apply_custom_styles():
    """
    Aplica estilos CSS personalizados para una interfaz más elegante y profesional.
    """
    
    custom_css = """
    <style>
    /* ===== VARIABLES DE COLOR ===== */
    :root {
        --primary-color: #1f4e79;
        --secondary-color: #40E0D0;
        --accent-color: #2E86AB;
        --success-color: #28a745;
        --warning-color: #ffc107;
        --danger-color: #dc3545;
        --light-gray: #f8f9fa;
        --medium-gray: #e9ecef;
        --dark-gray: #495057;
        --text-color: #2c3e50;
        --border-radius: 8px;
        --box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        --transition: all 0.3s ease;
    }
    
    /* ===== LAYOUT PRINCIPAL ===== */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    
    /* ===== SIDEBAR MEJORADO ===== */
    .css-1d391kg {
        background: linear-gradient(180deg, var(--primary-color) 0%, var(--accent-color) 100%);
        padding-top: 1rem;
    }
    
    .sidebar .sidebar-content {
        background: transparent;
    }
    
    /* Logo en sidebar */
    .sidebar .element-container img {
        border-radius: var(--border-radius);
        box-shadow: var(--box-shadow);
        margin-bottom: 1rem;
    }
    
    /* Controles del sidebar */
    .sidebar .stSelectbox > div > div {
        background-color: rgba(255, 255, 255, 0.9);
        border-radius: var(--border-radius);
        border: none;
        box-shadow: var(--box-shadow);
    }
    
    .sidebar .stNumberInput > div > div > input {
        background-color: rgba(255, 255, 255, 0.9);
        border-radius: var(--border-radius);
        border: 1px solid rgba(255, 255, 255, 0.3);
        color: var(--text-color);
    }
    
    .sidebar .stSlider > div > div > div {
        background-color: rgba(255, 255, 255, 0.2);
    }
    
    /* ===== HEADERS Y TÍTULOS ===== */
    .main h1 {
        color: var(--primary-color);
        font-weight: 700;
        margin-bottom: 2rem;
        text-align: center;
        font-size: 2.5rem;
        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .main h2 {
        color: var(--primary-color);
        font-weight: 600;
        margin-top: 2rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid var(--secondary-color);
    }
    
    .main h3 {
        color: var(--accent-color);
        font-weight: 500;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    
    /* ===== MÉTRICAS MEJORADAS ===== */
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, #ffffff 0%, var(--light-gray) 100%);
        border: 1px solid var(--medium-gray);
        border-radius: var(--border-radius);
        padding: 1rem;
        box-shadow: var(--box-shadow);
        transition: var(--transition);
    }
    
    [data-testid="metric-container"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    
    [data-testid="metric-container"] > div {
        color: var(--text-color);
    }
    
    [data-testid="metric-container"] [data-testid="metric-value"] {
        color: var(--primary-color);
        font-weight: 700;
        font-size: 1.8rem;
    }
    
    /* ===== BOTONES MEJORADOS ===== */
    .stButton > button {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--accent-color) 100%);
        color: white;
        border: none;
        border-radius: var(--border-radius);
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        transition: var(--transition);
        box-shadow: var(--box-shadow);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        background: linear-gradient(135deg, var(--accent-color) 0%, var(--primary-color) 100%);
    }
    
    .stButton > button:active {
        transform: translateY(0);
    }
    
    /* Botones secundarios */
    .stButton.secondary > button {
        background: linear-gradient(135deg, var(--secondary-color) 0%, #36d1dc 100%);
        color: var(--primary-color);
    }
    
    /* ===== TABS ELEGANTES ===== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: var(--light-gray);
        border-radius: var(--border-radius);
        padding: 0.25rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: var(--border-radius);
        color: var(--dark-gray);
        font-weight: 500;
        padding: 0.75rem 1.5rem;
        transition: var(--transition);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--accent-color) 100%);
        color: white;
        box-shadow: var(--box-shadow);
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: rgba(31, 78, 121, 0.1);
    }
    
    /* ===== ALERTAS Y MENSAJES ===== */
    .stAlert {
        border-radius: var(--border-radius);
        border: none;
        box-shadow: var(--box-shadow);
    }
    
    .stSuccess {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border-left: 4px solid var(--success-color);
    }
    
    .stWarning {
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
        border-left: 4px solid var(--warning-color);
    }
    
    .stError {
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
        border-left: 4px solid var(--danger-color);
    }
    
    .stInfo {
        background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%);
        border-left: 4px solid var(--accent-color);
    }
    
    /* ===== SELECTBOX Y INPUTS ===== */
    .stSelectbox > div > div {
        background-color: white;
        border: 1px solid var(--medium-gray);
        border-radius: var(--border-radius);
        box-shadow: var(--box-shadow);
    }
    
    .stNumberInput > div > div > input {
        background-color: white;
        border: 1px solid var(--medium-gray);
        border-radius: var(--border-radius);
        box-shadow: var(--box-shadow);
    }
    
    /* ===== PROGRESS BAR ===== */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, var(--secondary-color) 0%, var(--accent-color) 100%);
        border-radius: var(--border-radius);
    }
    
    /* ===== EXPANDER MEJORADO ===== */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, var(--light-gray) 0%, white 100%);
        border: 1px solid var(--medium-gray);
        border-radius: var(--border-radius);
        font-weight: 600;
        color: var(--primary-color);
    }
    
    .streamlit-expanderContent {
        background-color: white;
        border: 1px solid var(--medium-gray);
        border-top: none;
        border-radius: 0 0 var(--border-radius) var(--border-radius);
    }
    
    /* ===== DATAFRAME Y TABLAS ===== */
    .dataframe {
        border: none !important;
        border-radius: var(--border-radius);
        overflow: hidden;
        box-shadow: var(--box-shadow);
    }
    
    .dataframe thead th {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--accent-color) 100%);
        color: white;
        font-weight: 600;
        border: none;
        padding: 1rem 0.5rem;
    }
    
    .dataframe tbody td {
        border: 1px solid var(--medium-gray);
        padding: 0.75rem 0.5rem;
    }
    
    .dataframe tbody tr:nth-child(even) {
        background-color: var(--light-gray);
    }
    
    .dataframe tbody tr:hover {
        background-color: rgba(64, 224, 208, 0.1);
        transition: var(--transition);
    }
    
    /* ===== PLOTLY CHARTS ===== */
    .js-plotly-plot {
        border-radius: var(--border-radius);
        box-shadow: var(--box-shadow);
        background-color: white;
    }
    
    /* ===== LOADING SPINNER ===== */
    .stSpinner > div {
        border-top-color: var(--secondary-color) !important;
    }
    
    /* ===== RESPONSIVE DESIGN ===== */
    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
        
        .main h1 {
            font-size: 2rem;
        }
        
        [data-testid="metric-container"] {
            margin-bottom: 1rem;
        }
    }
    
    /* ===== ANIMACIONES SUTILES ===== */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .main > div {
        animation: fadeIn 0.5s ease-out;
    }
    
    /* ===== SCROLLBAR PERSONALIZADO ===== */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--light-gray);
        border-radius: var(--border-radius);
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, var(--secondary-color) 0%, var(--accent-color) 100%);
        border-radius: var(--border-radius);
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, var(--accent-color) 0%, var(--primary-color) 100%);
    }
    
    /* ===== CLASES UTILITARIAS ===== */
    .card {
        background: white;
        border-radius: var(--border-radius);
        padding: 1.5rem;
        box-shadow: var(--box-shadow);
        margin-bottom: 1rem;
        border: 1px solid var(--medium-gray);
    }
    
    .highlight {
        background: linear-gradient(135deg, var(--secondary-color) 0%, #36d1dc 100%);
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-weight: 600;
    }
    
    .text-center {
        text-align: center;
    }
    
    .text-primary {
        color: var(--primary-color);
    }
    
    .text-secondary {
        color: var(--secondary-color);
    }
    
    .mb-2 {
        margin-bottom: 1rem;
    }
    
    .mt-2 {
        margin-top: 1rem;
    }
    </style>
    """
    
    st.markdown(custom_css, unsafe_allow_html=True)

def create_metric_card(title: str, value: str, delta: str = None, help_text: str = None):
    """
    Crea una tarjeta de métrica personalizada con mejor diseño.
    
    Args:
        title: Título de la métrica
        value: Valor principal
        delta: Cambio o valor secundario (opcional)
        help_text: Texto de ayuda (opcional)
    """
    
    delta_html = f'<div class="metric-delta">{delta}</div>' if delta else ''
    help_html = f'<div class="metric-help">{help_text}</div>' if help_text else ''
    
    card_html = f"""
    <div class="card metric-card">
        <div class="metric-title">{title}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
        {help_html}
    </div>
    """
    
    st.markdown(card_html, unsafe_allow_html=True)

def create_section_header(title: str, subtitle: str = None, icon: str = None):
    """
    Crea un header de sección elegante.
    
    Args:
        title: Título principal
        subtitle: Subtítulo opcional
        icon: Emoji o icono opcional
    """
    
    icon_html = f'<span class="section-icon">{icon}</span> ' if icon else ''
    subtitle_html = f'<div class="section-subtitle">{subtitle}</div>' if subtitle else ''
    
    header_html = f"""
    <div class="section-header">
        <h2>{icon_html}{title}</h2>
        {subtitle_html}
    </div>
    """
    
    st.markdown(header_html, unsafe_allow_html=True)

def format_currency(value: float, decimals: int = 2) -> str:
    """
    Formatea un valor como moneda con el número especificado de decimales.
    
    Args:
        value: Valor numérico
        decimals: Número de decimales (default: 2)
        
    Returns:
        String formateado como moneda
    """
    if value == 0:
        return "$0.00"
    
    # Formatear con separadores de miles y decimales
    formatted = f"${value:,.{decimals}f}"
    return formatted

def create_status_badge(status: str, color: str = "primary") -> str:
    """
    Crea un badge de estado con colores personalizados.
    
    Args:
        status: Texto del estado
        color: Color del badge (primary, secondary, success, warning, danger)
        
    Returns:
        HTML del badge
    """
    
    color_classes = {
        "primary": "badge-primary",
        "secondary": "badge-secondary", 
        "success": "badge-success",
        "warning": "badge-warning",
        "danger": "badge-danger"
    }
    
    css_class = color_classes.get(color, "badge-primary")
    
    return f'<span class="badge {css_class}">{status}</span>'

def add_custom_metric_styles():
    """
    Agrega estilos específicos para métricas personalizadas.
    """
    
    metric_css = """
    <style>
    .metric-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        border-left: 4px solid var(--secondary-color);
        transition: var(--transition);
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    .metric-title {
        font-size: 0.9rem;
        color: var(--dark-gray);
        font-weight: 500;
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .metric-value {
        font-size: 2rem;
        color: var(--primary-color);
        font-weight: 700;
        margin-bottom: 0.25rem;
    }
    
    .metric-delta {
        font-size: 0.8rem;
        color: var(--success-color);
        font-weight: 600;
    }
    
    .metric-help {
        font-size: 0.75rem;
        color: var(--dark-gray);
        margin-top: 0.5rem;
        font-style: italic;
    }
    
    .section-header {
        margin: 2rem 0 1rem 0;
        padding-bottom: 1rem;
        border-bottom: 2px solid var(--secondary-color);
    }
    
    .section-icon {
        font-size: 1.2em;
        margin-right: 0.5rem;
    }
    
    .section-subtitle {
        font-size: 1rem;
        color: var(--dark-gray);
        font-weight: 400;
        margin-top: 0.5rem;
    }
    
    .badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        font-size: 0.75rem;
        font-weight: 600;
        border-radius: 4px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .badge-primary {
        background-color: var(--primary-color);
        color: white;
    }
    
    .badge-secondary {
        background-color: var(--secondary-color);
        color: var(--primary-color);
    }
    
    .badge-success {
        background-color: var(--success-color);
        color: white;
    }
    
    .badge-warning {
        background-color: var(--warning-color);
        color: var(--text-color);
    }
    
    .badge-danger {
        background-color: var(--danger-color);
        color: white;
    }
    </style>
    """
    
    st.markdown(metric_css, unsafe_allow_html=True)
