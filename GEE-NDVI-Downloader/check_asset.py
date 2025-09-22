"""
GEE Asset Checker
Utility script to check and verify GEE assets.

This script helps verify that assets were created properly
and provides information about their status and properties.
"""

import ee
import config
from authenticate import authenticate_gee


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


def check_asset_folder(folder_path):
    """
    Check the contents of a GEE asset folder.
    
    Args:
        folder_path: Path to the GEE asset folder
    """
    try:
        print(f"📁 Checking asset folder: {folder_path}")
        
        # Check if folder exists
        try:
            folder_info = ee.data.getAsset(folder_path)
            print(f"✅ Folder exists: {folder_info.get('name', 'Unknown')}")
            print(f"   Type: {folder_info.get('type', 'Unknown')}")
            print(f"   Created: {folder_info.get('createTime', 'Unknown')}")
        except Exception as e:
            print(f"❌ Folder check failed: {str(e)}")
            return
        
        # List assets in folder
        asset_list = ee.data.listAssets({'parent': folder_path})
        assets = asset_list.get('assets', [])
        
        print(f"\n📊 Asset Summary:")
        print(f"   Total assets: {len(assets)}")
        
        if assets:
            # Group by type
            by_type = {}
            total_size = 0
            
            for asset in assets:
                asset_type = asset.get('type', 'UNKNOWN')
                by_type[asset_type] = by_type.get(asset_type, 0) + 1
                
                # Try to get size if available
                size_bytes = asset.get('sizeBytes', 0)
                if size_bytes:
                    total_size += int(size_bytes)
            
            print(f"   By type: {dict(by_type)}")
            if total_size > 0:
                total_size_mb = total_size / (1024 * 1024)
                print(f"   Total size: {total_size_mb:.1f} MB")
            
            # Show first few assets
            print(f"\n📝 First 5 assets:")
            for i, asset in enumerate(assets[:5], 1):
                asset_name = asset['name'].split('/')[-1]
                asset_type = asset.get('type', 'UNKNOWN')
                created = asset.get('createTime', 'Unknown')
                print(f"   {i}. {asset_name} ({asset_type}) - {created}")
            
            if len(assets) > 5:
                print(f"   ... and {len(assets) - 5} more assets")
        
        return assets
        
    except Exception as e:
        print(f"❌ Error checking asset folder: {str(e)}")
        return []


def check_specific_asset(asset_path):
    """
    Check details of a specific asset.
    
    Args:
        asset_path: Full path to the asset
    """
    try:
        print(f"\n🔍 Checking specific asset: {asset_path}")
        
        # Get asset info
        asset_info = ee.data.getAsset(asset_path)
        
        print(f"✅ Asset found:")
        print(f"   Name: {asset_info.get('name', 'Unknown')}")
        print(f"   Type: {asset_info.get('type', 'Unknown')}")
        print(f"   Created: {asset_info.get('createTime', 'Unknown')}")
        print(f"   Updated: {asset_info.get('updateTime', 'Unknown')}")
        
        size_bytes = asset_info.get('sizeBytes', 0)
        if size_bytes:
            size_mb = int(size_bytes) / (1024 * 1024)
            print(f"   Size: {size_mb:.1f} MB")
        
        # If it's an image, get additional info
        if asset_info.get('type') == 'IMAGE':
            try:
                image = ee.Image(asset_path)
                
                # Get bands
                band_names = image.bandNames().getInfo()
                print(f"   Bands: {band_names}")
                
                # Get geometry info
                geometry = image.geometry()
                bounds = geometry.bounds().getInfo()
                print(f"   Bounds: {bounds}")
                
                # Get pixel count (sample)
                pixel_count = image.select(band_names[0]).reduceRegion(
                    reducer=ee.Reducer.count(),
                    geometry=geometry,
                    scale=100,
                    maxPixels=1e6
                ).getInfo()
                
                count = pixel_count.get(band_names[0], 0)
                print(f"   Estimated pixels: {count:,}")
                
            except Exception as e:
                print(f"   ⚠️  Could not get image details: {str(e)}")
        
        return asset_info
        
    except Exception as e:
        print(f"❌ Asset not found or error: {str(e)}")
        return None


def search_assets_by_pattern(folder_path, pattern):
    """
    Search for assets matching a pattern.
    
    Args:
        folder_path: Path to search in
        pattern: Pattern to match in asset names
    """
    try:
        print(f"\n🔍 Searching for assets with pattern: '{pattern}'")
        
        asset_list = ee.data.listAssets({'parent': folder_path})
        assets = asset_list.get('assets', [])
        
        matching_assets = []
        for asset in assets:
            asset_name = asset['name'].split('/')[-1]
            if pattern.lower() in asset_name.lower():
                matching_assets.append(asset)
        
        print(f"📊 Found {len(matching_assets)} assets matching pattern:")
        
        for i, asset in enumerate(matching_assets[:10], 1):  # Show first 10
            asset_name = asset['name'].split('/')[-1]
            asset_type = asset.get('type', 'UNKNOWN')
            created = asset.get('createTime', 'Unknown')
            print(f"   {i}. {asset_name} ({asset_type}) - {created}")
        
        if len(matching_assets) > 10:
            print(f"   ... and {len(matching_assets) - 10} more matching assets")
        
        return matching_assets
        
    except Exception as e:
        print(f"❌ Error searching assets: {str(e)}")
        return []


def check_tasks_status():
    """Check the status of recent GEE tasks."""
    try:
        print("\n📋 Checking recent task status...")
        
        # Get task list (most recent first)
        tasks = ee.data.getTaskList()
        
        if not tasks:
            print("ℹ️  No tasks found.")
            return
        
        # Filter NDVI-related tasks
        ndvi_tasks = [task for task in tasks[:50] if 'NDVI' in task.get('description', '')]
        
        if not ndvi_tasks:
            print("ℹ️  No recent NDVI tasks found.")
            return
        
        print(f"📊 Found {len(ndvi_tasks)} recent NDVI tasks:")
        
        # Group by status
        by_status = {}
        for task in ndvi_tasks:
            status = task.get('state', 'UNKNOWN')
            by_status[status] = by_status.get(status, 0) + 1
        
        print(f"   By status: {dict(by_status)}")
        
        # Show details of first few tasks
        print(f"\n📝 Recent tasks:")
        for i, task in enumerate(ndvi_tasks[:10], 1):
            task_id = task.get('id', 'Unknown')
            description = task.get('description', 'Unknown')
            state = task.get('state', 'Unknown')
            start_time = task.get('start_timestamp_ms', 0)
            
            if start_time:
                import datetime
                start_dt = datetime.datetime.fromtimestamp(int(start_time) / 1000)
                start_str = start_dt.strftime('%Y-%m-%d %H:%M')
            else:
                start_str = 'Unknown'
            
            print(f"   {i}. {description[:40]}... - {state} ({start_str})")
        
        return ndvi_tasks
        
    except Exception as e:
        print(f"❌ Error checking tasks: {str(e)}")
        return []


def main():
    """Main asset checking function."""
    print("🔍 GEE Asset Checker")
    print("=" * 50)
    
    print(f"📋 Current configuration:")
    print(f"   Asset folder: {config.OUTPUT_ASSET_FOLDER}")
    print(f"   Grid asset: {config.ASSET_ID}")
    
    if not initialize_gee():
        return
    
    print("\nSelect check mode:")
    print("1. Check asset folder contents")
    print("2. Check specific asset")
    print("3. Search assets by pattern")
    print("4. Check recent task status")
    print("5. Check grid FeatureCollection")
    
    choice = input("Enter choice (1-5): ").strip()
    
    if choice == '1':
        # Check asset folder
        check_asset_folder(config.OUTPUT_ASSET_FOLDER)
        
    elif choice == '2':
        # Check specific asset
        asset_name = input("Enter asset name (without folder path): ").strip()
        if asset_name:
            full_path = f"{config.OUTPUT_ASSET_FOLDER}/{asset_name}"
            check_specific_asset(full_path)
        else:
            print("❌ No asset name provided.")
            
    elif choice == '3':
        # Search by pattern
        pattern = input("Enter search pattern: ").strip()
        if pattern:
            search_assets_by_pattern(config.OUTPUT_ASSET_FOLDER, pattern)
        else:
            print("❌ No pattern provided.")
            
    elif choice == '4':
        # Check task status
        check_tasks_status()
        
    elif choice == '5':
        # Check grid FeatureCollection
        try:
            print(f"\n📁 Checking grid FeatureCollection: {config.ASSET_ID}")
            fc = ee.FeatureCollection(config.ASSET_ID)
            count = fc.size().getInfo()
            print(f"✅ FeatureCollection found with {count} features")
            
            # Get first feature as example
            first_feature = fc.first().getInfo()
            properties = first_feature.get('properties', {})
            print(f"   Example properties: {list(properties.keys())}")
            print(f"   ID field '{config.ID_FIELD}': {properties.get(config.ID_FIELD, 'Not found')}")
            
        except Exception as e:
            print(f"❌ Error checking FeatureCollection: {str(e)}")
    else:
        print("❌ Invalid choice. Exiting.")


if __name__ == "__main__":
    main()