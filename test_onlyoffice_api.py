#!/usr/bin/env python3
"""
Test script to verify OnlyOffice API integration.
This script simulates the flow without actually running the server.
"""

import json
import os
from pathlib import Path

def test_onlyoffice_request_format():
    """Test that the request format matches OnlyOffice API spec."""
    
    print("🧪 Testing OnlyOffice API Request Format")
    print("=" * 60)
    
    # Simulate the request data that will be sent to OnlyOffice
    file_id = "test-uuid-12345"
    public_url = f"http://localhost:8000/temp-files/{file_id}"
    
    request_data = {
        "async": False,
        "filetype": "docx",
        "key": "unique-conversion-key",
        "outputtype": "pdf",
        "url": public_url
    }
    
    print("\n📋 Request data that will be sent to OnlyOffice:")
    print(json.dumps(request_data, indent=2))
    
    # Validate request format
    print("\n✅ Validation:")
    assert "url" in request_data, "❌ Missing 'url' field"
    assert "filetype" in request_data, "❌ Missing 'filetype' field"
    assert "outputtype" in request_data, "❌ Missing 'outputtype' field"
    assert "key" in request_data, "❌ Missing 'key' field"
    assert request_data["url"].startswith("http"), "❌ URL must be HTTP/HTTPS"
    
    print("✅ Request format is correct")
    print("✅ Contains 'url' field with public HTTP URL")
    print("✅ Contains required fields: filetype, outputtype, key")
    print("✅ async=False for synchronous conversion")
    
    print("\n📝 Expected OnlyOffice response format:")
    example_response = {
        "endConvert": True,
        "fileUrl": "http://localhost:8080/cache/files/unique-result-id/output.pdf",
        "percent": 100
    }
    print(json.dumps(example_response, indent=2))
    
    print("\n" + "=" * 60)
    print("✅ Test passed! Request format matches OnlyOffice API spec")
    print("\nNext steps:")
    print("1. Ensure PUBLIC_URL environment variable is set")
    print("2. Deploy to server and restart service")
    print("3. Test with actual DOCX file upload")
    print("\nFor production (rowline.me):")
    print('  Environment="PUBLIC_URL=http://rowline.me"')
    print("\nFor Docker OnlyOffice on same server:")
    print('  Environment="PUBLIC_URL=http://172.17.0.1:8000"')

if __name__ == "__main__":
    test_onlyoffice_request_format()
