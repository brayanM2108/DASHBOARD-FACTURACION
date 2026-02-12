import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import datetime
import os

# --- Configuración de la página ---
st.set_page_config(page_title="Dashboard de Productividad", page_icon="📊", layout="wide")

PERSISTED_DATA_DIR = "persisted_data"
os.makedirs(PERSISTED_DATA_DIR, exist_ok=True)

FILES = {
    "PPL": os.path.join(PERSISTED_DATA_DIR, "df_ppl.parquet"),
    "Convenios": os.path.join(PERSISTED_DATA_DIR, "df_convenios.parquet"),
    "RIPS": os.path.join(PERSISTED_DATA_DIR, "df_rips.parquet"),
    "Facturacion": os.path.join(PERSISTED_DATA_DIR, "df_facturacion.parquet")
}


# --- FUNCIONES DE CARGA ---
def save_local(df, filepath):
    if df is not None and not df.empty:
        df.astype(str).to_parquet(filepath, index=False)


def load_local(filepath):
    return pd.read_parquet(filepath) if os.path.exists(filepath) else None


# --- INICIALIZACIÓN ---
if 'initialized' not in st.session_state:
    st.session_state.df_ppl = load_local(FILES["PPL"])
    st.session_state.df_convenios = load_local(FILES["Convenios"])
    st.session_state.df_rips = load_local(FILES["RIPS"])
    st.session_state.df_facturacion = load_local(FILES["Facturacion"])
    st.session_state.initialized = True

# --- CARGA DE ARCHIVOS ---
st.title("📥 Carga de Archivos")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Archivo 1: Legalizaciones (PPL + Convenios + RIPS)")

    file1 = st.file_uploader("Sube el archivo Excel/CSV", type=["xlsx", "xls", "csv"], key="file1")

    if file1 is not None:
        try:
            # Leer archivo
            # -------- LECTURA ROBUSTA DEL ARCHIVO --------
            if file1.name.endswith('.csv'):
                df_raw = pd.read_csv(file1, header=None)
            else:
                df_raw = pd.read_excel(file1, header=None)

            # Buscar la fila de encabezados (la que contiene ID_LEGALIZACION) por si hay algun encabezado o algo màs en la fila
            header_row = None
            for i, row in df_raw.iterrows():
                if row.astype(str).str.strip().str.upper().str.startswith("ID_LEGALIZACION").any():
                    header_row = i
                    break

            if header_row is None:
                st.error("❌ No se encontró la fila de columnas que contiene 'NRO_LEGALIZACION'")
                st.stop()

            # Releer usando ESA fila como encabezado
            if file1.name.endswith('.csv'):
                df_temp = pd.read_csv(file1, header=header_row)
            else:
                df_temp = pd.read_excel(file1, header=header_row)

            # Limpieza básica de columnas
            df_temp.columns = (
                df_temp.columns
                .astype(str)
                .str.strip()
                .str.replace('\n', ' ')
            )
            st.success(f"Encabezados detectados en fila: {header_row + 1}")
            st.write(df_temp.columns.tolist())

            # Botón para procesar
            if st.button("💾 Procesar y Guardar Legalizaciones", use_container_width=True):
                try:
                    # Verificar que existe la columna CONVENIO
                    if 'CONVENIO' not in df_temp.columns:
                        st.error("❌ No se encontró la columna 'CONVENIO' en el archivo")
                        st.stop()

                    # SEPARACIÓN AUTOMÁTICA:
                    # PPL = "Patrimonio Autonomo Fondo Atención Salud PPL 2024"
                    # Convenios = Todo lo demás
                    # RIPS = Por ahora vacío (agregar lógica si es necesario)

                    df_ppl = df_temp[df_temp['CONVENIO'] == 'Patrimonio Autonomo Fondo Atención Salud PPL 2024'].copy()
                    df_convenios = df_temp[
                        df_temp['CONVENIO'] != 'Patrimonio Autonomo Fondo Atención Salud PPL 2024'].copy()
                    df_rips = pd.DataFrame()  # Vacío por ahora

                    # Guardar en session_state
                    st.session_state.df_ppl = df_ppl if not df_ppl.empty else None
                    st.session_state.df_convenios = df_convenios if not df_convenios.empty else None
                    st.session_state.df_rips = df_rips if not df_rips.empty else None

                    # Guardar archivos locales
                    save_local(df_ppl, FILES["PPL"])
                    save_local(df_convenios, FILES["Convenios"])
                    save_local(df_rips, FILES["RIPS"])

                    # Mostrar resumen
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

with col2:
    st.subheader("Archivo 2: Facturación electronica")

    file3 = st.file_uploader("Sube el archivo de Facturación electronica", type=["xlsx", "xls", "csv"], key="file3")


st.markdown("---")


# --- BARRA LATERAL (FILTROS GLOBALES) ---
st.sidebar.header("📊 Estado de Datos")

# Mostrar estado de cada dataset
for nombre, key in [("PPL", "df_ppl"), ("Convenios", "df_convenios"),
                    ("RIPS", "df_rips"), ("Facturación", "df_facturacion")]:
    df = st.session_state.get(key)
    if df is not None and not df.empty:
        st.sidebar.success(f"✅ {nombre}: {len(df):,} registros")
    else:
        st.sidebar.warning(f"⚠️ {nombre}: Sin datos")

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Filtros de Análisis")

# Filtro de Tipo (Legalizaciones)
tipo_legalizacion = st.sidebar.multiselect(
    "Tipo de Legalización",
    ["PPL", "Convenios"],
    default=["PPL", "Convenios"]
)

# Recolectar facturadores de todas las fuentes
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

start_date, end_date = st.sidebar.date_input(
    "Rango de fechas",
    [datetime.date.today() - datetime.timedelta(days=30), datetime.date.today()]
)

# Botón para limpiar datos
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
    if df is None or df.empty:
        st.info(f"No hay datos cargados para la sección de {titulo}")
        return

    # Normalización de columnas de Usuario y Fecha
    col_u = 'USUARIO' if 'USUARIO' in df.columns else 'Usuario'
    col_f = next((c for c in ['FECHA_REAL', 'FECHA_FACTURA', 'FECHA', 'Fecha'] if c in df.columns), None)

    # Filtro por tipo (solo legalizaciones)
    if es_legalizacion and 'Tipo_Leg' in df.columns:
        df = df[df['Tipo_Leg'].isin(tipo_legalizacion)]

    # Filtro de Fecha
    if col_f:
        df[col_f] = pd.to_datetime(df[col_f], errors='coerce')
        df = df.dropna(subset=[col_f])
        df = df[(df[col_f].dt.date >= start_date) & (df[col_f].dt.date <= end_date)]

    # Determinar si el filtro de usuario está activo
    es_filtro_activo = 'Todos' not in sel_usuarios and len(sel_usuarios) > 0
    if es_filtro_activo:
        df = df[df[col_u].isin(sel_usuarios)]

    if df.empty:
        st.warning(f"No hay datos para mostrar en {titulo} con los filtros actuales.")
        return

    # Métricas superiores
    st.metric(f"Total Registros ({titulo})", f"{len(df):,}")

    if not es_filtro_activo:
        # --- MODO GENERAL: GRÁFICO DE BARRAS + TABLA % ---
        st.subheader(f"Productividad General: {titulo}")
        fig, ax = plt.subplots(figsize=(10, 6))
        counts = df[col_u].value_counts().reset_index()
        counts.columns = ['Usuario', 'Conteo']

        sns.barplot(data=counts, y='Usuario', x='Conteo', palette='viridis', ax=ax)
        for i, v in enumerate(counts['Conteo']):
            ax.text(v + 0.1, i, str(int(v)), color='black', va='center', fontweight='bold')

        ax.set_xlabel("Cantidad Total")
        st.pyplot(fig)

        st.subheader(f"Distribución Porcentual - {titulo}")
        counts['%'] = (counts['Conteo'] / counts['Conteo'].sum() * 100).round(2)
        st.table(counts.style.format({'%': '{:.2f}%'}))

    else:
        # --- MODO COMPARATIVO: LINEPLOT + TABLA RESUMEN ---
        st.subheader(f"Comparativa de Evolución Temporal ({titulo})")
        if col_f:
            df['Dia_Evolucion'] = df[col_f].dt.date
            evol = df.groupby(['Dia_Evolucion', col_u]).size().reset_index(name='Cuenta')

            fig2, ax2 = plt.subplots(figsize=(12, 5))
            sns.lineplot(data=evol, x='Dia_Evolucion', y='Cuenta', hue=col_u, marker='o', ax=ax2)
            ax2.grid(True, linestyle='--', alpha=0.6)
            plt.xticks(rotation=45)
            ax2.set_ylabel("Productividad Diaria")
            st.pyplot(fig2)

        st.subheader(f"Resumen de Usuarios Seleccionados")
        resumen_sel = df[col_u].value_counts().reset_index()
        resumen_sel.columns = ['Usuario', 'Total Realizado']
        st.table(resumen_sel)


# --- TABS (PÁGINAS) ---
tab_leg, tab_rips, tab_fact = st.tabs(["📁 Legalizaciones", "📄 RIPS", "💰 Facturación"])

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
        procesar_y_graficar(pd.concat(list_leg, ignore_index=True), "Legalizaciones", es_legalizacion=True)
    else:
        st.info("Carga el archivo de legalizaciones para visualizar los datos.")

with tab_rips:
    procesar_y_graficar(st.session_state.df_rips, "RIPS")

with tab_fact:
    procesar_y_graficar(st.session_state.df_facturacion, "Facturación")