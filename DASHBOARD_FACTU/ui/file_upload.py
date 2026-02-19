"""
Sección de carga de archivos
=============================
Interfaz para cargar archivos y procesar datos.
"""

import streamlit as st
from config.settings import COLUMN_MARKERS
from data.loaders import load_uploaded_file, save_all_data, load_facturadores_master
from service.legalizaciones_service import procesar_legalizaciones
from service.rips_service import procesar_rips
from service.facturador_service import procesar_facturacion
from data.processors import process_facturacion_electronica
from ui.components import show_success_message, show_error_message, show_warning_message


def render_file_upload_section():
    """Renderiza la sección completa de carga de archivos."""
    st.header("📂 Cargar Archivos")

    with st.expander("📁 Cargar Legalizaciones", expanded=False):
        render_legalizaciones_upload()

    with st.expander("📄 Cargar RIPS", expanded=False):
        render_rips_upload()

    with st.expander("💰 Cargar Facturación", expanded=False):
        render_facturacion_upload()

    with st.expander("🧾 Cargar Facturación Electrónica", expanded=False):
        render_facturacion_electronica_upload()

    with st.expander("👥 Actualizar Facturadores", expanded=False):
        render_facturadores_reload()

    with st.expander("🗑️ Limpiar Datos", expanded=False):
        render_clear_data_section()


def render_clear_data_section():
    """Renderiza la sección para limpiar datos cargados."""
    st.warning("⚠️ Esta acción eliminará los datos cargados de forma permanente.")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🗑️ Limpiar Legalizaciones", key="btn_clear_leg", use_container_width=True):
            clear_data_type(["df_ppl", "df_convenios"], ["ppl", "convenios"], "Legalizaciones")

        if st.button("🗑️ Limpiar RIPS", key="btn_clear_rips", use_container_width=True):
            clear_data_type(["df_rips"], ["rips"], "RIPS")

    with col2:
        if st.button("🗑️ Limpiar Facturación", key="btn_clear_fact", use_container_width=True):
            clear_data_type(["df_facturacion"], ["facturacion"], "Facturación")

        if st.button("🗑️ Limpiar Fact. Electrónica", key="btn_clear_fact_elec", use_container_width=True):
            clear_data_type(["df_facturacion_electronica"], ["facturacion_electronica"], "Facturación Electrónica")

    st.divider()

    if st.button("🗑️ LIMPIAR TODOS LOS DATOS", key="btn_clear_all", type="primary", use_container_width=True):
        clear_all_data()


def clear_data_type(session_keys, file_keys, nombre):
    """Limpia un tipo específico de datos."""
    import os
    from config.settings import FILES

    # Limpiar session_state
    for key in session_keys:
        if key in st.session_state:
            st.session_state[key] = None

    # Eliminar archivos parquet
    for file_key in file_keys:
        file_key_map = {
            "ppl": "PPL",
            "convenios": "Convenios",
            "rips": "RIPS",
            "facturacion": "Facturacion",
            "facturacion_electronica": "FacturacionElectronica"
        }
        mapped_key = file_key_map.get(file_key, file_key)
        if mapped_key in FILES and os.path.exists(FILES[mapped_key]):
            try:
                os.remove(FILES[mapped_key])
            except Exception as e:
                show_error_message(f"Error al eliminar archivo: {e}")
                return

    show_success_message(f"{nombre} limpiados correctamente.")
    st.rerun()


def clear_all_data():
    """Limpia todos los datos cargados."""
    import os
    from config.settings import FILES

    # Limpiar session_state
    keys_to_clear = ['df_ppl', 'df_convenios', 'df_rips', 'df_facturacion', 'df_facturacion_electronica', 'df_procesos']
    for key in keys_to_clear:
        if key in st.session_state:
            st.session_state[key] = None

    # Eliminar todos los archivos parquet (excepto facturadores)
    files_to_delete = ["PPL", "Convenios", "RIPS", "Facturacion", "FacturacionElectronica", "ArchivoProcesos"]
    for file_key in files_to_delete:
        if file_key in FILES and os.path.exists(FILES[file_key]):
            try:
                os.remove(FILES[file_key])
            except Exception as e:
                show_error_message(f"Error al eliminar {file_key}: {e}")
                return

    show_success_message("Todos los datos han sido limpiados correctamente.")
    st.rerun()


def render_legalizaciones_upload():
    """Renderiza el uploader de legalizaciones."""
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
                df = load_uploaded_file(uploaded_file, COLUMN_MARKERS["legalizaciones"])

                if df is None:
                    show_error_message("Error al cargar el archivo. No se encontró la columna marcadora 'ID_LEGALIZACION'.")
                    st.write("💡 Tip: Asegúrate de que tu archivo tenga una columna que comience con 'ID_LEGALIZACION'")
                    return

                st.success(f"✅ Paso 1 completado: {len(df):,} filas, {len(df.columns)} columnas")
                st.write("Primeras columnas:", list(df.columns[:10]))

                st.write("🔄 Paso 2: Validando estructura...")
                df_facturadores = st.session_state.get('df_facturadores')
                result = procesar_legalizaciones(df, df_facturadores)

                if result.get("error"):
                    show_error_message(f"Error en validación: {result['error']}")
                    st.write("Columnas disponibles:", list(df.columns))
                    return

                st.success("✅ Paso 2 completado: Validación exitosa")

                # Verificar que hay datos procesados
                df_ppl = result.get("df_ppl")
                df_convenios = result.get("df_convenios")

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
                st.session_state['df_ppl'] = df_ppl
                st.session_state['df_convenios'] = df_convenios

                save_all_data({
                    "ppl": df_ppl,
                    "convenios": df_convenios
                })

                show_success_message(f"✅ Legalizaciones procesadas: PPL={count_ppl:,}, Convenios={count_conv:,}")
                st.rerun()

            except Exception as e:
                show_error_message(f"Error inesperado: {e}")
                import traceback
                st.code(traceback.format_exc())


def render_rips_upload():
    """Renderiza el uploader de RIPS."""
    uploaded_file = st.file_uploader(
        "Selecciona archivo de RIPS",
        type=['csv', 'xlsx'],
        key="upload_rips"
    )

    if uploaded_file and st.button("Procesar RIPS", key="btn_process_rips"):
        with st.spinner("Procesando RIPS..."):
            try:
                df = load_uploaded_file(uploaded_file, COLUMN_MARKERS["rips"])

                if df is None:
                    show_error_message("Error al cargar el archivo. No se encontró la columna marcadora 'CÓDIGO'.")
                    return

                st.info(f"📋 Archivo cargado: {len(df):,} filas, {len(df.columns)} columnas")

                df_facturadores = st.session_state.get('df_facturadores')

                if df_facturadores is None or df_facturadores.empty:
                    show_warning_message("⚠️ No hay facturadores cargados. Los documentos no se convertirán a nombres.")
                else:
                    st.info(f"✅ Facturadores disponibles: {len(df_facturadores):,} registros")

                result = procesar_rips(df, df_facturadores)

                if result.get("error"):
                    show_error_message(result["error"])
                    return

                df_rips = result.get("df_rips")
                count_rips = len(df_rips) if df_rips is not None and not df_rips.empty else 0

                if count_rips == 0:
                    show_warning_message("No se encontraron registros después del procesamiento. Verifica que el archivo tenga registros con estado 'COMPLETO'.")
                    return

                # Mostrar muestra de la columna USUARIO FACTURÓ para verificar el cruce
                if 'USUARIO FACTURÓ' in df_rips.columns:
                    st.info(f"📊 Muestra de usuarios: {df_rips['USUARIO FACTURÓ'].unique()[:5].tolist()}")

                st.session_state['df_rips'] = df_rips
                save_all_data({"rips": df_rips})

                show_success_message(f"RIPS procesados: {count_rips:,} registros.")
                st.rerun()

            except Exception as e:
                show_error_message(f"Error inesperado: {e}")
                import traceback
                st.code(traceback.format_exc())


def render_facturacion_upload():
    """Renderiza el uploader de facturación."""
    uploaded_file = st.file_uploader(
        "Selecciona archivo de facturación",
        type=['csv', 'xlsx'],
        key="upload_facturacion"
    )

    if uploaded_file and st.button("Procesar Facturación", key="btn_process_fact"):
        with st.spinner("Procesando facturación..."):
            try:
                df = load_uploaded_file(uploaded_file, COLUMN_MARKERS["facturacion"])

                if df is None:
                    show_error_message("Error al cargar el archivo. No se encontró la columna marcadora 'NRO_LEGALIACION'.")
                    return

                st.info(f"📋 Archivo cargado: {len(df):,} filas, {len(df.columns)} columnas")

                df_facturadores = st.session_state.get('df_facturadores')
                result = procesar_facturacion(df, df_facturadores)

                if result.get("error"):
                    show_error_message(result["error"])
                    return

                df_facturacion = result.get("df_facturacion")
                count_fact = len(df_facturacion) if df_facturacion is not None and not df_facturacion.empty else 0

                if count_fact == 0:
                    show_warning_message("No se encontraron registros después del procesamiento.")
                    return

                st.session_state['df_facturacion'] = df_facturacion
                save_all_data({"facturacion": df_facturacion})

                show_success_message(f"Facturación procesada: {count_fact:,} registros.")
                st.rerun()

            except Exception as e:
                show_error_message(f"Error inesperado: {e}")
                import traceback
                st.code(traceback.format_exc())


def render_facturacion_electronica_upload():
    """Renderiza el uploader de facturación electrónica."""
    uploaded_file = st.file_uploader(
        "Selecciona archivo de facturación electrónica",
        type=['csv', 'xlsx'],
        key="upload_fact_elec"
    )

    if uploaded_file and st.button("Procesar Facturación Electrónica", key="btn_process_fact_elec"):
        with st.spinner("Procesando facturación electrónica..."):
            try:
                df = load_uploaded_file(uploaded_file, COLUMN_MARKERS["facturacion_electronica"])

                if df is None:
                    show_error_message("Error al cargar el archivo. No se encontró la columna marcadora 'IDENTIFICACION'.")
                    return

                st.info(f"📋 Archivo cargado: {len(df):,} filas, {len(df.columns)} columnas")

                df_proc = process_facturacion_electronica(df)
                count_fact_elec = len(df_proc) if df_proc is not None and not df_proc.empty else 0

                if count_fact_elec == 0:
                    show_warning_message("No se encontraron registros después del procesamiento. Verifica que el archivo tenga registros con estado 'ACTIVO'.")
                    return

                st.session_state['df_facturacion_electronica'] = df_proc
                save_all_data({"facturacion_electronica": df_proc})

                show_success_message(f"Facturación electrónica procesada: {count_fact_elec:,} registros.")
                st.rerun()

            except Exception as e:
                show_error_message(f"Error inesperado: {e}")
                import traceback
                st.code(traceback.format_exc())


def render_facturadores_reload():
    """Renderiza el botón para recargar facturadores."""
    df_facturadores = st.session_state.get('df_facturadores')

    if df_facturadores is not None and not df_facturadores.empty:
        st.success(f"✅ Facturadores cargados: {len(df_facturadores):,} registros")
        st.info(f"📋 Columnas disponibles: {', '.join(df_facturadores.columns.tolist())}")

        with st.expander("👀 Ver muestra de datos"):
            st.dataframe(df_facturadores.head(10))
    else:
        st.warning("⚠️ No hay facturadores cargados")

    st.info("El archivo de facturadores se carga automáticamente desde `FACTURADORES.xlsx`.")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔄 Recargar Facturadores", key="btn_reload_fact", use_container_width=True):
            with st.spinner("Recargando facturadores..."):
                df_facturadores = load_facturadores_master()

                if df_facturadores is None:
                    show_error_message("No se pudo cargar el archivo de facturadores.")
                    return

                st.session_state['df_facturadores'] = df_facturadores
                save_all_data({"facturadores": df_facturadores})

                show_success_message("Facturadores recargados correctamente.")
                st.rerun()

    with col2:
        if st.button("🔄 Recruzar RIPS", key="btn_recruzar_rips", use_container_width=True):
            with st.spinner("Recruzando RIPS con facturadores..."):
                df_rips = st.session_state.get('df_rips')
                df_facturadores = st.session_state.get('df_facturadores')

                if df_rips is None or df_rips.empty:
                    show_error_message("No hay datos de RIPS cargados.")
                    return

                if df_facturadores is None or df_facturadores.empty:
                    show_error_message("No hay facturadores cargados.")
                    return

                from service.rips_service import cruzar_documento_a_nombre
                from data.validators import find_column_variant
                from config.settings import COLUMN_NAMES

                # Buscar columna de usuario
                usuario_col = find_column_variant(df_rips, COLUMN_NAMES["usuario"])

                if usuario_col is None:
                    show_error_message("No se encontró columna de usuario en RIPS.")
                    return

                # Contar documentos numéricos ANTES del cruce
                docs_antes = df_rips[usuario_col].astype(str).apply(lambda x: x.isnumeric()).sum()

                # Aplicar cruce
                df_rips_cruzado = cruzar_documento_a_nombre(df_rips, df_facturadores)

                # Contar documentos numéricos DESPUÉS del cruce
                docs_despues = df_rips_cruzado[usuario_col].astype(str).apply(lambda x: x.isnumeric()).sum()
                docs_convertidos = docs_antes - docs_despues

                # Guardar
                st.session_state['df_rips'] = df_rips_cruzado
                save_all_data({"rips": df_rips_cruzado})

                if docs_convertidos > 0:
                    show_success_message(f"✅ RIPS recruzados: {docs_convertidos:,} documentos convertidos a nombres.")
                else:
                    show_warning_message(f"⚠️ No se convirtieron documentos. {docs_despues:,} documentos no están en el maestro de facturadores.")

                st.rerun()
