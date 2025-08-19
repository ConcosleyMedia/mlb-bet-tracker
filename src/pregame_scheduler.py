"""Pre-game notification scheduler"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict
from src.database import db
from src.config import Config

logger = logging.getLogger(__name__)


class PregameScheduler:
    """Schedule pre-game notifications at configured intervals"""
    
    def __init__(self):
        self.alert_times = Config.PRE_GAME_ALERTS  # [120, 30, 10] minutes before
        
    def schedule_todays_pregame_alerts(self) -> int:
        """Schedule all pre-game alerts for today's bets"""
        
        # Get all pending bets for today's games
        todays_bets = db.fetch_dict("""
            SELECT DISTINCT
                b.bet_id,
                b.game_id,
                b.community_id,
                b.raw_input,
                b.odds,
                b.units,
                g.game_time,
                g.home_team_id,
                g.away_team_id,
                c.community_name
            FROM bets b
            JOIN games g ON b.game_id = g.game_id
            JOIN communities c ON b.community_id = c.community_id
            WHERE b.status = 'Pending'
            AND g.game_date = CURRENT_DATE
            AND g.status IN ('Scheduled', 'Pre-Game')
        """)
        
        if not todays_bets:
            logger.info("No pending bets for today's games")
            return 0
        
        messages_scheduled = 0
        
        # Group bets by game and community
        game_community_bets = {}
        for bet in todays_bets:
            key = (bet['game_id'], bet['community_id'])
            if key not in game_community_bets:
                game_community_bets[key] = []
            game_community_bets[key].append(bet)
        
        # Schedule alerts for each game/community combination
        for (game_id, community_id), bets in game_community_bets.items():
            game_time = bets[0]['game_time']
            community_name = bets[0]['community_name']
            
            # Schedule each alert time
            for minutes_before in self.alert_times:
                alert_time = game_time - timedelta(minutes=minutes_before)
                
                # Only schedule if time hasn't passed
                if alert_time > datetime.now():
                    # Check if already scheduled
                    existing = db.fetchone("""
                        SELECT COUNT(*) FROM message_log
                        WHERE game_id = %s
                        AND community_id = %s
                        AND message_type = 'pregame'
                        AND scheduled_send_time = %s
                    """, (game_id, community_id, alert_time))[0]
                    
                    if existing == 0:
                        # Create consolidated message for all bets
                        title = self._get_pregame_title(minutes_before, len(bets))
                        content = self._get_pregame_content(bets, minutes_before, community_name)
                        
                        # Queue the message
                        db.execute("""
                            INSERT INTO message_log (
                                community_id, message_type, message_title,
                                message_content, game_id,
                                priority_level, scheduled_send_time
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, (
                            community_id,
                            'pregame',
                            title,
                            content,
                            game_id,
                            2,  # Medium priority
                            alert_time
                        ))
                        
                        messages_scheduled += 1
                        logger.info(f"Scheduled {minutes_before}min alert for game {game_id} in {community_name}")
        
        return messages_scheduled
    
    def _get_pregame_title(self, minutes_before: int, bet_count: int) -> str:
        """Generate pre-game alert title"""
        if minutes_before >= 120:
            return f"⚾ Today's {bet_count} {'Pick' if bet_count == 1 else 'Picks'} - First Pitch in 2 Hours!"
        elif minutes_before >= 30:
            return f"⏰ 30 Minutes Until First Pitch!"
        else:
            return f"🚨 10 MINUTES - Last Chance to Tail!"
    
    def _get_pregame_content(self, bets: List[Dict], minutes_before: int, community: str) -> str:
        """Generate pre-game alert content"""
        if minutes_before >= 120:
            # Full bet details
            content = f"Today's {community} plays:\n\n"
            for bet in bets:
                content += f"• {bet['raw_input']}\n"
            content += "\n🎯 Get your bets in early!"
            
        elif minutes_before >= 30:
            # Quick reminder
            content = "Don't forget today's picks:\n\n"
            for bet in bets[:3]:  # Show max 3
                content += f"• {bet['raw_input']}\n"
            if len(bets) > 3:
                content += f"• ... and {len(bets) - 3} more!\n"
            content += "\n⏱️ 30 minutes to first pitch!"
            
        else:
            # Urgent reminder
            content = "🚨 LAST CHANCE!\n\n"
            for bet in bets[:2]:  # Show max 2
                content += f"• {bet['raw_input']}\n"
            content += "\n💨 Game starts in 10 minutes!"
        
        return content