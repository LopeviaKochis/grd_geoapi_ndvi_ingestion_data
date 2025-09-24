"""
GEE Asset Downloader
Downloads NDVI assets from Google Earth Engine to local files.

This script is designed to run on a Debian server to download
the NDVI assets created by main.py to local GeoTIFF files.

Large Asset Downloader - For assets > 50MB
Uses Google Drive export method for large files
"""

import ee
import os
import time
import config
import requests
from authenticate import authenticate_gee

def list_assets_in_folder(asset_folder):
    """
    List all assets in a GEE Asset folder.
    
    Args:
        asset_folder: The GEE Asset folder path
        
    Returns:
        list: List of asset dictionaries with name and path
    """
    try:
        print(f"📁 Listing assets in: {asset_folder}")
        
        asset_list = ee.data.listAssets({'parent': asset_folder})
        assets = []
        
        for asset in asset_list.get('assets', []):
            asset_name = asset['name'].split('/')[-1]
            asset_path = asset['name']
            assets.append({
                'name': asset_name,
                'path': asset_path,
                'type': asset.get('type', 'IMAGE')
            })
        
        print(f"🔍 Found {len(assets)} assets in folder.")
        return assets
        
    except Exception as e:
        print(f"❌ Error listing assets: {str(e)}")
        return []

def check_local_files(local_dir):
    """Check which files already exist locally - chunks version CORREGIDA"""
    if not os.path.exists(local_dir):
        print(f"📁 Creating local directory: {local_dir}")
        os.makedirs(local_dir, exist_ok=True)
        return set()
    
    existing_files = set()
    processed_assets = set()
    
    # Get all files in directory ONCE (más eficiente)
    all_files = os.listdir(local_dir)
    
    # Extract base names from chunk files
    for filename in all_files:
        if '_chunk_' in filename and filename.endswith('.tif'):
            base_name = filename.split('_chunk_')[0]
            processed_assets.add(base_name)
    
    print(f"🔍 Found {len(processed_assets)} assets with chunks")
    
    # Check which assets have all 4 chunks complete
    complete_count = 0
    for asset_base in processed_assets:
        chunks_found = 0
        for i in range(2):
            for j in range(2):
                chunk_file = f"{asset_base}_chunk_{i}_{j}.tif"
                if chunk_file in all_files:  # ← CAMBIO AQUÍ: usar all_files en lugar de os.listdir()
                    chunks_found += 1
        
        # Only consider complete if all 4 chunks exist
        if chunks_found == 4:
            existing_files.add(f"{asset_base}.tif")
            complete_count += 1
    
    print(f"📂 Found {complete_count} complete assets (4 chunks each)")
    return existing_files

def download_asset_to_local(asset_path, asset_name, local_dir):
    """
    Download a single GEE asset to a local GeoTIFF file.
    
    Args:
        asset_path: Full GEE asset path
        asset_name: Asset name (without folder path)
        local_dir: Local directory to save the file
        
    Returns:
        dict: Result of the download operation
    """
    try:
        # Create output filename
        output_filename = f"{asset_name}.tif"
        output_path = os.path.join(local_dir, output_filename)
        
        # Load the asset as an image
        image = ee.Image(asset_path)
        
        # Get the image geometry (footprint)
        geometry = image.geometry()
        
        # Create download URL
        url = image.getDownloadURL({
            'scale': 10,
            'region': geometry,
            'filePerBand': False,
            'format': 'GEO_TIFF'
        })
        
        print(f"   🌐 Generated download URL for {asset_name}")
        
        # Download using requests
        import requests
        
        response = requests.get(url, timeout=300)  # 5 minute timeout
        response.raise_for_status()
        
        # Save to file
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
        print(f"   ✅ Downloaded: {output_filename} ({file_size:.1f} MB)")
        
        return {
            'success': True,
            'filename': output_filename,
            'size_mb': file_size,
            'error': None
        }
        
    except Exception as e:
        return {
            'success': False,
            'filename': f"{asset_name}.tif",
            'size_mb': 0,
            'error': str(e)
        }

def download_asset_in_chunks(asset_id, filename, chunk_size=2048):
    """Download asset by dividing into smaller geographic chunks"""
    
    print(f"📦 Downloading {filename} in chunks...")
    
    # Load the asset
    image = ee.Image(asset_id)
    
    # Get image bounds
    bounds = image.geometry().bounds()
    bounds_coords = bounds.coordinates().getInfo()[0]
    
    # Calculate bounding box
    min_lon = min([coord[0] for coord in bounds_coords])
    max_lon = max([coord[0] for coord in bounds_coords])
    min_lat = min([coord[1] for coord in bounds_coords])
    max_lat = max([coord[1] for coord in bounds_coords])
    
    print(f"   🗺️  Image bounds: {min_lon:.4f}, {min_lat:.4f} to {max_lon:.4f}, {max_lat:.4f}")
    
    # Calculate chunk dimensions
    lon_range = max_lon - min_lon
    lat_range = max_lat - min_lat
    
    # Divide into 4 chunks (2x2 grid) for ~38MB each
    chunks = []
    for i in range(2):
        for j in range(2):
            chunk_min_lon = min_lon + (i * lon_range / 2)
            chunk_max_lon = min_lon + ((i + 1) * lon_range / 2)
            chunk_min_lat = min_lat + (j * lat_range / 2)
            chunk_max_lat = min_lat + ((j + 1) * lat_range / 2)
            
            chunk_geometry = ee.Geometry.Rectangle([
                chunk_min_lon, chunk_min_lat, 
                chunk_max_lon, chunk_max_lat
            ])
            
            chunks.append({
                'geometry': chunk_geometry,
                'filename': f"{filename}_chunk_{i}_{j}.tif"
            })
    
    # Download each chunk
    downloaded_chunks = []
    for idx, chunk in enumerate(chunks):
        try:
            print(f"   📥 Downloading chunk {idx + 1}/4...")
            
            # Clip image to chunk
            chunk_image = image.clip(chunk['geometry'])
            
            # Get download URL
            url = chunk_image.getDownloadURL({
                'scale': 10,
                'crs': 'EPSG:4326',
                'format': 'GEO_TIFF'
            })
            
            # Download chunk
            response = requests.get(url, timeout=300)
            response.raise_for_status()
            
            # Save chunk
            chunk_path = os.path.join(config.LOCAL_OUTPUT_DIR, chunk['filename'])
            with open(chunk_path, 'wb') as f:
                f.write(response.content)
            
            downloaded_chunks.append(chunk_path)
            print(f"   ✅ Chunk {idx + 1}/4 downloaded: {len(response.content) / 1024 / 1024:.1f} MB")
            
            time.sleep(1)  # Avoid rate limits
            
        except Exception as e:
            print(f"   ❌ Chunk {idx + 1}/4 failed: {str(e)}")
            return False
    
    print(f"✅ {filename} downloaded in {len(downloaded_chunks)} chunks")
    return True

def download_large_assets():
    """Main function to download large assets"""
    
    if not authenticate_gee():
        return
    
    # Create output directory
    os.makedirs(config.LOCAL_OUTPUT_DIR, exist_ok=True)
    
    # ← AGREGAR ESTA LÍNEA:
    existing_files = check_local_files(config.LOCAL_OUTPUT_DIR)
    
    asset_folder = config.OUTPUT_ASSET_FOLDER
    
    try:
        # List assets
        assets_response = ee.data.listAssets({'parent': asset_folder})
        assets = assets_response.get('assets', [])
        
        if not assets:
            print("❌ No assets found.")
            return
        
        print(f"🔍 Found {len(assets)} assets to download in chunks:")
        
        success_count = 0
        for i, asset in enumerate(assets, 1):
            asset_id = asset['name']
            asset_name = asset_id.split('/')[-1]
            
            # ← AGREGAR ESTA VERIFICACIÓN:
            if f"{asset_name}.tif" in existing_files:
                print(f"\n[{i}/{len(assets)}] {asset_name}")
                print("   ⏭️  SKIPPING: Already downloaded (4 chunks)")
                continue
            
            print(f"\n[{i}/{len(assets)}] {asset_name}")
            
            if download_asset_in_chunks(asset_id, asset_name):
                success_count += 1
        
        print(f"\n🎉 Download complete!")
        print(f"✅ Successfully downloaded: {success_count}/{len(assets)} assets")
        print(f"📁 Files saved to: {config.LOCAL_OUTPUT_DIR}")
        print(f"📝 Note: Large assets were split into 4 chunks each")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def download_assets_batch(asset_list, local_dir, batch_size=5):
    """
    Download assets in batches to avoid overwhelming the system.
    
    Args:
        asset_list: List of asset dictionaries
        local_dir: Local directory to save files
        batch_size: Number of assets to download per batch
    """
    total_assets = len(asset_list)
    total_batches = (total_assets + batch_size - 1) // batch_size
    
    print(f"\n📊 Download Plan:")
    print(f"   Total assets: {total_assets}")
    print(f"   Batch size: {batch_size}")
    print(f"   Total batches: {total_batches}")
    print(f"   Local directory: {local_dir}")
    
    stats = {
        'downloaded': 0,
        'skipped': 0,
        'failed': 0,
        'total_size_mb': 0
    }
    
    # Check existing files
    existing_files = check_local_files(local_dir)
    
    start_time = time.time()
    
    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, total_assets)
        
        batch_assets = asset_list[start_idx:end_idx]
        
        print(f"\n📦 === BATCH {batch_num + 1}/{total_batches} ===")
        print(f"Processing {len(batch_assets)} assets...")
        
        for i, asset in enumerate(batch_assets, 1):
            asset_name = asset['name']
            asset_path = asset['path']
            output_filename = f"{asset_name}.tif"
            
            print(f"\n[{i}/{len(batch_assets)}] {asset_name}")
            
            # Check if file already exists
            if output_filename in existing_files:
                print(f"   ⏭️  SKIPPING: {output_filename} already exists locally")
                stats['skipped'] += 1
                continue
            
            # Download the asset
            result = download_asset_to_local(asset_path, asset_name, local_dir)
            
            if result['success']:
                stats['downloaded'] += 1
                stats['total_size_mb'] += result['size_mb']
            else:
                print(f"   ❌ FAILED: {result['error']}")
                stats['failed'] += 1
            
            # Small delay between downloads
            time.sleep(2)
        
        # Progress update
        elapsed = time.time() - start_time
        progress = ((batch_num + 1) / total_batches) * 100
        
        print(f"\n📊 Batch {batch_num + 1} Complete:")
        print(f"   ✅ Downloaded: {stats['downloaded']}")
        print(f"   ⏭️  Skipped: {stats['skipped']}")
        print(f"   ❌ Failed: {stats['failed']}")
        print(f"   🎯 Progress: {progress:.1f}%")
        
        # Wait between batches
        if batch_num < total_batches - 1:
            print("⏸️  Waiting 10 seconds before next batch...")
            time.sleep(10)
    
    # Final summary
    total_time = time.time() - start_time
    print(f"\n🎉 === DOWNLOAD COMPLETE ===")
    print(f"⏱️  Total time: {total_time/60:.1f} minutes")
    print(f"✅ Files downloaded: {stats['downloaded']}")
    print(f"⏭️  Files skipped: {stats['skipped']}")
    print(f"❌ Files failed: {stats['failed']}")
    print(f"💾 Total size: {stats['total_size_mb']:.1f} MB")
    print(f"📁 Files saved to: {local_dir}")


def download_specific_test_assets():
    """Download only the test assets in chunks"""
    if not authenticate_gee():
        return
    
    # Create output directory
    os.makedirs(config.LOCAL_OUTPUT_DIR, exist_ok=True)
    
    # Check existing files
    existing_files = check_local_files(config.LOCAL_OUTPUT_DIR)
    
    asset_folder = config.OUTPUT_ASSET_FOLDER
    
    try:
        # List assets
        assets_response = ee.data.listAssets({'parent': asset_folder})
        assets = assets_response.get('assets', [])
        
        # Filter for test assets
        test_assets = [asset for asset in assets if 'TEST' in asset['name']]
        
        if not test_assets:
            print("❌ No test assets found.")
            return
        
        print(f"🔍 Found {len(test_assets)} test assets to download:")
        
        success_count = 0
        for i, asset in enumerate(test_assets, 1):
            asset_id = asset['name']
            asset_name = asset_id.split('/')[-1]
            
            # Check if already exists
            if f"{asset_name}.tif" in existing_files:
                print(f"\n[{i}/{len(test_assets)}] {asset_name}")
                print("   ⏭️  SKIPPING: Already downloaded")
                continue
            
            print(f"\n[{i}/{len(test_assets)}] {asset_name}")
            
            if download_asset_in_chunks(asset_id, asset_name):
                success_count += 1
        
        print(f"\n🎉 Test download complete!")
        print(f"✅ Successfully downloaded: {success_count}/{len(test_assets)} assets")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def download_assets_with_pattern(pattern):
    """Download assets matching a specific pattern"""
    if not authenticate_gee():
        return
    
    # Create output directory
    os.makedirs(config.LOCAL_OUTPUT_DIR, exist_ok=True)
    
    # Check existing files
    existing_files = check_local_files(config.LOCAL_OUTPUT_DIR)
    
    asset_folder = config.OUTPUT_ASSET_FOLDER
    
    try:
        # List assets
        assets_response = ee.data.listAssets({'parent': asset_folder})
        assets = assets_response.get('assets', [])
        
        # Filter for pattern
        filtered_assets = [asset for asset in assets if pattern in asset['name']]
        
        if not filtered_assets:
            print(f"❌ No assets found matching pattern '{pattern}'.")
            return
        
        print(f"🔍 Found {len(filtered_assets)} assets matching '{pattern}' to download:")
        
        success_count = 0
        for i, asset in enumerate(filtered_assets, 1):
            asset_id = asset['name']
            asset_name = asset_id.split('/')[-1]
            
            # Check if already exists
            if f"{asset_name}.tif" in existing_files:
                print(f"\n[{i}/{len(filtered_assets)}] {asset_name}")
                print("   ⏭️  SKIPPING: Already downloaded")
                continue
            
            print(f"\n[{i}/{len(filtered_assets)}] {asset_name}")
            
            if download_asset_in_chunks(asset_id, asset_name):
                success_count += 1
        
        print(f"\n🎉 Pattern download complete!")
        print(f"✅ Successfully downloaded: {success_count}/{len(filtered_assets)} assets")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def initialize_gee():
    """Initialize Google Earth Engine."""
    try:
        print("🚀 Initializing Google Earth Engine...")
        
        creds = authenticate_gee()
        if not creds:
            print("❌ Failed to authenticate with Google Earth Engine.")
            return False
        
        print("✅ Google Earth Engine initialized successfully.")
        return True
        
    except Exception as e:
        print(f"❌ Failed to initialize GEE: {str(e)}")
        return False


def download_assets_with_pattern(pattern):
    """Download assets matching a specific pattern"""
    if not authenticate_gee():
        return
    
    # Create output directory
    os.makedirs(config.LOCAL_OUTPUT_DIR, exist_ok=True)
    
    # Check existing files
    existing_files = check_local_files(config.LOCAL_OUTPUT_DIR)
    
    asset_folder = config.OUTPUT_ASSET_FOLDER
    
    try:
        # List assets
        assets_response = ee.data.listAssets({'parent': asset_folder})
        assets = assets_response.get('assets', [])
        
        # Filter for pattern
        filtered_assets = [asset for asset in assets if pattern in asset['name']]
        
        if not filtered_assets:
            print(f"❌ No assets found matching pattern '{pattern}'.")
            return
        
        print(f"🔍 Found {len(filtered_assets)} assets matching '{pattern}' to download:")
        
        success_count = 0
        for i, asset in enumerate(filtered_assets, 1):
            asset_id = asset['name']
            asset_name = asset_id.split('/')[-1]
            
            # Check if already exists
            if f"{asset_name}.tif" in existing_files:
                print(f"\n[{i}/{len(filtered_assets)}] {asset_name}")
                print("   ⏭️  SKIPPING: Already downloaded")
                continue
            
            print(f"\n[{i}/{len(filtered_assets)}] {asset_name}")
            
            if download_asset_in_chunks(asset_id, asset_name):
                success_count += 1
        
        print(f"\n🎉 Pattern download complete!")
        print(f"✅ Successfully downloaded: {success_count}/{len(filtered_assets)} assets")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def main():
    """Main download function."""
    print("📥 GEE Asset Downloader")
    print("=" * 50)
    
    print(f"📋 Current configuration:")
    print(f"   Asset folder: {config.OUTPUT_ASSET_FOLDER}")
    print(f"   Local directory: {config.LOCAL_OUTPUT_DIR}")
    
    # Check if requests is available
    try:
        import requests
        print("✅ requests library available")
    except ImportError:
        print("❌ requests library not found. Installing...")
        import subprocess
        subprocess.check_call(["pip", "install", "requests"])
        import requests
        print("✅ requests library installed")
    
    if not authenticate_gee():
        return
    
    print("\nSelect download mode:")
    print("1. Download all assets (in chunks)")
    print("2. Download specific test assets (in chunks)")
    print("3. Download assets with specific pattern (in chunks)")
    
    choice = input("Enter choice (1, 2, or 3): ").strip()
    
    if choice == '1':
        # Download all assets using chunk method
        download_large_assets()
            
    elif choice == '2':
        # Download specific test assets
        download_specific_test_assets()
        
    elif choice == '3':
        # Download assets with pattern
        pattern = input("Enter pattern to match (e.g., 'TEST' or '4-'): ").strip()
        if pattern:
            download_assets_with_pattern(pattern)
        else:
            print("❌ No pattern provided.")
    else:
        print("❌ Invalid choice. Exiting.")

if __name__ == "__main__":
    main()