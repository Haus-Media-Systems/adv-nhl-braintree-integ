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
AUCTIONS_FILE = os.path.join(DATA_DIR, 'auctions.json')
BIDS_FILE = os.path.join(DATA_DIR, 'bids.json')
AUCTION_RESULTS_FILE = os.path.join(DATA_DIR, 'auction_results.json')

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
    """Load games data from file with enhanced debugging"""
    if default_games is None:
        default_games = []  # Games is a list, not a dict
    
    print("\n=== LOADING GAMES FROM STORAGE ===")
    print(f"Games file path: {GAMES_FILE}")
    
    if os.path.exists(GAMES_FILE):
        try:
            with open(GAMES_FILE, 'r') as f:
                content = f.read()
                print(f"File content length: {len(content)} bytes")
                if content:
                    result = json.loads(content)
                    print(f"Successfully loaded {len(result)} games")
                    
                    for i, game in enumerate(result):
                        print(f"Game {i+1}: {game.get('away')} @ {game.get('home')}")
                        print(f"  ID: {game.get('id')} (type: {type(game.get('id')).__name__})")
                        print(f"  Status: '{game.get('status')}' (type: {type(game.get('status')).__name__})")
                    
                    return result
                else:
                    print("File exists but is empty, returning default")
                    return default_games
        except Exception as e:
            print(f"Error loading from file: {e}")
            return default_games
    else:
        print("File does not exist, returning default")
        return default_games

def save_sponsors(sponsors_data):
    """Save sponsors data to file"""
    return save_data(sponsors_data, SPONSORS_FILE)

def load_sponsors(default_sponsors=None):
    """Load sponsors data from file"""
    if default_sponsors is None:
        default_sponsors = []  # Sponsors is a list, not a dict
    return load_data(SPONSORS_FILE, default_sponsors)

# Auction functions
def save_auctions(auctions_data):
    """Save auctions data to file"""
    return save_data(auctions_data, AUCTIONS_FILE)

def load_auctions(default_auctions=None):
    """Load auctions data from file"""
    if default_auctions is None:
        default_auctions = {}
    return load_data(AUCTIONS_FILE, default_auctions)

# Bid functions
def save_bids(bids_data):
    """Save bids data to file"""
    return save_data(bids_data, BIDS_FILE)

def load_bids(default_bids=None):
    """Load bids data from file"""
    if default_bids is None:
        default_bids = {}
    return load_data(BIDS_FILE, default_bids)

# Auction result functions
def save_auction_results(auction_results_data):
    """Save auction results data to file"""
    return save_data(auction_results_data, AUCTION_RESULTS_FILE)

def load_auction_results(default_auction_results=None):
    """Load auction results data from file"""
    if default_auction_results is None:
        default_auction_results = {}
    return load_data(AUCTION_RESULTS_FILE, default_auction_results)
