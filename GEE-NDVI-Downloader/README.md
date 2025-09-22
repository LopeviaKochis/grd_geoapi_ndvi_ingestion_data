# GEE NDVI Downloader# GEE NDVI Downloader



Automated system for downloading NDVI data from Google Earth Engine grid by grid using Sentinel-2 HARMONIZED collection.## Descripción del Proyecto



## System OverviewEste proyecto automatiza la descarga de datos de NDVI (Índice de Vegetación de Diferencia Normalizada) desde Google Earth Engine (GEE) cuadrícula por cuadrícula. El script utiliza una FeatureCollection de GEE como base para definir cada área de descarga y exporta las imágenes resultantes directamente a una carpeta en Google Drive.



This system processes Peruvian National Chart grids (cartas nacionales) to generate NDVI data with 2-pixel overlap for seamless mosaicking. The system now uses **GEE Assets** for storage instead of Google Drive, enabling deployment on headless servers.**Adaptado desde código JavaScript de GEE para usar Sentinel-2 con las mejores prácticas de procesamiento.**



## Key Features## Características Principales



- **Dual Environment Support**: Develop on Windows, deploy on Debian server- **Procesamiento automatizado**: Descarga NDVI para múltiples cuadrículas de forma automática

- **Asset-Based Storage**: Uses GEE Assets instead of Google Drive for server compatibility- **Basado en FeatureCollection**: Utiliza sus propias cuadrículas definidas en GEE

- **Overlap Functionality**: 2-pixel (20m) buffer for seamless grid mosaicking- **Exportación a Google Drive**: Guarda automáticamente los resultados en su Drive

- **Batch Processing**: Configurable batch sizes with progress tracking- **Datos Sentinel-2**: Utiliza imágenes de satélite Sentinel-2 HARMONIZED con resolución de 10m

- **Duplicate Prevention**: Checks existing assets before processing- **Filtro de nubes**: Automáticamente filtra imágenes con cobertura de nubes < 10%

- **Authentication Flexibility**: OAuth for development, Service Account for production- **Configuración flexible**: Fácil personalización de fechas, assets y carpetas de salida

- **Optimizado para Perú**: Diseñado específicamente para cuadrículas de cartas nacionales peruanas

## Architecture

## Requisitos Previos

### Windows Development Environment

- OAuth authentication (requires browser)### 1. Dependencias de Python

- Full IDE support for development and testingInstale las bibliotecas necesarias ejecutando:

- Asset export to GEE for server access```bash

pip install -r requirements.txt

### Debian Production Environment  ```

- Service Account authentication (headless)

- Asset download to local files### 2. Configuración de Google Earth Engine

- No GUI dependencies- **Cuenta de GEE**: Debe tener una cuenta registrada en [Google Earth Engine](https://earthengine.google.com/)

- **Autenticación**: Debe haber autenticado la API de GEE en su sistema

## Installation- **FeatureCollection**: Debe tener una FeatureCollection subida a GEE con sus cuadrículas de estudio



### 1. Clone and Install Dependencies### 3. Autenticación de GEE (Primera vez)

```bashSi es la primera vez que usa GEE en su sistema, ejecute:

git clone <repository>```bash

cd GEE-NDVI-Downloaderearthengine authenticate

pip install -r requirements.txt```

```

## Configuración

### 2. Authentication Setup

Antes de ejecutar el script, debe editar el archivo `config.py` con sus valores específicos:

#### For Windows Development (OAuth):

1. Download OAuth credentials from Google Cloud Console### Variables de Configuración

2. Save as `credentials.json` in project directory

3. Run: `python authenticate.py`1. **ASSET_ID**: Ruta completa a su FeatureCollection en GEE

   ```python

#### For Debian Server (Service Account):   ASSET_ID = 'users/su_usuario/nombre_de_su_coleccion'

1. Create service account in Google Cloud Console   ```

2. Download JSON key file

3. Save as `service-account-key.json` in project directory2. **START_DATE**: Fecha de inicio del período de estudio

4. Run: `python authenticate.py`   ```python

   START_DATE = '2024-01-01'

## Project Structure   ```



```3. **END_DATE**: Fecha de fin del período de estudio

GEE-NDVI-Downloader/   ```python

├── main.py                    # Core NDVI processing engine   END_DATE = '2024-01-31'

├── config.py                  # Configuration management   ```

├── authenticate.py            # Dual authentication system

├── download_assets.py         # Asset download utility (for Debian)4. **OUTPUT_FOLDER**: Nombre de la carpeta de destino en Google Drive

├── check_asset.py            # Asset verification utility   ```python

├── requirements.txt          # Python dependencies   OUTPUT_FOLDER = 'Mi_Carpeta_NDVI'

├── credentials.json          # OAuth credentials (not in repo)   ```

├── service-account-key.json  # Service account key (not in repo)

├── token.json               # OAuth token cache (auto-generated)5. **ID_FIELD**: Nombre del campo en su FeatureCollection que identifica cada cuadrícula

└── .gitignore               # Security exclusions   ```python

```   ID_FIELD = 'ID_CUADRICULA'

   ```

## Configuration (config.py)

6. **CLOUD_THRESHOLD**: Umbral de cobertura de nubes (porcentaje)

```python   ```python

# Asset paths   CLOUD_THRESHOLD = 10  # Filtra imágenes con más del 10% de nubes

ASSET_ID = 'projects/grd-geoapi-ndvi/assets/cartas_100k'   ```

OUTPUT_ASSET_FOLDER = 'projects/grd-geoapi-ndvi/assets/ndvi_outputs'

### Ejemplo de Configuración Completa

# Local output (for Debian server)```python

LOCAL_OUTPUT_DIR = '/home/user/ndvi_data'ASSET_ID = 'users/mi_usuario/cuadriculas_estudio'

START_DATE = '2024-03-01'

# Processing parametersEND_DATE = '2024-03-31'

START_DATE = '2024-01-01'OUTPUT_FOLDER = 'NDVI_Marzo_2024'

END_DATE = '2024-12-31'ID_FIELD = 'CODIGO_GRID'

CLOUD_THRESHOLD = 20CLOUD_THRESHOLD = 15  # Permite hasta 15% de cobertura de nubes

OVERLAP_BUFFER_METERS = 20```



# Batch sizes## Instrucciones de Uso

TEST_BATCH_SIZE = 11

PRODUCTION_BATCH_SIZE = 50### Ejecución del Script

```Una vez configurado el archivo `config.py`, ejecute el script principal:



## Usage Workflow```bash

python main.py

### 1. Development Phase (Windows)```



#### Test Processing:### Proceso de Ejecución

```bash1. **Inicialización**: El script se conecta a Google Earth Engine

python main.py2. **Carga de datos**: Carga su FeatureCollection y filtra imágenes Sentinel-2

# Choose option 1 (Test mode)3. **Filtro de nubes**: Aplica filtro de cobertura de nubes según configuración

```4. **Cálculo de NDVI**: Procesa las imágenes para calcular el NDVI usando bandas B8 (NIR) y B4 (Red)

5. **Creación de compuesto**: Genera una imagen compuesta (mediana) del período

#### Production Processing:6. **Exportación**: Inicia tareas de exportación para cada cuadrícula a Google Drive

```bash

python main.py  ### Salida Esperada

# Choose option 2 (Batch mode)- **Archivos GeoTIFF**: Un archivo por cuadrícula en formato `.tif`

# Select batch size (11 for test, 50 for production)- **Nomenclatura**: `NDVI_{ID_CUADRICULA}_{FECHA_INICIO}_{FECHA_FIN}.tif`

```- **Ubicación**: Carpeta especificada en `OUTPUT_FOLDER` en Google Drive

- **Resolución**: 10 metros (resolución nativa de Sentinel-2 para bandas B2, B3, B4, B8)

#### Check Assets:- **Proyección**: Sistema de coordenadas original de Sentinel-2 (UTM)

```bash

python check_asset.py### Monitoreo del Progreso

# Various options to verify assets were created- El script muestra el progreso en la consola

```- Puede monitorear las tareas en la [interfaz web de GEE](https://code.earthengine.google.com/)

- Las exportaciones grandes pueden tomar desde minutos hasta horas

### 2. Production Phase (Debian)

## Estructura del Proyecto

#### Download Assets:```

```bashGEE-NDVI-Downloader/

python download_assets.py├── .gitignore          # Archivos a ignorar en Git

# Choose download mode:├── requirements.txt    # Dependencias de Python

# 1. Download all assets├── README.md          # Este archivo de documentación

# 2. Download specific test assets  ├── config.py          # Archivo de configuración

# 3. Download assets with pattern└── main.py            # Script principal

``````



## Processing Details## Notas Importantes



### NDVI Calculation- **Límites de GEE**: Google Earth Engine tiene límites en el número de tareas simultáneas

- **Collection**: Sentinel-2 HARMONIZED (COPERNICUS/S2_HARMONIZED)- **Tamaño de área**: Cuadrículas muy grandes pueden requerir más tiempo de procesamiento

- **Bands**: B8 (NIR) and B4 (Red)- **Calidad de datos**: Se utilizan solo imágenes Sentinel-2 HARMONIZED con filtro de nubes

- **Formula**: NDVI = (B8 - B4) / (B8 + B4)- **Formato de salida**: Los archivos se exportan en formato GeoTIFF con proyección UTM

- **Resolution**: 10m spatial resolution- **Cobertura temporal**: Sentinel-2 tiene datos disponibles desde 2015-07-01 hasta la actualidad

- **Composite**: Median composite over date range- **Resolución espacial**: 10m para bandas multiespectrales (B2, B3, B4, B8)



### Overlap Implementation## Cambios Respecto al Código JavaScript Original

- **Buffer**: 20 meters (2 pixels at 10m resolution)

- **Purpose**: Seamless mosaicking of adjacent gridsEste proyecto Python está basado en código JavaScript de GEE y incluye las siguientes adaptaciones:

- **Method**: Geometry buffer applied before clipping

- **Colección de imágenes**: `COPERNICUS/S2_HARMONIZED` (Sentinel-2)

### Batch Processing- **Filtro de nubes**: Automático usando `CLOUDY_PIXEL_PERCENTAGE`

- **Test batches**: 11 grids per batch- **Bandas NDVI**: B8 (NIR) y B4 (Red) de Sentinel-2

- **Production batches**: 50 grids per batch  - **Resolución**: 10m en lugar de 30m

- **Progress tracking**: Real-time statistics and ETA- **Estructura modular**: Configuración separada en `config.py`

- **Error handling**: Individual grid failures don't stop batch- **Procesamiento por lotes**: Exportación automática cuadrícula por cuadrícula



## Authentication Methods## Solución de Problemas



### OAuth (Windows Development)### Error de Autenticación

- Requires browser access for initial authentication```

- Token cached locally for subsequent runsEEException: Please authorize access to your Earth Engine account

- Suitable for interactive development```

**Solución**: Ejecute `earthengine authenticate` y siga las instrucciones

### Service Account (Debian Production)

- No browser required (headless compatible)### Error de Asset no encontrado

- JSON key file authentication```

- Suitable for automated server deploymentEEException: Asset not found

```

## File Naming Convention**Solución**: Verifique que el `ASSET_ID` en `config.py` sea correcto y que tenga permisos de acceso



### Assets:### Sin imágenes para el período

``````

NDVI_{grid_id}_{start_date}_{end_date}_overlapNo images found for the specified date range

``````

**Solución**: Ajuste las fechas `START_DATE` y `END_DATE` o verifique la cobertura de nubes

### Local Files:

```## Contacto y Soporte

NDVI_{grid_id}_{start_date}_{end_date}_overlap.tif

```Para reportar problemas o sugerir mejoras, por favor:

1. Verifique que su configuración sea correcta

### Test Assets:2. Consulte la documentación oficial de [Google Earth Engine](https://developers.google.com/earth-engine/)

```3. Revise los mensajes de error en la consola para más detalles
NDVI_TEST_{grid_id}_{start_date}_{end_date}_overlap
```

## Troubleshooting

### Authentication Issues
```bash
python authenticate.py
# Test authentication and verify credentials
```

### Asset Verification
```bash
python check_asset.py
# Check asset folder contents and task status
```

### Common Issues

1. **"No token.json found"**
   - Run `python authenticate.py` first
   
2. **"Service account key not found"**
   - Place `service-account-key.json` in project directory
   
3. **"Asset folder not found"**
   - Verify `OUTPUT_ASSET_FOLDER` path in config.py
   - Check GEE project permissions

## Performance Estimates

- **Total grids**: 501 
- **Processing time**: ~5-15 minutes per grid
- **Total time**: 60-80 hours for all grids
- **Recommended batch size**: 11 (test), 50 (production)

## Security Notes

- Never commit credential files (`credentials.json`, `service-account-key.json`, `token.json`)
- Use `.gitignore` to exclude sensitive files
- Service account keys should have minimal required permissions

## Migration Notes

This system replaces the previous Google Drive-based approach:
- **Old**: Export to Google Drive → Download manually
- **New**: Export to GEE Assets → Download via script

Benefits:
- Headless server compatibility
- No Drive API dependencies
- Better automation support
- Centralized asset management