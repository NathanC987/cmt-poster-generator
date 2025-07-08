#!/usr/bin/env python3
"""
Simple test to verify Glacial Indifference font files are in place
"""

import os

def test_font_files():
    """Test that font files exist in the correct location"""
    print("🔤 Testing Glacial Indifference Font Files")
    print("=" * 50)
    
    font_dir = "app/fonts"
    expected_files = [
        "GlacialIndifference-Bold.ttf",
        "GlacialIndifference-Regular.ttf"
    ]
    
    print(f"1. Checking font directory: {font_dir}")
    if os.path.exists(font_dir):
        print(f"   ✅ Font directory exists: {os.path.abspath(font_dir)}")
    else:
        print(f"   ❌ Font directory not found: {os.path.abspath(font_dir)}")
        return False
    
    print("\n2. Checking font files...")
    all_found = True
    
    for font_file in expected_files:
        font_path = os.path.join(font_dir, font_file)
        if os.path.exists(font_path):
            file_size = os.path.getsize(font_path)
            print(f"   ✅ {font_file}: Found ({file_size:,} bytes)")
        else:
            print(f"   ❌ {font_file}: Not found")
            all_found = False
    
    print("\n3. Directory contents:")
    try:
        files = os.listdir(font_dir)
        for file in sorted(files):
            if file.endswith(('.ttf', '.otf')):
                file_path = os.path.join(font_dir, file)
                file_size = os.path.getsize(file_path)
                print(f"   📄 {file} ({file_size:,} bytes)")
            else:
                print(f"   📄 {file}")
    except Exception as e:
        print(f"   ❌ Error reading directory: {e}")
        return False
    
    print("\n" + "=" * 50)
    if all_found:
        print("🎉 All Glacial Indifference font files are in place!")
        print("🎨 Posters will use Glacial Indifference font family")
        return True
    else:
        print("⚠️  Some font files are missing")
        print("💡 Make sure both Bold and Regular variants are present")
        return False

if __name__ == "__main__":
    success = test_font_files()
    exit(0 if success else 1)
