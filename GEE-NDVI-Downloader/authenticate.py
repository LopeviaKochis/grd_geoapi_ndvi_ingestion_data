"""
Authentication script for Google Earth Engine.
Supports both OAuth (development/Windows) and Service Account (production/Debian).
"""

import ee
import json
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow

# Define the required scopes for GEE
SCOPES = [
    'https://www.googleapis.com/auth/earthengine'
]

def authenticate_service_account():
    """
    Authenticate with Google Earth Engine using Service Account.
    This method works on headless servers (Debian without GUI).
    """
    service_account_file = 'service-account-key.json'
    
    if not os.path.exists(service_account_file):
        return None
    
    try:
        print("🔑 Authenticating with service account...")
        credentials = service_account.Credentials.from_service_account_file(
            service_account_file,
            scopes=SCOPES
        )
        ee.Initialize(credentials=credentials)
        print("✅ Service account authentication successful!")
        return credentials
    except Exception as e:
        print(f"❌ Service account authentication failed: {str(e)}")
        return None

def authenticate_oauth():
    """
    Authenticate with Google Earth Engine using OAuth credentials.
    This method requires a browser (development/Windows).
    """
    credentials_file = 'credentials.json'
    token_file = 'token.json'
    
    creds = None
    
    # Check if token file exists (previously authenticated)
    if os.path.exists(token_file):
        print("📋 Loading existing OAuth credentials...")
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    # If there are no valid credentials, initiate OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing expired credentials...")
            creds.refresh(Request())
        else:
            print("🌐 Starting OAuth authentication flow...")
            if not os.path.exists(credentials_file):
                raise FileNotFoundError(
                    f"Credentials file '{credentials_file}' not found. "
                    "Please download it from Google Cloud Console."
                )
            
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_file, SCOPES)
            
            # Try to run local server (works on Windows/GUI environments)
            try:
                creds = flow.run_local_server(
                    port=8080,
                    host='localhost',
                    open_browser=True,
                    access_type='offline',  # Corregido: access_type
                    prompt='consent'        # Fuerza re-consentimiento
                )
            except Exception as e:
                # Fallback to console mode (works on headless servers)
                print("⚠️  GUI not available, using console authentication...")
                creds = flow.run_console()
        
        # Save the credentials for the next run
        print("💾 Saving credentials for future use...")
        with open(token_file, 'w') as token:
            token.write(creds.to_json())
    
    # Initialize Earth Engine with the credentials
    ee.Initialize(credentials=creds)
    print("✅ OAuth authentication successful!")
    return creds

def authenticate_gee():
    """
    Dual authentication: tries service account first, then OAuth.
    """
    print("🚀 Initializing Google Earth Engine authentication...")
    
    # Method 1: Try service account (production/Debian)
    credentials = authenticate_service_account()
    if credentials:
        return credentials
    
    # Method 2: Try OAuth (development/Windows)
    try:
        credentials = authenticate_oauth()
        return credentials
    except Exception as e:
        print(f"❌ OAuth authentication failed: {str(e)}")
        return None

def test_authentication():
    """
    Test the authentication by making a simple GEE API call.
    """
    try:
        # Test GEE access
        print("\n🧪 Testing Google Earth Engine access...")
        
        # Quick geometry test
        print("• Testing basic geometry operations...")
        peru_point = ee.Geometry.Point([-76.0, -12.0])  # Lima, Peru
        print("✅ Geometry operations working!")
        
        # Test collection access (limited)
        print("• Testing Sentinel-2 collection access...")
        test_collection = (ee.ImageCollection('COPERNICUS/S2_HARMONIZED')
                          .filterBounds(peru_point)
                          .filterDate('2024-01-01', '2024-01-31')
                          .limit(5))
        
        count = test_collection.size().getInfo()
        print(f"✅ Sentinel-2 access working! Found {count} images near Lima in Jan 2024.")
        
        # Test asset access
        print("• Testing asset access...")
        fc = ee.FeatureCollection('projects/grd-geoapi-ndvi/assets/cartas_100k')
        feature_count = fc.size().getInfo()
        print(f"✅ Asset access working! Found {feature_count} features in cartas_100k.")
        
        return True
    
    except Exception as e:
        print(f"❌ Authentication test failed: {str(e)}")
        return False

def main():
    """
    Main authentication function.
    """
    print("=== Google Earth Engine Authentication ===")
    print("This script will authenticate your access to Google Earth Engine.")
    print("Supports both service account (production) and OAuth (development).")
    print()
    
    try:
        # Authenticate
        creds = authenticate_gee()
        
        if not creds:
            print("\n❌ All authentication methods failed.")
            print("\nFor production (Debian server):")
            print("1. Create a service account in Google Cloud Console")
            print("2. Download the JSON key file")
            print("3. Save it as 'service-account-key.json' in this directory")
            print("\nFor development (Windows):")
            print("1. Download OAuth credentials from Google Cloud Console")
            print("2. Save it as 'credentials.json' in this directory")
            return
        
        # Test the authentication
        if test_authentication():
            print("\n🎉 Authentication setup complete!")
            print("✅ All systems ready for NDVI processing!")
            print("\nNext steps:")
            print("1. Review your config.py settings")
            print("2. Run 'python main.py' to start processing NDVI data")
        else:
            print("\n⚠️  Authentication completed but testing failed.")
            print("Please check your credentials and try again.")
            
    except Exception as e:
        print(f"\n❌ Authentication failed: {str(e)}")
        print("\nTroubleshooting tips:")
        print("1. Ensure you have the correct credentials file")
        print("2. Check that you have enabled the Earth Engine API")
        print("3. Verify your Google Cloud project has the necessary permissions")

if __name__ == "__main__":
    main()