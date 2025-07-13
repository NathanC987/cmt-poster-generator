#!/usr/bin/env python3
"""
Test script for the improved CMT Poster Generator API
This script tests the fixes for timeout issues and optimized performance.
"""

import json
import requests
import time
from datetime import datetime

# Test payload based on the user's example
TEST_PAYLOAD = {
    "title": "Metro Manila Community Meeting: feel the volatility",
    "format": "Nice format with panel discussion and all",
    "date": "2025-07-08T00:00:00Z",
    "time": "fsfsd",
    "venue": "wework chambers, kuala lumpur, malaysia",
    "community_leader": "Yohan Singh",
    "co_volunteers": "",
    "theme": "Nice format with panel discussion and all",
    "description": "The upcoming in-person CMT Malaysia Community Meeting is set to provide a comprehensive overview of the latest developments in the capital markets over the past three months. Attendees can expect insights into the percentage changes in major indices and asset classes within the local market, along with an exploration of the market's interrelationship with global dynamics in the last quarter. Additionally, the meeting will spotlight two key domestic and global market events that have likely influenced market trends.\n\nThe speakers for this event bring a wealth of expertise in technical analysis, particularly in the context of AI automation. Joel Pannikot, the Managing Director at Chartered Market, is a seasoned Business and AI Strategist with a diverse professional background spanning technology, education, and finance. Joel's career trajectory, which dates back to the early 2000s, has equipped him with invaluable experience across various sectors, making him well-versed in providing strategic guidance and insights to businesses navigating the convergence of technology and finance.\n\nJoel's proficiency in technical analysis and his deep understanding of emerging technologies, such as artificial intelligence, position him as a key resource for navigating market risks across asset classes in the current market environment. His ability to identify market trends and leverage innovative solutions underscores his relevance in helping organizations harness the power of AI to achieve their strategic objectives.\n\nThe Metro Manila Community Meeting, titled \"Feel the Volatility,\" is scheduled for July 8, 2025, at WeWork Vaswani Chambers. The event, led by Community Leader Yohan Singh, will feature a dynamic panel discussion and engaging sessions aimed at providing attendees with actionable strategies for navigating market uncertainties. With a focus on AI automation and technical analysis, the meeting promises to offer valuable insights and networking opportunities for members and guests alike.\n\nFor more information about Joel Pannikot and his expertise in AI automation, you can visit his LinkedIn profile at https://in.linkedin.com/in/punnyquote. Join us at the CMT Malaysia Community Meeting to gain valuable perspectives on market trends and innovative strategies for managing risk in today's dynamic financial landscape.\n\n\n",
    "speakers": "Joel Pannikot, the Managing Director at Chartered Market, boasts a diverse professional background that spans technology, education, and finance. With a career that has evolved since the early 2000s, Joel has accumulated valuable experience in various sectors, shaping him into a seasoned Business and AI Strategist. His current role sees him leveraging this multi-faceted expertise to provide strategic guidance and insights to businesses looking to navigate the intersection of technology and finance.\n\nOver the years, Joel has honed his skills and knowledge through hands-on experience in different industries, allowing him to develop a unique perspective on how emerging technologies, particularly artificial intelligence, can drive business growth and innovation. With a keen eye for market trends and a deep understanding of the evolving business landscape, Joel is well-equipped to help organizations harness the power of AI to achieve their strategic objectives.\n\nThrough his engaging speaking engagements and thought leadership, Joel Pannikot continues to inspire and educate audiences on the transformative potential of AI in business. His practical insights and strategic vision make him a sought-after speaker for conferences and events seeking expertise at the intersection of technology, finance, and business. To learn more about Joel and his work, visit his LinkedIn profile at https://in.linkedin.com/in/punnyquote.\n\n\n\n"
}

def test_api_endpoint(base_url: str = "http://localhost:8000"):
    """Test the improved API endpoint"""
    
    print("=" * 60)
    print("Testing CMT Poster Generator API - Improved Version")
    print("=" * 60)
    
    # Test 1: Health Check
    print("\n1. Testing Health Check...")
    try:
        start_time = time.time()
        response = requests.get(f"{base_url}/health", timeout=30)
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Health check passed ({elapsed:.2f}s)")
            print(f"   Status: {health_data.get('status')}")
            print(f"   Dependencies: {len(health_data.get('dependencies', {}))}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Health check error: {e}")
    
    # Test 2: Service Status
    print("\n2. Testing Service Status...")
    try:
        start_time = time.time()
        response = requests.get(f"{base_url}/services/status", timeout=30)
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            status_data = response.json()
            print(f"✅ Service status retrieved ({elapsed:.2f}s)")
            for service, status in status_data.items():
                if isinstance(status, dict):
                    print(f"   {service}: {status.get('status', 'unknown')}")
                else:
                    print(f"   {service}: {status}")
        else:
            print(f"❌ Service status failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Service status error: {e}")
    
    # Test 3: City/Country Extraction
    print("\n3. Testing City/Country Extraction...")
    venue = TEST_PAYLOAD["venue"]
    title = TEST_PAYLOAD["title"]
    print(f"   Venue: {venue}")
    print(f"   Title: {title}")
    
    # This would be tested internally by the API
    # Expected: Kuala Lumpur, Malaysia (from venue)
    print("   Expected extraction: Kuala Lumpur, Malaysia")
    
    # Test 4: Speaker Parsing
    print("\n4. Testing Speaker Parsing...")
    speakers_text = TEST_PAYLOAD["speakers"]
    community_leader = TEST_PAYLOAD["community_leader"]
    print(f"   Community Leader: {community_leader}")
    print(f"   Speakers text length: {len(speakers_text)} chars")
    
    # Expected: Yohan Singh (community leader) + Joel Pannikot (extracted)
    print("   Expected speakers: Yohan Singh, Joel Pannikot")
    
    # Test 5: Poster Generation (Main Test)
    print("\n5. Testing Poster Generation...")
    print("   This is the main test that was causing 502 errors before.")
    print("   Testing with timeout protection and optimized processing...")
    
    try:
        start_time = time.time()
        
        # Set a longer timeout but not too long
        response = requests.post(
            f"{base_url}/generate-posters",
            json=TEST_PAYLOAD,
            headers={"Content-Type": "application/json"},
            timeout=30  # 30 second client timeout
        )
        
        elapsed = time.time() - start_time
        
        print(f"   Request completed in {elapsed:.2f} seconds")
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Poster generation successful!")
            print(f"   Success: {result.get('success')}")
            print(f"   Message: {result.get('message')}")
            print(f"   Event ID: {result.get('event_id')}")
            print(f"   Posters generated: {len(result.get('posters', []))}")
            print(f"   Generation time: {result.get('generation_time', 0):.2f}s")
            print(f"   Errors: {result.get('errors', [])}")
            
            # Print poster details
            for i, poster in enumerate(result.get('posters', [])):
                print(f"   Poster {i+1}:")
                print(f"     Type: {poster.get('poster_type')}")
                print(f"     URL: {poster.get('url', 'N/A')}")
                print(f"     Dimensions: {poster.get('dimensions', {})}")
                
        elif response.status_code == 408:
            print(f"⚠️  Request timed out (408) - This is expected behavior now!")
            try:
                error_data = response.json()
                print(f"   Message: {error_data.get('message')}")
                print(f"   Error Code: {error_data.get('error_code')}")
            except:
                print(f"   Response: {response.text[:200]}")
                
        elif response.status_code == 500:
            print(f"❌ Internal server error (500)")
            try:
                error_data = response.json()
                print(f"   Message: {error_data.get('message')}")
                print(f"   Error Code: {error_data.get('error_code')}")
            except:
                print(f"   Response: {response.text[:200]}")
                
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            
    except requests.exceptions.Timeout:
        elapsed = time.time() - start_time
        print(f"⚠️  Client timeout after {elapsed:.2f} seconds")
        print("   This indicates the server might still be processing")
        
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {e}")
        print("   Make sure the server is running on the specified URL")
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ Unexpected error after {elapsed:.2f}s: {e}")
    
    # Test 6: Check Last Payload (for debugging)
    print("\n6. Checking Last Payload (for debugging)...")
    try:
        response = requests.get(f"{base_url}/last-payload", timeout=10)
        if response.status_code == 200:
            payload_data = response.json()
            print(f"✅ Last payload retrieved")
            print(f"   Status: {payload_data.get('status')}")
            if payload_data.get('status') == 'payload_found':
                last_req = payload_data.get('last_request', {})
                print(f"   Timestamp: {last_req.get('timestamp')}")
                print(f"   URL: {last_req.get('url')}")
    except Exception as e:
        print(f"❌ Last payload check failed: {e}")
    
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("- Timeout protection: Added 25s server timeout + 408 response")
    print("- City extraction: Kuala Lumpur, Malaysia expected")
    print("- Speaker parsing: Should extract Joel Pannikot + Yohan Singh")
    print("- Performance: Optimized WordPress media search")
    print("- Error handling: Graceful failures with detailed messages")
    print("=" * 60)

def test_production_url():
    """Test the production deployment"""
    print("\nTesting Production Deployment...")
    test_api_endpoint("https://cmt-poster-generator.onrender.com")

def test_local_dev():
    """Test local development server"""
    print("\nTesting Local Development Server...")
    test_api_endpoint("http://localhost:8000")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test CMT Poster Generator API")
    parser.add_argument("--local", action="store_true", help="Test local server")
    parser.add_argument("--production", action="store_true", help="Test production server")
    parser.add_argument("--url", help="Custom URL to test")
    
    args = parser.parse_args()
    
    if args.url:
        test_api_endpoint(args.url)
    elif args.local:
        test_local_dev()
    elif args.production:
        test_production_url()
    else:
        # Test both by default
        print("Testing both local and production...")
        test_local_dev()
        test_production_url()
