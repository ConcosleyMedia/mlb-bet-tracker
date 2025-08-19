"""Bet entry and management"""

from datetime import datetime
from typing import Optional, Dict, List
import logging
from src.database import db
from src.openai_parser import BetParser
from src.smart_validator import SmartBetValidator

logger = logging.getLogger(__name__)


class BetManager:
    """Manage bet entries and updates with smart validation"""
    
    def __init__(self):
        self.parser = BetParser()
        self.validator = SmartBetValidator()
    
    def log_bet(self, raw_input: str, community: str = 'StatEdge') -> Dict:
        """Log a new bet with smart validation"""
        
        logger.info(f"Processing bet: {raw_input}")
        
        # Smart validation first
        validation_result = self.validator.process_bet(raw_input, community)
        
        if not validation_result['success']:
            return {
                'success': False,
                'error': 'Bet validation failed',
                'validation': validation_result['validation']
            }
        
        # Parse with AI
        parsed = self.validator.parser.parse(raw_input)
        logger.info(f"AI interpretation: {parsed.get('interpretation', 'No interpretation')}")
        
        confidence = parsed.get('confidence', 0) or 0
        if confidence < 50:
            logger.warning(f"Low confidence: {confidence}%")
        
        # Get community ID
        community_result = db.fetchone(
            "SELECT community_id FROM communities WHERE community_name = %s",
            (community,)
        )
        
        if not community_result:
            logger.error(f"Community not found: {community}")
            return {'success': False, 'error': f'Community {community} not found'}
            
        community_id = community_result[0]
        
        # Use validated game context
        game_context = validation_result.get('game_context')
        game_id = game_context.get('game_id') if game_context else None
        
        # Find player and team IDs
        player_id = self.parser.find_player_id(parsed.get('player_name'))
        team_id = self.parser.find_team_id(parsed.get('team_name'))
        
        # If no game found, use fallback
        if not game_id:
            game_result = db.fetchone("""
                SELECT game_id FROM games 
                WHERE game_date = CURRENT_DATE 
                LIMIT 1
            """)
            
            if not game_result:
                # Create test game
                db.execute("""
                    INSERT INTO games (game_id, game_date, game_time, home_team_id, away_team_id, status)
                    VALUES (99999, CURRENT_DATE, CURRENT_TIMESTAMP, 143, 121, 'Scheduled')
                    ON CONFLICT (game_id) DO NOTHING
                """)
                game_id = 99999
            else:
                game_id = game_result[0]
        
        # Insert bet
        result = db.fetchone("""
            INSERT INTO bets (
                game_id, player_id, team_id,
                bet_type, bet_category, target_value, operator,
                odds, units, community_id, status,
                raw_input, ai_confidence, ai_interpretation
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Pending', %s, %s, %s
            ) RETURNING bet_id
        """, (
            game_id,
            player_id,
            team_id,
            parsed.get('bet_type', 'Unknown'),
            'player_prop' if player_id else 'team' if team_id else 'unknown',
            parsed.get('target_value'),
            parsed.get('operator'),
            parsed.get('odds', '-110'),
            parsed.get('units', 1),
            community_id,
            raw_input,
            parsed.get('confidence', 50),
            parsed.get('interpretation', '')
        ))
        
        if result:
            bet_id = result[0]
            logger.info(f"Bet logged successfully: ID {bet_id}")
            return {
                'success': True,
                'bet_id': bet_id,
                'validation': validation_result['validation']
            }
        
        return {'success': False, 'error': 'Failed to insert bet into database'}
    
    def get_active_bets(self) -> List[Dict]:
        """Get all active bets"""
        return db.fetch_dict("""
            SELECT 
                b.*,
                c.community_name,
                p.full_name as player_name,
                t.team_name
            FROM bets b
            JOIN communities c ON b.community_id = c.community_id
            LEFT JOIN players p ON b.player_id = p.player_id
            LEFT JOIN teams t ON b.team_id = t.team_id
            WHERE b.status IN ('Pending', 'Live')
            ORDER BY b.created_at DESC
        """)
    
    def get_todays_bets(self) -> List[Dict]:
        """Get bets for today's games (based on game date, not creation date)"""
        from datetime import date
        today = date.today()
        
        return db.fetch_dict("""
            SELECT 
                b.*,
                c.community_name,
                g.game_date,
                ht.team_name as home_team,
                at.team_name as away_team
            FROM bets b
            JOIN communities c ON b.community_id = c.community_id
            JOIN games g ON b.game_id = g.game_id
            JOIN teams ht ON g.home_team_id = ht.team_id
            JOIN teams at ON g.away_team_id = at.team_id
            WHERE g.game_date = %s
            ORDER BY b.created_at DESC
        """, (today,))
    
    def get_bet_counts(self) -> Dict[str, int]:
        """Get counts of bets by category"""
        from datetime import date
        today = date.today()
        
        all_bets = db.fetchone("SELECT COUNT(*) FROM bets")[0]
        
        # Count bets for TODAY'S GAMES (not bets created today)
        todays_bets = db.fetchone("""
            SELECT COUNT(*) 
            FROM bets b
            JOIN games g ON b.game_id = g.game_id
            WHERE g.game_date = %s
        """, (today,))[0]
        
        active_bets = db.fetchone("SELECT COUNT(*) FROM bets WHERE status IN ('Pending', 'Live')")[0]
        
        return {
            'all': all_bets,
            'today': todays_bets,
            'active': active_bets
        }
    
    def clear_all_bets(self) -> int:
        """Clear all bets from database and related pending messages"""
        bet_count = db.fetchone("SELECT COUNT(*) FROM bets")[0]
        msg_count = db.fetchone("SELECT COUNT(*) FROM message_log WHERE delivery_status = 'pending'")[0]
        
        if bet_count > 0:
            # Clear all bets
            db.execute("DELETE FROM bets")
            logger.info(f"Cleared {bet_count} bets from database")
        
        if msg_count > 0:
            # Clear all pending messages
            db.execute("DELETE FROM message_log WHERE delivery_status = 'pending'")
            logger.info(f"Cleared {msg_count} pending messages")
        
        return bet_count
    
    def clear_todays_bets(self) -> int:
        """Clear bets for today's games and related pending messages"""
        from datetime import date
        today = date.today()
        
        bet_count = db.fetchone("""
            SELECT COUNT(*) 
            FROM bets b
            JOIN games g ON b.game_id = g.game_id
            WHERE g.game_date = %s
        """, (today,))[0]
        
        # Count messages for today's games
        msg_count = db.fetchone("""
            SELECT COUNT(*) 
            FROM message_log m
            JOIN games g ON m.game_id = g.game_id
            WHERE g.game_date = %s AND m.delivery_status = 'pending'
        """, (today,))[0]
        
        if bet_count > 0:
            # Delete bets for today's games
            db.execute("""
                DELETE FROM bets 
                WHERE game_id IN (
                    SELECT game_id FROM games WHERE game_date = %s
                )
            """, (today,))
            logger.info(f"Cleared {bet_count} bets for today's games")
        
        if msg_count > 0:
            # Delete pending messages for today's games
            db.execute("""
                DELETE FROM message_log 
                WHERE game_id IN (
                    SELECT game_id FROM games WHERE game_date = %s
                ) AND delivery_status = 'pending'
            """, (today,))
            logger.info(f"Cleared {msg_count} pending messages for today's games")
        
        return bet_count
    
    def cancel_active_bets(self) -> int:
        """Mark all active bets as cancelled (safer than deletion)"""
        count = db.fetchone("SELECT COUNT(*) FROM bets WHERE status IN ('Pending', 'Live')")[0]
        if count > 0:
            db.execute("UPDATE bets SET status = 'Cancelled', updated_at = CURRENT_TIMESTAMP WHERE status IN ('Pending', 'Live')")
            logger.info(f"Cancelled {count} active bets")
        return count
    
    def update_old_bet_status(self) -> int:
        """Auto-update status for bets from past games"""
        from datetime import date
        today = date.today()
        
        # Mark ALL bets from past game dates as 'Completed' if still pending
        # (regardless of game status, since they're from previous days)
        result = db.execute("""
            UPDATE bets 
            SET status = 'Completed', 
                updated_at = CURRENT_TIMESTAMP
            WHERE status IN ('Pending', 'Live')
            AND game_id IN (
                SELECT game_id FROM games 
                WHERE game_date < %s
            )
        """, (today,))
        
        # Get the count of updated rows
        count = db.fetchone("""
            SELECT COUNT(*) FROM bets 
            WHERE status = 'Completed' 
            AND DATE(updated_at) = %s
            AND game_id IN (SELECT game_id FROM games WHERE game_date < %s)
        """, (today, today))
        
        count = count[0] if count else 0
        
        if count > 0:
            logger.info(f"Auto-updated {count} old bets to Completed status")
        
        return count
    
    def view_scheduled_messages(self) -> Dict:
        """Get all scheduled/pending messages with details"""
        messages = db.fetch_dict("""
            SELECT 
                m.message_id,
                m.community_id,
                c.community_name,
                m.message_type,
                m.message_title,
                m.message_content,
                m.scheduled_send_time,
                m.delivery_status,
                m.bet_id,
                m.game_id,
                m.priority_level,
                g.game_date,
                ht.team_name as home_team,
                at.team_name as away_team
            FROM message_log m
            JOIN communities c ON m.community_id = c.community_id
            LEFT JOIN games g ON m.game_id = g.game_id
            LEFT JOIN teams ht ON g.home_team_id = ht.team_id
            LEFT JOIN teams at ON g.away_team_id = at.team_id
            WHERE m.delivery_status = 'pending'
            ORDER BY m.scheduled_send_time ASC
        """)
        
        # Get summary by type
        summary = db.fetch_dict("""
            SELECT message_type, COUNT(*) as count
            FROM message_log 
            WHERE delivery_status = 'pending'
            GROUP BY message_type
            ORDER BY message_type
        """)
        
        return {
            'messages': messages,
            'summary': summary,
            'total': len(messages)
        }
    
    def clear_scheduled_messages(self, message_type: str = None) -> int:
        """Clear pending messages, optionally filtered by type"""
        if message_type:
            count = db.fetchone("""
                SELECT COUNT(*) FROM message_log 
                WHERE delivery_status = 'pending' AND message_type = %s
            """, (message_type,))[0]
            
            if count > 0:
                db.execute("""
                    DELETE FROM message_log 
                    WHERE delivery_status = 'pending' AND message_type = %s
                """, (message_type,))
                logger.info(f"Cleared {count} pending {message_type} messages")
        else:
            count = db.fetchone("""
                SELECT COUNT(*) FROM message_log WHERE delivery_status = 'pending'
            """)[0]
            
            if count > 0:
                db.execute("DELETE FROM message_log WHERE delivery_status = 'pending'")
                logger.info(f"Cleared {count} pending messages")
        
        return count