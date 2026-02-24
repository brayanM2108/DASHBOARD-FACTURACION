# 📊 Dashboard de Análisis de Productividad

Dashboard interactivo desarrollado con Streamlit para el análisis y visualización de datos de productividad, facturación y procesos operativos.

![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![Pandas](https://img.shields.io/badge/Pandas-2.0+-green.svg)
![Plotly](https://img.shields.io/badge/Plotly-5.18+-purple.svg)

## 🚀 Características

### 📈 Módulos de Análisis

- **Legalizaciones**: Análisis detallado de procesos de legalización con métricas de productividad por usuario
- **RIPS**: Seguimiento y análisis de registros individuales de prestación de servicios
- **Facturación**: Monitoreo de facturación electrónica y gestión de convenios
- **Procesos**: Control y seguimiento de procesos operativos con indicadores de rendimiento

### 🎯 Funcionalidades Principales

- **Visualizaciones Interactivas**: Gráficos dinámicos con Plotly para exploración de datos
- **Filtros Avanzados**: Sistema de filtrado por múltiples dimensiones (fecha, usuario, convenio, etc.)
- **Carga de Datos**: Interfaz para cargar y actualizar archivos de datos en formato Excel
- **Persistencia de Datos**: Sistema de caché con archivos Parquet para carga rápida
- **Filtrado Inteligente**: Filtrado automático de usuarios autorizados según archivo maestro
- **Métricas en Tiempo Real**: Indicadores KPI actualizados dinámicamente

## 📋 Requisitos

- Python 3.12 o superior
- pip (gestor de paquetes de Python)

## 🔧 Instalación

1. **Clonar el repositorio**
```bash
git clone <url-del-repositorio>
cd APPDASHBOARD
```

2. **Crear un entorno virtual** (recomendado)
```bash
python -m venv venv
# En Windows
venv\Scripts\activate
# En Linux/Mac
source venv/bin/activate
```

3. **Instalar dependencias**
```bash
cd DASHBOARD_FACTU
pip install -r requirements.txt
```

4. **Configurar archivo maestro de usuarios**

Coloca el archivo `FACTURADORES.xlsx` en el directorio `DASHBOARD_FACTU/` con la siguiente estructura:
- **DOCUMENTO**: Número de documento del usuario
- **NOMBRE**: Nombre completo del usuario

## 🎮 Uso

### Ejecución Local

```bash
streamlit run app.py
```


## 🎨 Interfaz

El dashboard cuenta con 4 pestañas principales:

### 1️⃣ Legalizaciones
- Métricas de productividad por usuario
- Filtros por fecha, usuario y convenio
- Visualizaciones de tendencias temporales
- Tabla detallada de registros

### 2️⃣ RIPS
- Análisis de registros de prestación de servicios
- Filtrado por usuario, convenio y fecha
- Gráficos de distribución y tendencias
- Exportación de datos filtrados

### 3️⃣ Facturación
- Seguimiento de facturación electrónica
- Análisis por facturador y convenio
- Métricas de valores facturados
- Filtros personalizados por pestaña

### 4️⃣ Procesos
- Monitoreo de procesos operativos
- Indicadores de rendimiento
- Análisis temporal de procesos
- Control de estados y seguimiento

## 🔄 Flujo de Datos

1. **Carga Inicial**: Los datos persistidos se cargan desde archivos Parquet al iniciar
2. **Actualización**: Nuevos archivos Excel pueden cargarse a través de la interfaz
3. **Procesamiento**: Los datos se validan, procesan y filtran según usuarios autorizados
4. **Visualización**: Las métricas y gráficos se actualizan dinámicamente
5. **Persistencia**: Los datos procesados se guardan en formato Parquet para futuras sesiones

## 🛠️ Tecnologías

- **[Streamlit](https://streamlit.io/)**: Framework de aplicaciones web para Python
- **[Pandas](https://pandas.pydata.org/)**: Análisis y manipulación de datos
- **[Plotly](https://plotly.com/)**: Visualizaciones interactivas
- **[PyArrow](https://arrow.apache.org/docs/python/)**: Formato Parquet para persistencia eficiente
- **[OpenPyXL](https://openpyxl.readthedocs.io/)**: Lectura de archivos Excel

## 📊 Características Técnicas

### Arquitectura
- **Patrón MVC**: Separación clara entre datos, servicios y UI
- **Session State**: Gestión eficiente del estado de la aplicación
- **Lazy Loading**: Carga diferida de datos para mejor rendimiento
- **Caching**: Sistema de caché con Parquet para reducir tiempos de carga

### Seguridad
- Filtrado automático de usuarios no autorizados
- Validación de integridad de datos
- Manejo seguro de archivos sensibles mediante Secrets

### Rendimiento
- Uso de Parquet para almacenamiento eficiente
- Procesamiento optimizado con Pandas
- Renderizado condicional de componentes
- Filtros pre-aplicados en la capa de servicio


## 📄 Licencia

Este proyecto es de uso interno. Todos los derechos reservados.

## 👤 Autor

**Brayan Melo**

---

**Versión**: 2.0  
**Última actualización**: Febrero 2026

