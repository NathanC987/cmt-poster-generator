#!/usr/bin/env python3
"""
Test script to verify Glacial Indifference font setup
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_font_service():
    """Test the font service configuration"""
    print("🔤 Testing Glacial Indifference Font Setup")
    print("=" * 50)
    
    try:
        from app.services.font_service import get_font_service
        
        # Initialize font service
        print("1. Initializing font service...")
        font_service = await get_font_service()
        print("   ✅ Font service initialized successfully")
        
        # Test font availability
        print("\n2. Testing font availability...")
        available_fonts = font_service.get_available_fonts()
        
        for font_type, font_path in available_fonts.items():
            if "GlacialIndifference" in font_path:
                print(f"   ✅ {font_type}: {font_path}")
            else:
                print(f"   ⚠️  {font_type}: {font_path} (fallback font)")
        
        # Test font loading
        print("\n3. Testing font loading...")
        title_font = font_service.get_title_font(48)
        subtitle_font = font_service.get_subtitle_font(28)
        body_font = font_service.get_body_font(24)
        
        print(f"   ✅ Title font loaded: {type(title_font).__name__}")
        print(f"   ✅ Subtitle font loaded: {type(subtitle_font).__name__}")
        print(f"   ✅ Body font loaded: {type(body_font).__name__}")
        
        # Run comprehensive test
        print("\n4. Running comprehensive font test...")
        test_results = font_service.test_fonts()
        
        print(f"   Available fonts: {len(test_results['available_fonts'])}")
        print(f"   Default font available: {test_results['default_font_available']}")
        
        for font_type, result in test_results['test_results'].items():
            status = result['status']
            if status == "success":
                font_path = result.get('font_path', 'default')
                if "GlacialIndifference" in font_path:
                    print(f"   ✅ {font_type}: Glacial Indifference loaded successfully")
                else:
                    print(f"   ⚠️  {font_type}: Using fallback font ({font_path})")
            else:
                print(f"   ❌ {font_type}: Error - {result.get('error', 'Unknown error')}")
        
        print("\n" + "=" * 50)
        print("🎉 Font setup test completed!")
        
        # Summary
        glacial_fonts = [path for path in available_fonts.values() if "GlacialIndifference" in path]
        if glacial_fonts:
            print(f"✅ Glacial Indifference fonts found: {len(glacial_fonts)}")
            print("🎨 Posters will use Glacial Indifference font family")
        else:
            print("⚠️  Glacial Indifference fonts not found - using system fallbacks")
            print("💡 Make sure font files are in app/fonts/ directory")
        
        return True
        
    except Exception as e:
        print(f"❌ Font service test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_font_service())
    sys.exit(0 if success else 1)
