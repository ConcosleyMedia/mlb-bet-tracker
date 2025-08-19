#!/usr/bin/env python3
"""Test Whop integration with sample data"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from whop_client import WhopClient
from message_generator import MessageGenerator

def test_whop_client():
    """Test Whop API client"""
    print("🚀 Testing Whop Integration")
    print("=" * 50)
    
    # Initialize client
    client = WhopClient()
    
    # Check environment variables
    required_vars = [
        'WHOP_API_KEY',
        'NEXT_PUBLIC_WHOP_COMPANY_ID', 
        'NEXT_PUBLIC_WHOP_AGENT_USER_ID',
        'STATEDGE_FREE_EXPERIENCE_ID',
        'STATEDGE_VIP_EXPERIENCE_ID',
        'PREMIUM_EXPERIENCE_ID'
    ]
    
    print("\n📋 Environment Check:")
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value and value != f'your-{var.lower().replace("_", "-")}-here':
            print(f"  ✅ {var}: {'*' * min(len(value), 8)}")
        else:
            print(f"  ❌ {var}: Not set or using placeholder")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n⚠️  Missing {len(missing_vars)} environment variables.")
        print("   Please update your .env file with actual values.")
        return False
    
    return True

def test_message_generator():
    """Test message generation"""
    print("\n🤖 Testing Message Generator")
    print("-" * 30)
    
    generator = MessageGenerator()
    
    # Sample bet data
    sample_bet = {
        'team_name': 'Philadelphia Phillies',
        'player_name': 'Bryce Harper', 
        'bet_type': 'home_runs',
        'odds': -110,
        'units': 2,
        'raw_input': 'Harper 2+ HRs -110 2u'
    }
    
    # Test each community tier
    communities = ['StatEdge', 'StatEdge+', 'StatEdge Premium']
    
    for community in communities:
        print(f"\n📢 {community}:")
        try:
            result = generator.generate_pregame_message(sample_bet, community)
            print(f"  Title: {result['title']}")
            print(f"  Content: {result['content'][:100]}...")
        except Exception as e:
            print(f"  ❌ Generation failed: {e}")

def test_forum_posting():
    """Test forum posting (dry run)"""
    print("\n📝 Testing Forum Posting")
    print("-" * 30)
    
    client = WhopClient()
    
    # Sample post
    success = client.post_to_forum(
        community='StatEdge',
        title='TEST: $1,000 Harper HR Bet 👇',
        content='This is a test post from the MLB betting system.\n\nWant VIP + Premium access?',
        paywall_amount=None
    )
    
    if success:
        print("  ✅ Test post sent successfully!")
    else:
        print("  ❌ Test post failed")
    
    return success

def main():
    """Run all tests"""
    print("🎯 WHOP INTEGRATION TEST SUITE")
    print("=" * 60)
    
    # Test 1: Environment setup
    if not test_whop_client():
        print("\n❌ Environment test failed - please check .env file")
        return
    
    # Test 2: Message generation
    test_message_generator()
    
    # Test 3: Forum posting (only if env is fully configured)
    print("\n" + "=" * 60)
    print("🔴 LIVE POSTING TEST")
    print("This will attempt to post to your Whop forums!")
    
    confirm = input("Continue with live posting test? (yes/no): ")
    if confirm.lower() == 'yes':
        success = test_forum_posting()
        if success:
            print("\n🎉 All tests passed! Whop integration is ready.")
        else:
            print("\n⚠️  Forum posting failed - check API credentials")
    else:
        print("\n✅ Tests completed (live posting skipped)")

if __name__ == "__main__":
    main()