# GEE NDVI Downloader

## Descripción del Proyecto

Este proyecto automatiza la descarga de datos de NDVI (Índice de Vegetación de Diferencia Normalizada) desde Google Earth Engine (GEE) cuadrícula por cuadrícula. El script utiliza una FeatureCollection de GEE como base para definir cada área de descarga y exporta las imágenes resultantes directamente a una carpeta en Google Drive.

**Adaptado desde código JavaScript de GEE para usar Sentinel-2 con las mejores prácticas de procesamiento.**

## Características Principales

- **Procesamiento automatizado**: Descarga NDVI para múltiples cuadrículas de forma automática
- **Basado en FeatureCollection**: Utiliza sus propias cuadrículas definidas en GEE
- **Exportación a Google Drive**: Guarda automáticamente los resultados en su Drive
- **Datos Sentinel-2**: Utiliza imágenes de satélite Sentinel-2 HARMONIZED con resolución de 10m
- **Filtro de nubes**: Automáticamente filtra imágenes con cobertura de nubes < 10%
- **Configuración flexible**: Fácil personalización de fechas, assets y carpetas de salida
- **Optimizado para Perú**: Diseñado específicamente para cuadrículas de cartas nacionales peruanas

## Requisitos Previos

### 1. Dependencias de Python
Instale las bibliotecas necesarias ejecutando:
```bash
pip install -r requirements.txt
```

### 2. Configuración de Google Earth Engine
- **Cuenta de GEE**: Debe tener una cuenta registrada en [Google Earth Engine](https://earthengine.google.com/)
- **Autenticación**: Debe haber autenticado la API de GEE en su sistema
- **FeatureCollection**: Debe tener una FeatureCollection subida a GEE con sus cuadrículas de estudio

### 3. Autenticación de GEE (Primera vez)
Si es la primera vez que usa GEE en su sistema, ejecute:
```bash
earthengine authenticate
```

## Configuración

Antes de ejecutar el script, debe editar el archivo `config.py` con sus valores específicos:

### Variables de Configuración

1. **ASSET_ID**: Ruta completa a su FeatureCollection en GEE
   ```python
   ASSET_ID = 'users/su_usuario/nombre_de_su_coleccion'
   ```

2. **START_DATE**: Fecha de inicio del período de estudio
   ```python
   START_DATE = '2024-01-01'
   ```

3. **END_DATE**: Fecha de fin del período de estudio
   ```python
   END_DATE = '2024-01-31'
   ```

4. **OUTPUT_FOLDER**: Nombre de la carpeta de destino en Google Drive
   ```python
   OUTPUT_FOLDER = 'Mi_Carpeta_NDVI'
   ```

5. **ID_FIELD**: Nombre del campo en su FeatureCollection que identifica cada cuadrícula
   ```python
   ID_FIELD = 'ID_CUADRICULA'
   ```

6. **CLOUD_THRESHOLD**: Umbral de cobertura de nubes (porcentaje)
   ```python
   CLOUD_THRESHOLD = 10  # Filtra imágenes con más del 10% de nubes
   ```

### Ejemplo de Configuración Completa
```python
ASSET_ID = 'users/mi_usuario/cuadriculas_estudio'
START_DATE = '2024-03-01'
END_DATE = '2024-03-31'
OUTPUT_FOLDER = 'NDVI_Marzo_2024'
ID_FIELD = 'CODIGO_GRID'
CLOUD_THRESHOLD = 15  # Permite hasta 15% de cobertura de nubes
```

## Instrucciones de Uso

### Ejecución del Script
Una vez configurado el archivo `config.py`, ejecute el script principal:

```bash
python main.py
```

### Proceso de Ejecución
1. **Inicialización**: El script se conecta a Google Earth Engine
2. **Carga de datos**: Carga su FeatureCollection y filtra imágenes Sentinel-2
3. **Filtro de nubes**: Aplica filtro de cobertura de nubes según configuración
4. **Cálculo de NDVI**: Procesa las imágenes para calcular el NDVI usando bandas B8 (NIR) y B4 (Red)
5. **Creación de compuesto**: Genera una imagen compuesta (mediana) del período
6. **Exportación**: Inicia tareas de exportación para cada cuadrícula a Google Drive

### Salida Esperada
- **Archivos GeoTIFF**: Un archivo por cuadrícula en formato `.tif`
- **Nomenclatura**: `NDVI_{ID_CUADRICULA}_{FECHA_INICIO}_{FECHA_FIN}.tif`
- **Ubicación**: Carpeta especificada en `OUTPUT_FOLDER` en Google Drive
- **Resolución**: 10 metros (resolución nativa de Sentinel-2 para bandas B2, B3, B4, B8)
- **Proyección**: Sistema de coordenadas original de Sentinel-2 (UTM)

### Monitoreo del Progreso
- El script muestra el progreso en la consola
- Puede monitorear las tareas en la [interfaz web de GEE](https://code.earthengine.google.com/)
- Las exportaciones grandes pueden tomar desde minutos hasta horas

## Estructura del Proyecto
```
GEE-NDVI-Downloader/
├── .gitignore          # Archivos a ignorar en Git
├── requirements.txt    # Dependencias de Python
├── README.md          # Este archivo de documentación
├── config.py          # Archivo de configuración
└── main.py            # Script principal
```

## Notas Importantes

- **Límites de GEE**: Google Earth Engine tiene límites en el número de tareas simultáneas
- **Tamaño de área**: Cuadrículas muy grandes pueden requerir más tiempo de procesamiento
- **Calidad de datos**: Se utilizan solo imágenes Sentinel-2 HARMONIZED con filtro de nubes
- **Formato de salida**: Los archivos se exportan en formato GeoTIFF con proyección UTM
- **Cobertura temporal**: Sentinel-2 tiene datos disponibles desde 2015-07-01 hasta la actualidad
- **Resolución espacial**: 10m para bandas multiespectrales (B2, B3, B4, B8)

## Cambios Respecto al Código JavaScript Original

Este proyecto Python está basado en código JavaScript de GEE y incluye las siguientes adaptaciones:

- **Colección de imágenes**: `COPERNICUS/S2_HARMONIZED` (Sentinel-2)
- **Filtro de nubes**: Automático usando `CLOUDY_PIXEL_PERCENTAGE`
- **Bandas NDVI**: B8 (NIR) y B4 (Red) de Sentinel-2
- **Resolución**: 10m en lugar de 30m
- **Estructura modular**: Configuración separada en `config.py`
- **Procesamiento por lotes**: Exportación automática cuadrícula por cuadrícula

## Solución de Problemas

### Error de Autenticación
```
EEException: Please authorize access to your Earth Engine account
```
**Solución**: Ejecute `earthengine authenticate` y siga las instrucciones

### Error de Asset no encontrado
```
EEException: Asset not found
```
**Solución**: Verifique que el `ASSET_ID` en `config.py` sea correcto y que tenga permisos de acceso

### Sin imágenes para el período
```
No images found for the specified date range
```
**Solución**: Ajuste las fechas `START_DATE` y `END_DATE` o verifique la cobertura de nubes

## Contacto y Soporte

Para reportar problemas o sugerir mejoras, por favor:
1. Verifique que su configuración sea correcta
2. Consulte la documentación oficial de [Google Earth Engine](https://developers.google.com/earth-engine/)
3. Revise los mensajes de error en la consola para más detalles