"""MLB Stats API integration"""

import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import logging
from src.config import Config
from src.database import db

logger = logging.getLogger(__name__)


class MLBAPI:
    """MLB Stats API client"""
    
    def __init__(self):
        self.base_url = Config.MLB_API_BASE_URL
        self.session = requests.Session()
    
    def _convert_utc_to_eastern(self, utc_time_str: str) -> datetime:
        """Convert MLB API UTC time to Eastern Time"""
        try:
            # Parse MLB API time format: 2025-08-19T18:20:00Z
            utc_time = datetime.fromisoformat(utc_time_str.replace('Z', '+00:00'))
            
            # Convert to Eastern Time (UTC-4 for EDT, UTC-5 for EST)
            # For now, assume EDT (summer time) - could be improved with proper timezone library
            eastern_time = utc_time - timedelta(hours=4)  # EDT conversion
            
            return eastern_time
            
        except Exception as e:
            logger.error(f"Failed to convert UTC time {utc_time_str}: {e}")
            # Fallback: return current time
            return datetime.now()
    
    def _get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make GET request to MLB API"""
        url = f"{self.base_url}/{endpoint}"
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"MLB API error: {e}")
            return {}
    
    def get_teams(self, sport_id: int = 1) -> List[Dict]:
        """Get all MLB teams"""
        data = self._get("teams", {"sportId": sport_id})
        return data.get('teams', [])
    
    def get_team_roster(self, team_id: int) -> List[Dict]:
        """Get roster for a specific team"""
        data = self._get(f"teams/{team_id}/roster")
        return data.get('roster', [])
    
    def get_schedule(self, date: Optional[str] = None) -> List[Dict]:
        """Get games for a specific date"""
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        params = {
            'sportId': 1,
            'date': date
        }
        
        data = self._get("schedule", params)
        dates = data.get('dates', [])
        
        if dates:
            return dates[0].get('games', [])
        return []
    
    def get_game_feed(self, game_id: int) -> Dict:
        """Get live game feed"""
        return self._get(f"game/{game_id}/feed/live")
    
    def update_teams_in_db(self) -> int:
        """Update all teams in database"""
        teams = self.get_teams()
        count = 0
        
        for team in teams:
            db.execute("""
                INSERT INTO teams (team_id, team_name, abbreviation, league, division)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (team_id) DO UPDATE SET
                    team_name = EXCLUDED.team_name,
                    abbreviation = EXCLUDED.abbreviation,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                team['id'],
                team['name'],
                team.get('abbreviation', '')[:10] if team.get('abbreviation') else '',
                team.get('league', {}).get('name', '')[:20] if team.get('league', {}).get('name') else '',
                team.get('division', {}).get('name', '')[:20] if team.get('division', {}).get('name') else ''
            ))
            count += 1
        
        logger.info(f"Updated {count} teams")
        return count
    
    def update_rosters_in_db(self, teams_only: List[int] = None) -> int:
        """Update player rosters in database"""
        if teams_only:
            # Only update specific teams (for today's games)
            teams = [(team_id,) for team_id in teams_only]
            logger.info(f"Updating rosters for {len(teams)} teams playing today")
        else:
            # Update all teams
            teams = db.fetchall("SELECT team_id FROM teams")
            logger.info(f"Updating rosters for all {len(teams)} teams")
        
        total_players = 0
        
        for i, (team_id,) in enumerate(teams, 1):
            try:
                logger.info(f"Loading roster for team {team_id} ({i}/{len(teams)})")
                roster = self.get_team_roster(team_id)
                
                team_players = 0
                for player in roster:
                    person = player.get('person', {})
                    position = player.get('position', {})
                    
                    db.execute("""
                        INSERT INTO players (
                            player_id, full_name, first_name, last_name,
                            position, jersey_number, team_id, status
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'Active')
                        ON CONFLICT (player_id) DO UPDATE SET
                            team_id = EXCLUDED.team_id,
                            position = EXCLUDED.position,
                            jersey_number = EXCLUDED.jersey_number,
                            status = 'Active',
                            updated_at = CURRENT_TIMESTAMP
                    """, (
                        person.get('id'),
                        person.get('fullName'),
                        person.get('firstName', ''),
                        person.get('lastName', ''),
                        position.get('abbreviation', ''),
                        player.get('jerseyNumber'),
                        team_id
                    ))
                    team_players += 1
                    total_players += 1
                
                logger.info(f"Team {team_id}: loaded {team_players} players")
                
            except Exception as e:
                logger.error(f"Failed to load roster for team {team_id}: {e}")
                continue
        
        logger.info(f"Updated {total_players} total players")
        return total_players
    
    def update_todays_games(self) -> List[Dict]:
        """Update today's games in database with probable pitchers and load rosters"""
        games = self.get_schedule()
        
        if not games:
            logger.info("No games scheduled for today")
            return []
        
        # Collect all team IDs playing today
        todays_teams = set()
        
        for game in games:
            home = game['teams']['home']['team']
            away = game['teams']['away']['team']
            
            todays_teams.add(home['id'])
            todays_teams.add(away['id'])
            
            # Get probable pitchers
            home_pitcher_id = None
            away_pitcher_id = None
            
            if 'probablePitcher' in game['teams']['home']:
                home_pitcher_id = game['teams']['home']['probablePitcher'].get('id')
            
            if 'probablePitcher' in game['teams']['away']:
                away_pitcher_id = game['teams']['away']['probablePitcher'].get('id')
            
            # Get venue ID if available (set to None if venue not in our database)
            venue_id = game.get('venue', {}).get('id')
            if venue_id:
                # Check if venue exists in our database
                venue_exists = db.fetchone("SELECT 1 FROM venues WHERE venue_id = %s", (venue_id,))
                if not venue_exists:
                    venue_id = None  # Don't reference non-existent venue
            
            # Convert game time from UTC to Eastern Time
            eastern_game_time = self._convert_utc_to_eastern(game['gameDate'])
            
            db.execute("""
                INSERT INTO games (
                    game_id, game_date, game_time,
                    home_team_id, away_team_id, venue_id, status,
                    home_probable_pitcher, away_probable_pitcher,
                    home_score, away_score
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (game_id) DO UPDATE SET
                    status = EXCLUDED.status,
                    home_probable_pitcher = EXCLUDED.home_probable_pitcher,
                    away_probable_pitcher = EXCLUDED.away_probable_pitcher,
                    home_score = EXCLUDED.home_score,
                    away_score = EXCLUDED.away_score,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                game['gamePk'],
                datetime.fromisoformat(game['officialDate']).date(),
                eastern_game_time,  # Now using converted Eastern Time!
                home['id'],
                away['id'],
                venue_id,
                game['status']['detailedState'],
                home_pitcher_id,
                away_pitcher_id,
                game['teams']['home'].get('score', 0),
                game['teams']['away'].get('score', 0)
            ))
        
        logger.info(f"Updated {len(games)} games with probable pitchers")
        
        # Now update rosters for all teams playing today
        if todays_teams:
            logger.info(f"Loading rosters for {len(todays_teams)} teams playing today")
            self.update_rosters_in_db(teams_only=list(todays_teams))
        
        return games
    
    def is_data_fresh(self) -> Dict[str, Any]:
        """Check if MLB data is fresh (from today)"""
        from datetime import date
        
        today = date.today()
        
        # Check if we have games for today
        today_games = db.fetchone(
            "SELECT COUNT(*) FROM games WHERE game_date = %s", 
            (today,)
        )
        
        # Check if we have games from previous days
        old_games = db.fetchone(
            "SELECT COUNT(*) FROM games WHERE game_date < %s", 
            (today,)
        )
        
        # Check last update timestamp for teams/players
        last_team_update = db.fetchone(
            "SELECT MAX(updated_at) FROM teams"
        )
        
        last_player_update = db.fetchone(
            "SELECT MAX(updated_at) FROM players"
        )
        
        today_games_count = today_games[0] if today_games else 0
        old_games_count = old_games[0] if old_games else 0
        
        # Data is fresh if we have today's games and recent updates
        is_fresh = today_games_count > 0
        
        return {
            'is_fresh': is_fresh,
            'today_games': today_games_count,
            'old_games': old_games_count,
            'today_date': today,
            'last_team_update': last_team_update[0] if last_team_update and last_team_update[0] else None,
            'last_player_update': last_player_update[0] if last_player_update and last_player_update[0] else None,
            'needs_refresh': not is_fresh or today_games_count == 0
        }
    
    def auto_refresh_if_stale(self) -> bool:
        """Automatically refresh data if it's stale"""
        freshness = self.is_data_fresh()
        
        if freshness['needs_refresh']:
            logger.info(f"Data is stale - auto-refreshing (today: {freshness['today_games']} games)")
            
            try:
                # Update teams first
                self.update_teams_in_db()
                
                # Update today's games and rosters
                games = self.update_todays_games()
                
                logger.info(f"Auto-refresh completed: {len(games)} games loaded for today")
                return True
                
            except Exception as e:
                logger.error(f"Auto-refresh failed: {e}")
                return False
        else:
            logger.info(f"Data is fresh - {freshness['today_games']} games for today")
            return True