# Configuration file for GEE NDVI Downloader

# Google Earth Engine Asset ID - Path to your FeatureCollection
from sys import platform


ASSET_ID = 'projects/grd-geoapi-ndvi/assets/cartas_100k'

# Date range for satellite data collection
START_DATE = '2017-06-01'
END_DATE = '2024-12-07'

# Output Asset Folder in Google Earth Engine (replaces Google Drive)
# All processed NDVI images will be stored here as GEE Assets
OUTPUT_ASSET_FOLDER = 'projects/grd-geoapi-ndvi/assets/ndvi_outputs'

# Detectar sistema operativo y configurar rutas apropiadas
if platform.system() == "Windows":
    LOCAL_OUTPUT_DIR = r'C:\Users\Pedro Lopevia\Desktop\ndvi_downloads'
else:
    LOCAL_OUTPUT_DIR = '/home/pedro/grd_api_ndvi/gee_grids'

# Field name in FeatureCollection that identifies each grid
ID_FIELD = 'CODIGO'

# Cloud coverage threshold for Sentinel-2 images (percentage)
CLOUD_THRESHOLD = 10

# Overlap buffer in meters to ensure seamless mosaicking between adjacent grids
# For Sentinel-2 with 10m resolution, 20 meters = 2 pixels overlap
# Files exported with this buffer will have '_overlap' suffix in filename
OVERLAP_BUFFER_METERS = 20

# Batch sizes for different processing modes
TEST_BATCH_SIZE = 11
PRODUCTION_BATCH_SIZE = 50