#!/usr/bin/env python3
"""Test fixed Whop integration with correct headers"""

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from whop_client import WhopGraphQLClient
from message_generator import MessageGenerator

async def test_fixed_whop():
    """Test corrected Whop integration"""
    
    print("🎯 TESTING FIXED WHOP INTEGRATION")
    print("=" * 50)
    
    # Initialize client
    client = WhopGraphQLClient()
    generator = MessageGenerator()
    
    try:
        # Initialize and test connection
        print("🔌 Initializing Whop client...")
        await client.initialize()
        
        # Test message generation
        sample_bet = {
            'team_name': 'Philadelphia Phillies',
            'player_name': 'Bryce Harper', 
            'bet_type': 'home_runs',
            'odds': -110,
            'units': 2,
            'raw_input': 'Harper 2+ HRs -110 2u'
        }
        
        print("\n🤖 Generating test messages...")
        
        # Test each community tier
        communities = ['StatEdge', 'StatEdge+', 'StatEdge Premium']
        generated_messages = {}
        
        for community in communities:
            try:
                message = generator.generate_pregame_message(sample_bet, community)
                generated_messages[community] = message
                print(f"✅ {community}: {message['title']}")
            except Exception as e:
                print(f"❌ {community} generation failed: {e}")
        
        # Test posting to each forum
        print("\n📢 LIVE FORUM POSTING TEST")
        print("=" * 35)
        
        success_count = 0
        total_tests = len(communities)
        
        for community in communities:
            if community not in generated_messages:
                continue
                
            message = generated_messages[community]
            print(f"\n📝 Posting to {community}...")
            print(f"   Title: {message['title']}")
            print(f"   Content: {message['content'][:80]}...")
            
            try:
                if community == 'StatEdge Premium':
                    success = await client.post_premium_bet(
                        title=f"🎯 TEST: {message['title']}",
                        content=f"{message['content']}\n\n🚀 This is a test from the MLB betting system!",
                        paywall_amount=19.99
                    )
                elif community == 'StatEdge+':
                    success = await client.post_vip_bet(
                        title=f"🔥 TEST: {message['title']}",
                        content=f"{message['content']}\n\n⚡ VIP test message!"
                    )
                else:  # StatEdge Free
                    success = await client.post_free_bet(
                        title=f"👇 TEST: {message['title']}",
                        content=f"{message['content']}\n\n💰 Free tier test!"
                    )
                
                if success:
                    print(f"   ✅ SUCCESS! Posted to {community}")
                    success_count += 1
                else:
                    print(f"   ❌ Failed to post to {community}")
                    
            except Exception as e:
                print(f"   💥 Exception posting to {community}: {e}")
        
        # Results summary
        print(f"\n🏆 TEST RESULTS")
        print("=" * 25)
        print(f"Successful posts: {success_count}/{total_tests}")
        
        if success_count == total_tests:
            print("🎉 ALL TESTS PASSED!")
            print("Your Whop integration is working perfectly!")
            print("Check your Whop communities for the test messages!")
        elif success_count > 0:
            print("⚠️  Partial success - some communities working")
        else:
            print("❌ All tests failed - check credentials and API setup")
        
    except Exception as e:
        print(f"💥 Critical error: {e}")
        
    finally:
        # Always close the client
        await client.close()
        print("\n🔌 Client closed")

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run async test
    asyncio.run(test_fixed_whop())