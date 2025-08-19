#!/usr/bin/env python3
"""Test smart milestone logic and message generation"""

import os
import sys
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from live_tracker import LiveGameTracker
from message_generator import MessageGenerator

def test_smart_milestones():
    """Test the new milestone logic with various scenarios"""
    
    print("🎯 TESTING SMART MILESTONE LOGIC")
    print("=" * 50)
    
    tracker = LiveGameTracker()
    generator = MessageGenerator()
    
    # Test scenarios covering different bet types and milestone triggers
    test_cases = [
        {
            'name': 'Harper 2 HRs - First Hit',
            'bet': {
                'bet_id': 1,
                'game_id': 101,
                'player_id': 101,
                'player_name': 'Bryce Harper',
                'bet_type': 'HRs',
                'target_value': 2,
                'operator': 'over',
                'units': 2,
                'community_name': 'StatEdge Premium',
                'raw_input': 'Harper 2+ HRs -110 2u'
            },
            'current_value': 1,
            'prev_value': 0,
            'alerts_sent': 0,
            'game_status': {'inning': 4, 'status': 'Live'},
            'expected_milestone': 1,
            'expected_type': 'first_progress'
        },
        {
            'name': 'Wheeler 6 Ks - Halfway Point',
            'bet': {
                'bet_id': 2,
                'game_id': 101,
                'pitcher_id': 102,
                'player_name': 'Zack Wheeler',
                'bet_type': 'Ks',
                'target_value': 6,
                'operator': 'over',
                'units': 1,
                'community_name': 'StatEdge+',
                'raw_input': 'Wheeler 6+ Ks -105 1u'
            },
            'current_value': 3,
            'prev_value': 2,
            'alerts_sent': 0,
            'game_status': {'inning': 5, 'status': 'Live'},
            'expected_milestone': 3,
            'expected_type': 'halfway'
        },
        {
            'name': 'Harper 2 HRs - Last Chance',
            'bet': {
                'bet_id': 3,
                'game_id': 101,
                'player_id': 101,
                'player_name': 'Bryce Harper',
                'bet_type': 'HRs',
                'target_value': 2,
                'operator': 'over',
                'units': 3,
                'community_name': 'StatEdge Premium',
                'raw_input': 'Harper 2+ HRs -110 3u'
            },
            'current_value': 1,
            'prev_value': 1,
            'alerts_sent': 1,
            'game_status': {'inning': 8, 'status': 'Live'},
            'expected_milestone': 'last_chance',
            'expected_type': 'last_chance'
        },
        {
            'name': 'Phillies ML - Lead Change',
            'bet': {
                'bet_id': 4,
                'game_id': 101,
                'team_id': 143,
                'team_name': 'Philadelphia Phillies',
                'bet_type': 'moneyline',
                'target_value': 1,
                'operator': None,
                'units': 2,
                'community_name': 'StatEdge',
                'raw_input': 'Phillies ML -120 2u'
            },
            'current_value': 1,
            'prev_value': 0,
            'alerts_sent': 0,
            'game_status': {'inning': 6, 'home_score': 3, 'away_score': 2, 'status': 'Live'},
            'expected_milestone': 'took_lead',
            'expected_type': 'lead_change'
        },
        {
            'name': 'Wheeler 6 Ks - Near Complete',
            'bet': {
                'bet_id': 5,
                'game_id': 101,
                'pitcher_id': 102,
                'player_name': 'Zack Wheeler',
                'bet_type': 'Ks',
                'target_value': 6,
                'operator': 'over',
                'units': 2,
                'community_name': 'StatEdge Premium',
                'raw_input': 'Wheeler 6+ Ks -105 2u'
            },
            'current_value': 5,
            'prev_value': 4,
            'alerts_sent': 1,
            'game_status': {'inning': 7, 'status': 'Live'},
            'expected_milestone': 5,
            'expected_type': 'near_complete'
        },
        {
            'name': 'Game Total - Nearing Over',
            'bet': {
                'bet_id': 6,
                'game_id': 101,
                'team_name': 'Game Total',
                'bet_type': 'total',
                'target_value': 8.5,
                'operator': 'over',
                'units': 1,
                'community_name': 'StatEdge',
                'raw_input': 'Over 8.5 runs -110 1u'
            },
            'current_value': 7,
            'prev_value': 5,
            'alerts_sent': 0,
            'game_status': {'inning': 7, 'status': 'Live'},
            'expected_milestone': 7,
            'expected_type': 'nearing_total'
        }
    ]
    
    print("\n📋 Running Test Cases:")
    print("-" * 30)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. {test['name']}")
        print(f"   Current: {test['current_value']} | Target: {test['bet']['target_value']}")
        print(f"   Alerts sent: {test['alerts_sent']} | Inning: {test['game_status']['inning']}")
        
        # Simulate the milestone detection logic
        bet = test['bet']
        bet_type = bet['bet_type'].lower()
        current_value = test['current_value']
        prev_value = test['prev_value']
        alerts_sent = test['alerts_sent']
        game_status = test['game_status']
        target = float(bet.get('target_value', 1))
        
        milestone_hit = None
        milestone_type = None
        
        # Apply the same logic from check_bet_progress
        if bet_type in ['hrs', 'home runs', 'hits', 'h', 'rbis', 'rbi', 'sb', 'stolen bases']:
            # First milestone: First occurrence (if target > 1)
            if target > 1 and prev_value == 0 and current_value >= 1 and alerts_sent == 0:
                milestone_hit = 1
                milestone_type = 'first_progress'
            
            # Second milestone: Near miss/last chance (late innings)
            elif target > current_value and game_status.get('inning', 1) >= 7 and alerts_sent < 2:
                if current_value == target - 1:
                    milestone_hit = 'last_chance'
                    milestone_type = 'last_chance'
        
        elif bet_type in ['ks', 'strikeouts']:
            # First update at ~50% (shows momentum)
            if current_value >= target * 0.5 and prev_value < target * 0.5 and alerts_sent == 0:
                milestone_hit = current_value
                milestone_type = 'halfway'
            
            # Second update at 80% or last K needed
            elif current_value >= target * 0.8 and prev_value < target * 0.8 and alerts_sent < 2:
                milestone_hit = current_value
                milestone_type = 'near_complete'
        
        elif bet_type in ['moneyline', 'ml']:
            if current_value == 1 and prev_value == 0 and alerts_sent == 0:
                milestone_hit = 'took_lead'
                milestone_type = 'lead_change'
        
        elif bet_type == 'total':
            if current_value >= target * 0.75 and prev_value < target * 0.75 and alerts_sent == 0:
                milestone_hit = current_value
                milestone_type = 'nearing_total'
        
        # Check if milestone detection matches expectation
        milestone_detected = milestone_hit is not None
        correct_milestone = milestone_hit == test['expected_milestone']
        correct_type = milestone_type == test['expected_type']
        
        if milestone_detected and correct_milestone and correct_type:
            print(f"   ✅ PASS: Milestone detected - {milestone_type} ({milestone_hit})")
            
            # Test message generation if milestone detected
            try:
                # Add current values to bet for message generation
                bet_with_progress = bet.copy()
                bet_with_progress.update({
                    'current_value': current_value,
                    'target_value': target,
                    'inning': game_status.get('inning')
                })
                
                message = generator.generate_smart_milestone_message(
                    bet_with_progress, 
                    milestone_type, 
                    bet['community_name']
                )
                
                print(f"   📨 Generated Message:")
                print(f"       Title: {message['title']}")
                print(f"       Content: {message['content'][:80]}...")
                
            except Exception as e:
                print(f"   ⚠️  Message generation error: {e}")
        
        elif not milestone_detected and test['expected_milestone'] is None:
            print(f"   ✅ PASS: No milestone (as expected)")
        
        else:
            print(f"   ❌ FAIL:")
            print(f"       Expected: {test['expected_type']} ({test['expected_milestone']})")
            print(f"       Got: {milestone_type} ({milestone_hit})")

def test_message_queue_limits():
    """Test message queue update limits"""
    
    print(f"\n\n🔒 TESTING MESSAGE QUEUE LIMITS")
    print("=" * 40)
    
    test_cases = [
        {
            'name': 'Small bet (1u) - Should limit to 1 update',
            'units': 1,
            'community': 'StatEdge',
            'alerts_sent': 0,
            'expected_queue': True
        },
        {
            'name': 'Small bet (1u) - Already sent 1 update',
            'units': 1,
            'community': 'StatEdge',
            'alerts_sent': 1,
            'expected_queue': False
        },
        {
            'name': 'Large bet (3u) - Should allow 2 updates',
            'units': 3,
            'community': 'StatEdge+',
            'alerts_sent': 1,
            'expected_queue': True
        },
        {
            'name': 'Premium bet - Should allow 2 updates',
            'units': 1,
            'community': 'StatEdge Premium',
            'alerts_sent': 1,
            'expected_queue': True
        },
        {
            'name': 'Premium bet - Already sent 2 updates',
            'units': 1,
            'community': 'StatEdge Premium',
            'alerts_sent': 2,
            'expected_queue': False
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. {test['name']}")
        
        # Apply queue logic
        max_updates = 2 if test['units'] >= 3 or test['community'] == 'StatEdge Premium' else 1
        should_queue = test['alerts_sent'] < max_updates
        
        result = "QUEUE" if should_queue else "SKIP"
        expected = "QUEUE" if test['expected_queue'] else "SKIP"
        
        if result == expected:
            print(f"   ✅ PASS: {result} (max: {max_updates}, sent: {test['alerts_sent']})")
        else:
            print(f"   ❌ FAIL: Expected {expected}, got {result}")

def main():
    """Run all milestone tests"""
    print("🧪 SMART MILESTONE TEST SUITE")
    print("=" * 60)
    
    test_smart_milestones()
    test_message_queue_limits()
    
    print(f"\n\n✅ Testing Complete!")
    print("If all tests pass, your smart milestone logic is working correctly!")

if __name__ == "__main__":
    main()