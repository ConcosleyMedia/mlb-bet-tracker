"""Live game tracking for bet progress"""

import logging
from datetime import datetime
from typing import Dict, List
from src.database import db
from src.mlb_api import MLBAPI

logger = logging.getLogger(__name__)


class LiveGameTracker:
    """Track live games and update bet progress"""
    
    def __init__(self):
        self.mlb_api = MLBAPI()
        self.active_games = {}
    
    def get_active_game_bets(self) -> List[Dict]:
        """Get all bets for games currently in progress"""
        return db.fetch_dict("""
            SELECT DISTINCT
                b.bet_id,
                b.game_id,
                b.player_id,
                b.bet_type,
                b.target_value,
                b.operator,
                b.result_value,
                g.status as game_status,
                g.home_team_id,
                g.away_team_id,
                p.full_name as player_name
            FROM bets b
            JOIN games g ON b.game_id = g.game_id
            LEFT JOIN players p ON b.player_id = p.player_id
            WHERE b.status IN ('Pending', 'Live')
            AND g.game_date = CURRENT_DATE
            AND g.status IN ('In Progress', 'Live')
        """)
    
    def update_game_stats(self, game_id: int) -> Dict:
        """Pull live stats from MLB API for a specific game"""
        try:
            # Get live game feed
            game_data = self.mlb_api.get_game_feed(game_id)
            
            if not game_data:
                return {}
            
            # Extract live data
            live_data = game_data.get('liveData', {})
            box_score = live_data.get('boxscore', {})
            
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
                live_data.get('linescore', {}).get('currentInning', 1),
                live_data.get('linescore', {}).get('inningState', 'Top'),
                live_data.get('linescore', {}).get('teams', {}).get('home', {}).get('runs', 0),
                live_data.get('linescore', {}).get('teams', {}).get('away', {}).get('runs', 0),
                game_id
            ))
            
            return {
                'game_id': game_id,
                'status': game_state.get('detailedState'),
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
                    db.execute("""
                        INSERT INTO player_game_stats (
                            game_id, player_id, at_bats, hits, home_runs,
                            runs, rbis, walks, strikeouts, stolen_bases
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (game_id, player_id) DO UPDATE SET
                            at_bats = EXCLUDED.at_bats,
                            hits = EXCLUDED.hits,
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
                    db.execute("""
                        INSERT INTO pitcher_game_stats (
                            game_id, pitcher_id, innings_pitched, 
                            strikeouts, walks_allowed, hits_allowed,
                            earned_runs, home_runs_allowed
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (game_id, pitcher_id) DO UPDATE SET
                            innings_pitched = EXCLUDED.innings_pitched,
                            strikeouts = EXCLUDED.strikeouts,
                            walks_allowed = EXCLUDED.walks_allowed,
                            hits_allowed = EXCLUDED.hits_allowed,
                            earned_runs = EXCLUDED.earned_runs,
                            home_runs_allowed = EXCLUDED.home_runs_allowed,
                            updated_at = CURRENT_TIMESTAMP
                    """, (
                        game_id, player_id,
                        pitching.get('inningsPitched', '0'),
                        pitching.get('strikeOuts', 0),
                        pitching.get('baseOnBalls', 0),
                        pitching.get('hits', 0),
                        pitching.get('earnedRuns', 0),
                        pitching.get('homeRuns', 0)
                    ))
    
    def check_bet_progress(self, bet: Dict) -> Dict:
        """Check progress on a specific bet"""
        bet_type = bet['bet_type'].lower()
        current_value = 0
        
        if bet_type in ['hrs', 'home runs']:
            stat = db.fetchone("""
                SELECT home_runs FROM player_game_stats
                WHERE game_id = %s AND player_id = %s
            """, (bet['game_id'], bet['player_id']))
            current_value = stat[0] if stat else 0
            
        elif bet_type in ['hits', 'h']:
            stat = db.fetchone("""
                SELECT hits FROM player_game_stats
                WHERE game_id = %s AND player_id = %s
            """, (bet['game_id'], bet['player_id']))
            current_value = stat[0] if stat else 0
            
        elif bet_type in ['ks', 'strikeouts']:
            stat = db.fetchone("""
                SELECT strikeouts FROM pitcher_game_stats
                WHERE game_id = %s AND pitcher_id = %s
            """, (bet['game_id'], bet['player_id']))
            current_value = stat[0] if stat else 0
            
        elif bet_type in ['rbis', 'rbi']:
            stat = db.fetchone("""
                SELECT rbis FROM player_game_stats
                WHERE game_id = %s AND player_id = %s
            """, (bet['game_id'], bet['player_id']))
            current_value = stat[0] if stat else 0
            
        elif bet_type in ['stolen bases', 'sb']:
            stat = db.fetchone("""
                SELECT stolen_bases FROM player_game_stats
                WHERE game_id = %s AND player_id = %s
            """, (bet['game_id'], bet['player_id']))
            current_value = stat[0] if stat else 0
        
        # Calculate progress
        target = float(bet['target_value'] or 0)
        progress = (current_value / target * 100) if target > 0 else 0
        
        # Determine if bet is hit
        operator = bet.get('operator', 'over')
        is_hit = False
        
        if operator == 'over':
            is_hit = current_value > target
        elif operator == 'under':
            is_hit = current_value < target
        elif operator == 'exactly':
            is_hit = current_value == target
        
        return {
            'bet_id': bet['bet_id'],
            'current_value': current_value,
            'target_value': target,
            'progress_percentage': min(progress, 100),
            'is_hit': is_hit,
            'operator': operator
        }
    
    def update_bet_tracking(self, bet_progress: Dict):
        """Update bet tracking table with progress"""
        db.execute("""
            INSERT INTO bet_tracking (
                bet_id, game_id, current_value, target_value,
                progress_percentage, is_live
            ) VALUES (%s, %s, %s, %s, %s, true)
            ON CONFLICT (bet_id) DO UPDATE SET
                current_value = EXCLUDED.current_value,
                progress_percentage = EXCLUDED.progress_percentage,
                updated_at = CURRENT_TIMESTAMP
        """, (
            bet_progress['bet_id'],
            bet_progress.get('game_id'),
            bet_progress['current_value'],
            bet_progress['target_value'],
            bet_progress['progress_percentage']
        ))
        
        # Update bet status
        if bet_progress['is_hit']:
            db.execute("""
                UPDATE bets 
                SET status = 'Won',
                    result_value = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE bet_id = %s
            """, (bet_progress['current_value'], bet_progress['bet_id']))
    
    def track_all_live_games(self):
        """Main tracking loop for all live games"""
        logger.info("Starting live game tracking...")
        
        # Get active bets
        active_bets = self.get_active_game_bets()
        
        if not active_bets:
            logger.info("No active bets to track")
            return
        
        # Group by game
        games_to_track = {}
        for bet in active_bets:
            game_id = bet['game_id']
            if game_id not in games_to_track:
                games_to_track[game_id] = []
            games_to_track[game_id].append(bet)
        
        logger.info(f"Tracking {len(games_to_track)} games with active bets")
        
        # Update each game
        for game_id, bets in games_to_track.items():
            logger.info(f"Updating game {game_id}...")
            
            # Get live stats
            game_update = self.update_game_stats(game_id)
            
            if game_update and 'boxscore' in game_update:
                # Update player stats
                self.update_player_stats(game_id, game_update['boxscore'])
                
                # Check each bet
                for bet in bets:
                    progress = self.check_bet_progress(bet)
                    self.update_bet_tracking(progress)
                    
                    logger.info(f"Bet {bet['bet_id']}: {bet.get('player_name', 'Team')} "
                              f"{progress['current_value']}/{progress['target_value']} "
                              f"({progress['progress_percentage']:.0f}%)")
        
        logger.info("Live tracking update complete")