#!/usr/bin/env python3
"""
Test script for video preview improvements
Run this to verify the enhanced video preview system is working correctly
"""

import requests
import json
from pathlib import Path

def test_static_files():
    """Test that all new static files are accessible"""
    base_url = "http://localhost:5000"
    
    files_to_test = [
        "/static/device-detection.js",
        "/static/vr-support.js",
        "/static/video-preview-enhanced.js",
        "/static/video-preview-debug.js"
    ]
    
    print("🧪 Testing static file accessibility...")
    
    for file_path in files_to_test:
        try:
            response = requests.get(f"{base_url}{file_path}")
            if response.status_code == 200:
                print(f"✅ {file_path} - OK ({len(response.content)} bytes)")
            else:
                print(f"❌ {file_path} - Error {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"⚠️  Server not running - cannot test {file_path}")
            return False
    
    return True


def test_main_page():
    """Test that the main page loads with new scripts"""
    try:
        response = requests.get("http://localhost:5000")
        if response.status_code == 200:
            content = response.text
            
            # Check for expected script inclusions in main page
            # Note: VR-specific includes were removed from templates.
            # Main page should include core preview scripts.
            scripts_to_check = [
                "video-preview-enhanced.js",
                "video-preview-debug.js",
                "optimized-utils.js",
            ]
            
            print("\n🧪 Testing script inclusions in main page...")
            
            for script in scripts_to_check:
                if script in content:
                    print(f"✅ {script} - Included")
                else:
                    print(f"❌ {script} - Missing")
            
            return True
        else:
            print(f"❌ Main page error: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("⚠️  Server not running - cannot test main page")
        return False


def check_file_structure():
    """Check that all files exist in the correct locations"""
    print("\n🧪 Testing file structure...")
    
    files_to_check = [
        "static/device-detection.js",
        "static/vr-support.js",
        "static/video-preview-enhanced.js",
        "static/video-preview-debug.js",
        "static/optimized-utils.js",
        "docs/VIDEO_PREVIEW_IMPROVEMENTS.md"
    ]
    
    for file_path in files_to_check:
        path = Path(file_path)
        if path.exists():
            size = path.stat().st_size
            print(f"✅ {file_path} - Exists ({size} bytes)")
        else:
            print(f"❌ {file_path} - Missing")


def generate_test_report():
    """Generate a test report"""
    print("\n" + "="*50)
    print("🎬 VIDEO PREVIEW IMPROVEMENTS TEST REPORT")
    print("="*50)
    
    print("\n📋 What was improved:")
    print("• Enhanced cross-platform device detection")
    print("• Intelligent video preview strategy selection")
    print("• VR-specific touch controls and optimizations")
    print("• Memory management and performance monitoring")
    print("• Error handling and fallback mechanisms")
    print("• Debug utilities for troubleshooting")
    
    print("\n🎯 Expected behavior by platform:")
    print("• Desktop: Hover-based previews with 500ms delay")
    print("• Mobile: Previews disabled (shows static indicator)")
    print("• VR (Quest): VR-specific features are archived;")
    print("  stubs remain in static/ for compatibility.")
    print("• Tablets: Touch button for preview activation")
    
    print("\n🔧 To test manually:")
    print("1. Open the video server in different browsers")
    print("2. Check browser console for device detection logs")
    print("3. Try hovering/touching video thumbnails")
    print("4. Add '?debug=true' to URL for debug panel")
    print("5. Test on mobile device or VR headset if available")
    
    print("\n📊 Files created/modified:")
    check_file_structure()

if __name__ == "__main__":
    print("🎬 Testing Video Preview Improvements")
    print("="*40)
    
    # Run tests
    test_main_page()
    test_static_files()
    
    # Generate report
    generate_test_report()
    
    print("\n✨ Testing complete!")
    print("💡 Start your video server and test the improvements manually")
    