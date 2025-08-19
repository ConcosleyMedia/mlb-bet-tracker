#!/usr/bin/env python3
"""Test simple Whop forum posting"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_simple_post():
    """Test with minimal mutation"""
    
    api_key = os.getenv('WHOP_API_KEY')
    company_id = os.getenv('NEXT_PUBLIC_WHOP_COMPANY_ID')
    agent_user_id = os.getenv('NEXT_PUBLIC_WHOP_AGENT_USER_ID')
    free_experience_id = os.getenv('STATEDGE_FREE_EXPERIENCE_ID')
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-Company-Id": company_id
    }
    
    print("🔍 Testing Simple Forum Post")
    print("=" * 35)
    
    # Try minimal mutation - just create without returning fields
    mutation = """
    mutation CreateForumPost($input: CreateForumPostInput!) {
        createForumPost(input: $input)
    }
    """
    
    variables = {
        "input": {
            "experience_id": free_experience_id,
            "title": "🎯 TEST: MLB System Works!",
            "content": "SUCCESS! The MLB betting system is now connected to Whop forums.\n\n🚀 This confirms the integration is working correctly!",
            "author_id": agent_user_id
        }
    }
    
    print(f"📝 Posting to Experience: {free_experience_id}")
    print(f"👤 Author: {agent_user_id}")
    print(f"🏢 Company: {company_id}")
    
    try:
        response = requests.post(
            "https://api.whop.com/graphql",
            json={"query": mutation, "variables": variables},
            headers=headers
        )
        
        print(f"\n🌐 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if 'data' in data and not data.get('errors'):
                print("✅ SUCCESS! Forum post created!")
                print("🎉 Check your Whop StatEdge (Free) forum for the test message!")
                return True
            elif 'errors' in data:
                print("❌ GraphQL Errors:")
                for error in data['errors']:
                    print(f"   - {error.get('message', 'Unknown error')}")
            else:
                print(f"📄 Full Response: {json.dumps(data, indent=2)}")
        else:
            print(f"❌ HTTP Error: {response.text}")
            
    except Exception as e:
        print(f"💥 Exception: {e}")
    
    return False

if __name__ == "__main__":
    if test_simple_post():
        print("\n🎯 WHOP INTEGRATION IS LIVE!")
        print("Your MLB betting system can now post to forums!")
    else:
        print("\n🔧 Still debugging the API...")