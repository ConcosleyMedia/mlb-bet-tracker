#!/usr/bin/env python3
"""Test Whop GraphQL with correct endpoint"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_corrected_graphql():
    """Test with corrected GraphQL endpoint"""
    
    api_key = os.getenv('WHOP_API_KEY')
    company_id = os.getenv('NEXT_PUBLIC_WHOP_COMPANY_ID')
    agent_user_id = os.getenv('NEXT_PUBLIC_WHOP_AGENT_USER_ID')
    free_experience_id = os.getenv('STATEDGE_FREE_EXPERIENCE_ID')
    
    print("🔍 Testing Corrected GraphQL Endpoint")
    print("=" * 45)
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-Company-Id": company_id
    }
    
    # Test 1: Simple introspection query to verify GraphQL is working
    print("\n📋 Test 1: GraphQL Introspection")
    try:
        response = requests.post(
            "https://api.whop.com/graphql",
            json={"query": "{ __schema { types { name } } }"},
            headers=headers
        )
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and '__schema' in data['data']:
                types = [t['name'] for t in data['data']['__schema']['types']]
                print(f"  ✅ GraphQL working! Found {len(types)} types")
                
                # Look for forum/post related types
                forum_types = [t for t in types if any(word in t.lower() for word in ['forum', 'post', 'experience', 'message'])]
                if forum_types:
                    print(f"  📝 Relevant types: {', '.join(forum_types[:5])}")
            else:
                print(f"  ❌ Unexpected response: {data}")
        else:
            print(f"  ❌ GraphQL failed: {response.text[:200]}")
    except Exception as e:
        print(f"  💥 Error: {e}")
    
    # Test 2: Try to query available mutations
    print("\n📋 Test 2: Available Mutations")
    try:
        mutation_query = """
        {
          __schema {
            mutationType {
              fields {
                name
                description
              }
            }
          }
        }
        """
        
        response = requests.post(
            "https://api.whop.com/graphql",
            json={"query": mutation_query},
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']['__schema']['mutationType']:
                mutations = data['data']['__schema']['mutationType']['fields']
                print(f"  ✅ Found {len(mutations)} mutations")
                
                # Look for post/forum related mutations
                post_mutations = [m for m in mutations if any(word in m['name'].lower() for word in ['post', 'forum', 'message', 'create'])]
                for mutation in post_mutations[:5]:
                    print(f"    - {mutation['name']}: {mutation.get('description', 'No description')}")
            else:
                print(f"  ❌ No mutations found")
        else:
            print(f"  ❌ Mutations query failed: {response.text[:200]}")
    except Exception as e:
        print(f"  💥 Error: {e}")
    
    # Test 3: Try the actual forum post mutation
    print("\n📋 Test 3: Forum Post Mutation")
    
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
            "title": "🎯 TEST: MLB System Integration",
            "content": "This is a test message from the MLB betting system to verify Whop forum integration is working correctly!\n\n🚀 If you can see this, the integration is successful!",
            "author_id": agent_user_id
        }
    }
    
    try:
        response = requests.post(
            "https://api.whop.com/graphql",
            json={"query": mutation, "variables": variables},
            headers=headers
        )
        
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  Response: {json.dumps(data, indent=2)}")
            
            if 'data' in data and 'createForumPost' in data['data']:
                print(f"  ✅ Forum post created successfully!")
                post = data['data']['createForumPost']
                print(f"    - ID: {post.get('id')}")
                print(f"    - Title: {post.get('title')}")
                return True
            elif 'errors' in data:
                print(f"  ❌ GraphQL errors:")
                for error in data['errors']:
                    print(f"    - {error.get('message', 'Unknown error')}")
            else:
                print(f"  ❌ Unexpected response format")
        else:
            print(f"  ❌ HTTP error: {response.text}")
            
    except Exception as e:
        print(f"  💥 Exception: {e}")
    
    return False

if __name__ == "__main__":
    success = test_corrected_graphql()
    if success:
        print("\n🎉 SUCCESS! Whop integration is working!")
    else:
        print("\n❌ Integration needs debugging")