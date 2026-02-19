"""
Lógica de negocio - Procesos
===================================
Funciones específicas para el procesamiento y análisis de procesos.
"""
import pandas as pd

class procesos_service:
    def __init__(self, df_procesos: pd.DataFrame):
        self.df_procesos = df_procesos.copy()
        self._procesar_datos()

    def _procesar_datos(self):
        """Procesa y limpia los datos de procesos"""
        if 'FECHA' in self.df_procesos.columns:
            self.df_procesos['FECHA'] = pd.to_datetime(
                self.df_procesos['FECHA'],
                format='%d/%m/%Y',
                errors='coerce'
            )

        if 'CANTIDAD' in self.df_procesos.columns:
            self.df_procesos['CANTIDAD'] = pd.to_numeric(
                self.df_procesos['CANTIDAD'],
                errors='coerce'
            )

    def obtener_resumen_por_persona(self):
        """Obtiene resumen de procesos por persona"""
        return self.df_procesos.groupby('NOMBRE').agg({
            'CANTIDAD': 'sum',
            'PROCESO': 'count'
        }).reset_index().rename(columns={'PROCESO': 'TOTAL_PROCESOS'})

    def obtener_resumen_por_proceso(self):
        """Obtiene resumen por tipo de proceso"""
        return self.df_procesos.groupby('PROCESO').agg({
            'CANTIDAD': 'sum',
            'NOMBRE': 'count'
        }).reset_index().rename(columns={'NOMBRE': 'PERSONAS'})

    def obtener_datos_filtrados(self, fecha_inicio=None, fecha_fin=None,
                                persona=None, proceso=None):
        """Filtra los datos según los criterios especificados"""
        df_filtrado = self.df_procesos.copy()

        if fecha_inicio:
            # Convertir date a Timestamp para comparar con datetime64[ns]
            fecha_inicio_ts = pd.Timestamp(fecha_inicio)
            df_filtrado = df_filtrado[df_filtrado['FECHA'] >= fecha_inicio_ts]
        if fecha_fin:
            # Convertir date a Timestamp para comparar con datetime64[ns]
            fecha_fin_ts = pd.Timestamp(fecha_fin)
            df_filtrado = df_filtrado[df_filtrado['FECHA'] <= fecha_fin_ts]
        if persona:
            df_filtrado = df_filtrado[df_filtrado['NOMBRE'] == persona]
        if proceso:
            df_filtrado = df_filtrado[df_filtrado['PROCESO'] == proceso]

        return df_filtrado