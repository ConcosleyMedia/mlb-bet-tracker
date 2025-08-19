#!/usr/bin/env python3
"""Debug Whop API integration - Try REST API"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_whop_rest_api():
    """Test Whop REST API endpoints"""
    
    api_key = os.getenv('WHOP_API_KEY')
    company_id = os.getenv('NEXT_PUBLIC_WHOP_COMPANY_ID')
    
    print("🔍 Testing Whop REST API")
    print("=" * 40)
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Test 1: Check if we can access the company info
    print("\n📋 Test 1: Company Info")
    try:
        response = requests.get(
            f"https://api.whop.com/api/v1/companies/{company_id}",
            headers=headers
        )
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            print(f"  ✅ Company accessible")
        else:
            print(f"  ❌ Company not accessible: {response.text[:200]}")
    except Exception as e:
        print(f"  💥 Error: {e}")
    
    # Test 2: Try to list experiences
    print("\n📋 Test 2: List Experiences")
    try:
        response = requests.get(
            f"https://api.whop.com/api/v1/companies/{company_id}/experiences",
            headers=headers
        )
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Found {len(data.get('data', []))} experiences")
            for exp in data.get('data', [])[:3]:
                print(f"    - {exp.get('id', 'unknown')} ({exp.get('name', 'unnamed')})")
        else:
            print(f"  ❌ Experiences not accessible: {response.text[:200]}")
    except Exception as e:
        print(f"  💥 Error: {e}")
    
    # Test 3: Try different GraphQL endpoint
    print("\n📋 Test 3: Alternative GraphQL Endpoint")
    try:
        # Try without /v1
        response = requests.post(
            "https://api.whop.com/graphql",
            json={"query": "{ __typename }"},
            headers=headers
        )
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            print(f"  ✅ GraphQL accessible at /graphql")
        else:
            print(f"  ❌ GraphQL failed: {response.text[:200]}")
    except Exception as e:
        print(f"  💥 Error: {e}")
    
    # Test 4: Try webhook/forum posting approach
    print("\n📋 Test 4: Forum Post via REST")
    experience_id = os.getenv('STATEDGE_FREE_EXPERIENCE_ID')
    try:
        post_data = {
            "title": "TEST: MLB System Integration",
            "content": "Testing forum posting from MLB betting system"
        }
        
        response = requests.post(
            f"https://api.whop.com/api/v1/experiences/{experience_id}/posts",
            json=post_data,
            headers=headers
        )
        print(f"  Status: {response.status_code}")
        if response.status_code in [200, 201]:
            print(f"  ✅ Forum post successful!")
        else:
            print(f"  ❌ Forum post failed: {response.text[:300]}")
    except Exception as e:
        print(f"  💥 Error: {e}")

def test_whop_webhook():
    """Test if this is a webhook-based integration"""
    
    print("\n🔗 Testing Webhook Approach")
    print("=" * 40)
    
    # Check if there are webhook URLs in environment
    webhook_vars = [var for var in os.environ.keys() if 'webhook' in var.lower()]
    if webhook_vars:
        print(f"  Found webhook variables: {webhook_vars}")
        for var in webhook_vars:
            print(f"    {var}: {os.getenv(var)}")
    else:
        print("  No webhook variables found in environment")
        print("  This might require Discord/Slack webhook URLs instead of GraphQL")

if __name__ == "__main__":
    test_whop_rest_api()
    test_whop_webhook()