"""
Procesamiento de datos
=======================
Funciones para transformar y limpiar datos cargados.
"""

import pandas as pd
from config.settings import (
    ESTADOS_VALIDOS_LEGALIZACIONES,
    ESTADOS_VALIDOS_RIPS,
    ESTADOS_VALIDOS_FACTURACION_ELECTRONICA,
    CONVENIO_PPL
)
from utils.date_helpers import parse_date_column


def process_legalizaciones(df, estado_column="ESTADO", fecha_column="FECHA_REAL", convenio_column="CONVENIO"):
    """
    Procesa el DataFrame de legalizaciones.

    Args:
        df (pd.DataFrame): DataFrame de legalizaciones
        estado_column (str): Nombre de columna de estado
        fecha_column (str): Nombre de columna de fecha
        convenio_column (str): Nombre de columna de convenio

    Returns:
        tuple: (df_ppl, df_convenios) - DataFrames separados
    """
    if df is None or df.empty:
        return None, None

    # Convertir fecha
    df = parse_date_column(df, fecha_column)

    # Normalizar y filtrar por estado válido
    if estado_column in df.columns:
        # Normalizar valores de estado a mayúsculas
        df[estado_column] = df[estado_column].astype(str).str.strip().str.upper()
        df = df[df[estado_column].isin(ESTADOS_VALIDOS_LEGALIZACIONES)]

    # Separar PPL y Convenios
    df_ppl = None
    df_convenios = None

    if convenio_column in df.columns:
        df_ppl = df[df[convenio_column] == CONVENIO_PPL].copy()
        df_convenios = df[df[convenio_column] != CONVENIO_PPL].copy()

    return df_ppl, df_convenios


def process_rips(df, estado_column="ESTADO", fecha_column="FECHA_REAL"):
    """
    Procesa el DataFrame de RIPS.

    Args:
        df (pd.DataFrame): DataFrame de RIPS
        estado_column (str): Nombre de columna de estado
        fecha_column (str): Nombre de columna de fecha

    Returns:
        pd.DataFrame: DataFrame procesado
    """
    if df is None or df.empty:
        return None

    # Convertir fecha
    df = parse_date_column(df, fecha_column)

    # Normalizar y filtrar por estado válido
    if estado_column in df.columns:
        df[estado_column] = df[estado_column].astype(str).str.strip().str.upper()
        df = df[df[estado_column].isin(ESTADOS_VALIDOS_RIPS)]

    return df


def process_facturacion(df, fecha_column="FECHA_FACTURA"):
    """
    Procesa el DataFrame de facturación.

    Args:
        df (pd.DataFrame): DataFrame de facturación
        fecha_column (str): Nombre de columna de fecha

    Returns:
        pd.DataFrame: DataFrame procesado
    """
    if df is None or df.empty:
        return None

    # Convertir fecha
    df = parse_date_column(df, fecha_column)

    return df


def process_facturacion_electronica(df, estado_column="ESTADO", fecha_column="FECHA RADICACIÓN"):
    """
    Procesa el DataFrame de facturación electrónica.

    Args:
        df (pd.DataFrame): DataFrame de facturación electrónica
        estado_column (str): Nombre de columna de estado
        fecha_column (str): Nombre de columna de fecha

    Returns:
        pd.DataFrame: DataFrame procesado
    """
    if df is None or df.empty:
        return None

    # Convertir fecha
    df = parse_date_column(df, fecha_column)

    # Normalizar y filtrar por estado válido
    if estado_column in df.columns:
        df[estado_column] = df[estado_column].astype(str).str.strip().str.upper()
        df = df[df[estado_column].isin(ESTADOS_VALIDOS_FACTURACION_ELECTRONICA)]

    return df


def merge_with_facturadores(df, df_facturadores, usuario_column="USUARIO"):
    """
    Combina un DataFrame con información de facturadores.

    Args:
        df (pd.DataFrame): DataFrame principal
        df_facturadores (pd.DataFrame): DataFrame de facturadores
        usuario_column (str): Nombre de columna de usuario

    Returns:
        pd.DataFrame: DataFrame combinado con información de facturadores
    """
    if df is None or df.empty or df_facturadores is None or df_facturadores.empty:
        return df

    if usuario_column not in df.columns or "USUARIO" not in df_facturadores.columns:
        return df

    # Realizar merge
    df_merged = pd.merge(
        df,
        df_facturadores,
        left_on=usuario_column,
        right_on="USUARIO",
        how="left"
    )

    return df_merged


def aggregate_by_user(df, usuario_column="USUARIO", date_column=None, group_by_date=False):
    """
    Agrupa datos por usuario y opcionalmente por fecha.

    Args:
        df (pd.DataFrame): DataFrame a agregar
        usuario_column (str): Nombre de columna de usuario
        date_column (str): Nombre de columna de fecha (opcional)
        group_by_date (bool): Si True, agrupa también por fecha

    Returns:
        pd.DataFrame: DataFrame agregado
    """
    if df is None or df.empty or usuario_column not in df.columns:
        return None

    if group_by_date and date_column and date_column in df.columns:
        # Agregar columna de fecha (solo día)
        df['FECHA'] = df[date_column].dt.date
        agg_df = df.groupby([usuario_column, 'FECHA']).size().reset_index(name='CANTIDAD')
    else:
        agg_df = df.groupby(usuario_column).size().reset_index(name='CANTIDAD')

    return agg_df


def process_procesos(df):
    """
    Procesa el DataFrame de procesos administrativos desde Google Sheets.

    Args:
        df (pd.DataFrame): DataFrame de procesos cargado desde Google Sheets

    Returns:
        pd.DataFrame: DataFrame procesado con columnas normalizadas
    """
    if df is None or df.empty:
        return None

    # Detectar si la primera fila contiene encabezados reales
    # Verificar si la primera fila tiene valores como 'FECHA', 'NOMBRE', etc.
    primera_fila = df.iloc[0].astype(str).str.upper()

    if 'FECHA' in primera_fila.values or 'NOMBRE' in primera_fila.values:
        # La primera fila son los encabezados reales
        df.columns = df.iloc[0].astype(str).str.strip().str.upper()
        df = df.iloc[1:].reset_index(drop=True)
    else:
        # Normalizar nombres de columnas existentes
        df.columns = df.columns.str.strip().str.upper()

    # Validar columnas requeridas
    columnas_requeridas = ['FECHA', 'NOMBRE', 'DOCUMENTO', 'PROCESO', 'CANTIDAD']

    # Buscar variantes de nombres de columnas
    mapeo_columnas = {}
    for col_requerida in columnas_requeridas:
        if col_requerida not in df.columns:
            # Buscar variantes
            for col in df.columns:
                if col_requerida in col or col in col_requerida:
                    mapeo_columnas[col] = col_requerida
                    break

    # Renombrar columnas si se encontraron variantes
    if mapeo_columnas:
        df = df.rename(columns=mapeo_columnas)

    # Verificar columnas faltantes
    columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
    if columnas_faltantes:
        raise ValueError(f"Faltan las siguientes columnas: {', '.join(columnas_faltantes)}. Columnas disponibles: {', '.join(df.columns.tolist())}")

    # Eliminar filas completamente vacías
    df = df.dropna(how='all')

    # Convertir fecha al formato correcto
    try:
        # Intentar múltiples formatos de fecha
        df['FECHA'] = pd.to_datetime(df['FECHA'], errors='coerce')
    except Exception as e:
        print(f"Advertencia: Error al convertir fechas: {e}")

    # Convertir cantidad a numérico
    df['CANTIDAD'] = pd.to_numeric(df['CANTIDAD'], errors='coerce')

    # Eliminar filas con valores nulos en columnas críticas
    df = df.dropna(subset=['FECHA', 'NOMBRE', 'CANTIDAD'])

    # Limpiar espacios en blanco en columnas de texto
    for col in ['NOMBRE', 'DOCUMENTO', 'PROCESO']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    return df

def merge_facturacion_with_electronica(df_facturacion, df_fact_elec):
    """
    Cruza facturación con facturación electrónica para obtener el USUARIO.

    Busca y asigna el usuario de facturación electrónica a cada factura mediante
    un cruce BUSCARX entre NRO_FACTURACLI (facturación) y FACTURA (electrónica).

    Args:
        df_facturacion (pd.DataFrame): DataFrame de facturación con columna 'NRO_FACTURACLI'
        df_fact_elec (pd.DataFrame): DataFrame de facturación electrónica con columnas
                                     'FACTURA', 'USUARIO' y 'ESTADO'

    Returns:
        pd.DataFrame: DataFrame de facturación con columna 'USUARIO' agregada/actualizada
    """
    if df_facturacion is None or df_facturacion.empty:
        return df_facturacion

    if df_fact_elec is None or df_fact_elec.empty:
        return df_facturacion

    # Crear una copia para no modificar el original
    df_result = df_facturacion.copy()

    # Normalizar columnas de texto a mayúsculas
    for df in [df_result, df_fact_elec]:
        for col in df.columns:
            if df[col].dtype == object:
                df[col] = df[col].astype(str).str.strip().str.upper()

    # Filtrar solo facturas electrónicas en estado ACTIVO
    estado_col = 'ESTADO' if 'ESTADO' in df_fact_elec.columns else 'Estado'
    if estado_col in df_fact_elec.columns:
        df_fact_elec_activa = df_fact_elec[df_fact_elec[estado_col] == 'ACTIVO'].copy()
    else:
        df_fact_elec_activa = df_fact_elec.copy()

    # Crear mapeo FACTURA → USUARIO
    if 'FACTURA' in df_fact_elec_activa.columns and 'USUARIO' in df_fact_elec_activa.columns:
        mapa_usuario = (
            df_fact_elec_activa
            .dropna(subset=['FACTURA', 'USUARIO'])
            .drop_duplicates(subset=['FACTURA'])
            .set_index('FACTURA')['USUARIO']
        )

        # Asignar USUARIO a facturación mediante NRO_FACTURACLI
        if 'NRO_FACTURACLI' in df_result.columns:
            df_result['USUARIO'] = df_result['NRO_FACTURACLI'].map(mapa_usuario)

    return df_result

def filtrar_por_facturadores(df, df_facturadores, columna_usuario, tipo_comparacion='DOCUMENTO'):
    """
    Filtra un DataFrame para mantener solo registros cuyos usuarios están en facturadores.

    Args:
        df (pd.DataFrame): DataFrame a filtrar
        df_facturadores (pd.DataFrame): DataFrame de facturadores maestro
        columna_usuario (str): Nombre de la columna de usuario en df
        tipo_comparacion (str): 'DOCUMENTO' o 'NOMBRE'

    Returns:
        pd.DataFrame: DataFrame filtrado con solo usuarios válidos
    """
    if df is None or df.empty:
        return df

    if df_facturadores is None or df_facturadores.empty:
        return df

    if columna_usuario is None or columna_usuario not in df.columns:
        return df

    if tipo_comparacion not in df_facturadores.columns:
        return df

    # Obtener lista de valores válidos de facturadores
    valores_validos = (
        df_facturadores[tipo_comparacion]
        .dropna()
        .astype(str)
        .str.strip()
        .str.upper()
        .unique().tolist()
    )

    # Normalizar columna de usuario
    df = df.copy()
    df['_usuario_norm'] = (
        df[columna_usuario]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # Filtrar solo los que están en facturadores
    df_filtrado = df[df['_usuario_norm'].isin(valores_validos)].copy()

    # Eliminar columna temporal
    df_filtrado = df_filtrado.drop(columns=['_usuario_norm'])

    return df_filtrado

