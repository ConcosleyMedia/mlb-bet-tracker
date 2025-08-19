#!/usr/bin/env python3
"""Test Discord webhook integration for Whop communities"""

import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def send_discord_webhook_test():
    """Send test messages to Discord webhooks"""
    
    print("🎯 TESTING DISCORD WEBHOOK INTEGRATION")
    print("=" * 50)
    
    # Common Discord webhook patterns to check in .env
    webhook_patterns = [
        'DISCORD_WEBHOOK_FREE',
        'DISCORD_WEBHOOK_VIP', 
        'DISCORD_WEBHOOK_PREMIUM',
        'STATEDGE_DISCORD_WEBHOOK',
        'STATEDGE_PLUS_WEBHOOK',
        'PREMIUM_DISCORD_WEBHOOK',
        'WEBHOOK_URL_FREE',
        'WEBHOOK_URL_VIP',
        'WEBHOOK_URL_PREMIUM'
    ]
    
    # Check environment for webhook URLs
    found_webhooks = {}
    for pattern in webhook_patterns:
        webhook_url = os.getenv(pattern)
        if webhook_url and 'discord.com/api/webhooks' in webhook_url:
            found_webhooks[pattern] = webhook_url
    
    print(f"🔍 Scanning environment for Discord webhooks...")
    
    if not found_webhooks:
        print("❌ No Discord webhook URLs found in environment")
        print("\n💡 SOLUTION: Add Discord webhooks to your .env file:")
        print("   # Discord Webhooks for each community")
        print("   DISCORD_WEBHOOK_FREE=https://discord.com/api/webhooks/...")
        print("   DISCORD_WEBHOOK_VIP=https://discord.com/api/webhooks/...")
        print("   DISCORD_WEBHOOK_PREMIUM=https://discord.com/api/webhooks/...")
        return False
    
    print(f"✅ Found {len(found_webhooks)} Discord webhooks!")
    
    # Test each webhook
    success_count = 0
    
    for webhook_name, webhook_url in found_webhooks.items():
        tier = webhook_name.split('_')[-1].lower()
        
        print(f"\n📢 Testing {webhook_name} ({tier.upper()} tier)")
        
        # Create tier-specific test message
        if tier == 'free':
            message = {
                "content": "🎯 **FREE TIER TEST** 👇💰\n\n**TEST: $1,000 Harper HR Slip**\nThis is a test from the MLB betting system!\n\n*Want VIP + Premium access? Link in bio*",
                "username": "StatEdge Bot"
            }
        elif tier in ['vip', 'plus']:
            message = {
                "content": "🔥 **VIP INSIDER TEST** ⚡\n\n**EXCLUSIVE: Harper 2+ HRs | 2k Play**\nMLB system integration test - VIP members only!\n\n*Professional insider knowledge*",
                "username": "StatEdge+ VIP"
            }
        elif tier == 'premium':
            message = {
                "content": "🌟💎 **$19,999 PREMIUM TEST** 🚀\n\n**EXCLUSIVE PREMIUM SELECTION**\nHarper 2+ Home Runs | Premium Value Play\n\n*💎 PREMIUM EXCLUSIVE - High-energy premium value*",
                "username": "StatEdge Premium"
            }
        else:
            message = {
                "content": f"🎯 **MLB SYSTEM TEST** - {tier.upper()}\n\nIntegration test successful!\nWebhook: {webhook_name}",
                "username": "MLB Bot"
            }
        
        try:
            response = requests.post(webhook_url, json=message)
            
            if response.status_code == 204:
                print(f"   ✅ SUCCESS! Test message sent to {tier.upper()} channel")
                success_count += 1
            else:
                print(f"   ❌ Failed: HTTP {response.status_code}")
                print(f"      Response: {response.text[:100]}")
                
        except Exception as e:
            print(f"   💥 Error: {e}")
    
    if success_count > 0:
        print(f"\n🎉 SUCCESS! {success_count}/{len(found_webhooks)} webhooks working!")
        print("Your MLB betting system can post to Discord channels!")
        return True
    else:
        print("\n❌ No successful webhook tests")
        return False

def create_webhook_env_template():
    """Create template for webhook environment variables"""
    
    template = """
# Add these Discord webhook URLs to your .env file:
# Get webhook URLs from your Discord server settings > Integrations > Webhooks

# StatEdge Free Community
DISCORD_WEBHOOK_FREE=https://discord.com/api/webhooks/YOUR_FREE_WEBHOOK_ID/YOUR_FREE_TOKEN

# StatEdge+ VIP Community  
DISCORD_WEBHOOK_VIP=https://discord.com/api/webhooks/YOUR_VIP_WEBHOOK_ID/YOUR_VIP_TOKEN

# StatEdge Premium Community
DISCORD_WEBHOOK_PREMIUM=https://discord.com/api/webhooks/YOUR_PREMIUM_WEBHOOK_ID/YOUR_PREMIUM_TOKEN
"""
    
    print("\n📋 WEBHOOK SETUP TEMPLATE:")
    print(template)

if __name__ == "__main__":
    if not send_discord_webhook_test():
        create_webhook_env_template()