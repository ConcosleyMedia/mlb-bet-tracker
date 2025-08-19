"""Randomized marketing message scheduler"""

import random
import logging
from datetime import datetime, time, timedelta
from typing import Dict, List
from src.database import db

logger = logging.getLogger(__name__)


class MarketingScheduler:
    """Schedule randomized marketing/upsell messages"""
    
    def __init__(self):
        self.daily_limit = 1  # Max 1 marketing message per community per day
        self.time_window = (10, 20)  # Between 10am and 8pm
        
    def schedule_daily_marketing(self) -> int:
        """Schedule today's marketing messages with random timing"""
        messages_scheduled = 0
        
        # Check each community
        communities = db.fetch_dict("""
            SELECT community_id, community_name, tier_level 
            FROM communities 
            WHERE active = true
            ORDER BY tier_level
        """)
        
        for community in communities:
            # Check if we already sent marketing today
            already_sent = db.fetchone("""
                SELECT COUNT(*) 
                FROM message_log 
                WHERE community_id = %s 
                AND message_type = 'marketing'
                AND DATE(created_at) = CURRENT_DATE
            """, (community['community_id'],))[0]
            
            if already_sent > 0:
                logger.info(f"Already sent marketing to {community['community_name']} today")
                continue
            
            # Schedule based on tier
            if community['tier_level'] == 1:  # Free
                messages_scheduled += self._schedule_free_upsell(community)
            elif community['tier_level'] == 2:  # Plus
                messages_scheduled += self._schedule_plus_upsell(community)
            elif community['tier_level'] == 3:  # Premium
                messages_scheduled += self._schedule_premium_teaser(community)
        
        return messages_scheduled
    
    def _schedule_free_upsell(self, community: Dict) -> int:
        """Schedule upsell message for free tier"""
        
        # Random time between 10am-8pm
        hour = random.randint(self.time_window[0], self.time_window[1])
        minute = random.randint(0, 59)
        send_time = datetime.now().replace(hour=hour, minute=minute, second=0)
        
        # If time already passed today, schedule for tomorrow
        if send_time <= datetime.now():
            send_time += timedelta(days=1)
        
        # Random message variations
        messages = [
            {
                'title': '🔓 2-Day VIP Trial Available!',
                'content': 'Get instant access to StatEdge+ premium picks!\n\n'
                          '✅ All VIP picks for 48 hours\n'
                          '✅ Live bet tracking\n'
                          '✅ Exclusive Discord access\n\n'
                          'Start your trial now → Link in bio'
            },
            {
                'title': '💎 See What Premium Members Won Today',
                'content': 'StatEdge+ members hit 3 winners today!\n\n'
                          '• Harper 2+ HRs ✅ (+150)\n'
                          '• Phillies ML ✅ (-130)\n'
                          '• Wheeler 7+ Ks ✅ (+110)\n\n'
                          'Upgrade for tomorrow\'s picks!'
            },
            {
                'title': '🚀 Level Up Your Betting',
                'content': 'Free picks are great, but VIP is better!\n\n'
                          'StatEdge+ Features:\n'
                          '• 3-4 daily premium picks\n'
                          '• 67% win rate this month\n'
                          '• Private Discord community\n\n'
                          'Try 2 days FREE → Link in bio'
            }
        ]
        
        selected = random.choice(messages)
        
        # Queue the message
        db.execute("""
            INSERT INTO message_log (
                community_id, message_type, message_title,
                message_content, priority_level,
                scheduled_send_time
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            community['community_id'],
            'marketing',
            selected['title'],
            selected['content'],
            1,  # Low priority
            send_time
        ))
        
        logger.info(f"Scheduled free upsell for {send_time}")
        return 1
    
    def _schedule_plus_upsell(self, community: Dict) -> int:
        """Schedule premium teaser for Plus tier"""
        
        # Random afternoon time (2pm-6pm)
        hour = random.randint(14, 18)
        minute = random.randint(0, 59)
        send_time = datetime.now().replace(hour=hour, minute=minute, second=0)
        
        if send_time <= datetime.now():
            send_time += timedelta(days=1)
        
        # Premium teaser messages
        messages = [
            {
                'title': '🌟 Premium Pick Preview',
                'content': 'Premium members getting this $19.99 pick:\n\n'
                          '🔒 [LOCKED] vs [LOCKED]\n'
                          'Bet Type: Player Prop\n'
                          'Confidence: ⭐⭐⭐⭐⭐\n\n'
                          'Unlock with Premium membership!'
            },
            {
                'title': '💎 Premium Members: +18.5u This Week',
                'content': 'StatEdge Premium is crushing it!\n\n'
                          'This week\'s Premium results:\n'
                          '• Monday: +4.2u ✅\n'
                          '• Tuesday: +6.1u ✅\n'
                          '• Wednesday: +8.2u ✅\n\n'
                          'Get tomorrow\'s premium picks!'
            }
        ]
        
        selected = random.choice(messages)
        
        db.execute("""
            INSERT INTO message_log (
                community_id, message_type, message_title,
                message_content, priority_level,
                scheduled_send_time
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            community['community_id'],
            'marketing',
            selected['title'],
            selected['content'],
            1,
            send_time
        ))
        
        logger.info(f"Scheduled Plus upsell for {send_time}")
        return 1
    
    def _schedule_premium_teaser(self, community: Dict) -> int:
        """Schedule exclusive unlock for Premium tier"""
        
        # Evening time (5pm-7pm)
        hour = random.randint(17, 19)
        minute = random.randint(0, 59)
        send_time = datetime.now().replace(hour=hour, minute=minute, second=0)
        
        if send_time <= datetime.now():
            send_time += timedelta(days=1)
        
        # Exclusive content
        messages = [
            {
                'title': '🎁 FREE Premium Pick Unlocked!',
                'content': 'Exclusive for Premium members:\n\n'
                          '⚾ Dodgers/Padres Under 8.5 (-105)\n'
                          'Pitching matchup favors under\n'
                          'Wind blowing in at 15mph\n\n'
                          'This pick is FREE for Premium members only!'
            },
            {
                'title': '🔥 Premium Insider Info',
                'content': 'Sharp money alert for Premium members:\n\n'
                          'Heavy action coming in on tomorrow\'s slate\n'
                          'Our models show value on 3 plays\n\n'
                          'Full analysis dropping at 10am!'
            }
        ]
        
        selected = random.choice(messages)
        
        db.execute("""
            INSERT INTO message_log (
                community_id, message_type, message_title,
                message_content, priority_level,
                scheduled_send_time
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            community['community_id'],
            'marketing',
            selected['title'],
            selected['content'],
            1,
            send_time
        ))
        
        logger.info(f"Scheduled Premium teaser for {send_time}")
        return 1