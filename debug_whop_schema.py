#!/usr/bin/env python3
"""Debug Whop GraphQL schema to find correct field names"""

import os
import sys
import asyncio
import aiohttp
import json
from dotenv import load_dotenv

load_dotenv()

async def debug_schema():
    """Query Whop GraphQL schema"""
    
    api_key = os.getenv('WHOP_API_KEY')
    company_id = os.getenv('NEXT_PUBLIC_WHOP_COMPANY_ID')
    agent_user_id = os.getenv('NEXT_PUBLIC_WHOP_AGENT_USER_ID')
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "x-on-behalf-of": agent_user_id,
        "x-company-id": company_id,
        "Content-Type": "application/json"
    }
    
    print("🔍 Debugging Whop GraphQL Schema")
    print("=" * 45)
    
    async with aiohttp.ClientSession() as session:
        
        # Query 1: Get input types
        print("\n📋 Querying Input Types...")
        input_query = """
        {
          __schema {
            types {
              name
              kind
              inputFields {
                name
                type {
                  name
                  kind
                }
              }
            }
          }
        }
        """
        
        try:
            async with session.post(
                "https://api.whop.com/public-graphql",
                json={"query": input_query},
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'data' in data:
                        types = data['data']['__schema']['types']
                        
                        # Look for CreateForumPostInput
                        for type_def in types:
                            if type_def['name'] and 'ForumPost' in type_def['name'] and 'Input' in type_def['name']:
                                print(f"\n🎯 Found: {type_def['name']}")
                                if type_def['inputFields']:
                                    for field in type_def['inputFields']:
                                        field_type = field['type']['name'] or field['type']['kind']
                                        print(f"   - {field['name']}: {field_type}")
                    else:
                        print(f"Schema query failed: {data}")
                else:
                    print(f"HTTP error: {response.status}")
        except Exception as e:
            print(f"Error querying schema: {e}")
        
        # Query 2: Get available mutations
        print("\n📋 Querying Available Mutations...")
        mutation_query = """
        {
          __schema {
            mutationType {
              fields {
                name
                args {
                  name
                  type {
                    name
                    kind
                  }
                }
              }
            }
          }
        }
        """
        
        try:
            async with session.post(
                "https://api.whop.com/public-graphql",
                json={"query": mutation_query},
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'data' in data and data['data']['__schema']['mutationType']:
                        mutations = data['data']['__schema']['mutationType']['fields']
                        
                        # Look for forum/post related mutations
                        for mutation in mutations:
                            if any(word in mutation['name'].lower() for word in ['forum', 'post', 'create']):
                                print(f"\n🎯 Mutation: {mutation['name']}")
                                for arg in mutation['args']:
                                    arg_type = arg['type']['name'] or arg['type']['kind']
                                    print(f"   - {arg['name']}: {arg_type}")
                    else:
                        print(f"Mutations query failed: {data}")
                else:
                    print(f"HTTP error: {response.status}")
        except Exception as e:
            print(f"Error querying mutations: {e}")

if __name__ == "__main__":
    asyncio.run(debug_schema())