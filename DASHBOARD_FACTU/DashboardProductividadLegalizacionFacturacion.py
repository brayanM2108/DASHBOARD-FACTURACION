"""
Dashboard de Productividad - Legalización y Facturación
========================================================

Este módulo implementa un dashboard interactivo en Streamlit para el análisis de productividad
en procesos de legalización y facturación de servicios de salud.

Características principales:
- Carga y procesamiento de archivos Excel/CSV con detección automática de encabezados
- Gestión persistente de datos mediante archivos Parquet
- Filtrado dinámico por tipo de legalización, usuario y rango de fechas
- Visualizaciones comparativas y evolutivas de productividad
- Integración de facturación con facturación electrónica mediante búsqueda de usuarios
- Descarga de reportes procesados

Estructura de datos:
- PPL: Legalizaciones del Patrimonio Autónomo Fondo Atención Salud PPL 2024
- Convenios: Legalizaciones de otros convenios
- RIPS: Registros Individuales de Prestación de Servicios de Salud
- Facturación: Datos de facturación general
- Facturación Electrónica: Mapeo de facturas a usuarios

Autor: Brayan Melo
Versión: 1.0
"""

from io import BytesIO
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import datetime
import os

# --- Configuración de la página ---
# Establece el título, ícono y diseño de la página de Streamlit
st.set_page_config(page_title="Dashboard de Productividad", page_icon="📊", layout="wide")

# Directorio para almacenamiento persistente de datos procesados
PERSISTED_DATA_DIR = "persisted_data"
os.makedirs(PERSISTED_DATA_DIR, exist_ok=True)

# Diccionario con las rutas de los archivos Parquet para cada tipo de dato
FILES = {
    "PPL": os.path.join(PERSISTED_DATA_DIR, "df_ppl.parquet"),
    "Convenios": os.path.join(PERSISTED_DATA_DIR, "df_convenios.parquet"),
    "RIPS": os.path.join(PERSISTED_DATA_DIR, "df_rips.parquet"),
    "Facturacion": os.path.join(PERSISTED_DATA_DIR, "df_facturacion.parquet")
}


# --- FUNCIONES DE CARGA ---
def save_local(df, filepath):
    """
    Guarda un DataFrame localmente en formato Parquet.

    Convierte todas las columnas a string antes de guardar para evitar
    problemas de compatibilidad de tipos de datos.

    Args:
        df (pd.DataFrame): DataFrame a guardar. Puede ser None o vacío.
        filepath (str): Ruta completa del archivo donde se guardará el DataFrame.

    Returns:
        None
    Nota:
        Si el DataFrame es None o está vacío, no se realiza ninguna acción.
    """
    if df is not None and not df.empty:
        df.astype(str).to_parquet(filepath, index=False)


def load_local(filepath):
    """
    Carga un DataFrame desde un archivo Parquet local.

    Args:
        filepath (str): Ruta completa del archivo Parquet a cargar.

    Returns:
        pd.DataFrame or None: El DataFrame cargado si el archivo existe,
                             None en caso contrario.
    """
    return pd.read_parquet(filepath) if os.path.exists(filepath) else None


def buscar_usuario_en_fact_electronica(df_fact, df_fact_elec):
    """
    Busca y asigna el usuario de facturación electrónica a cada factura.

    Esta función realiza una búsqueda tipo BUSCARX/VLOOKUP entre dos DataFrames:
    - df_fact: Contiene las facturas que necesitan el campo USUARIO
    - df_fact_elec: Contiene el mapeo FACTURA → USUARIO

    Proceso:
    1. Valida que ambos DataFrames existan y no estén vacíos
    2. Normaliza todos los valores de texto a mayúsculas y sin espacios
    3. Filtra solo las facturas electrónicas en estado ACTIVO
    4. Crea un mapeo único FACTURA → USUARIO
    5. Asigna el USUARIO a df_fact mediante la columna NRO_FACTURACLI

    Args:
        df_fact (pd.DataFrame): DataFrame de facturación con columna 'NRO_FACTURACLI'.
                               Se espera que tenga una columna USUARIO vacía o a completar.
        df_fact_elec (pd.DataFrame): DataFrame de facturación electrónica con columnas
                                    'FACTURA', 'USUARIO' y 'Estado'.

    Returns:
        pd.DataFrame: El DataFrame df_fact original con la columna 'USUARIO' actualizada.
                     Si hay facturas sin coincidencia, su USUARIO quedará como NaN.
                     Si alguno de los DataFrames de entrada es None o vacío, retorna df_fact sin cambios.
    """
    if (
            df_fact is None or df_fact.empty or
            df_fact_elec is None or df_fact_elec.empty
    ):
        return df_fact

    # -------- Normalización --------
    # Convierte todos los campos de texto a mayúsculas y elimina espacios
    # para garantizar coincidencias exactas independientemente del formato original
    for df in [df_fact, df_fact_elec]:
        for col in df.columns:
            if df[col].dtype == object:
                df[col] = (
                    df[col]
                    .astype(str)
                    .str.strip()
                    .str.upper()
                )

    # Filtra solo las facturas electrónicas en estado ACTIVO
    df_fact_elec_activa = df_fact_elec[
        df_fact_elec['Estado'] == 'ACTIVO'
        ]

    # -------- Mapa FACTURA → USUARIO --------
    # Crea un diccionario/Serie donde la clave es el número de factura
    # y el valor es el usuario asociado
    mapa_usuario = (
        df_fact_elec_activa
        .dropna(subset=['FACTURA', 'USUARIO'])
        .drop_duplicates(subset=['FACTURA'])
        .set_index('FACTURA')['USUARIO']
    )

    # -------- BUSCARX --------
    # Asigna el USUARIO a cada registro de df_fact
    df_fact['USUARIO'] = df_fact['NRO_FACTURACLI'].map(mapa_usuario)
    return df_fact


# --- INICIALIZACIÓN ---
# Carga los datos persistidos al iniciar la aplicación (solo una vez por sesión)
if 'initialized' not in st.session_state:
    st.session_state.df_ppl = load_local(FILES["PPL"])
    st.session_state.df_convenios = load_local(FILES["Convenios"])
    st.session_state.df_rips = load_local(FILES["RIPS"])
    st.session_state.df_facturacion = load_local(FILES["Facturacion"])

    st.session_state.df_fact_elec = load_local(
        os.path.join(PERSISTED_DATA_DIR, "df_fact_elec.parquet")
    )

    st.session_state.initialized = True

# --- CARGA DE ARCHIVOS ---
st.title("📥 Carga de Archivos")

col1, col2, col3, col4 = st.columns(3)

# --- Columna 1: Legalizaciones (PPL + Convenios + RIPS) ---
with col1:
    st.subheader("Archivo 1: Legalizaciones (PPL + Convenios + RIPS)")

    file1 = st.file_uploader("Sube el archivo de Legalizaciones", type=["xlsx", "xls", "csv"], key="file1")

    if file1 is not None:
        try:
            # -------- LECTURA ROBUSTA DEL ARCHIVO --------
            # Lee el archivo sin asumir dónde están los encabezados
            if file1.name.endswith('.csv'):
                df_raw = pd.read_csv(file1, header=None)
            else:
                df_raw = pd.read_excel(file1, header=None)

            # Busca la fila que contiene 'ID_LEGALIZACION' para identificar los encabezados
            header_row = None
            for i, row in df_raw.iterrows():
                if row.astype(str).str.strip().str.upper().str.startswith("ID_LEGALIZACION").any():
                    header_row = i
                    break

            if header_row is None:
                st.error("❌ No se encontró la fila de columnas que contiene 'ID_LEGALIZACION'")
                st.stop()

            # Relee el archivo usando la fila identificada como encabezado
            if file1.name.endswith('.csv'):
                df_temp = pd.read_csv(file1, header=header_row)
            else:
                df_temp = pd.read_excel(file1, header=header_row)

            # Limpia los nombres de las columnas (espacios, saltos de línea)
            df_temp.columns = (
                df_temp.columns
                .astype(str)
                .str.strip()
                .str.replace('\n', ' ')
            )
            st.success(f"✅ Archivo cargado: {len(df_temp):,} filas")
            st.info(f"📋 Encabezados detectados en fila: {header_row + 1}")

            # Botón para procesar y separar los datos
            if st.button("💾 Procesar y Guardar Legalizaciones", use_container_width=True):
                try:
                    # Verifica que existe la columna CONVENIO
                    if 'CONVENIO' not in df_temp.columns:
                        st.error("❌ No se encontró la columna 'CONVENIO' en el archivo")
                        st.stop()

                    # SEPARACIÓN AUTOMÁTICA basada en el valor del campo CONVENIO:
                    df_ppl = df_temp[df_temp['CONVENIO'] == 'Patrimonio Autonomo Fondo Atención Salud PPL 2024'].copy()
                    df_convenios = df_temp[
                        df_temp['CONVENIO'] != 'Patrimonio Autonomo Fondo Atención Salud PPL 2024'].copy()
                    df_rips = pd.DataFrame()  # Vacío por ahora

                    # Guarda en session_state
                    st.session_state.df_ppl = df_ppl if not df_ppl.empty else None
                    st.session_state.df_convenios = df_convenios if not df_convenios.empty else None
                    st.session_state.df_rips = df_rips if not df_rips.empty else None

                    # Guarda archivos locales en formato Parquet
                    save_local(df_ppl, FILES["PPL"])
                    save_local(df_convenios, FILES["Convenios"])
                    save_local(df_rips, FILES["RIPS"])

                    # Muestra resumen de procesamiento
                    total_procesado = len(df_ppl) + len(df_convenios) + len(df_rips)

                    st.success(f"""✅ Datos procesados y guardados:

**PPL:** {len(df_ppl):,} registros
**Convenios:** {len(df_convenios):,} registros
**RIPS:** {len(df_rips):,} registros

**Total procesado:** {total_procesado:,} / {len(df_temp):,} filas
                    """)

                    if total_procesado != len(df_temp):
                        st.warning(f"⚠️ Hay {len(df_temp) - total_procesado} registros sin clasificar")

                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Error al procesar: {e}")
                    import traceback

                    st.code(traceback.format_exc())

        except Exception as e:
            st.error(f"❌ Error al leer el archivo: {e}")
            import traceback

            st.code(traceback.format_exc())

# --- Columna 2: Facturación ---
with col2:
    st.subheader("Archivo 2: Facturación")

    file2 = st.file_uploader("Sube el archivo de facturación", type=["xlsx", "xls", "csv"], key="file2")

    if file2 is not None:
        try:
            # -------- LECTURA ROBUSTA DEL ARCHIVO --------
            if file2.name.endswith('.csv'):
                df_fact_temp = pd.read_csv(file2, header=None)
            else:
                df_fact_temp = pd.read_excel(file2, header=None)

            # Busca la fila que contiene 'NRO_LEGALIACION' para identificar los encabezados
            header_row = None
            for i, row in df_fact_temp.iterrows():
                if row.astype(str).str.strip().str.upper().str.startswith("NRO_LEGALIACION").any():
                    header_row = i
                    break

            if header_row is None:
                st.error("❌ No se encontró la fila de columnas que contiene 'NRO_LEGALIACION'")
            else:
                # Relee el archivo usando la fila identificada como encabezado
                if file2.name.endswith('.csv'):
                    df_fact = pd.read_csv(file2, header=header_row)
                else:
                    df_fact = pd.read_excel(file2, header=header_row)

                # Limpia los nombres de las columnas
                df_fact.columns = (
                    df_fact.columns
                    .astype(str)
                    .str.strip()
                    .str.replace('\n', ' ')
                )
                st.success(f"✅ Archivo cargado: {len(df_fact):,} filas")
                st.info(f"📋 Encabezados detectados en fila: {header_row + 1}")

                # Guardar temporalmente en session_state
                st.session_state.temp_df_fact = df_fact

        except Exception as e:
            st.error(f"❌ Error al leer archivo: {e}")

# --- Columna 3: Facturación Electrónica ---
with col3:
    st.subheader("Archivo 3: Facturación electrónica")

    file3 = st.file_uploader("Sube el archivo de Facturación electrónica", type=["xlsx", "xls", "csv"], key="file3")

    if file3 is not None:
        try:
            # -------- LECTURA ROBUSTA DEL ARCHIVO --------
            if file3.name.endswith('.csv'):
                df_fact_elec_temp = pd.read_csv(file3, header=None)
            else:
                df_fact_elec_temp = pd.read_excel(file3, header=None)

            # Busca la fila que contiene 'IDENTIFICACION' para identificar los encabezados
            header_row = None
            for i, row in df_fact_elec_temp.iterrows():
                if row.astype(str).str.strip().str.upper().str.startswith("IDENTIFICACION").any():
                    header_row = i
                    break

            if header_row is None:
                st.error("❌ No se encontró la fila de columnas que contiene 'IDENTIFICACION'")
            else:
                # Relee el archivo usando la fila identificada como encabezado
                if file3.name.endswith('.csv'):
                    df_fact_elec = pd.read_csv(file3, header=header_row)
                else:
                    df_fact_elec = pd.read_excel(file3, header=header_row)

                # Limpia los nombres de las columnas
                df_fact_elec.columns = (
                    df_fact_elec.columns
                    .astype(str)
                    .str.strip()
                    .str.replace('\n', ' ')
                )
                st.success(f"✅ Archivo cargado: {len(df_fact_elec):,} filas")
                st.info(f"📋 Encabezados detectados en fila: {header_row + 1}")

                # Guardar temporalmente en session_state
                st.session_state.temp_df_fact_elec = df_fact_elec

        except Exception as e:
            st.error(f"❌ Error al leer archivo: {e}")

st.markdown("---")

# --- SECCIÓN DE GUARDADO PARA FACTURACIÓN ---
# Solo se muestra cuando ambos archivos están cargados
if 'temp_df_fact' in st.session_state and 'temp_df_fact_elec' in st.session_state:
    st.success("✅ Ambos archivos de facturación están listos para guardar")

    col_resumen1, col_resumen2, col_resumen3 = st.columns([1, 1, 1])

    with col_resumen1:
        st.metric("Facturación", f"{len(st.session_state.temp_df_fact):,} filas")

    with col_resumen2:
        st.metric("Facturación Electrónica", f"{len(st.session_state.temp_df_fact_elec):,} filas")

    with col_resumen3:
        if st.button("💾 Guardar Ambos Archivos de Facturación", use_container_width=True, type="primary"):
            try:
                # Guardar Facturación
                st.session_state.df_facturacion = st.session_state.temp_df_fact
                save_local(st.session_state.temp_df_fact, FILES["Facturacion"])

                # Guardar Facturación Electrónica
                st.session_state.df_fact_elec = st.session_state.temp_df_fact_elec
                save_local(st.session_state.temp_df_fact_elec, os.path.join(PERSISTED_DATA_DIR, "df_fact_elec.parquet"))

                # Limpiar temporales
                del st.session_state.temp_df_fact
                del st.session_state.temp_df_fact_elec

                st.success("""✅ Archivos guardados exitosamente:
- Facturación
- Facturación Electrónica
                """)
                st.rerun()

            except Exception as e:
                st.error(f"❌ Error al guardar: {e}")

elif 'temp_df_fact' in st.session_state or 'temp_df_fact_elec' in st.session_state:
    st.info("ℹ️ Sube ambos archivos de facturación para poder guardarlos")

    if 'temp_df_fact' in st.session_state:
        st.write("✅ Facturación cargado")
    else:
        st.write("⏳ Falta Facturación")

    if 'temp_df_fact_elec' in st.session_state:
        st.write("✅ Facturación Electrónica cargado")
    else:
        st.write("⏳ Falta Facturación Electrónica")

st.markdown("---")

# --- BARRA LATERAL (FILTROS GLOBALES) ---
st.sidebar.header("📊 Estado de Datos")

# Muestra el estado de carga de cada dataset en la barra lateral
for nombre, key in [("PPL", "df_ppl"), ("Convenios", "df_convenios"),
                    ("RIPS", "df_rips"), ("Facturación", "df_facturacion")]:
    df = st.session_state.get(key)
    if df is not None and not df.empty:
        st.sidebar.success(f"✅ {nombre}: {len(df):,} registros")
    else:
        st.sidebar.warning(f"⚠️ {nombre}: Sin datos")

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Filtros de Análisis")

# --- Filtro de Tipo de Legalización ---
# Permite seleccionar entre PPL y Convenios
tipo_legalizacion = st.sidebar.multiselect(
    "Tipo de Legalización",
    ["PPL", "Convenios"],
    default=["PPL", "Convenios"]
)

# --- Filtro de Usuario/Facturador ---
# Recolecta todos los usuarios únicos de todos los datasets cargados
facturadores_total = []
for df_name in ['df_ppl', 'df_convenios', 'df_rips', 'df_facturacion']:
    df_temp = st.session_state.get(df_name)
    if df_temp is not None and not df_temp.empty:
        col_u = 'USUARIO' if 'USUARIO' in df_temp.columns else 'Usuario'
        if col_u in df_temp.columns:
            facturadores_total.extend(df_temp[col_u].dropna().unique())

sel_usuarios = st.sidebar.multiselect(
    "Seleccionar Facturador",
    ['Todos'] + sorted(list(set(facturadores_total))),
    default=['Todos']
)

# --- Filtro de Rango de Fechas ---
# Por defecto muestra los últimos 30 días
start_date, end_date = st.sidebar.date_input(
    "Rango de fechas",
    [datetime.date.today() - datetime.timedelta(days=30), datetime.date.today()]
)

# --- Botón para limpiar todos los datos ---
# Elimina los archivos Parquet y reinicia el session_state
if st.sidebar.button("🗑️ Limpiar todos los datos", use_container_width=True):
    for key in FILES.keys():
        filepath = FILES[key]
        if os.path.exists(filepath):
            os.remove(filepath)
        st.session_state[f"df_{key.lower()}"] = None
    st.sidebar.success("✅ Datos limpiados")
    st.rerun()


# --- FUNCIÓN MAESTRA DE VISUALIZACIÓN ---
def procesar_y_graficar(df, titulo, es_legalizacion=False):
    """
    Procesa y visualiza los datos de productividad según los filtros activos.

    Genera dos tipos de visualizaciones según el estado de los filtros:
    1. Modo General (sin filtro de usuario): Gráfico de barras horizontal con distribución porcentual
    2. Modo Comparativo (con filtro de usuario): Gráfico de líneas temporal + tabla resumen

    Args:
        df (pd.DataFrame): DataFrame con los datos a visualizar.
        titulo (str): Título descriptivo de la sección (ej: "Legalizaciones", "Facturación").
        es_legalizacion (bool): True si los datos corresponden a legalizaciones,
                               lo que activa el filtro por tipo (PPL/Convenios).

    Returns:
        None: Genera visualizaciones directamente en Streamlit.

    Comportamiento:
        - Normaliza automáticamente las columnas de Usuario y Fecha
        - Aplica filtros de tipo, fecha y usuario según configuración
        - Muestra advertencias si no hay datos después de filtrar
        - Genera métricas, gráficos y tablas adaptados al contexto
    """
    if df is None or df.empty:
        st.info(f"No hay datos cargados para la sección de {titulo}")
        return

    # Normalización de columnas de Usuario y Fecha
    # Busca variaciones comunes de los nombres de columnas
    col_u = 'USUARIO' if 'USUARIO' in df.columns else 'Usuario'
    col_f = next((c for c in ['FECHA_REAL', 'FECHA_FACTURA', 'FECHA', 'Fecha'] if c in df.columns), None)

    # Filtro por tipo (solo aplica para legalizaciones)
    if es_legalizacion and 'Tipo_Leg' in df.columns:
        df = df[df['Tipo_Leg'].isin(tipo_legalizacion)]

    # Filtro de Fecha
    # Convierte la columna de fecha a datetime y filtra por el rango seleccionado
    if col_f:
        df[col_f] = pd.to_datetime(df[col_f], errors='coerce')
        df = df.dropna(subset=[col_f])
        df = df[(df[col_f].dt.date >= start_date) & (df[col_f].dt.date <= end_date)]

    # Determina si hay un filtro activo de usuario
    es_filtro_activo = 'Todos' not in sel_usuarios and len(sel_usuarios) > 0
    if es_filtro_activo:
        df = df[df[col_u].isin(sel_usuarios)]

    if df.empty:
        st.warning(f"No hay datos para mostrar en {titulo} con los filtros actuales.")
        return

    # Muestra métrica de total de registros
    st.metric(f"Total Registros ({titulo})", f"{len(df):,}")

    if not es_filtro_activo:
        # --- MODO GENERAL: GRÁFICO DE BARRAS + TABLA % ---
        # Muestra la productividad general de todos los usuarios
        st.subheader(f"Productividad General: {titulo}")
        fig, ax = plt.subplots(figsize=(10, 6))
        counts = df[col_u].value_counts().reset_index()
        counts.columns = ['Usuario', 'Conteo']

        # Crea gráfico de barras horizontal con etiquetas de valor
        sns.barplot(data=counts, y='Usuario', x='Conteo', palette='viridis', ax=ax)
        for i, v in enumerate(counts['Conteo']):
            ax.text(v + 0.1, i, str(int(v)), color='black', va='center', fontweight='bold')

        ax.set_xlabel("Cantidad Total")
        st.pyplot(fig)

        # Muestra tabla con distribución porcentual
        st.subheader(f"Distribución Porcentual - {titulo}")
        counts['%'] = (counts['Conteo'] / counts['Conteo'].sum() * 100).round(2)
        st.table(counts.style.format({'%': '{:.2f}%'}))

    else:
        # --- MODO COMPARATIVO: LINEPLOT + TABLA RESUMEN ---
        # Compara la evolución temporal de los usuarios seleccionados
        st.subheader(f"Comparativa de Evolución Temporal ({titulo})")
        if col_f:
            df['Dia_Evolucion'] = df[col_f].dt.date
            evol = df.groupby(['Dia_Evolucion', col_u]).size().reset_index(name='Cuenta')

            # Crea gráfico de líneas mostrando evolución día a día
            fig2, ax2 = plt.subplots(figsize=(12, 5))
            sns.lineplot(data=evol, x='Dia_Evolucion', y='Cuenta', hue=col_u, marker='o', ax=ax2)
            ax2.grid(True, linestyle='--', alpha=0.6)
            plt.xticks(rotation=45)
            ax2.set_ylabel("Productividad Diaria")
            st.pyplot(fig2)

        # Muestra tabla resumen de usuarios seleccionados
        st.subheader(f"Resumen de Usuarios Seleccionados")
        resumen_sel = df[col_u].value_counts().reset_index()
        resumen_sel.columns = ['Usuario', 'Total Realizado']
        st.table(resumen_sel)


# --- TABS (PÁGINAS) ---
# Organiza el dashboard en tres pestañas principales
tab_leg, tab_rips, tab_fact = st.tabs(["📁 Legalizaciones", "📄 RIPS", "💰 Facturación"])

# --- Pestaña de Legalizaciones ---
# Combina datos de PPL y Convenios para análisis conjunto
with tab_leg:
    list_leg = []
    if st.session_state.df_ppl is not None and not st.session_state.df_ppl.empty:
        d_p = st.session_state.df_ppl.copy()
        d_p['Tipo_Leg'] = 'PPL'
        list_leg.append(d_p)
    if st.session_state.df_convenios is not None and not st.session_state.df_convenios.empty:
        d_c = st.session_state.df_convenios.copy()
        d_c['Tipo_Leg'] = 'Convenios'
        list_leg.append(d_c)

    if list_leg:
        df_leg_total = pd.concat(list_leg, ignore_index=True)

        procesar_y_graficar(df_leg_total, "Legalizaciones", es_legalizacion=True)

    else:
        st.info("Carga el archivo de legalizaciones para visualizar los datos.")

# --- Pestaña de RIPS ---
with tab_rips:
    procesar_y_graficar(st.session_state.df_rips, "RIPS")

# --- Pestaña de Facturación ---
# Incluye la integración con facturación electrónica y opción de descarga
with tab_fact:
    # Enriquece los datos de facturación con información de usuario desde facturación electrónica
    df_fact_final = buscar_usuario_en_fact_electronica(
        st.session_state.get('df_facturacion'),
        st.session_state.get('df_fact_elec')
    )

    st.subheader("📥 Descarga de Facturación con Usuario")

    if df_fact_final is None or df_fact_final.empty:
        st.warning("⚠️ No hay datos de facturación para mostrar")
    else:
        st.write("Total filas:", len(df_fact_final))

        # Genera archivo Excel en memoria para descarga
        buffer = BytesIO()
        df_fact_final.to_excel(buffer, index=False)
        buffer.seek(0)

        st.download_button(
            "⬇️ Descargar Excel – Facturación con Usuario",
            buffer,
            "facturacion_con_usuario.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    procesar_y_graficar(df_fact_final, "Facturación")