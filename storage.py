# storage.py
import json
import os

# File paths
DATA_DIR = 'data'
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
STRATEGIES_FILE = os.path.join(DATA_DIR, 'strategies.json')
MOMENTS_FILE = os.path.join(DATA_DIR, 'moments.json')
TEAMS_FILE = os.path.join(DATA_DIR, 'teams.json')
PLAYERS_FILE = os.path.join(DATA_DIR, 'players.json')
GAMES_FILE = os.path.join(DATA_DIR, 'games.json')
SPONSORS_FILE = os.path.join(DATA_DIR, 'sponsors.json')

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

def save_data(data, file_path):
    """Save data to a JSON file"""
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving data to {file_path}: {e}")
        return False

def load_data(file_path, default_data=None):
    """Load data from a JSON file, return default if file doesn't exist"""
    if default_data is None:
        default_data = {}
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        return default_data
    except Exception as e:
        print(f"Error loading data from {file_path}: {e}")
        return default_data

def save_users(users_data):
    """Save users data to file"""
    return save_data(users_data, USERS_FILE)

def load_users(default_users=None):
    """Load users data from file"""
    return load_data(USERS_FILE, default_users)

def save_strategies(strategies_data):
    """Save strategies data to file"""
    return save_data(strategies_data, STRATEGIES_FILE)

def load_strategies(default_strategies=None):
    """Load strategies data from file"""
    return load_data(STRATEGIES_FILE, default_strategies)

def save_moments(moments_data):
    """Save moments data to file"""
    return save_data(moments_data, MOMENTS_FILE)

def load_moments(default_moments=None):
    """Load moments data from file"""
    return load_data(MOMENTS_FILE, default_moments)

def save_teams(teams_data):
    """Save teams data to file"""
    return save_data(teams_data, TEAMS_FILE)

def load_teams(default_teams=None):
    """Load teams data from file"""
    return load_data(TEAMS_FILE, default_teams)

def save_players(players_data):
    """Save players data to file"""
    return save_data(players_data, PLAYERS_FILE)

def load_players(default_players=None):
    """Load players data from file"""
    return load_data(PLAYERS_FILE, default_players)

def save_games(games_data):
    """Save games data to file"""
    return save_data(games_data, GAMES_FILE)

def load_games(default_games=None):
    """Load games data from file"""
    if default_games is None:
        default_games = []  # Games is a list, not a dict
    return load_data(GAMES_FILE, default_games)

def save_sponsors(sponsors_data):
    """Save sponsors data to file"""
    return save_data(sponsors_data, SPONSORS_FILE)

def load_sponsors(default_sponsors=None):
    """Load sponsors data from file"""
    if default_sponsors is None:
        default_sponsors = []  # Sponsors is a list, not a dict
    return load_data(SPONSORS_FILE, default_sponsors)
