"""OpenAI-powered bet parsing"""

import openai
import json
from typing import Dict, Optional
import logging
from src.config import Config
from src.database import db

logger = logging.getLogger(__name__)

# Set OpenAI API key
openai.api_key = Config.OPENAI_API_KEY


class BetParser:
    """Parse bet strings using OpenAI"""
    
    def __init__(self):
        self.teams_cache = self._load_teams()
        
    def _load_teams(self) -> str:
        """Load teams for context"""
        teams = db.fetchall("SELECT team_name, abbreviation FROM teams LIMIT 30")
        return ", ".join([f"{name} ({abbr})" for name, abbr in teams])
    
    def parse(self, raw_input: str) -> Dict:
        """Parse a bet string using OpenAI"""
        
        prompt = f"""
        Parse this MLB bet into structured JSON format.
        
        Bet input: "{raw_input}"
        
        MLB Teams include: {self.teams_cache}
        
        Return ONLY a valid JSON object with these exact fields:
        {{
            "player_name": "full player name or null",
            "team_name": "full team name or null",
            "bet_type": "one of: Moneyline, Spread, HRs, Hits, Ks, RBIs, SBs, Total",
            "target_value": number or null,
            "operator": "over, under, exactly, or null",
            "odds": "-110 format",
            "units": number,
            "confidence": 0-100,
            "interpretation": "plain English explanation"
        }}
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an MLB betting expert. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            content = response.choices[0].message.content
            
            # Clean JSON if needed
            if "```" in content:
                content = content.split("```")[1].replace("json", "").strip()
                if "```" in content:
                    content = content.split("```")[0]
            
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"OpenAI parsing error: {e}")
            return {
                "player_name": None,
                "team_name": None,
                "bet_type": "Unknown",
                "target_value": None,
                "operator": None,
                "odds": "-110",
                "units": 1,
                "confidence": 0,
                "interpretation": raw_input
            }
    
    def find_player_id(self, player_name: str) -> Optional[int]:
        """Find player ID from name"""
        if not player_name:
            return None
            
        result = db.fetchone(
            "SELECT player_id FROM players WHERE LOWER(full_name) LIKE %s",
            (f"%{player_name.lower()}%",)
        )
        return result[0] if result else None
    
    def find_team_id(self, team_name: str) -> Optional[int]:
        """Find team ID from name"""
        if not team_name:
            return None
            
        result = db.fetchone(
            """SELECT team_id FROM teams 
               WHERE LOWER(team_name) LIKE %s 
               OR LOWER(abbreviation) = %s""",
            (f"%{team_name.lower()}%", team_name.lower())
        )
        return result[0] if result else None