"""
GEE NDVI Downloader - Main Script
Automates the download of NDVI data from Google Earth Engine grid by grid.

This script is adapted from JavaScript GEE code to Python, using:
- Sentinel-2 HARMONIZED collection (COPERNICUS/S2_HARMONIZED)
- Cloud filtering (CLOUDY_PIXEL_PERCENTAGE < threshold)
- NDVI calculation using B8 (NIR) and B4 (Red) bands
- 10m spatial resolution for optimal detail

Designed for processing Peruvian National Chart grids (cartas nacionales).
"""

import ee
import config
import time
from datetime import datetime
import os
import re
import math
from authenticate import authenticate_gee

def initialize_gee():
    """Initialize Google Earth Engine using authentication."""
    try:
        print("🚀 Initializing Google Earth Engine...")
        
        # Use the authenticate_gee function from authenticate.py
        creds = authenticate_gee()
        if not creds:
            print("❌ Failed to authenticate with Google Earth Engine.")
            return False
        
        print("✅ Google Earth Engine initialized successfully.")
        return True
        
    except Exception as e:
        print(f"❌ Failed to initialize GEE: {str(e)}")
        print("💡 Try running 'python authenticate.py' to fix authentication.")
        return False

def get_collection_info(collection, description="collection"):
    """Get quick info about an image collection."""
    try:
        count = collection.size().getInfo()
        if count > 0:
            first_image = ee.Image(collection.first())
            date = first_image.date().format('YYYY-MM-dd').getInfo()
            print(f"📊 {description}: {count} images (first: {date})")
        else:
            print(f"⚠️  {description}: No images found!")
        return count
    except Exception as e:
        print(f"❌ Error getting {description} info: {str(e)}")
        return 0

def check_existing_assets(asset_folder):
    """
    Check which NDVI assets already exist in the specified GEE Asset folder.
    
    Args:
        asset_folder: The GEE Asset folder path to check
        
    Returns:
        set: Set of existing asset names (without full path)
    """
    try:
        print(f"🔍 Checking existing assets in: {asset_folder}")
        
        # List all assets in the folder
        asset_list = ee.data.listAssets({'parent': asset_folder})
        existing_assets = set()
        
        for asset in asset_list.get('assets', []):
            asset_name = asset['name'].split('/')[-1]  # Get just the asset name
            existing_assets.add(asset_name)
        
        print(f"📊 Found {len(existing_assets)} existing assets in folder.")
        return existing_assets
        
    except Exception as e:
        print(f"⚠️  Warning: Could not list existing assets: {str(e)}")
        print("   Proceeding without duplicate checking...")
        return set()
    
def safe_filename(s):
    """
    Creates a GEE-safe filename by replacing only problematic characters.
    This version preserves uniqueness (e.g., 'ñ' becomes 'n-tilde').
    """
    s = s.replace('ñ', 'n-tilde')
    s = s.replace('Ñ', 'N-tilde')
    s = re.sub(r'[^a-zA-Z0-9_.-]', '_', s)
    # Add other specific replacements here if needed
    return s

def apply_overlap_buffer(geometry):
    """
    Applies a buffer to create overlap between adjacent grids.
    Uses the buffer distance defined in config.py.
    
    Args:
        geometry: Earth Engine geometry object
        
    Returns:
        Earth Engine geometry with buffer applied
    """
    try:
        return geometry.buffer(config.OVERLAP_BUFFER_METERS)
    except Exception as e:
        print(f"⚠️ Warning: Could not apply buffer to geometry. Using original geometry instead: {e}")
        return geometry
    
def generate_standard_asset_name(feature_id_safe, include_test_prefix=False):
    """
    Generates a standardized asset name for the NDVI export.
    
    Args:
        feature_id_safe: The sanitized feature ID to include in the asset name.
        include_test_prefix: If True, includes 'NDVI_TEST_' prefix for test runs.
    
    Returns:
        A standardized asset name string (without folder path).
    """
    if include_test_prefix:
        base_name = f"NDVI_TEST_{feature_id_safe}_{config.START_DATE}_{config.END_DATE}_overlap"
    else:
        base_name = f"NDVI_{feature_id_safe}_{config.START_DATE}_{config.END_DATE}_overlap"

    return base_name

def process_ndvi_single_grid(feature, ndvi_composite, existing_assets, is_test_mode=False):
    """
    Processes a single grid feature: clips NDVI, checks for existing asset, and exports if needed.
    
    Args:
        feature: The feature dictionary from the FeatureCollection.
        ndvi_composite: The NDVI composite image to clip.
        existing_assets: Set of existing asset names to check against.
        is_test_mode: Boolean indicating if this is a test run (affects asset name).

    Returns:
        dict: {'success': bool, 'asset_name': str, 'skipped': bool, 'error': str}
    """
    try:
        feature_id_raw = feature['properties'][config.ID_FIELD]
        feature_id_safe = safe_filename(feature_id_raw)
        feature_name = feature['properties'].get('NOMBRE', 'Unknown')

        asset_name = generate_standard_asset_name(feature_id_safe, include_test_prefix=is_test_mode)
        full_asset_path = f"{config.OUTPUT_ASSET_FOLDER}/{asset_name}"

        # Check if asset already exists
        if asset_name in existing_assets:
            print(f"   ⏭️  SKIPPING: Asset '{asset_name}' already exists.")
            return {'success': False, 
                    'asset_name': asset_name, 
                    'skipped': True, 
                    'error': None
                    }

        # Process geometry with overlap buffer
        original_geometry = ee.Geometry(feature['geometry'])
        buffered_geometry = apply_overlap_buffer(original_geometry)
        clipped_ndvi = ndvi_composite.clip(buffered_geometry)

        # Check if there's actually data in the region
        pixel_count = clipped_ndvi.select('NDVI').reduceRegion(
            reducer=ee.Reducer.count(),
            geometry=buffered_geometry,
            scale=100,
            maxPixels=1e6
        ).getInfo()

        ndvi_pixels = pixel_count.get('NDVI', 0)

        if ndvi_pixels == 0:
            print(f"   ⚠️  No NDVI data for grid {feature_id_raw}, skipping export")
            return {'success': False, 
                    'asset_name': asset_name, 
                    'skipped': True, 
                    'error': 'No NDVI data in region',
                    'feature_id': feature_id_raw,
                    }
        
        # Export to GEE Asset
        task = ee.batch.Export.image.toAsset(**{
            'image': clipped_ndvi,
            'description': asset_name,
            'assetId': full_asset_path,
            'scale': 10,
            'region': buffered_geometry,
            'maxPixels': 1e9
        })

        task.start()
        print(f"   🚀 Initiated export to asset: '{asset_name}' (with {config.OVERLAP_BUFFER_METERS}m overlap)")
        
        return {'success': True,
                'asset_name': asset_name,
                'skipped': False,
                'error': None,
                'feature_id': feature_id_raw,
                'pixels': ndvi_pixels
        }

    except Exception as e:
        return {'success': False,
                'asset_name': asset_name if 'asset_name' in locals() else 'Unknown',
                'skipped': False,
                'error': str(e),
                'feature_id': feature_id_raw if 'feature_id_raw' in locals() else 'Unknown'
        }
    
def process_batch(feature_list, batch_number, total_batches, ndvi_composite, existing_assets, is_test_mode=False):
    """Process a batch of grids."""
    batch_size = len(feature_list)
    print(f"\n📦 === BATCH {batch_number}/{total_batches} ===")
    print(f"Processing {batch_size} grids...")
    
    batch_stats = {
        'processed': 0,
        'skipped': 0,
        'failed': 0,
        'new_tasks': 0
    }
    
    start_time = time.time()
    
    for i, feature in enumerate(feature_list, 1):
        print(f"\n[{i}/{batch_size}] Processing grid {batch_number}-{i}...")
        
        result = process_ndvi_single_grid(feature, ndvi_composite, existing_assets, is_test_mode)
        
        if result['success']:
            if result['skipped']:
                print(f"   ⏭️  SKIPPED: {result['asset_name']} already exists")
                batch_stats['skipped'] += 1
            else:
                print(f"   ✅ EXPORTED: {result['asset_name']} ({result['pixels']} pixels)")
                batch_stats['new_tasks'] += 1
        else:
            print(f"   ❌ FAILED: {result['feature_id']} - {result['error']}")
            batch_stats['failed'] += 1
        
        batch_stats['processed'] += 1
        
        # Small delay between tasks
        time.sleep(1)
    
    elapsed = time.time() - start_time
    print(f"\n📊 Batch {batch_number} Summary:")
    print(f"   ⏱️  Time: {elapsed:.1f}s")
    print(f"   ✅ New tasks: {batch_stats['new_tasks']}")
    print(f"   ⏭️  Skipped: {batch_stats['skipped']}")
    print(f"   ❌ Failed: {batch_stats['failed']}")
    
    return batch_stats

def process_ndvi_batch_mode(batch_size=10):
    """
    Process all grids in batches with strict duplicate prevention using GEE Assets.
    
    Args:
        batch_size: Number of grids to process per batch (default: 10)
    """
    print(f"\n🏭 === BATCH PROCESSING MODE ===")
    print(f"Processing ALL 501 grids in batches of {batch_size}")
    print("⚠️  This will take approximately 60-80 hours total!")
    
    response = input("Are you sure you want to continue? (yes/no): ").lower().strip()
    if response != 'yes':
        print("❌ Batch processing cancelled.")
        return
    
    # Initialize
    if not initialize_gee():
        return
    
    # Get existing assets once at the beginning
    existing_assets = check_existing_assets(config.OUTPUT_ASSET_FOLDER)
    
    # Load all features
    print(f"📁 Loading FeatureCollection: {config.ASSET_ID}")
    feature_collection = ee.FeatureCollection(config.ASSET_ID)
    
    # Setup Sentinel-2 collection
    print(f"🛰️  Setting up Sentinel-2 collection...")
    collection_bounds = feature_collection.geometry()
    
    sentinel_collection = (ee.ImageCollection('COPERNICUS/S2_HARMONIZED')
                          .filterDate(config.START_DATE, config.END_DATE)
                          .filterBounds(collection_bounds)
                          .filterMetadata('CLOUDY_PIXEL_PERCENTAGE', 'Less_Than', config.CLOUD_THRESHOLD))
    
    available_images = get_collection_info(sentinel_collection, "Filtered Sentinel-2 collection")
    
    if available_images == 0:
        print("❌ No images found with current filters.")
        return
    
    # Calculate NDVI composite
    def calculate_ndvi_s2(image):
        ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
        return image.addBands(ndvi)
    
    print("🔢 Calculating NDVI composite (this may take a few minutes)...")
    ndvi_collection = sentinel_collection.map(calculate_ndvi_s2)
    ndvi_composite = ndvi_collection.select('NDVI').median()
    
    # Get all features
    all_features = feature_collection.getInfo()['features']
    total_features = len(all_features)
    
    # Calculate batches
    total_batches = math.ceil(total_features / batch_size)
    
    print(f"\n📊 Processing Plan:")
    print(f"   Total grids: {total_features}")
    print(f"   Batch size: {batch_size}")
    print(f"   Total batches: {total_batches}")
    print(f"   Existing assets: {len(existing_assets)}")
    print(f"   Output asset folder: {config.OUTPUT_ASSET_FOLDER}")
    print(f"   Estimated time: {total_batches * 15} minutes")
    
    # Overall statistics
    overall_stats = {
        'processed': 0,
        'skipped': 0,
        'failed': 0,
        'new_tasks': 0
    }
    
    start_time = time.time()
    
    # Process in batches
    for batch_num in range(1, total_batches + 1):
        start_idx = (batch_num - 1) * batch_size
        end_idx = min(start_idx + batch_size, total_features)
        
        batch_features = all_features[start_idx:end_idx]
        
        batch_stats = process_batch(
            batch_features, 
            batch_num, 
            total_batches, 
            ndvi_composite, 
            existing_assets,
            is_test_mode=False
        )
        
        # Update overall stats
        for key in batch_stats:
            overall_stats[key] += batch_stats[key]
        
        # Progress update
        progress = (batch_num / total_batches) * 100
        elapsed = time.time() - start_time
        eta = (elapsed / batch_num) * (total_batches - batch_num)
        
        print(f"\n🎯 Overall Progress: {progress:.1f}% ({batch_num}/{total_batches} batches)")
        print(f"⏱️  ETA: {eta/3600:.1f} hours remaining")
        
        # Wait between batches to avoid overwhelming GEE
        if batch_num < total_batches:
            print("⏸️  Waiting 30 seconds before next batch...")
            time.sleep(30)
    
    # Final summary
    total_time = time.time() - start_time
    print(f"\n🎉 === BATCH PROCESSING COMPLETE ===")
    print(f"⏱️  Total time: {total_time/3600:.2f} hours")
    print(f"✅ New tasks initiated: {overall_stats['new_tasks']}")
    print(f"⏭️  Assets skipped (already exist): {overall_stats['skipped']}")
    print(f"❌ Failed: {overall_stats['failed']}")
    print(f"📁 Check GEE Asset folder '{config.OUTPUT_ASSET_FOLDER}' for all assets.")
    print(f"💡 Run 'python download_assets.py' to download assets to local files.")

def process_ndvi_test(grids_to_process):
    """Test function with asset-based export."""
    print(f"\n🧪 === TEST MODE ===")
    print(f"Processing {len(grids_to_process)} test grids: {grids_to_process}")

    if not initialize_gee():
        return
    
    # Get existing assets
    existing_assets = check_existing_assets(config.OUTPUT_ASSET_FOLDER)
    
    # Load and filter features
    feature_collection = ee.FeatureCollection(config.ASSET_ID)
    test_features = feature_collection.filter(ee.Filter.inList(config.ID_FIELD, grids_to_process))
    
    found_count = test_features.size().getInfo()
    if found_count == 0:
        print("❌ No test grids found.")
        return
    
    # Setup Sentinel-2 and NDVI
    collection_bounds = test_features.geometry()
    sentinel_collection = (ee.ImageCollection('COPERNICUS/S2_HARMONIZED')
                          .filterDate(config.START_DATE, config.END_DATE)
                          .filterBounds(collection_bounds)
                          .filterMetadata('CLOUDY_PIXEL_PERCENTAGE', 'Less_Than', config.CLOUD_THRESHOLD))
    
    available_images = get_collection_info(sentinel_collection, "Filtered Sentinel-2 collection")
    if available_images == 0:
        print("⚠️  No satellite images found.")
        return
    
    def calculate_ndvi_s2(image):
        ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
        return image.addBands(ndvi)
    
    print("🔢 Calculating NDVI composite...")
    ndvi_collection = sentinel_collection.map(calculate_ndvi_s2)
    ndvi_composite = ndvi_collection.select('NDVI').median()
    
    # Process test features
    test_feature_list = test_features.getInfo()['features']
    
    tasks_initiated = 0
    for i, feature in enumerate(test_feature_list, 1):
        print(f"\n[{i}/{len(test_feature_list)}] Test grid:")
        
        result = process_ndvi_single_grid(feature, ndvi_composite, existing_assets, is_test_mode=True)
        
        if result['success']:
            if result['skipped']:
                print(f"   ⏭️  SKIPPED: {result['asset_name']} already exists")
            else:
                print(f"   ✅ EXPORTED: {result['asset_name']}")
                tasks_initiated += 1
        else:
            print(f"   ❌ FAILED: {result['error']}")
    
    print(f"\n🎉 Test complete! Initiated {tasks_initiated} new tasks.")
    print(f"📁 Check GEE Asset folder '{config.OUTPUT_ASSET_FOLDER}' for test assets.")
    print(f"💡 Run 'python download_assets.py' to download test assets locally.")

def main():
    """Main function with asset-based batch processing."""
    print("🌱 GEE NDVI Downloader")
    print("=" * 50)
    
    print(f"📋 Current configuration:")
    print(f"   Asset: {config.ASSET_ID}")
    print(f"   Dates: {config.START_DATE} to {config.END_DATE}")
    print(f"   Cloud threshold: {config.CLOUD_THRESHOLD}%")
    print(f"   Output asset folder: {config.OUTPUT_ASSET_FOLDER}")
    print(f"   Local output directory: {config.LOCAL_OUTPUT_DIR}")
    print(f"   Overlap buffer: {config.OVERLAP_BUFFER_METERS}m")
    
    print("\nSelect processing mode:")
    print("1. Test mode (process specific grids)")
    print("2. Batch mode (process all 501 grids)")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    # Select 1 or 2 option
    if choice == '1':
        TEST_GRIDS = ['4-p', '4-ñ']  # Modify as needed
        process_ndvi_test(TEST_GRIDS)
    elif choice == '2':
        # Use batch size from config
        batch_size = config.PRODUCTION_BATCH_SIZE if input("Use production batch size (50)? (y/n): ").lower() == 'y' else config.TEST_BATCH_SIZE
        process_ndvi_batch_mode(batch_size=batch_size)
    else:
        print("❌ Invalid choice. Exiting.")

if __name__ == "__main__":
    main()