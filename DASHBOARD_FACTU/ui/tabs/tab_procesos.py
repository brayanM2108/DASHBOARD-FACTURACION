import streamlit as st
import pandas as pd
import plotly.express as px
from data import save_all_data
from service.procesos_service import procesos_service
import re
from config.settings import PROCESOS_SHEET_URL
from ui.components import show_success_message, show_error_message, show_warning_message

def render_tab_procesos(filtros):
    """Renderiza el tab de procesos administrativos"""
    st.header("📊 Productividad de Procesos Administrativos")

    st.info("Sincroniza los datos para poder visualizar las métricas y gráficos relacionados.")

    if st.button("🔄 Sincronizar Desde Google Sheets", key="btn_sync_sheets", use_container_width=True):
            with st.spinner("Sincronizando datos desde Google Sheets..."):
                try:

                    # Extraer sheet_id y gid usando regex
                    match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', PROCESOS_SHEET_URL)
                    if not match:
                        show_error_message("❌ No se pudo extraer el ID del Google Sheet.")
                        st.code(f"URL: {PROCESOS_SHEET_URL}")
                        return

                    sheet_id = match.group(1)

                    # Extraer gid (por defecto 0)
                    gid = '0'
                    gid_match = re.search(r'[#&]gid=([0-9]+)', PROCESOS_SHEET_URL)
                    if gid_match:
                        gid = gid_match.group(1)

                    # Construir URL de exportación
                    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

                    st.write(f"🔍 Sheet ID: `{sheet_id}`")
                    st.write(f"🔍 GID: `{gid}`")

                    # Cargar datos
                    st.write("🔄 Cargando datos desde Google Sheets...")
                    df_procesos_raw = pd.read_csv(csv_url)

                    if df_procesos_raw.empty:
                        show_warning_message("⚠️ La hoja está vacía.")
                        return

                    st.success(f"📋 Datos cargados: {len(df_procesos_raw):,} filas, {len(df_procesos_raw.columns)} columnas")
                    st.write("Columnas originales:", list(df_procesos_raw.columns[:5]))

                    # Procesar datos
                    st.write("🔄 Procesando y normalizando datos...")
                    from data.processors import process_procesos
                    df_procesos = process_procesos(df_procesos_raw)

                    if df_procesos is None or df_procesos.empty:
                        show_warning_message("⚠️ No se pudieron procesar los datos.")
                        return

                    st.success(f"✅ Datos procesados: {len(df_procesos):,} registros válidos")
                    st.write("Columnas finales:", list(df_procesos.columns))
                    st.write("Vista previa:")
                    st.dataframe(df_procesos.head(3))

                    # Guardar en session state y persistir
                    st.session_state['df_procesos'] = df_procesos
                    save_all_data({"procesos": df_procesos})

                    show_success_message(f"✅ Sincronización exitosa: {len(df_procesos):,} registros.")
                    st.rerun()

                except Exception as e:
                    show_error_message(f"❌ Error al sincronizar: {str(e)}")
                    st.error("💡 **Posibles causas:**")
                    st.markdown("""
                    1. El Google Sheet **no está compartido públicamente**
                       - Abre el Google Sheet
                       - Click en "Compartir" → "Cambiar a cualquier persona con el enlace"
                       - Asegúrate que esté en modo "Lector"
                    2. La URL tiene comillas en el archivo `.env` (no debe tenerlas)
                    3. El ID de la hoja (gid) es incorrecto
                    """)

                    # Mostrar traceback completo
                    import traceback
                    with st.expander("🔍 Ver detalles técnicos"):
                        st.code(traceback.format_exc())
                return

    # Obtener datos desde session state
    df_procesos = st.session_state.get('df_procesos')

    if df_procesos is None or df_procesos.empty:
        st.info("⚠️ No hay datos de procesos cargados. Ve a 'Cargar Archivos' para sincronizar desde Google Sheets.")
        return

    # Validar que tenga las columnas requeridas
    columnas_requeridas = ['FECHA', 'NOMBRE', 'DOCUMENTO', 'PROCESO', 'CANTIDAD']
    columnas_faltantes = [col for col in columnas_requeridas if col not in df_procesos.columns]

    if columnas_faltantes:
        st.error(f"❌ Error: El archivo no tiene las columnas requeridas: {', '.join(columnas_faltantes)}")
        st.info("💡 Ve a 'Cargar Archivos' y sincroniza nuevamente desde Google Sheets.")

        with st.expander("🔍 Ver columnas disponibles"):
            st.write("Columnas actuales:", list(df_procesos.columns))
            st.dataframe(df_procesos.head(3))

        # Botón para limpiar datos incorrectos
        if st.button("🗑️ Limpiar datos y volver a sincronizar", key="btn_clear_procesos"):
            st.session_state['df_procesos'] = None
            import os
            from config.settings import FILES
            if os.path.exists(FILES['ArchivoProcesos']):
                os.remove(FILES['ArchivoProcesos'])
            st.success("✅ Datos limpiados. Ve a 'Cargar Archivos' para sincronizar nuevamente.")
            st.rerun()
        return

    service = procesos_service(df_procesos)

    # Filtros
    col1, col2 = st.columns(2)
    with col1:
        try:
            fecha_min = df_procesos['FECHA'].min()
            if pd.isna(fecha_min):
                fecha_min = pd.Timestamp.now()
        except:
            fecha_min = pd.Timestamp.now()
        fecha_inicio = st.date_input("Fecha inicio", value=fecha_min)

    with col2:
        try:
            fecha_max = df_procesos['FECHA'].max()
            if pd.isna(fecha_max):
                fecha_max = pd.Timestamp.now()
        except:
            fecha_max = pd.Timestamp.now()
        fecha_fin = st.date_input("Fecha fin", value=fecha_max)

    col3, col4 = st.columns(2)
    with col3:
        personas = ['Todos'] + sorted(df_procesos['NOMBRE'].unique().tolist())
        persona_sel = st.selectbox("Persona", personas)
    with col4:
        procesos = ['Todos'] + sorted(df_procesos['PROCESO'].unique().tolist())
        proceso_sel = st.selectbox("Proceso", procesos)

    # Aplicar filtros
    df_filtrado = service.obtener_datos_filtrados(
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        persona=persona_sel if persona_sel != 'Todos' else None,
        proceso=proceso_sel if proceso_sel != 'Todos' else None
    )

    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Registros", len(df_filtrado))
    with col2:
        st.metric("Total Cantidad", f"{df_filtrado['CANTIDAD'].sum():,.0f}")
    with col3:
        st.metric("Personas", df_filtrado['NOMBRE'].nunique())
    with col4:
        st.metric("Tipos de Procesos", df_filtrado['PROCESO'].nunique())

    # Gráficos
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Cantidad por Persona")
        resumen_persona = df_filtrado.groupby('NOMBRE')['CANTIDAD'].sum().reset_index()
        fig1 = px.bar(resumen_persona, x='NOMBRE', y='CANTIDAD',
                      color='CANTIDAD', color_continuous_scale='Blues')
        fig1.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        # Determinar qué mostrar en el gráfico circular según filtros
        if proceso_sel != 'Todos' and persona_sel == 'Todos':
            # Si hay proceso específico y todas las personas: mostrar distribución por persona
            st.subheader("Distribución por Persona")
            resumen_grafico = df_filtrado.groupby('NOMBRE')['CANTIDAD'].sum().reset_index()
            fig2 = px.pie(resumen_grafico, values='CANTIDAD', names='NOMBRE', hole=0.4)
        else:
            # En otros casos: mostrar distribución por proceso
            st.subheader("Cantidad por Proceso")
            resumen_proceso = df_filtrado.groupby('PROCESO')['CANTIDAD'].sum().reset_index()
            fig2 = px.pie(resumen_proceso, values='CANTIDAD', names='PROCESO', hole=0.4)

        st.plotly_chart(fig2, use_container_width=True)

    # Gráfico de tendencia temporal
    st.subheader("Tendencia Temporal")
    df_temporal = df_filtrado.groupby('FECHA')['CANTIDAD'].sum().reset_index()
    fig3 = px.line(df_temporal, x='FECHA', y='CANTIDAD', markers=True)
    st.plotly_chart(fig3, use_container_width=True)
