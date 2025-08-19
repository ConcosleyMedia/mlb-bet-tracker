"""Whop GraphQL API client for forum posting"""

import os
import asyncio
import aiohttp
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class WhopGraphQLClient:
    """Async Whop GraphQL API integration"""
    
    def __init__(self):
        self.api_key = os.getenv('WHOP_API_KEY')
        self.company_id = os.getenv('NEXT_PUBLIC_WHOP_COMPANY_ID')
        self.agent_user_id = os.getenv('NEXT_PUBLIC_WHOP_AGENT_USER_ID')
        
        # Forum experience IDs
        self.free_experience_id = os.getenv('STATEDGE_FREE_EXPERIENCE_ID')
        self.vip_experience_id = os.getenv('STATEDGE_VIP_EXPERIENCE_ID')
        self.premium_experience_id = os.getenv('PREMIUM_EXPERIENCE_ID')
        
        self.graphql_url = "https://api.whop.com/public-graphql"
        self.session = None
        
    def _get_headers(self) -> Dict:
        """Get authentication headers with CRITICAL fixes"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "x-on-behalf-of": self.agent_user_id,  # CRITICAL: This was missing!
            "x-company-id": self.company_id,       # CRITICAL: lowercase, not X-Company-Id
            "Content-Type": "application/json"
        }
    
    async def initialize(self):
        """Initialize async HTTP session"""
        if not self.session:
            self.session = aiohttp.ClientSession()
            
        # Test connection
        await self._test_connection()
    
    async def close(self):
        """Close async HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
    async def _test_connection(self):
        """Test GraphQL connection with simple query"""
        test_query = """
        query {
            __typename
        }
        """
        
        try:
            async with self.session.post(
                self.graphql_url,
                json={"query": test_query},
                headers=self._get_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'data' in data and '__typename' in data['data']:
                        logger.info("✅ Whop GraphQL connection successful")
                        return True
                    else:
                        logger.warning(f"GraphQL response: {data}")
                else:
                    logger.error(f"Connection test failed: {response.status}")
        except Exception as e:
            logger.error(f"Connection test error: {e}")
            
        return False
    
    async def post_free_bet(self, title: str, content: str) -> bool:
        """Post to StatEdge Free community"""
        return await self._post_to_forum(
            experience_id=self.free_experience_id,
            title=title,
            content=content,
            community_name="StatEdge Free"
        )
    
    async def post_vip_bet(self, title: str, content: str) -> bool:
        """Post to StatEdge+ VIP community"""
        return await self._post_to_forum(
            experience_id=self.vip_experience_id,
            title=title,
            content=content,
            community_name="StatEdge+ VIP"
        )
    
    async def post_premium_bet(self, title: str, content: str, paywall_amount: float = 19.99) -> bool:
        """Post to StatEdge Premium community with paywall"""
        return await self._post_to_forum(
            experience_id=self.premium_experience_id,
            title=title,
            content=content,
            paywall_amount=paywall_amount,
            community_name="StatEdge Premium"
        )
    
    async def _post_to_forum(self, 
                           experience_id: str,
                           title: str, 
                           content: str,
                           community_name: str,
                           paywall_amount: Optional[float] = None) -> bool:
        """Internal method to post to specific forum"""
        
        if not experience_id:
            logger.error(f"No experience ID for {community_name}")
            return False
        
        # GraphQL mutation for forum post with field selections
        mutation = """
        mutation CreateForumPost($input: CreateForumPostInput!) {
            createForumPost(input: $input) {
                id
            }
        }
        """
        
        variables = {
            "input": {
                "forumExperienceId": experience_id,  # Correct field name
                "title": title,
                "content": content
                # No author_id - inferred from authenticated user
            }
        }
        
        # Add paywall for premium posts
        if paywall_amount:
            variables["input"]["paywallAmount"] = paywall_amount  # Correct field name
            variables["input"]["paywallCurrency"] = "usd"  # Must be lowercase
        
        try:
            logger.info(f"Posting to {community_name}: {title}")
            
            async with self.session.post(
                self.graphql_url,
                json={"query": mutation, "variables": variables},
                headers=self._get_headers()
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    
                    if 'data' in data and not data.get('errors'):
                        logger.info(f"✅ Posted to {community_name}: {title}")
                        return True
                    elif 'errors' in data:
                        logger.error(f"❌ GraphQL errors for {community_name}:")
                        for error in data['errors']:
                            logger.error(f"  - {error.get('message', 'Unknown error')}")
                    else:
                        logger.error(f"❌ Unexpected response for {community_name}: {data}")
                else:
                    error_text = await response.text()
                    logger.error(f"❌ HTTP {response.status} for {community_name}: {error_text}")
                
        except Exception as e:
            logger.error(f"❌ Exception posting to {community_name}: {e}")
            
        return False