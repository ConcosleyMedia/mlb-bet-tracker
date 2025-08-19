"""Streak detection for cross-tier messaging"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List
from src.database import db

logger = logging.getLogger(__name__)


class StreakDetector:
    """Detect winning streaks and trigger cross-tier notifications"""
    
    def __init__(self):
        self.streak_threshold = 3  # 3 consecutive wins triggers notification
        
    def check_all_streaks(self) -> List[Dict]:
        """Check all communities for active winning streaks"""
        streaks = []
        
        # Check each community
        communities = db.fetch_dict("SELECT * FROM communities WHERE active = true")
        
        for community in communities:
            streak = self.check_community_streak(community['community_id'])
            if streak and streak['is_active']:
                streaks.append(streak)
                
        return streaks
    
    def check_community_streak(self, community_id: int) -> Dict:
        """Check if a specific community has an active winning streak"""
        
        # Get recent bets for this community
        recent_bets = db.fetch_dict("""
            SELECT 
                bet_id,
                status,
                created_at,
                settled_at,
                raw_input,
                odds,
                units
            FROM bets
            WHERE community_id = %s
            AND status IN ('Won', 'Lost')
            AND settled_at >= CURRENT_DATE - INTERVAL '7 days'
            ORDER BY settled_at DESC
            LIMIT 10
        """, (community_id,))
        
        if not recent_bets:
            return {'is_active': False}
        
        # Count consecutive wins from most recent
        consecutive_wins = 0
        winning_bets = []
        
        for bet in recent_bets:
            if bet['status'] == 'Won':
                consecutive_wins += 1
                winning_bets.append(bet)
            else:
                # Hit a loss, stop counting
                break
        
        # Check if we have an active streak
        if consecutive_wins >= self.streak_threshold:
            # Check if we've already notified about this streak
            last_notification = db.fetchone("""
                SELECT MAX(created_at) 
                FROM message_log 
                WHERE community_id = %s 
                AND message_type = 'streak'
                AND created_at >= %s
            """, (community_id, winning_bets[-1]['settled_at']))
            
            already_notified = last_notification and last_notification[0]
            
            return {
                'is_active': True,
                'community_id': community_id,
                'consecutive_wins': consecutive_wins,
                'winning_bets': winning_bets[:self.streak_threshold],
                'already_notified': bool(already_notified)
            }
        
        return {'is_active': False}
    
    def trigger_streak_notifications(self, streak: Dict) -> int:
        """Queue cross-tier streak notifications"""
        if streak['already_notified']:
            logger.info(f"Streak already notified for community {streak['community_id']}")
            return 0
        
        # Get community details
        community = db.fetchone("""
            SELECT community_name, tier_level 
            FROM communities 
            WHERE community_id = %s
        """, (streak['community_id'],))
        
        if not community:
            return 0
        
        community_name, tier_level = community
        messages_queued = 0
        
        # Determine which communities to notify
        target_communities = []
        if tier_level == 3:  # Premium
            target_communities = [1, 2, 3]  # Notify Free, Plus, Premium
        elif tier_level == 2:  # Plus
            target_communities = [1, 2]  # Notify Free, Plus
        else:  # Free
            target_communities = [1]  # Notify Free only
        
        # Queue messages for each target community
        for target_tier in target_communities:
            target_community = db.fetchone("""
                SELECT community_id, community_name 
                FROM communities 
                WHERE tier_level = %s
            """, (target_tier,))
            
            if target_community:
                target_id, target_name = target_community
                
                # Create streak message
                consecutive_wins = streak['consecutive_wins']
                title = f"🔥 {consecutive_wins}-BET WIN STREAK!"
                
                if target_tier < tier_level:
                    # Cross-tier notification
                    content = f"{community_name} members are on fire with {consecutive_wins} straight wins! 🎯\n\n"
                    content += "Recent wins:\n"
                    for bet in streak['winning_bets'][:3]:
                        content += f"• {bet['raw_input']} ✅\n"
                    content += f"\nWant access to {community_name} picks? Upgrade now!"
                else:
                    # Same-tier notification
                    content = f"We're on a {consecutive_wins}-bet winning streak! 🔥\n\n"
                    content += "Keep the momentum going!"
                
                # Queue the message
                db.execute("""
                    INSERT INTO message_log (
                        community_id, message_type, message_title,
                        message_content, priority_level,
                        scheduled_send_time
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    target_id,
                    'streak',
                    title,
                    content,
                    3,  # High priority for streaks
                    datetime.now()
                ))
                
                messages_queued += 1
                logger.info(f"Queued streak notification for {target_name}")
        
        return messages_queued