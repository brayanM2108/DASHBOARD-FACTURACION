"""
File Upload Section
=============================
Interface for uploading files and processing data.
"""

import streamlit as st

from config.settings import COLUMN_MARKERS, COLUMN_NAMES
from data.loaders import (
    load_billers_master_cached,
    load_uploaded_dataframe,
    save_all_persisted_frames,
)
from data.processors import process_electronic_billing_data
from data.validators import find_first_column_variant
from service.legalizations_service import process_legalizations
from service.rips_service import map_document_to_name, process_rips
from ui.components import show_error_message, show_success_message, show_warning_message


def _clear_streamlit_caches():
    """Invalidate Streamlit caches after data mutations."""
    st.cache_data.clear()


def render_file_upload_section():
    """Render the entire file upload section."""
    st.header("📂 Cargar Archivos")

    with st.expander("📁 Cargar Legalizaciones", expanded=False):
        render_legalizaciones_upload()

    with st.expander("🧾 Cargar Facturación Electrónica", expanded=False):
        render_facturacion_electronica_upload()

    with st.expander("👥 Actualizar Facturadores", expanded=False):
        render_facturadores_reload()

    with st.expander("🗑️ Limpiar Datos", expanded=False):
        render_clear_data_section()


def render_clear_data_section():
    """Render the section to clear loaded data."""
    st.warning("⚠️ Esta acción eliminará los datos cargados de forma permanente.")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🗑️ Limpiar Legalizaciones", key="btn_clear_leg", width="stretch"):
            clear_data_type(
                ["ppl_legalizations_df", "agreement_legalizations_df"],
                ["PPL", "Convenios"],
                "Legalizaciones",
            )

        if st.button("🗑️ Limpiar RIPS", key="btn_clear_rips", width="stretch"):
            clear_data_type(["rips_df"], ["RIPS"], "RIPS")

    with col2:
        if st.button("🗑️ Limpiar Facturación", key="btn_clear_fact", width="stretch"):
            clear_data_type(["billing_df"], ["Facturacion"], "Facturación")

        if st.button("🗑️ Limpiar Fact. Electrónica", key="btn_clear_fact_elec", width = "stretch"):
            clear_data_type(["electronic_billing_df"], ["FacturacionElectronica"], "Facturación Electrónica")

    st.divider()

    if st.button("🗑️ LIMPIAR TODOS LOS DATOS", key="btn_clear_all", type="primary", width="stretch"):
        clear_all_data()


def clear_data_type(session_keys, file_keys, nombre):

    """Clean a specific type of data."""

    import os
    from config.settings import FILES

    # Limpiar session_state
    for key in session_keys:
        if key in st.session_state:
            st.session_state[key] = None

    # Eliminar archivos parquet
    for file_key in file_keys:
        if file_key in FILES and os.path.exists(FILES[file_key]):
            try:
                os.remove(FILES[file_key])
            except Exception as e:
                show_error_message(f"Error al eliminar archivo: {e}")
                return

    _clear_streamlit_caches()
    show_success_message(f"{nombre} limpiados correctamente.")
    st.rerun()


def clear_all_data():
    """Clear all uploaded data."""
    import os
    from config.settings import FILES

    # Limpiar session_state
    keys_to_clear = [
        'ppl_legalizations_df',
        'agreement_legalizations_df',
        'rips_df',
        'billing_df',
        'billers_df',
        'electronic_billing_df',
        'administrative_processes_df',
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            st.session_state[key] = None

    files_to_delete = ["PPL", "Convenios", "RIPS", "Facturacion", "FacturacionElectronica", "ArchivoProcesos"]
    for file_key in files_to_delete:
        if file_key in FILES and os.path.exists(FILES[file_key]):
            try:
                os.remove(FILES[file_key])
            except Exception as e:
                show_error_message(f"Error al eliminar {file_key}: {e}")
                return

    _clear_streamlit_caches()
    show_success_message("Todos los datos han sido limpiados correctamente.")
    st.rerun()


def render_legalizaciones_upload():
    """Render the legalization uploader"""
    uploaded_file = st.file_uploader(
        "Selecciona archivo de legalizaciones",
        type=['csv', 'xlsx'],
        key="upload_legalizaciones"
    )

    if uploaded_file:
        st.write(f"📁 Archivo seleccionado: {uploaded_file.name}")

    if uploaded_file and st.button("Procesar Legalizaciones", key="btn_process_leg"):
        with st.spinner("Procesando legalizaciones..."):
            try:
                st.write("🔄 Paso 1: Cargando archivo...")
                df = load_uploaded_dataframe(uploaded_file, COLUMN_MARKERS["legalizaciones"])

                if df is None:
                    show_error_message("Error al cargar el archivo. No se encontró la columna marcadora 'ID_LEGALIZACION'.")
                    st.write("💡 Tip: Asegúrate de que tu archivo tenga una columna que comience con 'ID_LEGALIZACION'")
                    return

                st.success(f"✅ Paso 1 completado: {len(df):,} filas, {len(df.columns)} columnas")
                st.write("Primeras columnas:", list(df.columns[:10]))

                st.write("🔄 Paso 2: Validando estructura...")
                df_facturadores = st.session_state.get('billers_df')
                result = process_legalizations(df, df_facturadores)

                if result.get("error"):
                    show_error_message(f"Error en validación: {result['error']}")
                    st.write("Columnas disponibles:", list(df.columns))
                    return

                st.success("✅ Paso 2 completado: Validación exitosa")

                df_ppl = result.get("ppl_df")
                df_convenios = result.get("agreements_df")

                count_ppl = len(df_ppl) if df_ppl is not None and not df_ppl.empty else 0
                count_conv = len(df_convenios) if df_convenios is not None and not df_convenios.empty else 0

                st.write(f"📊 Resultados: PPL={count_ppl}, Convenios={count_conv}")

                if count_ppl == 0 and count_conv == 0:
                    show_warning_message("No se encontraron registros después del procesamiento.")
                    st.write("Verifica que:")
                    st.write("- El archivo tenga registros con ESTADO = 'ACTIVA' o 'Activa'")
                    st.write("- El archivo tenga la columna CONVENIO")
                    if 'ESTADO' in df.columns:
                        st.write("Valores únicos de ESTADO:", df['ESTADO'].unique().tolist()[:10])
                    return

                st.write("🔄 Paso 3: Guardando datos...")
                st.session_state['ppl_legalizations_df'] = df_ppl
                st.session_state['agreement_legalizations_df'] = df_convenios

                save_all_persisted_frames({
                    "ppl_legalizations": df_ppl,
                    "agreement_legalizations": df_convenios,
                })
                _clear_streamlit_caches()

                show_success_message(f"✅ Legalizaciones procesadas: PPL={count_ppl:,}, Convenios={count_conv:,}")
                st.rerun()

            except Exception as e:
                show_error_message(f"Error inesperado: {e}")
                import traceback
                st.code(traceback.format_exc())

"""
def render_rips_upload():
#    Render the RIPS uploader
    uploaded_file = st.file_uploader(
        "Selecciona archivo de RIPS",
        type=['csv', 'xlsx'],
        key="upload_rips"
    )

    if uploaded_file and st.button("Procesar RIPS", key="btn_process_rips"):
        with st.spinner("Procesando RIPS..."):
            try:
                df = load_uploaded_dataframe(uploaded_file, COLUMN_MARKERS["rips"])

                if df is None:
                    show_error_message("Error al cargar el archivo. No se encontró la columna marcadora 'CÓDIGO'.")
                    return

                st.info(f"📋 Archivo cargado: {len(df):,} filas, {len(df.columns)} columnas")

                df_facturadores = st.session_state.get('billers_df')

                if df_facturadores is None or df_facturadores.empty:
                    show_warning_message("⚠️ No hay facturadores cargados. Los documentos no se convertirán a nombres.")
                else:
                    st.info(f"✅ Facturadores disponibles: {len(df_facturadores):,} registros")

                result = process_rips(df, df_facturadores)

                if result.get("error"):
                    show_error_message(result["error"])
                    return

                df_rips = result.get("rips_df")
                count_rips = len(df_rips) if df_rips is not None and not df_rips.empty else 0

                if count_rips == 0:
                    show_warning_message("No se encontraron registros después del procesamiento. Verifica que el archivo tenga registros con estado 'COMPLETO'.")
                    return

                if 'USUARIO FACTURÓ' in df_rips.columns:
                    st.info(f"📊 Muestra de usuarios: {df_rips['USUARIO FACTURÓ'].unique()[:5].tolist()}")

                st.session_state['rips_df'] = df_rips
                save_all_persisted_frames({"rips": df_rips})
                _clear_streamlit_caches()

                show_success_message(f"RIPS procesados: {count_rips:,} registros.")
                st.rerun()

            except Exception as e:
                show_error_message(f"Error inesperado: {e}")
                import traceback
                st.code(traceback.format_exc())
"""
                
def render_facturacion_electronica_upload():
    """Render the electronic invoicing uploader."""
    uploaded_file = st.file_uploader(
        "Selecciona archivo de facturación electrónica",
        type=['csv', 'xlsx'],
        key="upload_fact_elec"
    )

    if uploaded_file and st.button("Procesar Facturación Electrónica", key="btn_process_fact_elec"):
        with st.spinner("Procesando facturación electrónica..."):
            try:
                df = load_uploaded_dataframe(uploaded_file, COLUMN_MARKERS["facturacion_electronica"])

                if df is None:
                    show_error_message("Error al cargar el archivo. No se encontró la columna marcadora 'IDENTIFICACION'.")
                    return

                st.info(f"📋 Archivo cargado: {len(df):,} filas, {len(df.columns)} columnas")

                df_proc = process_electronic_billing_data(df)
                count_fact_elec = len(df_proc) if df_proc is not None and not df_proc.empty else 0

                if count_fact_elec == 0:
                    show_warning_message("No se encontraron registros después del procesamiento. Verifica que el archivo tenga registros con estado 'ACTIVO'.")
                    return

                st.session_state['electronic_billing_df'] = df_proc
                save_all_persisted_frames({"electronic_billing": df_proc})
                _clear_streamlit_caches()

                show_success_message(f"Facturación electrónica procesada: {count_fact_elec:,} registros.")
                st.rerun()

            except Exception as e:
                show_error_message(f"Error inesperado: {e}")
                import traceback
                st.code(traceback.format_exc())


def render_facturadores_reload():
    """Render the button to recharge billing devices."""
    df_facturadores = st.session_state.get('billers_df')

    st.info("El archivo de facturadores se carga automáticamente desde `FACTURADORES.xlsx`.")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔄 Recargar Facturadores", key="btn_reload_fact", width="stretch"):
            with st.spinner("Recargando facturadores..."):
                df_facturadores = load_billers_master_cached()

                if df_facturadores is None:
                    show_error_message("No se pudo cargar el archivo de facturadores.")
                    return

                st.session_state['billers_df'] = df_facturadores
                save_all_persisted_frames({"billers": df_facturadores})
                _clear_streamlit_caches()

                show_success_message("Facturadores recargados correctamente.")
                st.rerun()

    with col2:
        if st.button("🔄 Recruzar RIPS", key="btn_recruzar_rips", width="stretch"):
            with st.spinner("Recruzando RIPS con facturadores..."):
                df_rips = st.session_state.get('rips_df')
                df_facturadores = st.session_state.get('billers_df')

                if df_rips is None or df_rips.empty:
                    show_error_message("No hay datos de RIPS cargados.")
                    return

                if df_facturadores is None or df_facturadores.empty:
                    show_error_message("No hay facturadores cargados.")
                    return

                usuario_col = find_first_column_variant(df_rips, COLUMN_NAMES["usuario"])

                if usuario_col is None:
                    show_error_message("No se encontró columna de usuario en RIPS.")
                    return

                docs_antes = df_rips[usuario_col].astype(str).apply(lambda x: x.isnumeric()).sum()

                df_rips_cruzado = map_document_to_name(df_rips, df_facturadores)

                docs_despues = df_rips_cruzado[usuario_col].astype(str).apply(lambda x: x.isnumeric()).sum()
                docs_convertidos = docs_antes - docs_despues

                st.session_state['rips_df'] = df_rips_cruzado
                save_all_persisted_frames({"rips": df_rips_cruzado})
                _clear_streamlit_caches()

                if docs_convertidos > 0:
                    show_success_message(f"✅ RIPS recruzados: {docs_convertidos:,} documentos convertidos a nombres.")
                else:
                    show_warning_message(f"⚠️ No se convirtieron documentos. {docs_despues:,} documentos no están en el maestro de facturadores.")

                st.rerun()
