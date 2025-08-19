"""Smart bet validation - Only accept bets for players actually playing today"""

from datetime import datetime, date
from typing import Dict, Optional, List, Tuple
import logging
from src.database import db
from src.openai_parser import BetParser

logger = logging.getLogger(__name__)


class SmartBetValidator:
    """Intelligent bet validation that checks if players are actually playing today"""
    
    def __init__(self):
        self.parser = BetParser()
        self.todays_games = []
        self.probable_pitchers = {}
        self.active_players = {}
    
    def load_todays_context(self) -> bool:
        """Load today's games, probable pitchers, and active players"""
        try:
            # Get today's games (use actual today, not database CURRENT_DATE due to timezone issues)
            today = date.today()
            self.todays_games = db.fetch_dict("""
                SELECT 
                    g.*,
                    ht.team_name as home_team_name,
                    ht.abbreviation as home_abbr,
                    at.team_name as away_team_name,
                    at.abbreviation as away_abbr,
                    hp.full_name as home_pitcher_name,
                    ap.full_name as away_pitcher_name
                FROM games g
                JOIN teams ht ON g.home_team_id = ht.team_id
                JOIN teams at ON g.away_team_id = at.team_id
                LEFT JOIN players hp ON g.home_probable_pitcher = hp.player_id
                LEFT JOIN players ap ON g.away_probable_pitcher = ap.player_id
                WHERE g.game_date = %s
            """, (today,))
            
            # Build pitcher lookup
            for game in self.todays_games:
                if game.get('home_pitcher_name'):
                    self.probable_pitchers[game['home_pitcher_name'].lower()] = {
                        'game_id': game['game_id'],
                        'team': game['home_team_name'],
                        'opponent': game['away_team_name'],
                        'player_id': game['home_probable_pitcher']
                    }
                if game.get('away_pitcher_name'):
                    self.probable_pitchers[game['away_pitcher_name'].lower()] = {
                        'game_id': game['game_id'],
                        'team': game['away_team_name'],
                        'opponent': game['home_team_name'],
                        'player_id': game['away_probable_pitcher']
                    }
            
            # Get active players in today's games
            if self.todays_games:
                team_ids = []
                for game in self.todays_games:
                    team_ids.extend([game['home_team_id'], game['away_team_id']])
                
                if team_ids:
                    players = db.fetch_dict("""
                        SELECT p.*, t.team_name, t.abbreviation
                        FROM players p
                        JOIN teams t ON p.team_id = t.team_id
                        WHERE p.team_id = ANY(%s)
                        AND p.status = 'Active'
                    """, (team_ids,))
                    
                    for player in players:
                        key = player['full_name'].lower()
                        self.active_players[key] = player
            
            logger.info(f"Loaded context: {len(self.todays_games)} games, {len(self.probable_pitchers)} pitchers, {len(self.active_players)} players")
            
            # Warn about incomplete data
            if self.todays_games and len(self.active_players) < len(self.todays_games) * 20:
                logger.warning(f"Low player count: {len(self.active_players)} players for {len(self.todays_games)} games (expected ~{len(self.todays_games) * 25})")
            
            if self.todays_games and len(self.probable_pitchers) == 0:
                logger.warning("No probable pitchers loaded - they may not be announced yet")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load today's context: {e}")
            return False
    
    def validate_bet(self, raw_input: str) -> Dict:
        """Validate a bet and return validation results"""
        
        # Parse the bet
        parsed = self.parser.parse(raw_input)
        
        validation = {
            'valid': False,
            'warnings': [],
            'errors': [],
            'suggestions': [],
            'game_context': None,
            'parsed_bet': parsed
        }
        
        # Check if we have today's data
        if not self.todays_games:
            validation['errors'].append("❌ No games loaded for today. Please update MLB data first.")
            return validation
        
        player_name = parsed.get('player_name') or ''
        player_name = player_name.lower().strip() if player_name else ''
        
        team_name = parsed.get('team_name') or ''
        team_name = team_name.lower().strip() if team_name else ''
        
        bet_type = parsed.get('bet_type') or ''
        bet_type = bet_type.lower() if bet_type else ''
        
        # If it's a pitcher bet (strikeouts), validate against probable pitchers
        if bet_type in ['ks', 'strikeouts'] and player_name:
            return self._validate_pitcher_bet(player_name, validation)
        
        # If it's a player bet, validate against active roster
        elif player_name:
            return self._validate_player_bet(player_name, validation)
        
        # If it's a team bet, validate against today's games
        elif team_name:
            return self._validate_team_bet(team_name, validation)
        
        # Unknown bet type
        validation['warnings'].append("⚠️ Could not determine bet type - allowing anyway")
        validation['valid'] = True
        return validation
    
    def _validate_pitcher_bet(self, player_name: str, validation: Dict) -> Dict:
        """Validate a pitcher strikeout bet"""
        
        # Direct name match
        if player_name in self.probable_pitchers:
            pitcher_info = self.probable_pitchers[player_name]
            validation['valid'] = True
            validation['game_context'] = pitcher_info
            validation['suggestions'].append(f"✅ {player_name.title()} is the probable pitcher for {pitcher_info['team']} vs {pitcher_info['opponent']}")
            return validation
        
        # Fuzzy matching for names
        matches = []
        for pitcher, info in self.probable_pitchers.items():
            if any(word in pitcher for word in player_name.split()):
                matches.append((pitcher, info))
        
        if matches:
            validation['errors'].append(f"❌ '{player_name.title()}' not found as probable pitcher today")
            validation['suggestions'].append("🎯 Did you mean one of today's probable pitchers:")
            for pitcher, info in matches[:3]:
                validation['suggestions'].append(f"   • {pitcher.title()} ({info['team']} vs {info['opponent']})")
        else:
            validation['errors'].append(f"❌ '{player_name.title()}' is not a probable pitcher today")
            self._add_todays_pitcher_suggestions(validation)
        
        return validation
    
    def _validate_player_bet(self, player_name: str, validation: Dict) -> Dict:
        """Validate a general player bet"""
        
        # Direct name match
        if player_name in self.active_players:
            player_info = self.active_players[player_name]
            
            # Find their game today
            game_context = self._find_player_game(player_info['team_id'])
            if game_context:
                validation['valid'] = True
                validation['game_context'] = game_context
                validation['suggestions'].append(f"✅ {player_name.title()} plays for {player_info['team_name']} in today's game")
            else:
                validation['errors'].append(f"❌ {player_info['team_name']} is not playing today")
            
            return validation
        
        # Fuzzy matching
        matches = []
        for name, info in self.active_players.items():
            if any(word in name for word in player_name.split()):
                matches.append((name, info))
        
        if matches:
            validation['errors'].append(f"❌ '{player_name.title()}' not found in today's active rosters")
            validation['suggestions'].append("🎯 Did you mean:")
            for name, info in matches[:3]:
                validation['suggestions'].append(f"   • {name.title()} ({info['team_name']})")
        else:
            validation['errors'].append(f"❌ '{player_name.title()}' not found in any team playing today")
            self._add_todays_game_suggestions(validation)
        
        return validation
    
    def _validate_team_bet(self, team_name: str, validation: Dict) -> Dict:
        """Validate a team bet"""
        
        for game in self.todays_games:
            if (team_name in game['home_team_name'].lower() or 
                team_name in game['away_team_name'].lower() or
                team_name in game.get('home_abbr', '').lower() or
                team_name in game.get('away_abbr', '').lower()):
                
                validation['valid'] = True
                validation['game_context'] = {
                    'game_id': game['game_id'],
                    'matchup': f"{game['away_team_name']} @ {game['home_team_name']}"
                }
                validation['suggestions'].append(f"✅ Found game: {game['away_team_name']} @ {game['home_team_name']}")
                return validation
        
        validation['errors'].append(f"❌ '{team_name.title()}' is not playing today")
        self._add_todays_game_suggestions(validation)
        return validation
    
    def _find_player_game(self, team_id: int) -> Optional[Dict]:
        """Find the game for a player's team"""
        for game in self.todays_games:
            if game['home_team_id'] == team_id or game['away_team_id'] == team_id:
                return {
                    'game_id': game['game_id'],
                    'matchup': f"{game['away_team_name']} @ {game['home_team_name']}"
                }
        return None
    
    def _add_todays_pitcher_suggestions(self, validation: Dict):
        """Add suggestions for today's probable pitchers"""
        if self.probable_pitchers:
            validation['suggestions'].append("🎯 Today's probable pitchers:")
            for pitcher, info in list(self.probable_pitchers.items())[:5]:
                validation['suggestions'].append(f"   • {pitcher.title()} ({info['team']} vs {info['opponent']})")
    
    def _add_todays_game_suggestions(self, validation: Dict):
        """Add suggestions for today's games"""
        if self.todays_games:
            validation['suggestions'].append("🎯 Today's games:")
            for game in self.todays_games:  # Show all games, not just first 5
                validation['suggestions'].append(f"   • {game['away_team_name']} @ {game['home_team_name']}")
    
    def process_bet(self, raw_input: str, community: str = 'StatEdge') -> Dict:
        """Process a bet with full validation and auto-refresh if needed"""
        
        # Check if MLB data needs refreshing before validation
        from src.mlb_api import MLBAPI
        mlb_api = MLBAPI()
        
        # Auto-refresh if data is stale
        if not mlb_api.auto_refresh_if_stale():
            logger.warning("Auto-refresh failed, but continuing with existing data")
        
        # Always reload today's context to ensure fresh data
        if not self.load_todays_context():
            return {
                'success': False,
                'error': 'Failed to load today\'s MLB data',
                'suggestion': 'Try updating MLB data first (option 1)'
            }
        
        # Validate the bet
        validation = self.validate_bet(raw_input)
        
        return {
            'success': validation['valid'],
            'validation': validation,
            'game_context': validation.get('game_context')
        }