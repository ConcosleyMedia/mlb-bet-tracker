"""Production-ready live game tracking with automated message triggers"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from src.database import db
from src.mlb_api import MLBAPI

logger = logging.getLogger(__name__)


class LiveGameTracker:
    """Production live game tracker with message triggering"""
    
    def __init__(self):
        self.mlb_api = MLBAPI()
        self.milestone_thresholds = [0.25, 0.50, 0.75, 0.90, 1.0]  # 25%, 50%, 75%, 90%, 100%
    
    def get_active_game_bets(self) -> List[Dict]:
        """Get all bets for games currently in progress"""
        return db.fetch_dict("""
            SELECT DISTINCT
                b.bet_id,
                b.game_id,
                b.player_id,
                b.pitcher_id,
                b.team_id,
                b.bet_type,
                b.target_value,
                b.operator,
                b.odds,
                b.units,
                b.community_id,
                b.raw_input,
                b.status,
                g.status as game_status,
                g.inning,
                g.inning_state,
                g.home_team_id,
                g.away_team_id,
                p.full_name as player_name,
                c.community_name,
                bt.current_value as last_value,
                bt.progress_percentage as last_progress,
                bt.milestone_alerts
            FROM bets b
            JOIN games g ON b.game_id = g.game_id
            JOIN communities c ON b.community_id = c.community_id
            LEFT JOIN players p ON b.player_id = p.player_id
            LEFT JOIN bet_tracking bt ON b.bet_id = bt.bet_id
            WHERE b.status IN ('Pending', 'Live')
            AND g.game_date = DATE(TIMEZONE('America/New_York', NOW()))
            AND g.status IN ('In Progress', 'Live', 'Warmup', 'Pre-Game', 'Scheduled')
            ORDER BY b.community_id, b.bet_id
        """)
    
    def update_game_stats(self, game_id: int) -> Dict:
        """Pull live stats from MLB API for a specific game"""
        try:
            # Get live game feed
            game_data = self.mlb_api.get_game_feed(game_id)
            
            if not game_data:
                logger.warning(f"No data returned for game {game_id}")
                return {}
            
            # Extract live data
            live_data = game_data.get('liveData', {})
            box_score = live_data.get('boxscore', {})
            linescore = live_data.get('linescore', {})
            
            # Update game status
            game_state = game_data.get('gameData', {}).get('status', {})
            
            db.execute("""
                UPDATE games 
                SET status = %s,
                    inning = %s,
                    inning_state = %s,
                    home_score = %s,
                    away_score = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE game_id = %s
            """, (
                game_state.get('detailedState', 'In Progress'),
                linescore.get('currentInning', 1),
                linescore.get('inningState', 'Top'),
                linescore.get('teams', {}).get('home', {}).get('runs', 0),
                linescore.get('teams', {}).get('away', {}).get('runs', 0),
                game_id
            ))
            
            # Check if game is final
            is_final = game_state.get('abstractGameState') == 'Final'
            
            return {
                'game_id': game_id,
                'status': game_state.get('detailedState'),
                'is_final': is_final,
                'inning': linescore.get('currentInning', 1),
                'inning_state': linescore.get('inningState'),
                'boxscore': box_score
            }
            
        except Exception as e:
            logger.error(f"Failed to update game {game_id}: {e}")
            return {}
    
    def update_player_stats(self, game_id: int, box_score: Dict):
        """Update player stats from box score"""
        teams_data = box_score.get('teams', {})
        
        for side in ['home', 'away']:
            team_data = teams_data.get(side, {})
            players = team_data.get('players', {})
            
            for player_key, player_data in players.items():
                if not player_key.startswith('ID'):
                    continue
                    
                player_id = int(player_key.replace('ID', ''))
                stats = player_data.get('stats', {})
                
                # Batting stats
                if 'batting' in stats and stats['batting']:
                    batting = stats['batting']
                    
                    # Calculate total bases
                    hits = batting.get('hits', 0)
                    doubles = batting.get('doubles', 0)
                    triples = batting.get('triples', 0)
                    home_runs = batting.get('homeRuns', 0)
                    total_bases = hits + doubles + (2 * triples) + (3 * home_runs)
                    
                    db.execute("""
                        INSERT INTO player_game_stats (
                            game_id, player_id, at_bats, hits, singles,
                            doubles, triples, home_runs,
                            runs, rbis, walks, strikeouts, stolen_bases
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (game_id, player_id) DO UPDATE SET
                            at_bats = EXCLUDED.at_bats,
                            hits = EXCLUDED.hits,
                            singles = EXCLUDED.singles,
                            doubles = EXCLUDED.doubles,
                            triples = EXCLUDED.triples,
                            home_runs = EXCLUDED.home_runs,
                            runs = EXCLUDED.runs,
                            rbis = EXCLUDED.rbis,
                            walks = EXCLUDED.walks,
                            strikeouts = EXCLUDED.strikeouts,
                            stolen_bases = EXCLUDED.stolen_bases,
                            updated_at = CURRENT_TIMESTAMP
                    """, (
                        game_id, player_id,
                        batting.get('atBats', 0),
                        batting.get('hits', 0),
                        batting.get('hits', 0) - batting.get('doubles', 0) - batting.get('triples', 0) - batting.get('homeRuns', 0),
                        batting.get('doubles', 0),
                        batting.get('triples', 0),
                        batting.get('homeRuns', 0),
                        batting.get('runs', 0),
                        batting.get('rbi', 0),
                        batting.get('baseOnBalls', 0),
                        batting.get('strikeOuts', 0),
                        batting.get('stolenBases', 0)
                    ))
                
                # Pitching stats
                if 'pitching' in stats and stats['pitching']:
                    pitching = stats['pitching']
                    
                    # Ensure pitcher exists in players table first, then pitchers table
                    db.execute("""
                        INSERT INTO players (player_id, full_name, first_name, last_name)
                        VALUES (%s, 'Unknown Pitcher', 'Unknown', 'Pitcher')
                        ON CONFLICT (player_id) DO NOTHING
                    """, (player_id,))
                    
                    db.execute("""
                        INSERT INTO pitchers (pitcher_id)
                        VALUES (%s)
                        ON CONFLICT (pitcher_id) DO NOTHING
                    """, (player_id,))
                    
                    db.execute("""
                        INSERT INTO pitcher_game_stats (
                            game_id, pitcher_id, innings_pitched, 
                            strikeouts, walks_allowed, hits_allowed,
                            earned_runs, home_runs_allowed, pitch_count
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (game_id, pitcher_id) DO UPDATE SET
                            innings_pitched = EXCLUDED.innings_pitched,
                            strikeouts = EXCLUDED.strikeouts,
                            walks_allowed = EXCLUDED.walks_allowed,
                            hits_allowed = EXCLUDED.hits_allowed,
                            earned_runs = EXCLUDED.earned_runs,
                            home_runs_allowed = EXCLUDED.home_runs_allowed,
                            pitch_count = EXCLUDED.pitch_count,
                            updated_at = CURRENT_TIMESTAMP
                    """, (
                        game_id, player_id,
                        float(pitching.get('inningsPitched', '0.0') or '0.0'),
                        pitching.get('strikeOuts', 0),
                        pitching.get('baseOnBalls', 0),
                        pitching.get('hits', 0),
                        pitching.get('earnedRuns', 0),
                        pitching.get('homeRuns', 0),
                        pitching.get('numberOfPitches', 0)
                    ))
    
    def check_bet_progress(self, bet: Dict) -> Dict:
        """Check progress on a specific bet with smart milestone logic"""
        bet_type = bet['bet_type'].lower()
        current_value = 0
        game_id = bet['game_id']
        player_id = bet.get('player_id') or bet.get('pitcher_id')
        
        # Get previous tracking data
        prev_tracking = db.fetchone("""
            SELECT current_value, milestone_alerts, alert_sent
            FROM bet_tracking 
            WHERE bet_id = %s
        """, (bet['bet_id'],))
        
        prev_value = float(prev_tracking[0]) if prev_tracking else 0
        milestone_alerts = prev_tracking[1] if prev_tracking else {}
        alerts_sent = len(milestone_alerts) if milestone_alerts else 0
        
        # Map bet types to database columns
        stat_mapping = {
            'hrs': ('player_game_stats', 'home_runs'),
            'home runs': ('player_game_stats', 'home_runs'),
            'hits': ('player_game_stats', 'hits'),
            'h': ('player_game_stats', 'hits'),
            'total bases': ('player_game_stats', 'total_bases_calculated'),
            'bases': ('player_game_stats', 'total_bases_calculated'),
            'ks': ('pitcher_game_stats', 'strikeouts'),
            'strikeouts': ('pitcher_game_stats', 'strikeouts'),
            'rbis': ('player_game_stats', 'rbis'),
            'rbi': ('player_game_stats', 'rbis'),
            'stolen bases': ('player_game_stats', 'stolen_bases'),
            'sb': ('player_game_stats', 'stolen_bases'),
            'runs': ('player_game_stats', 'runs'),
            'walks': ('player_game_stats', 'walks'),
            'bb': ('player_game_stats', 'walks')
        }
        
        # Get current stat value
        if bet_type in stat_mapping:
            table, column = stat_mapping[bet_type]
            player_column = 'pitcher_id' if table == 'pitcher_game_stats' else 'player_id'
            
            # Special handling for total bases calculation
            if column == 'total_bases_calculated':
                stat = db.fetchone(f"""
                    SELECT singles, doubles, triples, home_runs FROM {table}
                    WHERE game_id = %s AND {player_column} = %s
                """, (game_id, player_id))
                
                if stat:
                    singles, doubles, triples, home_runs = stat
                    # Correct total bases calculation: singles(1) + doubles(2) + triples(3) + home_runs(4)
                    current_value = float((singles or 0) * 1 + (doubles or 0) * 2 + (triples or 0) * 3 + (home_runs or 0) * 4)
                else:
                    current_value = 0.0
            else:
                stat = db.fetchone(f"""
                    SELECT {column} FROM {table}
                    WHERE game_id = %s AND {player_column} = %s
                """, (game_id, player_id))
                
                current_value = float(stat[0]) if stat else 0.0
        
        # Team bets (moneyline, spread, total)
        elif bet_type in ['moneyline', 'ml', 'spread', 'total']:
            game_info = db.fetchone("""
                SELECT home_score, away_score, status, 
                       home_team_id, away_team_id
                FROM games WHERE game_id = %s
            """, (game_id,))
            
            if game_info:
                home_score, away_score, status, home_id, away_id = game_info
                
                if bet_type in ['moneyline', 'ml']:
                    # For moneyline, only mark as won if game is FINAL and team won
                    if status in ['Final', 'Game Over', 'Completed']:
                        # Game is final - check who won
                        if bet['team_id'] == home_id:
                            current_value = 1 if home_score > away_score else 0
                        else:
                            current_value = 1 if away_score > home_score else 0
                    else:
                        # Game is still live - show progress but don't mark as hit
                        current_value = 0
                        
                elif bet_type == 'total':
                    current_value = home_score + away_score
        
        # Calculate progress
        target = float(bet.get('target_value') or 1)
        progress = (current_value / target * 100) if target > 0 else 0
        
        # Determine if bet is hit based on operator
        operator = bet.get('operator', 'over')
        
        # Get game status for smart milestone logic
        game_status = db.fetchone("""
            SELECT inning, inning_state, status, home_score, away_score
            FROM games WHERE game_id = %s
        """, (game_id,))
        
        game_status = {
            'inning': game_status[0] if game_status else 1,
            'inning_state': game_status[1] if game_status else 'Top',
            'status': game_status[2] if game_status else 'Live',
            'home_score': game_status[3] if game_status else 0,
            'away_score': game_status[4] if game_status else 0
        }
        
        # Smart milestone detection based on bet type
        milestone_hit = None
        milestone_type = None
        
        # Player props: Smart thresholds based on target value
        if bet_type.lower() in ['hrs', 'home runs', 'hits', 'h', 'rbis', 'rbi', 'sb', 'stolen bases', 'total bases', 'bases']:
            target = float(bet.get('target_value', 2))
            
            # Low targets (≤2.5): Trigger on first progress
            if target <= 2.5:
                if prev_value == 0 and current_value >= 1 and alerts_sent == 0:
                    milestone_hit = 1
                    milestone_type = 'first_progress'
            
            # Medium targets (2.5-4.0): Trigger at 50% and near completion
            elif target <= 4.0:
                if current_value >= target * 0.5 and prev_value < target * 0.5 and alerts_sent == 0:
                    milestone_hit = current_value
                    milestone_type = 'halfway'
                elif current_value >= target * 0.8 and prev_value < target * 0.8 and alerts_sent < 2:
                    milestone_hit = current_value
                    milestone_type = 'near_complete'
            
            # High targets (>4.0): Use existing 50% and 80% logic
            else:
                if current_value >= target * 0.5 and prev_value < target * 0.5 and alerts_sent == 0:
                    milestone_hit = current_value
                    milestone_type = 'halfway'
                elif current_value >= target * 0.8 and prev_value < target * 0.8 and alerts_sent < 2:
                    milestone_hit = current_value
                    milestone_type = 'near_complete'
        
        # Strikeouts: Smart thresholds based on target value
        elif bet_type in ['ks', 'strikeouts']:
            target = float(bet.get('target_value', 6))
            
            # Low targets (≤2.5): Trigger on first strikeout
            if target <= 2.5:
                if prev_value == 0 and current_value >= 1 and alerts_sent == 0:
                    milestone_hit = 1
                    milestone_type = 'first_progress'
            
            # Medium/High targets (>2.5): Use 50% and 80% thresholds
            else:
                # First update at ~50% (shows momentum)
                if current_value >= target * 0.5 and prev_value < target * 0.5 and alerts_sent == 0:
                    milestone_hit = current_value
                    milestone_type = 'halfway'
                
                # Second update at 80% or last K needed
                elif current_value >= target * 0.8 and prev_value < target * 0.8 and alerts_sent < 2:
                    milestone_hit = current_value
                    milestone_type = 'near_complete'
        
        # Moneyline: Update on lead changes
        elif bet_type in ['moneyline', 'ml']:
            if current_value == 1 and prev_value == 0 and alerts_sent == 0:
                milestone_hit = 'took_lead'
                milestone_type = 'lead_change'
        
        # Spread: Update when first covered
        elif bet_type == 'spread':
            if current_value >= target and prev_value < target and alerts_sent == 0:
                milestone_hit = 'covering'
                milestone_type = 'spread_covered'
        
        # Totals: Smart thresholds based on target value
        elif bet_type == 'total':
            target = float(bet.get('target_value', 8.5))
            
            # Low targets (≤2.5): Trigger on first score
            if target <= 2.5:
                if prev_value == 0 and current_value >= 1 and alerts_sent == 0:
                    milestone_hit = 1
                    milestone_type = 'first_progress'
            
            # Higher targets: Use 75% threshold
            else:
                if current_value >= target * 0.75 and prev_value < target * 0.75 and alerts_sent == 0:
                    milestone_hit = current_value
                    milestone_type = 'nearing_total'
        
        # Check if bet is hit (case-insensitive operator comparison)
        is_hit = False
        operator_lower = operator.lower() if operator else None
        
        if operator_lower == 'over':
            is_hit = current_value > target
        elif operator_lower == 'under':
            is_hit = current_value < target
        elif operator_lower == 'exactly':
            is_hit = current_value == target
        elif operator is None and bet_type in ['moneyline', 'ml']:
            is_hit = current_value == 1
        
        return {
            'bet_id': bet['bet_id'],
            'game_id': game_id,
            'current_value': current_value,
            'target_value': target,
            'progress_percentage': min((current_value / target * 100) if target > 0 else 0, 100),
            'is_hit': is_hit,
            'operator': operator,
            'milestone_hit': milestone_hit,
            'milestone_type': milestone_type,
            'last_value': prev_value,
            'value_changed': current_value != prev_value,
            'alerts_sent': alerts_sent
        }
    
    def update_bet_tracking(self, bet: Dict, progress: Dict, game_status: Dict):
        """Update bet tracking with milestone alerts"""
        
        # Update or insert tracking record
        existing = db.fetchone(
            "SELECT tracking_id, milestone_alerts FROM bet_tracking WHERE bet_id = %s",
            (bet['bet_id'],)
        )
        
        milestone_alerts = {}
        if existing:
            tracking_id, alerts = existing
            milestone_alerts = alerts or {}
        
        # Record new milestone
        if progress['milestone_hit']:
            milestone_key = str(progress['milestone_hit'])
            milestone_alerts[milestone_key] = {
                'hit_at': datetime.now().isoformat(),
                'inning': game_status.get('inning', 1),
                'value': progress['current_value']
            }
        
        # Insert or update tracking - check if exists first
        existing_tracking = db.fetchone(
            "SELECT tracking_id FROM bet_tracking WHERE bet_id = %s",
            (bet['bet_id'],)
        )
        
        if existing_tracking:
            # Update existing
            db.execute("""
                UPDATE bet_tracking SET
                    current_value = %s,
                    progress_percentage = %s,
                    last_update_inning = %s,
                    milestone_alerts = %s::jsonb,
                    updated_at = CURRENT_TIMESTAMP
                WHERE bet_id = %s
            """, (
                progress['current_value'],
                progress['progress_percentage'],
                game_status.get('inning', 1),
                json.dumps(milestone_alerts) if milestone_alerts else '{}',
                bet['bet_id']
            ))
        else:
            # Insert new
            db.execute("""
                INSERT INTO bet_tracking (
                    bet_id, game_id, current_value, target_value,
                    progress_percentage, is_live, last_update_inning,
                    milestone_alerts
                ) VALUES (%s, %s, %s, %s, %s, true, %s, %s::jsonb)
            """, (
                bet['bet_id'],
                bet['game_id'],
                progress['current_value'],
                progress['target_value'],
                progress['progress_percentage'],
                game_status.get('inning', 1),
                json.dumps(milestone_alerts) if milestone_alerts else '{}'
            ))
        
        # Update bet status
        new_status = None
        if progress['is_hit']:
            new_status = 'Won'
        elif game_status.get('is_final'):
            new_status = 'Lost'
        elif bet['status'] == 'Pending':
            new_status = 'Live'
        
        if new_status:
            db.execute("""
                UPDATE bets 
                SET status = %s,
                    result_value = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE bet_id = %s
            """, (new_status, progress['current_value'], bet['bet_id']))
    
    def queue_message(self, bet: Dict, progress: Dict, message_type: str, game_status: Dict):
        """Queue contextual messages based on smart milestones"""
        
        # Skip if we've already sent max updates (1-2 based on bet value)
        max_updates = 2 if bet.get('units', 1) >= 3 or bet.get('community_name') == 'StatEdge Premium' else 1
        if progress.get('alerts_sent', 0) >= max_updates and message_type != 'won':
            return
        
        # Generate contextual message based on milestone type
        milestone_type = progress.get('milestone_type')
        
        if message_type == 'milestone' and milestone_type:
            if milestone_type == 'first_progress':
                # First progress for low targets (hits, bases, etc.)
                player_name = bet.get('player_name', 'Player')
                bet_type_display = bet.get('bet_type', 'stat')
                current_val = int(progress['current_value'])
                target_val = progress['target_value']
                
                # Calculate remaining with proper betting math
                import math
                needed_total = math.ceil(target_val) if target_val != int(target_val) else int(target_val) + 1
                remaining = max(0, needed_total - current_val)
                
                message_title = f"⚾ {player_name} gets the first!"
                
                if remaining == 1:
                    message_content = f"{player_name} got {current_val}! Just 1 more {bet_type_display.lower()} to go! 🎯"
                else:
                    message_content = f"{player_name} got {current_val}! Need {remaining} more {bet_type_display.lower()} to cash! 🎯"
            
            elif milestone_type == 'halfway':
                # Strikeouts momentum with bet details
                player_name = bet.get('player_name', 'Pitcher')
                current_val = int(progress['current_value'])
                target_val = int(progress['target_value'])
                remaining = target_val - current_val
                
                message_title = f"🔥 {player_name} Strikeouts"
                message_content = f"{player_name} has {current_val} Ks - need {remaining} more for Over {target_val}! 💪"
            
            elif milestone_type == 'last_chance':
                # Late game opportunity
                message_title = f"👀 {bet['player_name']} - Last chance!"
                message_content = f"{bet['player_name']} needs 1 more {bet['bet_type']} - " \
                                f"{game_status.get('inning', 'late')} inning, let's see some magic! ✨"
            
            elif milestone_type == 'lead_change':
                # Moneyline update
                team_name = bet.get('team_name') or 'Team'
                message_title = f"💪 {team_name} takes the lead!"
                score_info = f"{game_status.get('home_score', '?')}-{game_status.get('away_score', '?')}"
                message_content = f"{team_name} now leading {score_info} in the {game_status.get('inning', '?')}th! 🎯"
            
            elif milestone_type == 'spread_covered':
                # Spread update
                team_name = bet.get('team_name') or 'Team'
                message_title = f"📈 {team_name} covering the spread!"
                message_content = f"{team_name} now covering {bet.get('target_value', 'the spread')}! Keep it going 🔥"
            
            elif milestone_type == 'nearing_total':
                # Totals update - simple 1-line format with game info
                current_val = int(progress['current_value'])
                target_val = progress['target_value']
                
                # Get game info to identify which total bet
                game_info = db.fetchone("""
                    SELECT home_team_id, away_team_id 
                    FROM games WHERE game_id = %s
                """, (bet['game_id'],))
                
                if game_info:
                    home_team = db.fetchone("SELECT team_name FROM teams WHERE team_id = %s", (game_info[0],))
                    away_team = db.fetchone("SELECT team_name FROM teams WHERE team_id = %s", (game_info[1],))
                    team_names = f"{away_team[0] if away_team else 'Away'} vs {home_team[0] if home_team else 'Home'}"
                else:
                    team_names = "Game"
                
                # Use proper betting math
                import math
                needed_total = math.ceil(target_val) if target_val != int(target_val) else int(target_val) + 1
                remaining = max(0, needed_total - current_val)
                
                message_title = f"🎯 {team_names} Total Update"
                message_content = f"{team_names} Total at {current_val} - need {remaining} more for Over {target_val}! 🔥"
            
            elif milestone_type == 'near_complete':
                # Near completion with bet details
                player_name = bet.get('player_name', 'Player')
                current_val = int(progress['current_value'])
                target_val = int(progress['target_value'])
                bet_type_display = bet.get('bet_type', 'stat')
                remaining = target_val - current_val
                
                message_title = f"🔥 {player_name} Almost There!"
                message_content = f"{player_name} has {current_val} {bet_type_display.lower()} - need {remaining} more for Over {target_val}! 🎯"
            
            else:
                # Fallback
                return
        
        elif message_type == 'won':
            # Win messages show bet details for all tiers (no paywall for results)
            message_title = f"🎉 WINNER - {bet.get('player_name') or bet.get('team_name', 'Bet')}"
            message_content = f"{bet['raw_input']} ✅ HITS! " \
                            f"Final: {progress['current_value']}/{progress['target_value']} " \
                            f"| {bet['odds']} | {bet['units']}u 💰"
        
        else:
            return
        
        # Insert into message queue
        db.execute("""
            INSERT INTO message_log (
                community_id, message_type, message_title,
                message_content, bet_id, game_id,
                priority_level, scheduled_send_time
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            bet['community_id'],
            message_type,
            message_title,
            message_content,
            bet['bet_id'],
            bet['game_id'],
            2 if message_type == 'won' else 1,
            datetime.now()
        ))
        
        logger.info(f"Queued {message_type} ({milestone_type}) message for bet {bet['bet_id']}")
    
    def track_all_live_games(self) -> Dict:
        """Main tracking loop for all live games - production ready"""
        start_time = datetime.now()
        logger.info(f"Starting live tracking run at {start_time}")
        
        tracking_summary = {
            'start_time': start_time,
            'games_tracked': 0,
            'bets_checked': 0,
            'bets_updated': 0,
            'messages_queued': 0,
            'winners': [],
            'errors': []
        }
        
        try:
            # Get active bets
            active_bets = self.get_active_game_bets()
            tracking_summary['bets_checked'] = len(active_bets)
            
            if not active_bets:
                logger.info("No active bets to track")
                return tracking_summary
            
            # Group by game for efficiency
            games_to_track = {}
            for bet in active_bets:
                game_id = bet['game_id']
                if game_id not in games_to_track:
                    games_to_track[game_id] = []
                games_to_track[game_id].append(bet)
            
            tracking_summary['games_tracked'] = len(games_to_track)
            logger.info(f"Tracking {len(games_to_track)} games with {len(active_bets)} active bets")
            
            # Update each game
            for game_id, bets in games_to_track.items():
                try:
                    logger.info(f"Updating game {game_id} with {len(bets)} bets...")
                    
                    # Get live stats
                    game_update = self.update_game_stats(game_id)
                    
                    if not game_update or 'boxscore' not in game_update:
                        logger.warning(f"No box score data for game {game_id}")
                        continue
                    
                    # Update player stats
                    self.update_player_stats(game_id, game_update['boxscore'])
                    
                    # Check each bet
                    for bet in bets:
                        try:
                            # Check progress
                            progress = self.check_bet_progress(bet)
                            
                            # Queue messages for milestones or wins BEFORE updating tracking
                            if progress['milestone_hit'] and not game_update.get('is_final'):
                                self.queue_message(bet, progress, 'milestone', game_update)
                                tracking_summary['messages_queued'] += 1
                            
                            if progress['is_hit'] and bet['status'] != 'Won':
                                self.queue_message(bet, progress, 'won', game_update)
                                tracking_summary['messages_queued'] += 1
                            
                            # Update tracking (this will increment alerts_sent count)
                            self.update_bet_tracking(bet, progress, game_update)
                            tracking_summary['bets_updated'] += 1
                            
                            # Create descriptive bet name for logging
                            if bet.get('player_name'):
                                bet_description = f"{bet['player_name']} {bet.get('bet_type', '')}"
                            elif bet.get('bet_type', '').lower() in ['moneyline', 'ml']:
                                # Try to get team name from the bet
                                team_name = "Team"
                                if bet.get('raw_input'):
                                    raw = bet['raw_input'].lower()
                                    if 'brewers' in raw: team_name = "Brewers"
                                    elif 'cubs' in raw: team_name = "Cubs"
                                    elif 'yankees' in raw: team_name = "Yankees"
                                    elif 'red sox' in raw: team_name = "Red Sox"
                                bet_description = f"{team_name} ML"
                            elif bet.get('bet_type', '').lower() == 'total':
                                bet_description = f"Game Total {bet.get('target_value', '')}O/U"
                            elif bet.get('bet_type', '').lower() == 'spread':
                                bet_description = f"Spread {bet.get('target_value', '')}"
                            else:
                                bet_description = f"{bet.get('bet_type', 'Team Bet')}"
                            
                            # Log progress
                            logger.info(
                                f"Bet {bet['bet_id']} ({bet['community_name']}): "
                                f"{bet_description} "
                                f"{progress['current_value']}/{progress['target_value']} "
                                f"({progress['progress_percentage']:.0f}%) "
                                f"{'✅ WON' if progress['is_hit'] else ''}"
                            )
                            
                            # Add to winners list if bet hit
                            if progress['is_hit']:
                                tracking_summary['winners'].append({
                                    'bet_id': bet['bet_id'],
                                    'player': bet.get('player_name', 'Team bet'),
                                    'community': bet['community_name']
                                })
                            
                            # Queue progress update if value changed significantly
                            elif progress['value_changed'] and progress['progress_percentage'] > 0:
                                # Only send progress updates for significant changes
                                if abs(progress['current_value'] - progress.get('last_value', 0)) >= 1:
                                    self.queue_message(bet, progress, 'progress', game_update)
                                    tracking_summary['messages_queued'] += 1
                        
                        except Exception as e:
                            error_msg = f"Error tracking bet {bet['bet_id']}: {e}"
                            logger.error(error_msg)
                            tracking_summary['errors'].append(error_msg)
                
                except Exception as e:
                    error_msg = f"Error updating game {game_id}: {e}"
                    logger.error(error_msg)
                    tracking_summary['errors'].append(error_msg)
            
            # Mark bets as lost if games are final
            db.execute("""
                UPDATE bets b
                SET status = 'Lost',
                    updated_at = CURRENT_TIMESTAMP
                FROM games g
                WHERE b.game_id = g.game_id
                AND b.status IN ('Pending', 'Live')
                AND g.status IN ('Final', 'Game Over', 'Completed')
                AND b.bet_id NOT IN (
                    SELECT bet_id FROM bets WHERE status = 'Won'
                )
            """)
            
        except Exception as e:
            error_msg = f"Critical tracking error: {e}"
            logger.error(error_msg)
            tracking_summary['errors'].append(error_msg)
        
        # Log summary
        end_time = datetime.now()
        tracking_summary['end_time'] = end_time
        tracking_summary['duration_seconds'] = (end_time - start_time).total_seconds()
        
        logger.info(
            f"Tracking complete in {tracking_summary['duration_seconds']:.1f}s: "
            f"{tracking_summary['bets_updated']} bets updated, "
            f"{tracking_summary['messages_queued']} messages queued, "
            f"{len(tracking_summary['winners'])} winners"
        )
        
        return tracking_summary