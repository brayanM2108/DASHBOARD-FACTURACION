"""
Configuración global del Dashboard de Productividad
====================================================
Contiene todas las constantes, rutas de archivos y configuraciones
compartidas por toda la aplicación.
"""

import os

# --- Directorios ---
PERSISTED_DATA_DIR = "persisted_data"
os.makedirs(PERSISTED_DATA_DIR, exist_ok=True)

# --- Archivos maestros ---
FACTURADORES_FILE = "FACTURADORES.xlsx"
FACTURADORES_SHEET = 1

# --- Rutas de archivos Parquet ---
FILES = {
    "PPL": os.path.join(PERSISTED_DATA_DIR, "df_ppl.parquet"),
    "Convenios": os.path.join(PERSISTED_DATA_DIR, "df_convenios.parquet"),
    "RIPS": os.path.join(PERSISTED_DATA_DIR, "df_rips.parquet"),
    "Facturacion": os.path.join(PERSISTED_DATA_DIR, "df_facturacion.parquet"),
    "Facturadores": os.path.join(PERSISTED_DATA_DIR, "df_facturadores.parquet"),
    "FacturacionElectronica": os.path.join(PERSISTED_DATA_DIR, "df_fact_elec.parquet")
}

# --- Estados válidos ---
# IMPORTANTE: Todos en mayúsculas porque las columnas se normalizan a mayúsculas
ESTADOS_VALIDOS_LEGALIZACIONES = ['ACTIVA']
ESTADOS_VALIDOS_RIPS = ['COMPLETO']
ESTADOS_VALIDOS_FACTURACION_ELECTRONICA = ['ACTIVO']

# --- Identificadores de columnas ---
# Marcadores para detectar encabezados en archivos
COLUMN_MARKERS = {
    "legalizaciones": "ID_LEGALIZACION",
    "rips": "CÓDIGO",
    "facturacion": "NRO_LEGALIACION",
    "facturacion_electronica": "IDENTIFICACION"
}

# --- Nombres de columnas normalizadas ---
# IMPORTANTE: Todas en mayúsculas porque las columnas se normalizan a mayúsculas
COLUMN_NAMES = {
    "usuario": ["USUARIO", "USUARIO FACTURÓ", "USUARIO_FACTURO"],
    "fecha": ["FECHA_REAL", "FECHA_FACTURA", "FECHA", "FECHA RADICACIÓN", "FECHA LEGALIZACIÓN"],
    "estado": ["ESTADO"],
    "convenio": "CONVENIO"
}

# --- Valores especiales ---
CONVENIO_PPL = "Patrimonio Autonomo Fondo Atención Salud PPL 2024"

# --- Configuración de Streamlit ---
PAGE_CONFIG = {
    "page_title": "Dashboard de Productividad",
    "page_icon": "📊",
    "layout": "wide"
}

# --- Configuración de visualizaciones ---
PLOT_CONFIG = {
    "figsize_barplot": (10, 6),
    "figsize_lineplot": (12, 5),
    "palette": "viridis"
}
