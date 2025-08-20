"""Configuration management for MLB Betting System"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    # APIs
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    MLB_API_BASE_URL = os.getenv('MLB_API_BASE_URL', 'https://statsapi.mlb.com/api/v1.1')
    
    # Environment
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    
    # Betting settings
    DEFAULT_UNITS = 1.0
    DEFAULT_ODDS = '-110'
    
    # Message timings (in minutes before game)
    PRE_GAME_ALERTS = [120, 30, 10]  # 2 hours, 30 min, 10 min
    
    # Live update frequency (seconds)
    LIVE_UPDATE_INTERVAL = 300  # 5 minutes
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        required = ['DATABASE_URL', 'OPENAI_API_KEY']
        missing = [key for key in required if not getattr(cls, key)]
        
        if missing:
            raise ValueError(f"Missing required config: {', '.join(missing)}")
        
        return True

# Validate on import
Config.validate()