"""
GEE Asset Downloader
Downloads NDVI assets from Google Earth Engine to local files.

This script is designed to run on a Debian server to download
the NDVI assets created by main.py to local GeoTIFF files.
"""

import ee
import os
import time
import config
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
    """
    Check which files already exist locally.
    
    Args:
        local_dir: Local directory path to check
        
    Returns:
        set: Set of existing filenames (with .tif extension)
    """
    if not os.path.exists(local_dir):
        print(f"📁 Creating local directory: {local_dir}")
        os.makedirs(local_dir, exist_ok=True)
        return set()
    
    existing_files = set()
    for filename in os.listdir(local_dir):
        if filename.endswith('.tif'):
            existing_files.add(filename)
    
    print(f"🔍 Found {len(existing_files)} existing local files.")
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


def download_specific_assets(asset_names, local_dir):
    """
    Download specific assets by name.
    
    Args:
        asset_names: List of asset names to download
        local_dir: Local directory to save files
    """
    print(f"\n🎯 === SELECTIVE DOWNLOAD ===")
    print(f"Downloading {len(asset_names)} specific assets...")
    
    if not initialize_gee():
        return
    
    # List all assets in folder
    all_assets = list_assets_in_folder(config.OUTPUT_ASSET_FOLDER)
    
    # Filter to requested assets
    assets_to_download = []
    for asset in all_assets:
        if asset['name'] in asset_names:
            assets_to_download.append(asset)
    
    if not assets_to_download:
        print("❌ No matching assets found.")
        return
    
    print(f"🔍 Found {len(assets_to_download)} matching assets out of {len(asset_names)} requested.")
    
    # Download the assets
    download_assets_batch(assets_to_download, local_dir, batch_size=3)


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
    
    if not initialize_gee():
        return
    
    print("\nSelect download mode:")
    print("1. Download all assets")
    print("2. Download specific test assets")
    print("3. Download assets with specific pattern")
    
    choice = input("Enter choice (1, 2, or 3): ").strip()
    
    if choice == '1':
        # Download all assets
        assets = list_assets_in_folder(config.OUTPUT_ASSET_FOLDER)
        if assets:
            download_assets_batch(assets, config.LOCAL_OUTPUT_DIR)
        else:
            print("❌ No assets found in folder.")
            
    elif choice == '2':
        # Download specific test assets
        test_assets = ['NDVI_TEST_4-p_2024-01-01_2024-12-31_overlap', 
                      'NDVI_TEST_4-n-tilde_2024-01-01_2024-12-31_overlap']
        download_specific_assets(test_assets, config.LOCAL_OUTPUT_DIR)
        
    elif choice == '3':
        # Download assets with pattern
        pattern = input("Enter pattern to match (e.g., 'TEST' or '4-'): ").strip()
        if pattern:
            assets = list_assets_in_folder(config.OUTPUT_ASSET_FOLDER)
            filtered_assets = [asset for asset in assets if pattern in asset['name']]
            
            if filtered_assets:
                print(f"🔍 Found {len(filtered_assets)} assets matching pattern '{pattern}'")
                download_assets_batch(filtered_assets, config.LOCAL_OUTPUT_DIR)
            else:
                print(f"❌ No assets found matching pattern '{pattern}'.")
        else:
            print("❌ No pattern provided.")
    else:
        print("❌ Invalid choice. Exiting.")


if __name__ == "__main__":
    main()