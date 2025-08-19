#!/usr/bin/env python3
"""Debug Whop API integration"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_whop_api():
    """Debug Whop API call"""
    
    # Get credentials
    api_key = os.getenv('WHOP_API_KEY')
    company_id = os.getenv('NEXT_PUBLIC_WHOP_COMPANY_ID')
    agent_user_id = os.getenv('NEXT_PUBLIC_WHOP_AGENT_USER_ID')
    free_experience_id = os.getenv('STATEDGE_FREE_EXPERIENCE_ID')
    
    print("🔍 Debugging Whop API")
    print("=" * 40)
    
    print(f"API Key: {api_key[:10]}...")
    print(f"Company ID: {company_id}")
    print(f"Agent User ID: {agent_user_id}")
    print(f"Free Experience ID: {free_experience_id}")
    
    # Headers
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-Company-Id": company_id
    }
    
    print(f"\n📡 Headers:")
    for key, value in headers.items():
        if key == "Authorization":
            print(f"  {key}: Bearer {value[7:17]}...")
        else:
            print(f"  {key}: {value}")
    
    # GraphQL mutation
    mutation = """
    mutation CreateForumPost($input: CreateForumPostInput!) {
        createForumPost(input: $input) {
            id
            title
            content
            created_at
        }
    }
    """
    
    variables = {
        "input": {
            "experience_id": free_experience_id,
            "title": "TEST: MLB Betting System Integration",
            "content": "This is a test post from the MLB betting system to verify Whop integration is working correctly.",
            "author_id": agent_user_id
        }
    }
    
    print(f"\n📝 GraphQL Variables:")
    print(json.dumps(variables, indent=2))
    
    # Make the request
    url = "https://api.whop.com/v1/graphql"
    
    try:
        response = requests.post(
            url,
            json={"query": mutation, "variables": variables},
            headers=headers
        )
        
        print(f"\n🌐 Response:")
        print(f"  Status Code: {response.status_code}")
        print(f"  Headers: {dict(response.headers)}")
        
        try:
            response_json = response.json()
            print(f"  JSON Response:")
            print(json.dumps(response_json, indent=2))
        except:
            print(f"  Raw Response: {response.text}")
            
        if response.status_code == 200:
            print("\n✅ API call successful!")
            return True
        else:
            print(f"\n❌ API call failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n💥 Exception occurred: {e}")
        return False

if __name__ == "__main__":
    test_whop_api()