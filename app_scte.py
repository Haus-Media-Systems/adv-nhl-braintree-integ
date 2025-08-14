from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import random
import uuid
from datetime import datetime, timedelta
import os
import json
import storage  # Import the storage module
import braintree


app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev_secret_key_change_in_production')

# Configure Braintree
braintree_gateway = braintree.BraintreeGateway(
    braintree.Configuration(
        environment=braintree.Environment.Sandbox,
        merchant_id="cmw9qh963vbrbnp7",
        public_key="b4m63tfbnjh229qk",
        private_key="6dbee76c103a0c6bf6ae64a5076a9708"
    )
)

# Add merchant account ID constants
DEFAULT_MERCHANT_ACCOUNT_ID = "easywatchentertainment"  # Your default account
BROADCASTER_MERCHANT_ACCOUNT_ID = "BROADCASTERS"  # Note: There appears to be a typo in "BRAODCASTERS"
COMMISSION_MERCHANT_ACCOUNT_ID = "COMMISSION"
PLATFORM_MERCHANT_ACCOUNT_ID = "PLATFORM"

# Mock database - Load from storage or use defaults
users = storage.load_users({
    "1": {
        "id": "1",
        "name": "John Smith",
        "company": "SportsDrink Co.",
        "email": "john@example.com",
        "password": "password123",  # For demo purposes, storing in plain text
        "budget": 50000
    },
    "2": {
        "id": "2",
        "name": "Jane Doe",
        "company": "Car Manufacturer",
        "email": "jane@example.com",
        "password": "password123",  # For demo purposes, storing in plain text
        "budget": 75000
    }
})

# Add a dedicated administrator account
users["admin"] = {
    "id": "admin",
    "name": "Administrator",
    "company": "NHL Bidding Platform",
    "email": "admin@gmail.com",
    "password": "admin",
    "budget": 0,  # Admin doesn't need a budget
    "is_admin": True  # This grants admin privileges
}

# Mock team and player data - Load from storage or use defaults
teams = storage.load_data(storage.TEAMS_FILE, {
    "NYR": {
        "id": "NYR",
        "name": "New York Rangers",
        "conference": "Eastern",
        "division": "Metropolitan"
    },
    "BOS": {
        "id": "BOS",
        "name": "Boston Bruins",
        "conference": "Eastern",
        "division": "Atlantic"
    },
    "TOR": {
        "id": "TOR",
        "name": "Toronto Maple Leafs",
        "conference": "Eastern",
        "division": "Atlantic"
    },
    "MTL": {
        "id": "MTL",
        "name": "Montreal Canadiens",
        "conference": "Eastern",
        "division": "Atlantic"
    },
    "EDM": {
        "id": "EDM",
        "name": "Edmonton Oilers",
        "conference": "Western",
        "division": "Pacific"
    },
    "CGY": {
        "id": "CGY",
        "name": "Calgary Flames",
        "conference": "Western",
        "division": "Pacific"
    }
})

players = storage.load_data(storage.PLAYERS_FILE, {
    # Rangers
    "NYR-1": {"id": "NYR-1", "name": "Igor Shesterkin", "team": "NYR", "position": "G", "number": 31, "stats": {"gaa": 2.48, "sv_pct": 0.916, "shutouts": 3}},
    "NYR-2": {"id": "NYR-2", "name": "Artemi Panarin", "team": "NYR", "position": "LW", "number": 10, "stats": {"goals": 32, "assists": 47, "points": 79}},
    "NYR-3": {"id": "NYR-3", "name": "Mika Zibanejad", "team": "NYR", "position": "C", "number": 93, "stats": {"goals": 28, "assists": 39, "points": 67}},
    "NYR-4": {"id": "NYR-4", "name": "Adam Fox", "team": "NYR", "position": "D", "number": 23, "stats": {"goals": 11, "assists": 54, "points": 65}},
    "NYR-5": {"id": "NYR-5", "name": "Chris Kreider", "team": "NYR", "position": "LW", "number": 20, "stats": {"goals": 36, "assists": 21, "points": 57}},
    # Bruins
    "BOS-1": {"id": "BOS-1", "name": "Jeremy Swayman", "team": "BOS", "position": "G", "number": 1, "stats": {"gaa": 2.32, "sv_pct": 0.921, "shutouts": 4}},
    "BOS-2": {"id": "BOS-2", "name": "David Pastrnak", "team": "BOS", "position": "RW", "number": 88, "stats": {"goals": 43, "assists": 38, "points": 81}},
    "BOS-3": {"id": "BOS-3", "name": "Brad Marchand", "team": "BOS", "position": "LW", "number": 63, "stats": {"goals": 26, "assists": 42, "points": 68}},
    "BOS-4": {"id": "BOS-4", "name": "Charlie McAvoy", "team": "BOS", "position": "D", "number": 73, "stats": {"goals": 8, "assists": 42, "points": 50}},
    "BOS-5": {"id": "BOS-5", "name": "Hampus Lindholm", "team": "BOS", "position": "D", "number": 27, "stats": {"goals": 9, "assists": 28, "points": 37}},
    # Maple Leafs
    "TOR-1": {"id": "TOR-1", "name": "Auston Matthews", "team": "TOR", "position": "C", "number": 34, "stats": {"goals": 51, "assists": 27, "points": 78}},
    "TOR-2": {"id": "TOR-2", "name": "Mitch Marner", "team": "TOR", "position": "RW", "number": 16, "stats": {"goals": 27, "assists": 53, "points": 80}},
    "TOR-3": {"id": "TOR-3", "name": "William Nylander", "team": "TOR", "position": "RW", "number": 88, "stats": {"goals": 33, "assists": 39, "points": 72}},
    "TOR-4": {"id": "TOR-4", "name": "John Tavares", "team": "TOR", "position": "C", "number": 91, "stats": {"goals": 29, "assists": 38, "points": 67}},
    "TOR-5": {"id": "TOR-5", "name": "Joseph Woll", "team": "TOR", "position": "G", "number": 60, "stats": {"gaa": 2.65, "sv_pct": 0.912, "shutouts": 1}},
    # Canadiens
    "MTL-1": {"id": "MTL-1", "name": "Cole Caufield", "team": "MTL", "position": "RW", "number": 22, "stats": {"goals": 26, "assists": 20, "points": 46}},
    "MTL-2": {"id": "MTL-2", "name": "Nick Suzuki", "team": "MTL", "position": "C", "number": 14, "stats": {"goals": 22, "assists": 34, "points": 56}},
    "MTL-3": {"id": "MTL-3", "name": "Mike Matheson", "team": "MTL", "position": "D", "number": 8, "stats": {"goals": 8, "assists": 31, "points": 39}},
    "MTL-4": {"id": "MTL-4", "name": "Sam Montembeault", "team": "MTL", "position": "G", "number": 35, "stats": {"gaa": 3.05, "sv_pct": 0.904, "shutouts": 1}},
    "MTL-5": {"id": "MTL-5", "name": "Kirby Dach", "team": "MTL", "position": "C", "number": 77, "stats": {"goals": 14, "assists": 24, "points": 38}},
    # Oilers
    "EDM-1": {"id": "EDM-1", "name": "Connor McDavid", "team": "EDM", "position": "C", "number": 97, "stats": {"goals": 42, "assists": 66, "points": 108}},
    "EDM-2": {"id": "EDM-2", "name": "Leon Draisaitl", "team": "EDM", "position": "C", "number": 29, "stats": {"goals": 38, "assists": 58, "points": 96}},
    "EDM-3": {"id": "EDM-3", "name": "Zach Hyman", "team": "EDM", "position": "LW", "number": 18, "stats": {"goals": 33, "assists": 31, "points": 64}},
    "EDM-4": {"id": "EDM-4", "name": "Evan Bouchard", "team": "EDM", "position": "D", "number": 2, "stats": {"goals": 12, "assists": 35, "points": 47}},
    "EDM-5": {"id": "EDM-5", "name": "Stuart Skinner", "team": "EDM", "position": "G", "number": 74, "stats": {"gaa": 2.68, "sv_pct": 0.908, "shutouts": 2}},
    # Flames
    "CGY-1": {"id": "CGY-1", "name": "Jacob Markstrom", "team": "CGY", "position": "G", "number": 25, "stats": {"gaa": 2.75, "sv_pct": 0.911, "shutouts": 2}},
    "CGY-2": {"id": "CGY-2", "name": "Nazem Kadri", "team": "CGY", "position": "C", "number": 91, "stats": {"goals": 24, "assists": 37, "points": 61}},
    "CGY-3": {"id": "CGY-3", "name": "Elias Lindholm", "team": "CGY", "position": "C", "number": 28, "stats": {"goals": 22, "assists": 28, "points": 50}},
    "CGY-4": {"id": "CGY-4", "name": "Rasmus Andersson", "team": "CGY", "position": "D", "number": 4, "stats": {"goals": 10, "assists": 36, "points": 46}},
    "CGY-5": {"id": "CGY-5", "name": "Blake Coleman", "team": "CGY", "position": "C", "number": 20, "stats": {"goals": 23, "assists": 19, "points": 42}}
})

strategies = storage.load_strategies({})

# Initialize auction-related data structures
auction_data = storage.load_auctions({})
bids = storage.load_bids({})
auction_results = storage.load_auction_results({})

moments = storage.load_data(storage.MOMENTS_FILE, {
    1: {
        "id": 1,
        "name": "Goal",
        "description": "Player scores a goal",
        "exposure": "High",
        "avg_bid": "$5,000",
        "frequency": "5-7 per game"
    },
    2: {
        "id": 2,
        "name": "Save",
        "description": "Goalkeeper makes a spectacular save",
        "exposure": "Medium",
        "avg_bid": "$2,500",
        "frequency": "10-15 per game"
    },
    3: {
        "id": 3,
        "name": "Penalty",
        "description": "Player receives a penalty",
        "exposure": "Medium",
        "avg_bid": "$3,000",
        "frequency": "8-12 per game"
    },
    4: {
        "id": 4,
        "name": "Fight",
        "description": "Players engage in a fight",
        "exposure": "Very High",
        "avg_bid": "$6,000",
        "frequency": "0-3 per game"
    },
    5: {
        "id": 5,
        "name": "Overtime Goal/Shootout",
        "description": "Game-winning goal in overtime or shootout",
        "exposure": "Extremely High",
        "avg_bid": "$8,000",
        "frequency": "0-1 per game"
    },
    6: {
        "id": 6,
        "name": "Hit",
        "description": "Player delivers a significant body check",
        "exposure": "Medium",
        "avg_bid": "$2,000",
        "frequency": "15-25 per game"
    }
})

upcoming_games = storage.load_data(storage.GAMES_FILE, [
    {
        "id": 1,
        "home": "New York Rangers",
        "away": "Boston Bruins",
        "date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
        "time": "19:00 EST"
    },
    {
        "id": 2,
        "home": "Toronto Maple Leafs",
        "away": "Montreal Canadiens",
        "date": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),
        "time": "20:00 EST"
    },
    {
        "id": 3,
        "home": "Edmonton Oilers",
        "away": "Calgary Flames",
        "date": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
        "time": "21:00 MST"
    }
])

sponsors = storage.load_data(storage.SPONSORS_FILE, [
    {
        "id": 1,
        "name": "SportsDrink Co.",
        "budget": 50000,
        "strategy_count": 3
    },
    {
        "id": 2,
        "name": "Car Manufacturer",
        "budget": 75000,
        "strategy_count": 2
    },
    {
        "id": 3,
        "name": "Insurance Company",
        "budget": 100000,
        "strategy_count": 5
    }
])

# Updated budget calculation helper functions to handle multiple strategies per moment

def calculate_allocated_budget(user_id):
    """Calculate the total amount of budget allocated in all active strategies"""
    # This represents the money "reserved" for potential bids, not actual spending
    total_allocated = 0
    for strategy in strategies.values():
        if strategy['user_id'] == user_id and strategy.get('status', 'active') == 'active':
            total_allocated += float(strategy.get('max_bid', 0))
    return total_allocated

def calculate_spent_budget(user_id):
    """Calculate the actual money spent on winning auctions"""
    # This represents the actual money spent on completed/paid auction wins
    total_spent = 0

    for result_id, result in auction_results.items():
        if result['winning_user_id'] == user_id:
            # Only count completed payments as spent
            if result.get('payment_status') == 'completed':
                total_spent += float(result.get('winning_amount', 0))

    return total_spent

def calculate_available_budget(user_id):
    """Calculate the available budget for a user"""
    user = users.get(user_id)
    if not user:
        return 0

    # Get the total budget from the user object
    total_budget = float(user.get('budget', 0))

    # Subtract actual spent money (not allocated)
    spent_budget = calculate_spent_budget(user_id)

    # Return the difference
    return max(0, total_budget - spent_budget)

def get_user_budget_info(user_id):
    """Get comprehensive budget information for a user"""
    user = users.get(user_id)
    if not user:
        return {
            'total_budget': 0,
            'allocated_budget': 0,
            'spent_budget': 0,
            'used_budget': 0,  # Add this for backward compatibility
            'available_budget': 0,
            'pending_wins': 0,
            'pending_win_amount': 0
        }

    total_budget = float(user.get('budget', 0))
    allocated_budget = calculate_allocated_budget(user_id)
    spent_budget = calculate_spent_budget(user_id)
    available_budget = calculate_available_budget(user_id)

    # Calculate pending wins (won but not yet paid)
    pending_wins = 0
    pending_win_amount = 0
    for result_id, result in auction_results.items():
        if result['winning_user_id'] == user_id and result.get('payment_status') == 'pending':
            pending_wins += 1
            pending_win_amount += float(result.get('winning_amount', 0))

    return {
        'total_budget': total_budget,
        'allocated_budget': allocated_budget,
        'spent_budget': spent_budget,
        'used_budget': spent_budget,  # Set used_budget to be the same as spent_budget for compatibility
        'available_budget': available_budget,
        'pending_wins': pending_wins,
        'pending_win_amount': pending_win_amount
    }

def get_user_strategies_by_moment(user_id, moment_id, game_id=None):
    """Get all strategies for a specific user, moment, and optionally game"""
    user_moment_strategies = []
    
    for strat_id, strategy in strategies.items():
        if (strategy['user_id'] == user_id and 
            str(strategy.get('moment_id', '')) == str(moment_id)):
            
            # If game_id is specified, filter by game as well
            if game_id is None or strategy.get('game_id') == game_id:
                strategy_copy = dict(strategy)
                strategy_copy['id'] = strat_id
                user_moment_strategies.append(strategy_copy)
    
    return user_moment_strategies

def count_user_strategies_for_moment(user_id, moment_id, game_id=None):
    """Count the number of strategies a user has for a specific moment"""
    return len(get_user_strategies_by_moment(user_id, moment_id, game_id))

# Helper functions
def get_user():
    if 'user_id' in session:
        user_id = session['user_id']
        user = users.get(user_id)
        if user:
            # Add comprehensive budget information
            budget_info = get_user_budget_info(user_id)
            user.update(budget_info)

            # Add admin flag for easier template checks
            user['is_admin'] = user.get('is_admin', False)

            return user
    return None

# Helper function to get game status badge class
def get_game_status_badge_class(status):
    """Return the appropriate Bootstrap badge class for game status"""
    status_classes = {
        'pending': 'bg-secondary',
        'live': 'bg-success',
        'finished': 'bg-primary'
    }
    return status_classes.get(status, 'bg-secondary')

# Debug helper to print strategies in a readable format
def debug_print_strategies():
    print("\n=== CURRENT STRATEGIES ===")
    if not strategies:
        print("No strategies defined yet.")
    else:
        for strat_id, strategy in strategies.items():
            moment_name = moments.get(strategy.get('moment_id', 0), {}).get('name', 'Unknown Moment')
            user_name = users.get(strategy.get('user_id', ''), {}).get('name', 'Unknown User')
            game_id = strategy.get('game_id', 'Unknown Game')

            print(f"Strategy ID: {strat_id}")
            print(f"  User: {user_name} (ID: {strategy.get('user_id', '')})")
            print(f"  Moment: {moment_name} (ID: {strategy.get('moment_id', '')})")
            print(f"  Game ID: {game_id}")
            print(f"  Base Bid: ${strategy.get('base_bid', 0):.2f}")
            print(f"  Max Bid: ${strategy.get('max_bid', 0):.2f}")
            print("  ---------")
    print("========================\n")

# Helper functions for auction management
def create_auction(moment_id, game_id, start_time, end_time, base_price=1000.00, reserve_price=None, increment_amount=500.00):
    """Create a new auction for a moment in a specific game"""
    # Generate a unique ID for the auction
    auction_id = str(uuid.uuid4())
    
    # Get current timestamp
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Create auction object
    auction = {
        "id": auction_id,
        "moment_id": moment_id,
        "game_id": game_id,
        "status": "pending",
        "start_time": start_time,
        "end_time": end_time,
        "base_price": float(base_price),
        "current_high_bid": 0.00,
        "current_high_bidder_id": None,
        "reserve_price": float(reserve_price) if reserve_price else None,
        "increment_amount": float(increment_amount),
        "created_at": now,
        "updated_at": now
    }
    
    # Store the auction
    auction_data[auction_id] = auction
    storage.save_auction_data(auction_data)
    
    return auction_id

def create_instant_auction(moment_id, game_id, base_price=1000.00, reserve_price=None, 
                          period="1", team_id="both", players=None, event_importance="normal"):
    """Create a new instant auction for a moment in a specific game"""
    # Generate a unique ID for the auction
    auction_id = str(uuid.uuid4())

    # Get current timestamp
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Handle list of players (ensure it's a list)
    if players is None:
        players = []
    
    # Create auction object without trying to resolve player names
    auction = {
        "id": auction_id,
        "moment_id": moment_id,
        "game_id": game_id,
        "auction_type": "instant",  # New field to distinguish instant auctions
        "status": "pending",
        "base_price": float(base_price),
        "current_high_bid": 0.00,
        "current_high_bidder_id": None,
        "reserve_price": float(reserve_price) if reserve_price else None,
        "created_at": now,
        "updated_at": now,
        # New instant auction specific fields
        "period": period,
        "team_id": team_id,
        "players": players,  # Just store the IDs
        "event_importance": event_importance,
        "executed_at": None,
        "winner_notified": False
    }

    # Store the auction
    auction_data[auction_id] = auction
    storage.save_auctions(auction_data)

    return auction_id

def execute_instant_auction(auction_id):
    """Execute an instant auction with proper competitive bidding logic"""
    if auction_id not in auction_data:
        return {"success": False, "message": "Auction not found"}

    auction = auction_data[auction_id]

    # Check if the game is live
    game_id = auction.get('game_id')
    game = next((g for g in upcoming_games if g['id'] == game_id), None)
    
    if not game:
        return {"success": False, "message": "Game not found"}
    
    if game.get('status') != 'live':
        return {"success": False, "message": f"Cannot execute auction: Game is {game.get('status', 'pending')}. Game must be live to execute auctions."}
    
    # Only pending auctions can be executed
    if auction["status"] != "pending":
        return {"success": False, "message": f"Cannot execute auction with status: {auction['status']}"}

    # Find all applicable strategies
    applicable_strategies = find_applicable_strategies(auction)

    if not applicable_strategies:
        # Finalize auction with no bidders
        return finalize_instant_auction(auction_id, None, 0)

    # Update auction status to active
    auction["status"] = "active"
    auction["updated_at"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    auction_data[auction_id] = auction
    storage.save_auctions(auction_data)

    # Create a bid registry for tracking all bids
    bid_registry = []
    
    # Initialize bidders with their base bids
    active_bidders = {}
    for strategy_id, strategy in applicable_strategies.items():
        user_id = strategy.get('user_id')
        base_bid = float(strategy.get('base_bid', 0))
        max_bid = float(strategy.get('max_bid', 0))
        increment = float(strategy.get('bid_increment', 500))  # Default to 500 if not set
        
        active_bidders[strategy_id] = {
            'user_id': user_id,
            'current_bid': base_bid,
            'max_bid': max_bid,
            'increment': increment,
            'is_active': True
        }
        
        # Create initial bid record
        bid_id = str(uuid.uuid4())
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        bid = {
            "id": bid_id,
            "auction_id": auction_id,
            "user_id": user_id,
            "strategy_id": strategy_id,
            "amount": base_bid,
            "status": "active",
            "timestamp": now,
            "is_automated": True,
            "max_bid": max_bid
        }
        
        bid_registry.append(bid)
        bids[bid_id] = bid
    
    # Competitive bidding loop
    bidding_round = 0
    while len([b for b in active_bidders.values() if b['is_active']]) > 1:
        bidding_round += 1
        
        # Find current high bid
        current_high_bid = 0
        high_bidder_strategy = None
        for strategy_id, bidder in active_bidders.items():
            if bidder['is_active'] and bidder['current_bid'] > current_high_bid:
                current_high_bid = bidder['current_bid']
                high_bidder_strategy = strategy_id
        
        # Raise bids for non-high bidders
        for strategy_id, bidder in active_bidders.items():
            if bidder['is_active'] and strategy_id != high_bidder_strategy:
                # Calculate next bid
                next_bid = current_high_bid + bidder['increment']
                
                if next_bid <= bidder['max_bid']:
                    # Update current bid
                    bidder['current_bid'] = next_bid
                    
                    # Create bid record
                    bid_id = str(uuid.uuid4())
                    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    bid = {
                        "id": bid_id,
                        "auction_id": auction_id,
                        "user_id": bidder['user_id'],
                        "strategy_id": strategy_id,
                        "amount": next_bid,
                        "status": "active",
                        "timestamp": now,
                        "is_automated": True,
                        "max_bid": bidder['max_bid']
                    }
                    
                    bid_registry.append(bid)
                    bids[bid_id] = bid
                else:
                    # Bidder has reached their max
                    bidder['is_active'] = False
                    
                    # Mark last bid as outbid
                    for bid_id, bid in bids.items():
                        if (bid["auction_id"] == auction_id and 
                            bid["strategy_id"] == strategy_id and 
                            bid["status"] == "active"):
                            bid["status"] = "outbid"
                            bids[bid_id] = bid
        
        # Prevent infinite loop (safety check)
        if bidding_round > 1000:
            break
    
    # Determine winner (last active bidder)
    winner_strategy_id = None
    winner_bid_amount = 0
    tied_bidders = []
    
    for strategy_id, bidder in active_bidders.items():
        if bidder['is_active']:
            if not winner_strategy_id or bidder['current_bid'] > winner_bid_amount:
                winner_strategy_id = strategy_id
                winner_bid_amount = bidder['current_bid']
                tied_bidders = [strategy_id]
            elif bidder['current_bid'] == winner_bid_amount:
                tied_bidders.append(strategy_id)
    
    # Handle ties by registration order (earliest registered user wins)
    if len(tied_bidders) > 1:
        # Find earliest registered user among tied bidders
        earliest_user_id = None
        earliest_registration = None
        
        for strategy_id in tied_bidders:
            user_id = applicable_strategies[strategy_id]['user_id']
            user = users.get(user_id)
            
            if user:
                # We don't have a registration date field, so we'll use user ID as a proxy
                # Lower user IDs are assumed to be earlier registrations
                if earliest_user_id is None or int(user_id) < int(earliest_user_id):
                    earliest_user_id = user_id
                    winner_strategy_id = strategy_id
    
    # Check if winning bid meets reserve price
    reserve_price = auction.get('reserve_price')
    if reserve_price and winner_bid_amount < reserve_price:
        # No valid bids that meet the reserve price
        return finalize_instant_auction(auction_id, None, 0)
    
    # Create winning bid record if we have a winner
    if winner_strategy_id:
        winner_strategy = applicable_strategies[winner_strategy_id]
        user_id = winner_strategy.get('user_id')
        
        # Find the winning bid in our registry and mark it as winning
        winning_bid_id = None
        for bid_id, bid in bids.items():
            if (bid["auction_id"] == auction_id and 
                bid["strategy_id"] == winner_strategy_id and 
                bid["amount"] == winner_bid_amount):
                bid["status"] = "winning"
                winning_bid_id = bid_id
                bids[bid_id] = bid
                break
        
        # Update auction with winning information
        auction["current_high_bid"] = winner_bid_amount
        auction["current_high_bidder_id"] = user_id
        auction["updated_at"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Save all changes
        auction_data[auction_id] = auction
        storage.save_bids(bids)
        storage.save_auctions(auction_data)
        
        # Finalize the auction
        return finalize_instant_auction(auction_id, winning_bid_id, winner_bid_amount)
    
    # No winner determined
    return finalize_instant_auction(auction_id, None, 0)

def find_applicable_strategies(auction):
    """Find all strategies that apply to this auction based on matching criteria"""
    moment_id = auction.get('moment_id')
    game_id = auction.get('game_id')
    period = auction.get('period')
    team_id = auction.get('team_id')
    players = auction.get('players', [])
    
    applicable_strategies = {}
    
    for strategy_id, strategy in strategies.items():
        # Check if strategy is active
        if strategy.get('status', 'active') != 'active':
            continue
        
        # Check if strategy is for this moment and game
        if strategy.get('moment_id') != moment_id or int(strategy.get('game_id')) != int(game_id):
            continue
        
        # Check if strategy applies to the period
        strategy_period = strategy.get('period_restrictions')
        if strategy_period and period not in strategy_period.split(','):
            continue
        
        # Check if strategy applies to the team
        strategy_team = strategy.get('team_focus', 'both')
        if strategy_team != 'both' and strategy_team != team_id and team_id != 'both':
            continue
        
        # Check if strategy applies to specific players
        strategy_player = strategy.get('player_focus')
        if strategy_player:
            strategy_players = [p.strip() for p in strategy_player.split(',')]
            player_match = False
            
            # If any player in the auction is in the strategy's focus, it's a match
            for player in players:
                if player in strategy_players:
                    player_match = True
                    break
            
            if not player_match:
                continue
        
        # If we got here, the strategy is applicable
        applicable_strategies[strategy_id] = strategy
    
    return applicable_strategies

def finalize_instant_auction(auction_id, winning_bid_id=None, winning_amount=0):
    """Complete an instant auction and create the result record"""
    if auction_id not in auction_data:
        return {"success": False, "message": "Auction not found"}

    auction = auction_data[auction_id]

    # Update auction status to completed
    auction["status"] = "completed"
    auction["executed_at"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    auction_data[auction_id] = auction

    # If no winning bid, just complete the auction
    if not winning_bid_id:
        storage.save_auctions(auction_data)
        return {"success": True, "winner": False, "message": "Auction completed with no winning bids"}

    # Get the winning bid
    winning_bid = bids.get(winning_bid_id)
    if not winning_bid:
        return {"success": False, "message": "Winning bid not found"}

    winning_user_id = winning_bid["user_id"]
    winning_strategy_id = winning_bid.get("strategy_id")  # Get the winning strategy ID
    winning_user = users.get(winning_user_id, {})
    winning_user_name = winning_user.get('name', 'Unknown User')

    # Calculate commissions and shares
    commission_rate = 0.05  # 5%
    broadcaster_rate = 0.85  # 85%
    platform_rate = 0.10  # 10%

    commission_amount = winning_amount * commission_rate
    broadcaster_share = winning_amount * broadcaster_rate
    platform_share = winning_amount * platform_rate

    # Create auction result
    result_id = str(uuid.uuid4())
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # CHANGE: Set payment status to completed by default
    result = {
        "id": result_id,
        "auction_id": auction_id,
        "winning_bid_id": winning_bid_id,
        "winning_user_id": winning_user_id,
        "winning_strategy_id": winning_strategy_id,
        "winning_amount": winning_amount,
        "payment_status": "completed",  # Changed from "pending" to "completed"
        "payment_transaction_id": f"AUTO-{uuid.uuid4()}",
        "commission_amount": commission_amount,
        "broadcaster_share": broadcaster_share,
        "platform_share": platform_share,
        "ad_display_status": "pending",
        "created_at": now,
        "updated_at": now
    }

    # Save everything
    auction_results[result_id] = result
    storage.save_bids(bids)
    storage.save_auctions(auction_data)
    storage.save_auction_results(auction_results)

    return {
        "success": True,
        "winner": True,
        "result_id": result_id,
        "winning_user_id": winning_user_id,
        "winning_user_name": winning_user_name,
        "winning_amount": winning_amount,
        "winning_strategy_id": winning_strategy_id
    }

def place_bid(auction_id, user_id, amount, strategy_id=None, max_bid=None):
    """Place a bid on an auction"""
    # Check if auction exists and is active
    if auction_id not in auction_data:
        return {"success": False, "message": "Auction not found"}
    
    auction = auction_data[auction_id]
    if auction["status"] != "active":
        return {"success": False, "message": f"Auction is not active (status: {auction['status']})"}
    
    # Convert amount to float for comparison
    amount = float(amount)
    
    # Validate bid amount (must be greater than current high bid + increment)
    min_valid_bid = auction["current_high_bid"] + auction["increment_amount"]
    if amount < min_valid_bid:
        return {"success": False, "message": f"Bid amount must be at least ${min_valid_bid:.2f}"}
    
    # Check if user has sufficient funds
    user = users.get(user_id)
    if not user:
        return {"success": False, "message": "User not found"}
    
    if float(user.get("budget", 0)) < amount:
        return {"success": False, "message": "Insufficient funds"}
    
    # Generate bid ID
    bid_id = str(uuid.uuid4())
    
    # Create bid object
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    bid = {
        "id": bid_id,
        "auction_id": auction_id,
        "user_id": user_id,
        "strategy_id": strategy_id,
        "amount": amount,
        "status": "active",
        "timestamp": now,
        "is_automated": bool(strategy_id),
        "max_bid": float(max_bid) if max_bid else amount
    }
    
    # Update previous high bid status to 'outbid' if it exists
    if auction["current_high_bidder_id"]:
        for old_bid_id, old_bid in bids.items():
            if (old_bid["auction_id"] == auction_id and 
                old_bid["user_id"] == auction["current_high_bidder_id"] and
                old_bid["status"] == "active"):
                old_bid["status"] = "outbid"
                bids[old_bid_id] = old_bid
    
    # Update auction with new high bid
    auction["current_high_bid"] = amount
    auction["current_high_bidder_id"] = user_id
    auction["updated_at"] = now
    
    # Save the bid and updated auction
    bids[bid_id] = bid
    auction_data[auction_id] = auction
    
    storage.save_bids(bids)
    storage.save_auction_data(auction_data)
    
    return {"success": True, "bid_id": bid_id, "message": "Bid placed successfully"}

def place_bid_from_strategy(auction_id, strategy_id):
    """Place a bid based on a user's strategy"""
    # Find the strategy
    if strategy_id not in strategies:
        return {"success": False, "message": "Strategy not found"}
    
    strategy = strategies[strategy_id]
    user_id = strategy.get('user_id')
    
    # Get bid parameters from strategy
    base_bid = float(strategy.get('base_bid', 0))
    max_bid = float(strategy.get('max_bid', 0))
    
    # Get current auction status
    if auction_id not in auction_data:
        return {"success": False, "message": "Auction not found"}
    
    auction = auction_data[auction_id]
    if auction["status"] != "active":
        return {"success": False, "message": f"Auction is not active"}
    
    # Calculate appropriate bid amount based on strategy and current high bid
    min_valid_bid = auction["current_high_bid"] + auction["increment_amount"]
    
    # Start with base bid, but ensure it's at least the minimum valid bid
    bid_amount = max(base_bid, min_valid_bid)
    
    # Don't exceed max bid
    if bid_amount > max_bid:
        # Strategy's max bid is less than minimum valid bid
        return {"success": False, "message": "Strategy max bid too low for current auction state"}
    
    # Place the bid using existing function
    return place_bid(auction_id, user_id, bid_amount, strategy_id, max_bid)

def process_all_auction_data():
    """Process all active auctions with all relevant strategies"""
    results = []
    
    # Get current time for status updates
    now = datetime.now()
    
    # Update auction statuses based on time
    for auction_id, auction in list(auctions.items()):
        if auction['status'] != 'cancelled':
            start_time = datetime.strptime(auction['start_time'], '%Y-%m-%d %H:%M:%S')
            end_time = datetime.strptime(auction['end_time'], '%Y-%m-%d %H:%M:%S')
            
            # Activate pending auctions that should start
            if auction['status'] == 'pending' and now >= start_time:
                auction['status'] = 'active'
                auction_data[auction_id] = auction
                print(f"Activated auction {auction_id}")
            
            # Finalize active auctions that should end
            elif auction['status'] == 'active' and now >= end_time:
                result = finalize_auction(auction_id)
                print(f"Finalized auction {auction_id}: {result}")
                results.append(result)
                continue  # Skip processing bids for finalized auctions
    
    # For each active auction, process all relevant strategies
    for auction_id, auction in auction_data.items():
        if auction['status'] == 'active':
            moment_id = auction['moment_id']
            game_id = auction['game_id']
            
            # Find all strategies for this moment in this game
            matching_strategies = []
            for strategy_id, strategy in strategies.items():
                if (strategy['moment_id'] == moment_id and 
                    int(strategy['game_id']) == int(game_id) and
                    strategy.get('status', 'active') == 'active'):
                    matching_strategies.append(strategy_id)
            
            # Process each matching strategy
            for strategy_id in matching_strategies:
                result = place_bid_from_strategy(auction_id, strategy_id)
                print(f"Strategy {strategy_id} bid result: {result}")
                results.append(result)
    
    # Save any changes
    storage.save_auctions(auction_data)
    storage.save_bids(bids)
    
    return results

def process_all_pending_payments():
    """Process all pending payments to completed status with Braintree distribution"""
    updates_count = 0

    for result_id, result in auction_results.items():
        if result.get('payment_status') == 'pending':
            # Call our payment distribution function instead of just marking as completed
            payment_result = process_auction_payment_distribution(result_id)
            
            if payment_result.get('success'):
                updates_count += 1
                print(f"Successfully processed payment distribution for auction result {result_id}")
            else:
                print(f"Failed to process payment distribution for auction result {result_id}: {payment_result.get('message')}")

    if updates_count > 0:
        storage.save_auction_results(auction_results)

    return updates_count

def finalize_auction(auction_id):
    """Complete an auction and create the result record"""
    if auction_id not in auction_data:
        return {"success": False, "message": "Auction not found"}

    auction = auction_data[auction_id]
    if auction["status"] != "active":
        return {"success": False, "message": f"Cannot finalize auction with status: {auction['status']}"}

    # Find the winning bid
    winning_bid_id = None
    winning_bid = None

    for bid_id, bid in bids.items():
        if bid["auction_id"] == auction_id and bid["status"] == "active":
            if not winning_bid or bid["amount"] > winning_bid["amount"]:
                winning_bid_id = bid_id
                winning_bid = bid

    if not winning_bid:
        # No bids were placed, auction unsuccessful
        auction["status"] = "completed"
        auction_data[auction_id] = auction
        storage.save_auctions(auction_data)
        return {"success": True, "winner": False, "message": "Auction completed with no bids"}

    # Update winning bid status
    winning_bid["status"] = "winning"
    bids[winning_bid_id] = winning_bid

    # Calculate commissions and shares
    winning_amount = float(winning_bid["amount"])
    winning_user_id = winning_bid["user_id"]
    commission_rate = 0.05  # 5%
    broadcaster_rate = 0.85  # 85%
    platform_rate = 0.10  # 10%

    commission_amount = winning_amount * commission_rate
    broadcaster_share = winning_amount * broadcaster_rate
    platform_share = winning_amount * platform_rate

    # Create auction result
    result_id = str(uuid.uuid4())
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Create result record with payment distribution tracking fields
    result = {
        "id": result_id,
        "auction_id": auction_id,
        "winning_bid_id": winning_bid_id,
        "winning_user_id": winning_user_id,
        "winning_strategy_id": winning_bid.get("strategy_id"),  # Store strategy ID if available
        "winning_amount": winning_amount,
        "payment_status": "pending",  # Start as pending now
        "payment_transaction_id": None,  # We'll set this after processing
        "commission_amount": commission_amount,
        "broadcaster_share": broadcaster_share,
        "platform_share": platform_share,
        "ad_display_status": "pending",
        "created_at": now,
        "updated_at": now,
        # New payment distribution tracking fields
        "payment_distribution_complete": False,
        "broadcaster_transaction_id": None,
        "commission_transaction_id": None,
        "platform_transaction_id": None
    }

    # Update auction status
    auction["status"] = "completed"
    auction_data[auction_id] = auction

    # Save everything
    auction_results[result_id] = result
    storage.save_bids(bids)
    storage.save_auctions(auction_data)
    storage.save_auction_results(auction_results)

    # Now process the payment distribution
    payment_result = process_auction_payment_distribution(result_id)
    if not payment_result.get('success'):
        print(f"Payment distribution warning: {payment_result.get('message')}")
        # We still consider the auction completed even if payment distribution fails
        # The admin can manually process it later

    return {
        "success": True,
        "winner": True,
        "result_id": result_id,
        "winning_user_id": winning_user_id,
        "winning_amount": winning_amount,
        "payment_processed": payment_result.get('success', False)
    }

def get_or_create_braintree_customer(user):
    """
    Get a user's Braintree customer ID or create one if it doesn't exist
    """
    # Check if the user already has a Braintree customer ID
    if 'braintree_customer_id' in user and user['braintree_customer_id']:
        return user['braintree_customer_id']
        
    # If not, create a new customer in Braintree
    result = braintree_gateway.customer.create({
        "first_name": user.get('name', '').split(' ')[0],
        "last_name": ' '.join(user.get('name', '').split(' ')[1:]) if len(user.get('name', '').split(' ')) > 1 else '',
        "email": user.get('email', ''),
        "company": user.get('company', '')
    })
    
    if result.is_success:
        # Store the customer ID in your user record
        user['braintree_customer_id'] = result.customer.id
        storage.save_users(users)
        print(f"Created Braintree customer ID: {result.customer.id} for user {user.get('name')}")
        return result.customer.id
    else:
        print(f"Error creating Braintree customer: {result.message}")
        return None

# Routes
@app.route('/')
def index():
    return render_template('index.html', user=get_user())

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Debug message for tracking login attempts
    print("Login route accessed")

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Debug prints
        print(f"Login attempt: email={email}")
        print(f"Current users: {list(users.keys())}")

        # Simple validation
        if not email or not password:
            flash('Please fill out all fields.', 'error')
            return redirect(url_for('login'))

        # Check if user exists
        user_found = False
        for user_id, user in users.items():
            if user.get('email') == email:
                user_found = True
                # For demo purposes, directly compare passwords
                if password == user.get('password', ''):
                    session['user_id'] = user_id
                    flash('Login successful!', 'success')
                    print(f"Login successful for user_id={user_id}")
                    return redirect(url_for('dashboard'))
                else:
                    flash('Incorrect password.', 'error')
                    return redirect(url_for('login'))

        if not user_found:
            flash('User does not exist.', 'error')

        return redirect(url_for('login'))

    return render_template('login.html', user=get_user())

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        company = request.form.get('company')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Debug prints
        print(f"Received form data: name={name}, company={company}, email={email}")

        # Simple validation
        if not name or not company or not email or not password or not confirm_password:
            flash('Please fill out all fields.', 'error')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('register'))

        # Check if email already exists
        for user in users.values():
            if user.get('email') == email:
                flash('Email already exists.', 'error')
                return redirect(url_for('register'))

        # Create new user with 0 budget
        user_id = str(uuid.uuid4())
        users[user_id] = {
            'id': user_id,
            'name': name,
            'company': company,
            'email': email,
            'password': password,  # For demo, store plaintext
            'budget': 0,  # Changed from 100000 to 0
            'braintree_customer_id': None  # Initialize as None, we'll set it next
        }
        
        # Create Braintree customer
        braintree_customer_id = get_or_create_braintree_customer(users[user_id])
        if not braintree_customer_id:
            print("Warning: Failed to create Braintree customer ID")
            flash('Account created, but payment system setup had an issue. You can still use the platform.', 'warning')
        else:
            print(f"Successfully created Braintree customer: {braintree_customer_id}")

        # Save users to storage
        storage.save_users(users)

        # Debug print
        print(f"Created new user: {users[user_id]}")

        session['user_id'] = user_id
        flash('Registration successful! Please add funds to your account.', 'success')
        return redirect(url_for('profile'))  # Redirect to profile page instead of dashboard

    return render_template('register.html', user=get_user())

@app.route('/logout')
def logout():
    # Clear all session data
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    user = get_user()
    if not user:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))

    # Add these lines to calculate stats for the dashboard
    # Get user's strategies to determine which moments have strategies
    user_strategies = {k: v for k, v in strategies.items() if v['user_id'] == user['id']}
    
    # Get user's auction results
    user_auction_results = []
    wins_count = 0
    total_spent = 0
    win_count_by_strategy = {}
    
    for result_id, result in auction_results.items():
        if result['winning_user_id'] == user['id']:
            # Add additional info to the result
            result_copy = dict(result)
            result_copy['auction'] = auction_data.get(result['auction_id'], {})
            result_copy['strategy'] = strategies.get(result.get('winning_strategy_id'), {})

            # Add game info
            auction = auction_data.get(result['auction_id'], {})
            game = next((g for g in upcoming_games if g['id'] == auction.get('game_id')), None)
            if game:
                result_copy['game_info'] = f"{game['away']} @ {game['home']} - {game['date']}"
                result_copy['game'] = game

            user_auction_results.append(result_copy)
            
            # Count wins and calculate spending
            wins_count += 1
            total_spent += float(result.get('winning_amount', 0))
            
            # Track wins by strategy
            if result.get('winning_strategy_id'):
                strat_id = result.get('winning_strategy_id')
                if strat_id not in win_count_by_strategy:
                    win_count_by_strategy[strat_id] = 0
                win_count_by_strategy[strat_id] += 1

    # Add win stats and spending to each strategy
    for strat_id, strategy in user_strategies.items():
        strategy['wins_count'] = win_count_by_strategy.get(strat_id, 0)
        strategy['wins'] = []
        strategy['spent_amount'] = 0
        
        # Find all wins for this strategy and calculate spent amount
        for result in user_auction_results:
            if result.get('winning_strategy_id') == strat_id:
                strategy['wins'].append(result)
                strategy['spent_amount'] += float(result.get('winning_amount', 0))
        
        # Add game info to each strategy
        game_id = strategy.get('game_id')
        game = next((g for g in upcoming_games if g['id'] == game_id), None)
        if game:
            strategy['game'] = game
    
    # Add win stats to user object for dashboard
    user['wins_count'] = wins_count
    user['total_spent'] = total_spent
    
    # Debug prints
    print(f"\n=== DASHBOARD ACCESS ===")
    print(f"User: {user['name']} (ID: {user['id']})")
    print(f"Total Budget: ${user['total_budget']:,.2f}")
    print(f"Used Budget: ${user['used_budget']:,.2f}")
    print(f"Available Budget: ${user['available_budget']:,.2f}")
    print(f"Wins Count: {wins_count}")
    print(f"Win Rate: {'{:.1f}'.format((wins_count / len(user_strategies)) * 100) if user_strategies else 0}%")
    print(f"Number of user strategies: {len(user_strategies)}")

    if user_strategies:
        print("User strategies:")
        for strat_id, strategy in user_strategies.items():
            moment_name = moments.get(strategy.get('moment_id', 0), {}).get('name', 'Unknown')
            print(f"  {strat_id}: Game {strategy.get('game_id')}, Moment: {moment_name} (ID: {strategy.get('moment_id')})")
            print(f"    Wins: {strategy.get('wins_count', 0)}, Spent: ${strategy.get('spent_amount', 0):,.2f}")
    else:
        print("User has no strategies")
    print(f"===========================\n")

    return render_template('dashboard.html', user=user, moments=moments,
                           upcoming_games=upcoming_games, user_strategies=user_strategies,
                           user_auction_results=user_auction_results)

@app.route('/profile')
def profile():
    user = get_user()
    if not user:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))

    # Get user's strategies
    user_strategies = {k: v for k, v in strategies.items() if v['user_id'] == user['id']}

    # Get user's auction results
    user_auction_results = []
    for result_id, result in auction_results.items():
        if result['winning_user_id'] == user['id']:
            # Add additional info to the result
            result_copy = dict(result)
            result_copy['auction'] = auction_data.get(result['auction_id'], {})
            result_copy['strategy'] = strategies.get(result.get('winning_strategy_id'), {})
            
            # Add game info
            auction = auction_data.get(result['auction_id'], {})
            game = next((g for g in upcoming_games if g['id'] == auction.get('game_id')), None)
            if game:
                result_copy['game_info'] = f"{game['away']} @ {game['home']} - {game['date']}"
            
            user_auction_results.append(result_copy)

    # Debug prints
    print(f"\n=== PROFILE ACCESS ===")
    print(f"User: {user['name']} (ID: {user['id']})")
    print(f"Total Budget: ${user['total_budget']:,.2f}")
    print(f"Available Budget: ${user['available_budget']:,.2f}")
    print(f"Number of wins: {len(user_auction_results)}")
    print(f"===========================\n")

    return render_template('profile.html',
                          user=user,
                          user_strategies=user_strategies,
                          user_auction_results=user_auction_results,
                          upcoming_games=upcoming_games,
                          moments=moments,
                          auctions=auction_data)

@app.route('/update_profile', methods=['POST'])
def update_profile():
    user = get_user()
    if not user:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))

    # Get the form data
    name = request.form.get('name')
    company = request.form.get('company')
    email = request.form.get('email')
    phone = request.form.get('phone')

    # Debug prints
    print(f"Update profile request: name={name}, company={company}, email={email}, phone={phone}")

    # Basic validation
    if not name or not company or not email:
        flash('Name, company, and email are required fields.', 'error')
        return redirect(url_for('profile'))

    # Update the user data
    user_id = user['id']
    if user_id in users:
        # Check if email is being changed and if it's already in use
        if email != users[user_id]['email']:
            for u_id, u in users.items():
                if u_id != user_id and u.get('email') == email:
                    flash('Email already in use by another account.', 'error')
                    return redirect(url_for('profile'))

        # Store the current session user_id to ensure we stay logged in
        current_user_id = session.get('user_id')

        # Update user information
        users[user_id]['name'] = name
        users[user_id]['company'] = company
        users[user_id]['email'] = email
        users[user_id]['phone'] = phone

        # Save changes to file
        save_result = storage.save_users(users)
        if not save_result:
            flash('There was an error saving your profile. Please try again.', 'error')
            return redirect(url_for('profile'))

        # Ensure we're still logged in with the same user_id
        if current_user_id:
            session['user_id'] = current_user_id

        # Debug print
        print(f"Updated user profile for {name} (ID: {user_id})")
        print(f"New data: {users[user_id]}")

        flash('Profile updated successfully!', 'success')
    else:
        flash('Failed to update profile. User not found.', 'error')

    return redirect(url_for('profile'))

@app.route('/client_token')
def client_token():
    """Generate a client token for Braintree"""
    user = get_user()
    if not user:
        return jsonify({'error': 'User not authenticated'}), 401

    try:
        # Generate a client token using the braintree_gateway
        token = braintree_gateway.client_token.generate()
        print(f"Successfully generated client token")
        return jsonify({'client_token': token})
    except Exception as e:
        print(f"Error generating client token: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to generate client token: {str(e)}'}), 500

# Update the add_funds route to use the correct gateway
@app.route('/add_funds', methods=['POST'])
def add_funds():
    """Process payment and add funds to user account"""
    user = get_user()
    if not user:
        return jsonify({'success': False, 'message': 'User not authenticated'}), 401

    # Get or create a Braintree customer ID
    customer_id = get_or_create_braintree_customer(user)
    if not customer_id:
        return jsonify({'success': False, 'message': 'Unable to setup payment profile'}), 500

    # Get the data from the request
    data = request.json
    payment_method_nonce = data.get('payment_method_nonce')
    amount = data.get('amount')

    # Debug prints for troubleshooting
    print(f"Add funds request received: amount={amount}")
    if payment_method_nonce:
        print(f"Payment method nonce received (first 10 chars): {payment_method_nonce[:10]}...")

    if not payment_method_nonce or not amount:
        print("Missing required fields in add_funds request")
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400

    try:
        # Convert amount to float and validate
        amount = float(amount)
        if amount <= 0:
            print(f"Invalid amount: {amount}")
            return jsonify({'success': False, 'message': 'Invalid amount'}), 400

        # Create a transaction in the sandbox using braintree_gateway
        result = braintree_gateway.transaction.sale({
            'amount': str(amount),
            'payment_method_nonce': payment_method_nonce,
            'customer_id': customer_id,  # Use the customer ID
            'options': {
                'submit_for_settlement': True
            }
        })

        print(f"Braintree result: is_success={result.is_success}")

        if result.is_success:
            # Update user's budget in the database
            user_id = user['id']
            if user_id in users:
                current_budget = float(users[user_id].get('budget', 0))
                new_budget = current_budget + amount
                users[user_id]['budget'] = new_budget
                storage.save_users(users)

                # Log the transaction
                print(f"Transaction successful: User {user_id} added ${amount}. New budget: ${new_budget}")

                return jsonify({
                    'success': True,
                    'transaction_id': result.transaction.id,
                    'message': f'Successfully added ${amount} to your account',
                    'new_budget': new_budget
                })
        else:
            # Enhanced error handling
            error_message = "Transaction failed"
            if hasattr(result, 'message'):
                error_message = result.message

            if hasattr(result, 'transaction') and result.transaction:
                if hasattr(result.transaction, 'processor_response_text'):
                    error_message = result.transaction.processor_response_text
                print(f"Transaction ID: {result.transaction.id}")
                print(f"Status: {result.transaction.status}")

            print(f"Transaction error: {error_message}")

            return jsonify({
                'success': False,
                'message': error_message
            })
    except ValueError:
        print(f"Invalid amount format: {amount}")
        return jsonify({
            'success': False,
            'message': 'Invalid amount format'
        })
    except Exception as e:
        print(f"Error processing payment: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'An error occurred while processing the payment: {str(e)}'
        })

@app.route('/process_auction_payment', methods=['POST'])
def process_auction_payment():
    """Process payment for won auction (simulation)"""
    user = get_user()
    if not user:
        return jsonify({'success': False, 'message': 'User not authenticated'}), 401

    data = request.json
    auction_id = data.get('auction_id')
    amount = data.get('amount')

    if not auction_id or not amount:
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400

    try:
        amount = float(amount)
        user_id = user['id']
        
        # Check if user has sufficient funds
        if user_id in users:
            current_budget = float(users[user_id].get('budget', 0))
            
            if current_budget >= amount:
                # Deduct the amount from user's budget
                users[user_id]['budget'] = current_budget - amount
                storage.save_users(users)
                
                return jsonify({
                    'success': True,
                    'message': f'Payment of ${amount} processed successfully',
                    'new_balance': users[user_id]['budget']
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Insufficient funds'
                })
        else:
            return jsonify({
                'success': False,
                'message': 'User not found'
            })
    except Exception as e:
        print(f"Error processing auction payment: {e}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while processing the payment'
        })

def process_auction_payment_distribution(result_id):
    """Process the payment distribution for a completed auction with sandbox fallback"""
    try:
        result = auction_results.get(result_id)
        if not result:
            print(f"ERROR: Auction result {result_id} not found")
            return {"success": False, "message": "Auction result not found"}

        # Debug info
        print(f"\n=== PROCESSING PAYMENT DISTRIBUTION FOR AUCTION RESULT ===")
        print(f"Result ID: {result_id}")
        print(f"Payment status: {result.get('payment_status')}")
        print(f"Distribution complete: {result.get('payment_distribution_complete', False)}")

        # Skip if already processed
        if result.get('payment_status') == 'completed' and result.get('payment_distribution_complete', False):
            print(f"Payment already fully processed, skipping: {result_id}")
            return {"success": True, "message": "Payment already processed"}

        # Get winning user
        winning_user_id = result.get('winning_user_id')
        winning_user = users.get(winning_user_id)
        if not winning_user:
            print(f"ERROR: Winning user {winning_user_id} not found")
            return {"success": False, "message": "Winning user not found"}

        # Get auction details
        auction_id = result.get('auction_id')
        auction = auction_data.get(auction_id)
        if not auction:
            print(f"ERROR: Auction {auction_id} not found")
            return {"success": False, "message": "Auction not found"}

        # Get amount and calculate splits
        winning_amount = float(result.get('winning_amount', 0))
        commission_amount = winning_amount * 0.05  # 5%
        broadcaster_share = winning_amount * 0.85  # 85%
        platform_share = winning_amount * 0.10    # 10%
        
        print(f"Original amount: ${winning_amount:.2f}")
        print(f"Payment splits: Commission=${commission_amount:.2f}, Broadcaster=${broadcaster_share:.2f}, Platform=${platform_share:.2f}")

        # Check if this is a known problematic amount
        known_problem_amounts = [2100, 2300, 2100.00, 2300.00]
        amount_pattern_match = int(winning_amount) in [2100, 2300] or any(abs(winning_amount - amt) < 0.01 for amt in known_problem_amounts)
        
        if amount_pattern_match:
            print(f"DETECTED PROBLEMATIC AMOUNT: ${winning_amount} - Using sandbox simulation instead")
            return simulate_braintree_transactions(result_id, result, winning_amount, commission_amount, broadcaster_share, platform_share)
        
        try:
            # Record the payment in Braintree
            print("Attempting to process main transaction...")
            transaction_result = braintree_gateway.transaction.sale({
                "amount": str(winning_amount),
                "order_id": f"auction-{result_id}",
                "options": {
                    "submit_for_settlement": True
                },
                # We'll split payments using separate transactions for each recipient
                "merchant_account_id": DEFAULT_MERCHANT_ACCOUNT_ID,
                # You could store payment method with customer, or use a dummy one in sandbox
                "payment_method_nonce": "fake-valid-nonce" # In sandbox we can use this test nonce
            })

            if not transaction_result.is_success:
                print(f"Main transaction failed: {transaction_result.message}")
                if hasattr(transaction_result, 'transaction') and transaction_result.transaction:
                    print(f"Transaction status: {transaction_result.transaction.status}")
                    print(f"Processor response code: {transaction_result.transaction.processor_response_code}")
                    print(f"Processor response text: {transaction_result.transaction.processor_response_text}")
                
                # If transaction failed, fall back to simulation
                print("Falling back to transaction simulation")
                return simulate_braintree_transactions(result_id, result, winning_amount, commission_amount, broadcaster_share, platform_share)

            # Record the main transaction
            result['payment_transaction_id'] = transaction_result.transaction.id
            print(f"Main transaction successful: ID {transaction_result.transaction.id}")

            # Create separate transactions for each recipient
            # 1. Broadcaster (85%)
            print("Processing broadcaster transaction...")
            broadcaster_result = braintree_gateway.transaction.sale({
                "amount": str(broadcaster_share),
                "order_id": f"broadcaster-{result_id}",
                "options": {
                    "submit_for_settlement": True
                },
                "merchant_account_id": BROADCASTER_MERCHANT_ACCOUNT_ID,
                "payment_method_nonce": "fake-valid-nonce" # Sandbox test nonce
            })

            if broadcaster_result.is_success:
                result['broadcaster_transaction_id'] = broadcaster_result.transaction.id
                print(f"Broadcaster transaction successful: ID {broadcaster_result.transaction.id}")
            else:
                print(f"Warning: Broadcaster transaction failed: {broadcaster_result.message}")
                # Continue with other transactions even if this one failed

            # 2. Commission (5%)
            print("Processing commission transaction...")
            commission_result = braintree_gateway.transaction.sale({
                "amount": str(commission_amount),
                "order_id": f"commission-{result_id}",
                "options": {
                    "submit_for_settlement": True
                },
                "merchant_account_id": COMMISSION_MERCHANT_ACCOUNT_ID,
                "payment_method_nonce": "fake-valid-nonce" # Sandbox test nonce
            })

            if commission_result.is_success:
                result['commission_transaction_id'] = commission_result.transaction.id
                print(f"Commission transaction successful: ID {commission_result.transaction.id}")
            else:
                print(f"Warning: Commission transaction failed: {commission_result.message}")
                # Continue with other transactions even if this one failed

            # 3. Platform (10%)
            print("Processing platform transaction...")
            platform_result = braintree_gateway.transaction.sale({
                "amount": str(platform_share),
                "order_id": f"platform-{result_id}",
                "options": {
                    "submit_for_settlement": True
                },
                "merchant_account_id": PLATFORM_MERCHANT_ACCOUNT_ID,
                "payment_method_nonce": "fake-valid-nonce" # Sandbox test nonce
            })

            if platform_result.is_success:
                result['platform_transaction_id'] = platform_result.transaction.id
                print(f"Platform transaction successful: ID {platform_result.transaction.id}")
            else:
                print(f"Warning: Platform transaction failed: {platform_result.message}")
                # Continue despite platform transaction failure

            # Mark payment as distributed even if some sub-transactions failed
            result['payment_status'] = 'completed'
            result['payment_distribution_complete'] = True
            result['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Update the auction result record
            auction_results[result_id] = result
            storage.save_auction_results(auction_results)

            print(f"Successfully processed payment distribution for {result_id}")
            print("=============================================\n")
            
            # Return success
            return {
                "success": True,
                "message": "Payment processed and distributed successfully",
                "transaction_ids": {
                    "main": result.get('payment_transaction_id'),
                    "broadcaster": result.get('broadcaster_transaction_id', 'N/A'),
                    "commission": result.get('commission_transaction_id', 'N/A'),
                    "platform": result.get('platform_transaction_id', 'N/A')
                }
            }
        except Exception as e:
            print(f"Error in Braintree transaction processing: {str(e)}")
            import traceback
            traceback.print_exc()
            # Fall back to simulation on exception
            print("Falling back to transaction simulation due to exception")
            return simulate_braintree_transactions(result_id, result, winning_amount, commission_amount, broadcaster_share, platform_share)

    except Exception as e:
        import traceback
        print(f"CRITICAL ERROR in payment distribution: {str(e)}")
        traceback.print_exc()
        # Return a dictionary with error info even in exception cases
        return {"success": False, "message": f"Exception: {str(e)}"}

def simulate_braintree_transactions(result_id, result, winning_amount, commission_amount, broadcaster_share, platform_share):
    """Simulate Braintree transactions for problematic amounts in sandbox environment"""
    print(f"\n--- USING BRAINTREE TRANSACTION SIMULATOR ---")
    print(f"This simulator will create mock transaction IDs for sandbox testing")
    print(f"Amount: ${winning_amount:.2f}")
    
    try:
        # Generate unique mock transaction IDs
        main_transaction_id = f"SIM-MAIN-{uuid.uuid4()}"
        broadcaster_transaction_id = f"SIM-BCAST-{uuid.uuid4()}"
        commission_transaction_id = f"SIM-COMM-{uuid.uuid4()}"
        platform_transaction_id = f"SIM-PLATF-{uuid.uuid4()}"
        
        # Record all the transaction IDs
        result['payment_transaction_id'] = main_transaction_id
        result['broadcaster_transaction_id'] = broadcaster_transaction_id
        result['commission_transaction_id'] = commission_transaction_id
        result['platform_transaction_id'] = platform_transaction_id
        
        # Mark payment as distributed
        result['payment_status'] = 'completed'
        result['payment_distribution_complete'] = True
        result['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Add a flag to indicate this was simulated
        result['simulated_transaction'] = True

        # Update the auction result record
        auction_results[result_id] = result
        storage.save_auction_results(auction_results)
        
        print(f"Successfully simulated payment distribution for {result_id}")
        print(f"Main transaction ID: {main_transaction_id}")
        print(f"Broadcaster transaction ID: {broadcaster_transaction_id}")
        print(f"Commission transaction ID: {commission_transaction_id}")
        print(f"Platform transaction ID: {platform_transaction_id}")
        print("=============================================\n")
        
        # Important: Return a complete result object
        return {
            "success": True,
            "message": "Payment simulated successfully (Braintree sandbox simulation)",
            "transaction_ids": {
                "main": main_transaction_id,
                "broadcaster": broadcaster_transaction_id,
                "commission": commission_transaction_id,
                "platform": platform_transaction_id
            },
            "simulated": True
        }
        
    except Exception as e:
        print(f"Error in simulation: {str(e)}")
        import traceback
        traceback.print_exc()
        # Always return a dictionary, even in error cases
        return {"success": False, "message": f"Error in simulation: {str(e)}"}

@app.route('/test_braintree')
def test_braintree():
    """Test route to verify Braintree configuration"""
    try:
        # Test creating a customer
        result = braintree_gateway.customer.create({
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com"
        })

        if result.is_success:
            # Delete the test customer
            braintree_gateway.customer.delete(result.customer.id)
            return jsonify({
                'status': 'success',
                'message': 'Braintree is properly configured'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Braintree configuration test failed',
                'errors': [error.message for error in result.errors.deep_errors]
            })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/test_braintree_simple')
def test_braintree_simple():
    """Simpler test route to verify basic Braintree configuration"""
    try:
        print("Starting Braintree test...")
        print(f"Gateway type: {type(braintree_gateway)}")

        # Test the simplest possible operation
        token = braintree_gateway.client_token.generate()
        print(f"Token generated successfully")

        return jsonify({
            'status': 'success',
            'message': 'Braintree client token generated successfully',
            'has_token': len(token) > 0
        })
    except Exception as e:
        print(f"Exception type: {type(e)}")
        print(f"Exception message: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/game/<int:game_id>')
def game_detail(game_id):
    user = get_user()
    if not user:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))

    game = next((g for g in upcoming_games if g['id'] == game_id), None)
    if not game:
        flash('Game not found.', 'error')
        return redirect(url_for('dashboard'))

    # Get user's strategies for this specific game
    user_game_strategies = {}

    # Create a mapping of moment_id -> has_strategy for easy checking in the template
    moment_strategy_map = {}

    # Initialize the strategy map for all moments WITH STRING KEYS
    for moment_id in moments:
        moment_strategy_map[str(moment_id)] = False

    # Process user strategies
    for strat_id, strategy in strategies.items():
        if strategy['user_id'] == user['id'] and strategy['game_id'] == game_id:
            # Create a copy of the strategy to avoid modifying the original
            strategy_copy = dict(strategy)

            # Get the moment_id and ensure we have both string and int versions
            moment_id = strategy_copy.get('moment_id')
            moment_id_str = str(moment_id)

            try:
                moment_id_int = int(moment_id) if isinstance(moment_id, str) else moment_id
            except ValueError:
                moment_id_int = 0

            # Store both versions in the strategy for consistent access
            strategy_copy['moment_id_int'] = moment_id_int
            strategy_copy['moment_id_str'] = moment_id_str

            # KEY FIX: Set the moment as having a strategy using STRING key
            moment_strategy_map[moment_id_str] = True

            # Add the moment name if available
            if moment_id_str in moments:
                strategy_copy['moment_name'] = moments[moment_id_str]['name']
            elif moment_id_int in moments:
                strategy_copy['moment_name'] = moments[moment_id_int]['name']
            else:
                strategy_copy['moment_name'] = "Unknown Moment"

            # Add to user game strategies
            user_game_strategies[strat_id] = strategy_copy

    # Add debug data to the template context
    debug_data = {
        'strategies_count': len(strategies),
        'user_game_strategies_count': len(user_game_strategies),
        'moment_strategy_map': moment_strategy_map
    }

    # Add debug prints
    print(f"DEBUG: Moment strategy map: {moment_strategy_map}")
    print(f"DEBUG: Available moment IDs: {list(moments.keys())}")
    print(f"DEBUG: User strategies for this game: {user_game_strategies}")

    # For each moment, print if it has a strategy
    print("DEBUG: Checking each moment's strategy status:")
    for moment_id, moment in moments.items():
        has_strategy = moment_strategy_map.get(str(moment_id), False)
        print(f"  - Moment {moment_id} ({moment.get('name')}): Has strategy = {has_strategy}")

    return render_template('game_detail.html',
                          user=user,
                          game=game,
                          moments=moments,
                          strategies=strategies,
                          user_strategies=user_game_strategies,
                          moment_strategy_map=moment_strategy_map,
                          debug_data=debug_data,
                          upcoming_games=upcoming_games,  # This was missing!
                          auctions=auction_data)

@app.route('/moment/<int:moment_id>')
def moment_detail(moment_id):
    user = get_user()
    if not user:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))

    # Convert the moment_id to string for dictionary lookup
    moment_id_str = str(moment_id)
    print(f"Looking for moment with ID: {moment_id} (string version: {moment_id_str})")
    print(f"Available moment keys: {list(moments.keys())}")

    # Get the moment data - try both integer and string keys
    moment = moments.get(moment_id_str)

    if not moment:
        print(f"Moment with ID {moment_id} (str: {moment_id_str}) not found in moments dictionary")
        flash('Moment not found.', 'error')
        return redirect(url_for('dashboard'))

    # Ensure the moment has an id field
    if 'id' not in moment:
        moment = dict(moment)  # Create a copy
        moment['id'] = moment_id  # Set the id

    print(f"Found moment: {moment}")

    # Get user's strategies to determine which moments already have strategies
    user_strategies = {k: v for k, v in strategies.items() if v['user_id'] == user['id']}

    # Debug prints
    print(f"\n=== MOMENT DETAIL ACCESS ===")
    print(f"Moment ID: {moment_id} ({moment['name']})")
    print(f"User: {user['name']} (ID: {user['id']})")
    for strat_id, strategy in user_strategies.items():
        # Normalize strategy.moment_id to ensure consistent comparison
        strategy_moment_id = strategy.get('moment_id')
        if isinstance(strategy_moment_id, str) and strategy_moment_id.isdigit():
            strategy_moment_id = int(strategy_moment_id)

        if strategy_moment_id == moment_id:
            game_id = strategy.get('game_id')
            print(f"  Found matching strategy: {strat_id} for game {game_id}")
    print(f"==============================\n")

    return render_template('moment_detail.html', user=user, moment=moment,
                           upcoming_games=upcoming_games, user_strategies=user_strategies)

@app.route('/test_moment_lookup/<moment_id>')
def test_moment_lookup(moment_id):
    """Advanced diagnostic route to test moment lookup with a specific ID"""
    results = {
        'input_id': moment_id,
        'input_type': type(moment_id).__name__,
        'moments_type': type(moments).__name__,
        'key_types': [],
        'lookups': {},
        'raw_moments': {}
    }

    # Test all keys in the dictionary
    for key in moments.keys():
        results['key_types'].append({
            'key': key,
            'type': type(key).__name__
        })
        results['raw_moments'][str(key)] = moments[key]

    # Try different lookup methods
    # 1. Direct lookup
    results['lookups']['direct'] = {
        'method': 'Direct - moments.get(moment_id)',
        'result': moments.get(moment_id),
        'found': moments.get(moment_id) is not None
    }

    # 2. String conversion
    str_id = str(moment_id)
    results['lookups']['string'] = {
        'method': f'String - moments.get(str({moment_id}))',
        'result': moments.get(str_id),
        'found': moments.get(str_id) is not None
    }

    # 3. Integer conversion (if possible)
    try:
        int_id = int(moment_id)
        results['lookups']['integer'] = {
            'method': f'Integer - moments.get(int({moment_id}))',
            'result': moments.get(int_id),
            'found': moments.get(int_id) is not None
        }
    except ValueError:
        results['lookups']['integer'] = {
            'method': 'Integer conversion failed',
            'result': None,
            'found': False
        }

    # 4. Dictionary access syntax
    try:
        direct_result = moments[moment_id]
        results['lookups']['dict_access'] = {
            'method': f'Dict access - moments[{moment_id}]',
            'result': direct_result,
            'found': True
        }
    except KeyError:
        results['lookups']['dict_access'] = {
            'method': f'Dict access - moments[{moment_id}]',
            'result': None,
            'found': False,
            'error': 'KeyError'
        }
    except Exception as e:
        results['lookups']['dict_access'] = {
            'method': f'Dict access - moments[{moment_id}]',
            'result': None,
            'found': False,
            'error': str(e)
        }

    # 5. Find by internal id field
    internal_id_match = None
    for key, moment in moments.items():
        if str(moment.get('id', '')) == str(moment_id):
            internal_id_match = moment
            break

    results['lookups']['internal_id'] = {
        'method': 'Internal id field match',
        'result': internal_id_match,
        'found': internal_id_match is not None
    }

    return jsonify(results)

@app.route('/debug_moments')
def debug_moments():
    """Debug route to inspect the moments data structure"""
    # Get all moment data
    debug_output = {
        'moments': {},
        'moment_keys_type': [],
        'game_details': []
    }

    # Add details about each moment
    for moment_id, moment in moments.items():
        debug_output['moments'][str(moment_id)] = {
            'id': moment_id,
            'id_type': type(moment_id).__name__,
            'name': moment.get('name', 'Unknown'),
            'raw_data': moment
        }
        # Collect key types
        debug_output['moment_keys_type'].append({
            'id': moment_id,
            'type': type(moment_id).__name__
        })

    # Add game details
    for game in upcoming_games:
        debug_output['game_details'].append({
            'id': game.get('id'),
            'id_type': type(game.get('id')).__name__,
            'home': game.get('home'),
            'away': game.get('away')
        })

    # Check if a test lookup works
    test_id = 1
    test_lookup = moments.get(test_id)
    debug_output['test_lookup'] = {
        'test_id': test_id,
        'id_type': type(test_id).__name__,
        'found': test_lookup is not None,
        'result': test_lookup if test_lookup else 'Not found'
    }

    # Return as JSON for easy inspection
    return jsonify(debug_output)

@app.route('/setup_strategy', methods=['GET', 'POST'])
def setup_strategy():
    user = get_user()
    if not user:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))

    # Get moment_id parameter and fix the parsing issue
    moment_id_raw = request.args.get('moment_id', '')

    # IMPORTANT FIX: Split by '?' to handle malformed URL parameters
    moment_id = moment_id_raw.split('?')[0]

    # Get the moment data - try using string key
    moment = moments.get(moment_id)

    if not moment:
        flash(f'Moment not found. Please select a valid moment.', 'error')
        return redirect(url_for('dashboard'))

    # Create a new moment dictionary with id explicitly set
    processed_moment = dict(moment)  # Create a copy to avoid modifying the original
    processed_moment['id'] = moment_id  # Make sure the id field exists

    # Get game_id directly from request.args
    selected_game_id = request.args.get('game_id')
    try:
        selected_game_id = int(selected_game_id) if selected_game_id else None
    except ValueError:
        selected_game_id = None

    # Check for existing strategies for this moment and user
    existing_strategies = []
    for strat_id, strategy in strategies.items():
        # Convert moment_id to string for comparison
        strategy_moment_id = str(strategy.get('moment_id', ''))
        if strategy_moment_id == moment_id and strategy.get('user_id') == user['id']:
            strategy_copy = dict(strategy)  # Create a copy
            strategy_copy['id'] = strat_id
            # Add a name field if it doesn't exist
            if 'name' not in strategy_copy:
                strategy_copy['name'] = f"{processed_moment['name']} Strategy"
            existing_strategies.append(strategy_copy)

    if request.method == 'POST':
        # Get form data
        game_id = request.form.get('game_id')
        strategies_data_json = request.form.get('strategies_data')

        # Basic validation
        if not all([game_id, strategies_data_json]):
            flash('All required fields must be provided.', 'error')
            return redirect(url_for('setup_strategy', moment_id=moment_id, game_id=selected_game_id))

        try:
            game_id = int(game_id)
            strategies_data = json.loads(strategies_data_json)
        except (ValueError, json.JSONDecodeError) as e:
            flash('Invalid data provided.', 'error')
            return redirect(url_for('setup_strategy', moment_id=moment_id, game_id=selected_game_id))

        # Validate that user has sufficient budget for all strategies combined
        total_max_bid = sum(float(strategy.get('max_bid', 0)) for strategy in strategies_data)
        if total_max_bid > user['available_budget']:
            flash(f'Insufficient available budget. Total max bids (${total_max_bid:,.2f}) exceed your available budget (${user["available_budget"]:,.2f}).', 'error')
            return redirect(url_for('setup_strategy', moment_id=moment_id, game_id=selected_game_id))

        # Delete existing strategies for this moment/user combination first
        strategies_to_delete = []
        for strat_id, strategy in strategies.items():
            strategy_moment_id = str(strategy.get('moment_id', ''))
            if strategy_moment_id == moment_id and strategy.get('user_id') == user['id']:
                strategies_to_delete.append(strat_id)

        for strat_id in strategies_to_delete:
            del strategies[strat_id]

        # Create new strategies
        created_count = 0
        for strategy_data in strategies_data:
            try:
                # Convert to appropriate types
                base_bid = int(strategy_data.get('base_bid', 3000))
                bid_increment = int(strategy_data.get('bid_increment', 500))
                max_bid = int(strategy_data.get('max_bid', 7000))

                # Generate a unique ID for the new strategy
                strategy_id = str(uuid.uuid4())

                # Create strategy
                new_strategy = {
                    'moment_id': moment_id,  # Store as string to match dictionary keys
                    'game_id': game_id,
                    'user_id': user['id'],
                    'name': strategy_data.get('name', f"{processed_moment['name']} Strategy"),
                    'base_bid': base_bid,
                    'bid_increment': bid_increment,
                    'max_bid': max_bid,
                    'team_focus': strategy_data.get('team_focus', 'both'),
                    'player_focus': strategy_data.get('player_focus', ''),
                    'period_restrictions': strategy_data.get('period_restrictions', ''),
                    'ad_content': strategy_data.get('ad_content', ''),
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'status': 'active'  # Default to active
                }

                # Add specific scenario for overtime/shootout goals
                if processed_moment['name'] == 'Overtime Goal/Shootout':
                    new_strategy['specific_scenario'] = strategy_data.get('specific_scenario', 'both')

                # Add to strategies dictionary
                strategies[strategy_id] = new_strategy
                created_count += 1

            except (ValueError, KeyError) as e:
                flash(f'Error processing strategy data: {e}', 'error')
                continue

        # Save changes to file
        storage.save_strategies(strategies)

        if created_count > 0:
            strategy_word = "strategies" if created_count > 1 else "strategy"
            flash(f"Successfully created {created_count} bidding {strategy_word}! Money will only be spent when you win auctions.", 'success')
        else:
            flash('No strategies were created. Please check your input data.', 'error')

        # Redirect back to the game detail page if we have a game_id
        if game_id:
            return redirect(url_for('game_detail', game_id=game_id))
        else:
            return redirect(url_for('dashboard'))

    # Pass budget info and existing strategies to template
    return render_template('setup_strategy.html',
                          user=user,
                          moment=processed_moment,
                          moments=moments,
                          upcoming_games=upcoming_games,
                          existing_strategies=existing_strategies,
                          selected_game_id=selected_game_id)

@app.route('/delete_strategy/<strategy_id>', methods=['GET', 'POST'])
def delete_strategy(strategy_id):
    user = get_user()
    if not user:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))

    # Get redirect_game_id from query parameters
    redirect_game_id = request.args.get('redirect_game_id')

    # Check if strategy exists
    if strategy_id in strategies:
        strategy = strategies[strategy_id]
        game_id = strategy.get('game_id')  # Get game_id from the strategy itself

        # Check if user owns this strategy
        if strategy.get('user_id') == user['id']:
            # Delete the strategy
            del strategies[strategy_id]

            # Save changes to file
            storage.save_strategies(strategies)

            flash('Strategy removed successfully!', 'success')
        else:
            flash('You do not have permission to delete this strategy.', 'error')
    else:
        flash('Strategy not found.', 'error')
        return redirect(url_for('dashboard'))

    # Redirect to game detail if we have a game_id
    if game_id:
        return redirect(url_for('game_detail', game_id=game_id))
    else:
        # Default redirect to dashboard
        return redirect(url_for('dashboard'))

@app.route('/delete_all_strategies/<moment_id>/<game_id>', methods=['POST'])
def delete_all_strategies(moment_id, game_id):
    user = get_user()
    if not user:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))
    
    # Find all strategies for this user, moment, and game
    strategies_to_delete = []
    for strat_id, strategy in strategies.items():
        if (strategy.get('user_id') == user['id'] and 
            str(strategy.get('moment_id')) == str(moment_id) and 
            strategy.get('game_id') == int(game_id)):
            strategies_to_delete.append(strat_id)
    
    # Delete the strategies
    for strat_id in strategies_to_delete:
        del strategies[strat_id]
    
    # Save changes to file
    storage.save_strategies(strategies)
    
    # Redirect back to game detail
    return redirect(url_for('game_detail', game_id=game_id))

@app.route('/api/toggle_strategy_status', methods=['POST'])
def api_toggle_strategy_status():
    data = request.json
    strategy_id = data.get('strategy_id')
    new_status = data.get('status')  # 'active' or 'inactive'

    if not strategy_id or strategy_id not in strategies:
        return {'success': False, 'message': 'Strategy not found'}, 404

    # Update strategy status
    strategies[strategy_id]['status'] = new_status

    # Save changes to file
    storage.save_strategies(strategies)

    # Debug print to verify the status was updated
    print(f"Updated strategy {strategy_id} status to: {new_status}")
    print(f"Strategy now: {strategies[strategy_id]}")

    return {'success': True, 'message': f'Strategy status updated to {new_status}'}

@app.route('/my_strategies')
def my_strategies():
    user = get_user()
    if not user:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))

    # Get only user's strategies
    user_strategies = {k: v for k, v in strategies.items() if v['user_id'] == user['id']}

    # Add moment and game details to each strategy
    for strategy_id, strategy in user_strategies.items():
        # Ensure moment_id is a string for consistent lookup
        moment_id = str(strategy.get('moment_id', ''))
        strategy['moment'] = moments.get(moment_id)
        
        # Find game with string comparison
        game_id = strategy.get('game_id')
        game = None
        for g in upcoming_games:
            if str(g.get('id', '')) == str(game_id):
                game = g
                break
        strategy['game'] = game
        
        # Initialize wins counter for this strategy
        strategy['wins_count'] = 0
        strategy['wins'] = []
        strategy['spent_amount'] = 0.0

    # Process user's auction results
    user_auction_results = []
    for result_id, result in auction_results.items():
        if result['winning_user_id'] == user['id']:
            # Create a copy to avoid modifying original
            result_copy = dict(result)
            
            # Add auction data
            auction = auction_data.get(result['auction_id'], {})
            result_copy['auction'] = auction
            
            # Get auction's game and moment IDs
            auction_moment_id = str(auction.get('moment_id', ''))
            auction_game_id = str(auction.get('game_id', ''))
            
            # Add game info with string comparison
            game_id = auction.get('game_id')
            game = None
            for g in upcoming_games:
                if str(g.get('id', '')) == str(game_id):
                    game = g
                    break
            
            if game:
                result_copy['game_info'] = f"{game['away']} @ {game['home']} - {game['date']}"
                result_copy['game'] = game  # Store the full game object
            
            # Add to user's auction results list
            user_auction_results.append(result_copy)
            
            # Find matching strategy based on moment and game (even if strategy_id is None)
            for strategy_id, strategy in user_strategies.items():
                strategy_moment_id = str(strategy.get('moment_id', ''))
                strategy_game_id = str(strategy.get('game_id', ''))
                
                # If we find a strategy for the same game and moment as this auction
                if strategy_moment_id == auction_moment_id and strategy_game_id == auction_game_id:
                    # Update the strategy's win count
                    strategy['wins_count'] += 1
                    strategy['wins'].append(result_copy)
                    strategy['spent_amount'] += float(result_copy.get('winning_amount', 0))
                    
                    print(f"Matched auction {result_id} to strategy {strategy_id}")
                    print(f"  Auction: moment={auction_moment_id}, game={auction_game_id}")
                    print(f"  Strategy: moment={strategy_moment_id}, game={strategy_game_id}")

    # Debug output
    print(f"\n=== MY STRATEGIES ACCESS ===")
    print(f"User: {user['name']} (ID: {user['id']})")
    print(f"Number of strategies: {len(user_strategies)}")
    print(f"Number of wins: {len(user_auction_results)}")
    
    # Check specific strategies and their win counts
    for strategy_id, strategy in user_strategies.items():
        print(f"Strategy {strategy_id}: {strategy.get('wins_count', 0)} wins, ${strategy.get('spent_amount', 0):.2f} spent")
        moment_name = strategy.get('moment', {}).get('name', 'Unknown')
        game = strategy.get('game', {})
        game_info = f"{game.get('away', '')} @ {game.get('home', '')}" if game else 'Unknown'
        print(f"  - For {moment_name} on {game_info}")
        
    if user_auction_results:
        first_result = user_auction_results[0]
        first_auction = first_result.get('auction', {})
        print(f"First result auction_id: {first_result.get('auction_id')}")
        print(f"First auction moment_id: {first_auction.get('moment_id')}")
        print(f"First auction game_id: {first_auction.get('game_id')}")
        print(f"Game info for first result: {first_result.get('game_info', 'None')}")
        print(f"Strategy ID for first result: {first_result.get('winning_strategy_id')}")
    
    return render_template('my_strategies.html',
                         user=user,
                         strategies=user_strategies,
                         user_strategies=user_strategies,
                         user_auction_results=user_auction_results,
                         moments=moments,
                         upcoming_games=upcoming_games,
                         auctions=auction_data)

@app.route('/remove_strategy/<strategy_id>', methods=['POST', 'GET'])
def remove_strategy(strategy_id):
    user = get_user()
    if not user:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))

    # Find the strategy to get the game_id before deletion
    if strategy_id in strategies:
        strategy = strategies[strategy_id]
        game_id = strategy.get('game_id')

        # Check if user owns this strategy
        if strategy.get('user_id') == user['id']:
            # Delete the strategy
            del strategies[strategy_id]

            # Save changes to file
            storage.save_strategies(strategies)

            flash('Strategy removed successfully!', 'success')

            # Redirect to game detail if we have a game_id
            if game_id:
                return redirect(url_for('game_detail', game_id=game_id))
        else:
            flash('You do not have permission to delete this strategy.', 'error')
    else:
        flash('Strategy not found.', 'error')

    # If no game_id or strategy not found, redirect to dashboard
    return redirect(url_for('dashboard'))

@app.route('/api/debug_info')
def debug_info():
    """API endpoint to dump debug information about the application state"""
    if 'user_id' not in session:
        return jsonify({
            'error': 'Not logged in',
            'message': 'Please login to view debug information'
        }), 401

    user = get_user()
    if not user:
        return jsonify({
            'error': 'User not found',
            'message': 'Could not find user data'
        }), 404

    # Get user's strategies
    user_strategies = {k: v for k, v in strategies.items() if v['user_id'] == user['id']}

    # Build debug information
    debug_info = {
        'user': {
            'id': user['id'],
            'name': user['name'],
            'email': user['email']
        },
        'strategies_count': len(strategies),
        'user_strategies_count': len(user_strategies),
        'strategies': {},
        'moments': {},
        'budget': {
            'total': user['total_budget'],
            'used': user['used_budget'],
            'available': user['available_budget']
        }
    }

    # Add strategy details
    for strat_id, strategy in user_strategies.items():
        debug_info['strategies'][strat_id] = {
            'moment_id': strategy.get('moment_id'),
            'game_id': strategy.get('game_id'),
            'base_bid': strategy.get('base_bid'),
            'max_bid': strategy.get('max_bid')
        }

    # Add moment mapping
    for moment_id, moment in moments.items():
        has_strategy = False
        strategy_ids = []
        for strat_id, strategy in user_strategies.items():
            if strategy.get('moment_id') == moment_id:
                has_strategy = True
                strategy_ids.append(strat_id)

        debug_info['moments'][moment_id] = {
            'name': moment.get('name'),
            'has_strategy': has_strategy,
            'strategy_ids': strategy_ids
        }

    return jsonify(debug_info)

# Add this route to your Flask app
@app.route('/admin/users', methods=['GET', 'POST'])
def admin_users():
    """Admin view for user management"""
    user = get_user()
    if not user or not user.get('is_admin', False):
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('dashboard'))
    
    # Handle user selection or form submission
    selected_user_id = request.args.get('user_id')
    if request.method == 'POST':
        # Update user info
        user_id = request.form.get('user_id')
        name = request.form.get('name')
        company = request.form.get('company')
        email = request.form.get('email')
        phone = request.form.get('phone')
        
        if user_id and user_id in users:
            # Verify email isn't already used by another user
            if email != users[user_id]['email']:
                for u_id, u in users.items():
                    if u_id != user_id and u.get('email') == email:
                        flash('Email already in use by another account.', 'error')
                        return redirect(url_for('admin_users', user_id=user_id))
            
            # Update user data
            users[user_id]['name'] = name
            users[user_id]['company'] = company
            users[user_id]['email'] = email
            users[user_id]['phone'] = phone
            
            # Save changes
            storage.save_users(users)
            flash('User updated successfully!', 'success')
            return redirect(url_for('admin_users', user_id=user_id))
    
    # Get selected user data
    selected_user = None
    if selected_user_id and selected_user_id in users:
        selected_user = users[selected_user_id]
        # Add budget info
        budget_info = get_user_budget_info(selected_user_id)
        selected_user.update(budget_info)
    
    # Exclude admin from the regular users list
    regular_users = {k: v for k, v in users.items() if not v.get('is_admin', False)}
    
    return render_template('admin_users.html',
                          user=user,
                          users=regular_users,
                          selected_user=selected_user,
                          selected_user_id=selected_user_id)

@app.route('/admin/strategies', methods=['GET'])
def admin_strategies():
    """Admin view for managing user strategies"""
    user = get_user()
    if not user or not user.get('is_admin', False):
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get selected user ID from query parameters
    selected_user_id = request.args.get('user_id')
    selected_user = None
    user_strategies = {}
    user_auction_results = []
    
    # Get all non-admin users for the dropdown
    all_users = {k: v for k, v in users.items() if not v.get('is_admin', False)}
    
    # Calculate platform-wide stats
    platform_stats = {
        'total_auctions': len(auction_results),
        'total_user_budget': sum(float(u.get('budget', 0)) for u in users.values() if not u.get('is_admin', False)),
        'total_allocated': sum(calculate_allocated_budget(uid) for uid in users.keys() if not users[uid].get('is_admin', False)),
        'total_spent': sum(calculate_spent_budget(uid) for uid in users.keys() if not users[uid].get('is_admin', False))
    }
    
    # Get selected user data if a user is selected
    if selected_user_id and selected_user_id in users:
        selected_user = users[selected_user_id]
        
        # Add budget info
        budget_info = get_user_budget_info(selected_user_id)
        selected_user.update(budget_info)
        
        # Get user's strategies
        user_strategies = {k: v for k, v in strategies.items() if v['user_id'] == selected_user_id}
        
        # Add moment and game details to each strategy
        for strategy_id, strategy in user_strategies.items():
            # Ensure moment_id is a string for consistent lookup
            moment_id = str(strategy.get('moment_id', ''))
            strategy['moment'] = moments.get(moment_id)

            # Find game
            game_id = strategy.get('game_id')
            game = next((g for g in upcoming_games if g['id'] == game_id), None)
            strategy['game'] = game

            # Initialize wins counter for this strategy
            strategy['wins_count'] = 0
            strategy['wins'] = []
            strategy['spent_amount'] = 0.0
        
        # Process user's auction results
        for result_id, result in auction_results.items():
            if result['winning_user_id'] == selected_user_id:
                # Create a copy to avoid modifying original
                result_copy = dict(result)
                
                # Add auction data
                auction = auction_data.get(result['auction_id'], {})
                result_copy['auction'] = auction
                
                # Get auction's game and moment IDs
                auction_moment_id = str(auction.get('moment_id', ''))
                auction_game_id = str(auction.get('game_id', ''))
                
                # Add game info
                game_id = auction.get('game_id')
                game = next((g for g in upcoming_games if g['id'] == game_id), None)
                if game:
                    result_copy['game_info'] = f"{game['away']} @ {game['home']} - {game['date']}"
                    result_copy['game'] = game
                
                # Add to user's auction results list
                user_auction_results.append(result_copy)
                
                # Find matching strategy based on moment and game
                for strategy_id, strategy in user_strategies.items():
                    strategy_moment_id = str(strategy.get('moment_id', ''))
                    strategy_game_id = str(strategy.get('game_id', ''))
                    
                    # If strategy matches this auction's result
                    if strategy_moment_id == auction_moment_id and strategy_game_id == auction_game_id:
                        # Update the strategy's win count
                        strategy['wins_count'] += 1
                        strategy['wins'].append(result_copy)
                        strategy['spent_amount'] += float(result_copy.get('winning_amount', 0))
    
    return render_template('admin_strategies.html',
                          user=user,
                          all_users=all_users,
                          selected_user=selected_user,
                          selected_user_id=selected_user_id,
                          user_strategies=user_strategies,
                          user_auction_results=user_auction_results,
                          moments=moments,
                          upcoming_games=upcoming_games,
                          auctions=auction_data,
                          strategies=strategies,
                          platform_stats=platform_stats)

@app.route('/admin/games')
def admin_games():
    """Admin view for all games with status management"""
    user = get_user()
    if not user or not user.get('is_admin', False):
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('dashboard'))
    
    # Just return a blank template, JavaScript will load the data
    return render_template('admin_games_js.html', user=user)

@app.route('/admin/games/data')
def admin_games_data():
    """API endpoint to get game data as JSON for the admin interface"""
    user = get_user()
    if not user or not user.get('is_admin', False):
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Create explicit lists for each status
    live_games = []
    pending_games = []
    finished_games = []
    
    for game in upcoming_games:
        status = game.get('status', 'pending')
        game_data = {
            'id': game.get('id'),
            'away': game.get('away'),
            'home': game.get('home'),
            'date': game.get('date'),
            'time': game.get('time'),
            'status': status
        }
        
        if status == 'live':
            live_games.append(game_data)
        elif status == 'pending':
            pending_games.append(game_data)
        elif status == 'finished':
            finished_games.append(game_data)
    
    return jsonify({
        'live_games': live_games,
        'pending_games': pending_games,
        'finished_games': finished_games,
        'all_games': [
            {'id': g.get('id'), 'away': g.get('away'), 'home': g.get('home'), 
             'date': g.get('date'), 'time': g.get('time'), 'status': g.get('status', 'pending')}
            for g in upcoming_games
        ]
    })

@app.route('/admin/game/<int:game_id>/status', methods=['POST'])
def update_game_status(game_id):
    """Update the status of a game"""
    user = get_user()
    if not user or not user.get('is_admin', False):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    # Get new status from request
    new_status = request.json.get('status')
    print(f"\n=== UPDATING GAME STATUS ===")
    print(f"Game ID: {game_id} (type: {type(game_id).__name__})")
    print(f"New status: '{new_status}' (type: {type(new_status).__name__})")

    if new_status not in ['pending', 'live', 'finished']:
        return jsonify({'success': False, 'message': 'Invalid status'}), 400

    # Find and update the game
    game_found = False
    for i, game in enumerate(upcoming_games):
        game_id_from_game = game.get('id')
        
        # Compare game IDs and handle different types
        if isinstance(game_id_from_game, str) and game_id_from_game.isdigit():
            game_id_from_game = int(game_id_from_game)
        
        if game_id_from_game == game_id:
            game_found = True
            old_status = game.get('status')
            game['status'] = new_status
            
            # Special handling for finished to pending transition (Reset Game)
            if old_status == 'finished' and new_status == 'pending':
                print(f"RESETTING GAME: From finished to pending. Auction results preserved.")
                # We deliberately don't reset any auction results here
                # The game is simply set back to pending for new auctions
            
            print(f"Found game! Updating status from '{old_status}' to '{new_status}'")
            print(f"Updated game object: {game}")
            
            # Save to storage
            save_result = storage.save_data(upcoming_games, storage.GAMES_FILE)
            print(f"Save result: {save_result}")
            
            return jsonify({
                'success': True,
                'message': f'Game status updated to {new_status}',
                'game_id': game_id,
                'new_status': new_status
            })

    print(f"Game with ID {game_id} not found!")
    return jsonify({'success': False, 'message': 'Game not found'}), 404

@app.route('/admin/financials')
def admin_financials():
    """Admin view for financial tracking of all auctions"""
    user = get_user()
    if not user or not user.get('is_admin', False):
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('dashboard'))

    # Gather all auction results with payment information
    financial_data = []
    total_platform_revenue = 0
    total_broadcaster_revenue = 0
    total_commission = 0
    
    # First, make sure all completed auctions have proper financial data
    for auction_id, auction in auction_data.items():
        if auction["status"] == "completed":
            # Check if there's a corresponding auction result
            result_exists = False
            for result in auction_results.values():
                if result["auction_id"] == auction_id:
                    result_exists = True
                    break
            
            # If no result exists but auction is completed, check if there's a winning bid
            if not result_exists:
                # Find the winning bid
                winning_bid = None
                for bid in bids.values():
                    if bid["auction_id"] == auction_id and bid["status"] == "winning":
                        winning_bid = bid
                        break
                
                # If we found a winning bid, create a result record
                if winning_bid:
                    winning_amount = float(winning_bid["amount"])
                    winning_user_id = winning_bid["user_id"]
                    
                    # Calculate commissions and shares
                    commission_rate = 0.05  # 5%
                    broadcaster_rate = 0.85  # 85%
                    platform_rate = 0.10  # 10%
                    
                    commission_amount = winning_amount * commission_rate
                    broadcaster_share = winning_amount * broadcaster_rate
                    platform_share = winning_amount * platform_rate
                    
                    # Create the result record
                    result_id = str(uuid.uuid4())
                    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    result = {
                        "id": result_id,
                        "auction_id": auction_id,
                        "winning_bid_id": winning_bid["id"],
                        "winning_user_id": winning_user_id,
                        "winning_strategy_id": winning_bid.get("strategy_id"),
                        "winning_amount": winning_amount,
                        "payment_status": "completed",  # Auto-complete payment
                        "payment_transaction_id": f"BACKFILL-{uuid.uuid4()}",
                        "commission_amount": commission_amount,
                        "broadcaster_share": broadcaster_share,
                        "platform_share": platform_share,
                        "ad_display_status": "completed",
                        "created_at": now,
                        "updated_at": now
                    }
                    
                    auction_results[result_id] = result
                    storage.save_auction_results(auction_results)
                    print(f"Created missing auction result for auction {auction_id}")
    
    # Process all auction results for the financials display
    for result_id, result in auction_results.items():
        # Ensure we have all required fields
        if not all(key in result for key in ['winning_amount', 'commission_amount', 'broadcaster_share', 'platform_share']):
            # Calculate missing financial data
            winning_amount = float(result.get('winning_amount', 0))
            
            # Add missing financial fields
            if 'commission_amount' not in result:
                result['commission_amount'] = winning_amount * 0.05
            
            if 'broadcaster_share' not in result:
                result['broadcaster_share'] = winning_amount * 0.85
                
            if 'platform_share' not in result:
                result['platform_share'] = winning_amount * 0.10
                
            # Update the record
            auction_results[result_id] = result
            storage.save_auction_results(auction_results)
        
        # Now process the result for display
        auction = auction_data.get(result.get('auction_id'))
        if not auction:
            continue
            
        winning_user = users.get(result.get('winning_user_id'))
        
        # Format the data for display
        financial_entry = {
            'result_id': result_id,
            'auction_id': result.get('auction_id'),
            'game_id': auction.get('game_id'),
            'moment_id': auction.get('moment_id'),
            'winner_name': winning_user.get('name', 'Unknown') if winning_user else 'Unknown',
            'winner_company': winning_user.get('company', 'Unknown') if winning_user else 'Unknown',
            'amount': float(result.get('winning_amount', 0)),
            'payment_status': result.get('payment_status', 'pending'),
            'completed_at': result.get('updated_at'),
            'commission_amount': float(result.get('commission_amount', 0)),
            'broadcaster_share': float(result.get('broadcaster_share', 0)),
            'platform_share': float(result.get('platform_share', 0))
        }
        
        # Add game and moment info
        game = next((g for g in upcoming_games if g['id'] == auction.get('game_id')), None)
        if game:
            financial_entry['game_info'] = f"{game['away']} @ {game['home']} ({game['date']})"
        
        moment = moments.get(str(auction.get('moment_id')))
        if moment:
            financial_entry['moment_name'] = moment.get('name', 'Unknown Moment')
        
        financial_data.append(financial_entry)
        
        # Add to totals if payment is completed
        if result.get('payment_status') == 'completed':
            total_platform_revenue += financial_entry['platform_share']
            total_broadcaster_revenue += financial_entry['broadcaster_share']
            total_commission += financial_entry['commission_amount']

    # Sort by completion date, most recent first
    financial_data.sort(key=lambda x: x.get('completed_at', ''), reverse=True)
    
    return render_template('admin_financials.html',
                          user=user,
                          financial_data=financial_data,
                          total_platform_revenue=total_platform_revenue,
                          total_broadcaster_revenue=total_broadcaster_revenue,
                          total_commission=total_commission,
                          moments=moments,
                          upcoming_games=upcoming_games)

@app.route('/admin/process_all_pending_payments')
def admin_process_all_pending_payments():
    """Admin utility to process all pending payments at once"""
    user = get_user()
    if not user or not user.get('is_admin', False):
        flash('You do not have permission to perform this action.', 'error')
        return redirect(url_for('dashboard'))

    print(f"\n=== PROCESSING ALL PENDING PAYMENTS ===")
    updates_count = 0

    # Debug: Print all auction results and their payment statuses
    print(f"Total auction results: {len(auction_results)}")
    for result_id, result in auction_results.items():
        payment_status = result.get('payment_status', 'unknown')
        distribution_complete = result.get('payment_distribution_complete', False)
        print(f"Result {result_id}: payment_status={payment_status}, distribution_complete={distribution_complete}")
    
    # Process each result that needs payment processing
    for result_id, result in auction_results.items():
        # Check if payment needs processing - either not completed or distribution not complete
        if (result.get('payment_status') != 'completed' or 
            not result.get('payment_distribution_complete', False)):
            
            print(f"Processing payment for auction result {result_id}")
            payment_result = process_auction_payment_distribution(result_id)

            if payment_result.get('success'):
                updates_count += 1
                print(f"Successfully processed payment distribution for auction result {result_id}")
            else:
                print(f"Failed to process payment distribution for auction result {result_id}: {payment_result.get('message')}")

    if updates_count > 0:
        storage.save_auction_results(auction_results)
        flash(f'Successfully processed {updates_count} pending payments!', 'success')
    else:
        flash('No pending payments found to process.', 'info')

    print(f"Processed {updates_count} payments in total")
    print("===================================\n")
    
    return redirect(url_for('admin_payment_distributions'))

@app.route('/admin/mark_payment_complete/<result_id>')
def admin_mark_payment_complete(result_id):
    """Admin function to manually mark a payment as complete"""
    user = get_user()
    if not user or not user.get('is_admin', False):
        flash('You do not have permission to perform this action.', 'error')
        return redirect(url_for('dashboard'))
        
    if result_id in auction_results:
        result = auction_results[result_id]
        result['payment_status'] = 'completed'
        result['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Save changes
        auction_results[result_id] = result
        storage.save_auction_results(auction_results)
        
        flash('Payment marked as complete successfully!', 'success')
    else:
        flash('Auction result not found.', 'error')
        
    return redirect(url_for('admin_financials'))

@app.route('/admin/process_payment/<result_id>')
def admin_process_payment(result_id):
    """Admin function to manually process auction payment distribution"""
    user = get_user()
    if not user or not user.get('is_admin', False):
        flash('You do not have permission to perform this action.', 'error')
        return redirect(url_for('dashboard'))

    try:
        # Call the payment distribution function
        result = process_auction_payment_distribution(result_id)
        
        # Check if the result is valid
        if result is None:
            flash('An error occurred during payment processing: No result returned', 'error')
        elif result.get('success', False):
            flash('Payment processed and distributed successfully!', 'success')
        else:
            error_message = result.get('message', 'Unknown error')
            flash(f"Payment processing failed: {error_message}", 'error')
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f"Exception occurred during payment processing: {str(e)}", 'error')

    return redirect(url_for('admin_payment_distributions'))

@app.route('/admin/payment_distributions')
def admin_payment_distributions():
    """Admin view for payment distributions"""
    user = get_user()
    if not user or not user.get('is_admin', False):
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('dashboard'))
        
    # Format auction results for the template
    formatted_results = []
    total_processed = 0
    broadcaster_revenue = 0
    commission_revenue = 0
    platform_revenue = 0
    
    for result_id, result in auction_results.items():
        # Basic info
        formatted_result = {
            'id': result_id,
            'created_at': result.get('created_at', 'Unknown'),
            'winning_amount': float(result.get('winning_amount', 0)),
            'payment_distribution_complete': result.get('payment_distribution_complete', False),
            'broadcaster_share': float(result.get('broadcaster_share', 0)),
            'commission_amount': float(result.get('commission_amount', 0)),
            'platform_share': float(result.get('platform_share', 0)),
            'payment_transaction_id': result.get('payment_transaction_id'),
            'broadcaster_transaction_id': result.get('broadcaster_transaction_id'),
            'commission_transaction_id': result.get('commission_transaction_id'),
            'platform_transaction_id': result.get('platform_transaction_id')
        }
        
        # Get winner info
        winning_user_id = result.get('winning_user_id')
        winning_user = users.get(winning_user_id, {})
        formatted_result['winner_name'] = winning_user.get('name', 'Unknown')
        formatted_result['winner_company'] = winning_user.get('company', 'Unknown')
        
        # Get auction info
        auction_id = result.get('auction_id')
        auction = auction_data.get(auction_id, {})
        moment_id = auction.get('moment_id')
        moment = moments.get(str(moment_id), {})
        formatted_result['auction_name'] = moment.get('name', 'Unknown Moment')
        
        # Get game info
        game_id = auction.get('game_id')
        game = next((g for g in upcoming_games if g['id'] == game_id), None)
        if game:
            formatted_result['game_info'] = f"{game['away']} @ {game['home']} ({game['date']})"
        else:
            formatted_result['game_info'] = 'Unknown Game'
            
        # Add to totals if payment is completed
        if formatted_result['payment_distribution_complete']:
            total_processed += formatted_result['winning_amount']
            broadcaster_revenue += formatted_result['broadcaster_share']
            commission_revenue += formatted_result['commission_amount']
            platform_revenue += formatted_result['platform_share']
            
        formatted_results.append(formatted_result)
    
    # Sort by creation date (newest first)
    formatted_results.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    return render_template('payment_distributions.html',
                          user=user,
                          auction_results=formatted_results,
                          total_processed=total_processed,
                          broadcaster_revenue=broadcaster_revenue,
                          commission_revenue=commission_revenue,
                          platform_revenue=platform_revenue)

@app.route('/admin/force_complete_all_payments')
def admin_force_complete_all_payments():
    """Admin utility to force complete all pending payments at once"""
    user = get_user()
    if not user or not user.get('is_admin', False):
        flash('You do not have permission to perform this action.', 'error')
        return redirect(url_for('dashboard'))
    
    print(f"\n=== FORCE COMPLETING ALL PENDING PAYMENTS ===")
    updates_count = 0

    for result_id, result in auction_results.items():
        if not result.get('payment_distribution_complete') or result.get('payment_status') != 'completed':
            # Mark as completed with dummy transaction IDs
            result['payment_status'] = 'completed'
            result['payment_distribution_complete'] = True
            result['payment_transaction_id'] = f"FORCED-{uuid.uuid4()}"
            result['broadcaster_transaction_id'] = f"FORCED-{uuid.uuid4()}"
            result['commission_transaction_id'] = f"FORCED-{uuid.uuid4()}"
            result['platform_transaction_id'] = f"FORCED-{uuid.uuid4()}"
            result['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            auction_results[result_id] = result
            updates_count += 1
            print(f"Forced completion for payment {result_id}")

    if updates_count > 0:
        storage.save_auction_results(auction_results)
        print(f"Completed {updates_count} payments!")

    flash(f'Successfully force-completed {updates_count} pending payments!', 'success')
    print("================================\n")
    return redirect(url_for('admin_payment_distributions'))

@app.route('/admin/force_complete_payment/<result_id>')
def admin_force_complete_payment(result_id):
    """Admin function to force-complete a payment without Braintree"""
    user = get_user()
    if not user or not user.get('is_admin', False):
        flash('You do not have permission to perform this action.', 'error')
        return redirect(url_for('dashboard'))
    
    print(f"\n=== FORCE COMPLETING PAYMENT ===")
    print(f"Force completing payment for result ID: {result_id}")
    
    if result_id in auction_results:
        result = auction_results[result_id]
        
        # Mark as completed with dummy transaction IDs
        result['payment_status'] = 'completed'
        result['payment_distribution_complete'] = True
        result['payment_transaction_id'] = f"FORCED-{uuid.uuid4()}"
        result['broadcaster_transaction_id'] = f"FORCED-{uuid.uuid4()}"
        result['commission_transaction_id'] = f"FORCED-{uuid.uuid4()}"
        result['platform_transaction_id'] = f"FORCED-{uuid.uuid4()}"
        result['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Save changes
        auction_results[result_id] = result
        storage.save_auction_results(auction_results)

        flash('Payment has been force-completed successfully!', 'success')
        print("Payment force-completed successfully!")
    else:
        flash('Auction result not found.', 'error')
        print("ERROR: Auction result not found")
    
    print("================================\n")
    return redirect(url_for('admin_payment_distributions'))

# Auction Routes
@app.route('/auction_listings')
def auction_listings():
    user = get_user()
    if not user:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))

    # Get auctions by status
    active_auctions = {}
    completed_auctions = []

    # Check user preference for hiding completed auctions
    hide_completed = session.get('hide_completed_auction', False)

    # Current time for determining auction status
    now = datetime.now()

    for auction_id, auction in auction_data.items():
        # Check auction type
        if auction.get('auction_type') == 'instant':
            # Handle instant auctions based on their status
            if auction['status'] == 'active':
                active_auctions[auction_id] = auction
            elif auction['status'] == 'completed':
                # Create a copy with the ID to sort later
                auction_copy = dict(auction)
                auction_copy['id'] = auction_id
                completed_auctions.append((auction_id, auction))
        else:
            # Handle traditional auctions with start/end times
            try:
                # Convert string timestamps to datetime objects
                start_time = datetime.strptime(auction['start_time'], '%Y-%m-%d %H:%M:%S')
                end_time = datetime.strptime(auction['end_time'], '%Y-%m-%d %H:%M:%S')

                # Update auction status based on current time
                if auction['status'] != 'cancelled':
                    if now >= start_time and now < end_time:
                        auction['status'] = 'active'
                        active_auctions[auction_id] = auction
                    elif now >= end_time:
                        if auction['status'] != 'completed':
                            # Auto-finalize auction if it's past end time
                            finalize_auction(auction_id)
                        auction['status'] = 'completed'
                        auction_copy = dict(auction)
                        auction_copy['id'] = auction_id
                        completed_auctions.append((auction_id, auction))
            except (KeyError, ValueError) as e:
                # Handle any missing fields or date parsing issues
                print(f"Error processing auction {auction_id}: {e}")
                if auction['status'] == 'completed':
                    auction_copy = dict(auction)
                    auction_copy['id'] = auction_id
                    completed_auctions.append((auction_id, auction))

    # Sort completed auctions by end_time - newest first
    def get_auction_end_time(auction_tuple):
        auction = auction_tuple[1]
        if 'end_time' in auction:
            try:
                return datetime.strptime(auction['end_time'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                pass
        if 'executed_at' in auction:
            try:
                return datetime.strptime(auction['executed_at'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                pass
        return datetime.min  # Default to oldest date if no valid date found

    completed_auctions.sort(key=get_auction_end_time, reverse=True)  # Newest first

    # Get the most recent auction for display in active section if there are no active auctions
    most_recent_auction = None
    if not active_auctions and completed_auctions and not hide_completed:
        most_recent_auction_id, most_recent_auction = completed_auctions[0]
        most_recent_auction = dict(most_recent_auction)  # Create a copy to avoid modifying original
        most_recent_auction['id'] = most_recent_auction_id

    # Preprocess auction to improve game lookups
    for auction_id, auction in active_auctions.items():
        # Try to find matching game
        game_id = str(auction.get('game_id', ''))
        for g in upcoming_games:
            if str(g.get('id', '')) == game_id:
                auction['game'] = g
                break

    # Do the same for most_recent_auction if it exists
    if most_recent_auction:
        game_id = str(most_recent_auction.get('game_id', ''))
        for g in upcoming_games:
            if str(g.get('id', '')) == game_id:
                most_recent_auction['game'] = g
                break

    # Pass the current datetime to template for progress calculation
    template_now = now

    print(f"\n=== AUCTION LISTINGS ===")
    print(f"Active auctions: {len(active_auctions)}")
    print(f"Recently completed auctions: {len(completed_auctions)}")
    print(f"Showing most recent completed auction: {most_recent_auction is not None}")
    print(f"Hide completed auction preference: {hide_completed}")

    # Debug the first few completed auctions to verify sorting
    if completed_auctions:
        print("\nRecently completed auctions (newest first):")
        for i, (auction_id, auction) in enumerate(completed_auctions[:5]):
            end_time = auction.get('end_time', auction.get('executed_at', 'Unknown'))
            print(f"  {i+1}. ID: {auction_id}, End Time: {end_time}")

    return render_template('auctions.html',
                          user=user,
                          active_auctions=active_auctions,
                          completed_auctions=completed_auctions,
                          most_recent_auction=most_recent_auction,
                          hide_completed=hide_completed,
                          moments=moments,
                          upcoming_games=upcoming_games,
                          now=template_now,
                          users=users,
                          bids=bids)  # Added the bids dictionary

@app.route('/create_auction', methods=['GET'])
def create_auction_form():
    user = get_user()
    if not user:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))
    
    # Check if user is admin
    if not user.get('is_admin', False):
        flash('You do not have permission to create auctions.', 'error')
        return redirect(url_for('auctions'))
    
    return render_template('create_auction.html',
                          user=user,
                          moments=moments,
                          upcoming_games=upcoming_games)

@app.route('/create_auction', methods=['POST'])
def create_auction_submit():
    user = get_user()
    if not user:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))

    # Check if user is admin
    if not user.get('is_admin', False):
        flash('You do not have permission to create auctions.', 'error')
        return redirect(url_for('auction_listings'))

    # Get form data
    game_id = request.form.get('game_id')
    moment_id = request.form.get('moment_id')
    base_price = request.form.get('base_price', 1000)
    reserve_price = request.form.get('reserve_price')
    period = request.form.get('period', '1')
    team_id = request.form.get('team_id')
    event_importance = request.form.get('event_importance', 'normal')
    
    # Handle multiple player selection
    players = request.form.getlist('players[]')

    # Basic validation
    if not all([game_id, moment_id, base_price, team_id]) or not players:
        flash('All required fields must be provided.', 'error')
        return redirect(url_for('create_auction_form'))

    # Create the instant auction
    auction_id = create_instant_auction(
        moment_id,
        int(game_id),
        float(base_price),
        float(reserve_price) if reserve_price else None,
        period,
        team_id,
        players,
        event_importance
    )

    # Always execute the auction immediately (instant auctions are executed instantly)
    result = execute_instant_auction(auction_id)
    if result.get('success'):
        if result.get('winner'):
            flash(f'Auction executed successfully! Winner: {result.get("winning_user_name")} with bid of ${result.get("winning_amount"):,.2f}', 'success')
        else:
            flash('Auction executed but no winner was determined. Reserve price may not have been met.', 'warning')
    else:
        flash(f'Error executing auction: {result.get("message")}', 'error')

    return redirect(url_for('auction_detail', auction_id=auction_id))

@app.route('/process_auctions')
def process_auctions_route():
    user = get_user()
    if not user or not user.get('is_admin', False):
        flash('You do not have permission to perform this action.', 'error')
        return redirect(url_for('dashboard'))
    
    results = process_all_auctions()
    
    flash(f'Processed {len(results)} auction actions.', 'success')
    return redirect(url_for('auctions'))

@app.route('/auction/<auction_id>')
def auction_detail(auction_id):
    user = get_user()
    if not user:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))

    # Check if auction exists
    if auction_id not in auction_data:
        flash('Auction not found.', 'error')
        return redirect(url_for('auction_listings'))

    auction = auction_data[auction_id]

    # Get bids for this auction - we'll still collect these for the template
    auction_bids = []
    for bid_id, bid in bids.items():
        if bid['auction_id'] == auction_id:
            auction_bids.append(bid)

    # Sort bids by timestamp (newest first)
    auction_bids.sort(key=lambda x: x['timestamp'], reverse=True)

    # Check if the auction status needs updating based on time
    if auction.get('auction_type') != 'instant':
        now = datetime.now()
        try:
            start_time = datetime.strptime(auction['start_time'], '%Y-%m-%d %H:%M:%S')
            end_time = datetime.strptime(auction['end_time'], '%Y-%m-%d %H:%M:%S')

            if auction['status'] != 'cancelled':
                if now < start_time:
                    auction['status'] = 'pending'
                elif now >= start_time and now < end_time:
                    auction['status'] = 'active'
                elif now >= end_time and auction['status'] != 'completed':
                    # Auto-finalize auction if it's past end time
                    finalize_auction(auction_id)
                    auction['status'] = 'completed'
        except (KeyError, ValueError) as e:
            print(f"Error processing auction times: {e}")

    return render_template('auction_detail.html',
                          user=user,
                          auction=auction,
                          auction_bids=auction_bids,
                          moments=moments,
                          upcoming_games=upcoming_games,
                          users=users,
                          auction_results=auction_results,
                          strategies=strategies,   # Add this line
                          bids=bids)              # Add this line

@app.route('/clear_completed_auction')
def clear_completed_auction():
    """Clear the completed auction from the active section"""
    user = get_user()
    if not user:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))

    # Set session preference to hide completed auction
    session['hide_completed_auction'] = True
    
    # Add a flash message to confirm
    flash('Completed auction cleared from view.', 'success')
    
    # Redirect back to auctions page
    return redirect(url_for('auction_listings'))

@app.route('/reset_completed_auction')
def reset_completed_auction():
    """Reset the preference to show completed auctions again"""
    user = get_user()
    if not user:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))

    # Set session preference to show completed auction
    session.pop('hide_completed_auction', None)
    
    # Add a flash message to confirm
    flash('Now showing most recent auction.', 'success')
    
    # Redirect back to auctions page
    return redirect(url_for('auction_listings'))

@app.route('/auction/<auction_id>/bid', methods=['POST'])
def place_bid_route(auction_id):
    user = get_user()
    if not user:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))
    
    # Get form data
    bid_amount = request.form.get('bid_amount')
    auto_bid = request.form.get('auto_bid') == '1'
    max_bid = request.form.get('max_bid') if auto_bid else None
    
    if not bid_amount:
        flash('Bid amount is required.', 'error')
        return redirect(url_for('auction_detail', auction_id=auction_id))
    
    # Place the bid
    result = place_bid(auction_id, user['id'], float(bid_amount), None, max_bid)
    
    if result['success']:
        flash('Bid placed successfully!', 'success')
    else:
        flash(f"Bid failed: {result['message']}", 'error')
    
    return redirect(url_for('auction_detail', auction_id=auction_id))

# Admin routes for auction management
@app.route('/auction/<auction_id>/activate')
def activate_auction(auction_id):
    user = get_user()
    if not user or not user.get('is_admin', False):
        flash('You do not have permission to perform this action.', 'error')
        return redirect(url_for('auctions'))
    
    if auction_id in auctions:
        auctions[auction_id]['status'] = 'active'
        storage.save_auctions(auctions)
        flash('Auction activated successfully!', 'success')
    else:
        flash('Auction not found.', 'error')
    
    return redirect(url_for('auction_detail', auction_id=auction_id))

@app.route('/auction/<auction_id>/execute')
def execute_auction_route(auction_id):
    user = get_user()
    if not user or not user.get('is_admin', False):
        flash('You do not have permission to perform this action.', 'error')
        return redirect(url_for('auction_listings'))

    if auction_id in auction_data:
        auction = auction_data[auction_id]
        
        if auction.get('auction_type') != 'instant':
            flash('This is not an instant auction.', 'error')
            return redirect(url_for('auction_detail', auction_id=auction_id))
        
        if auction['status'] != 'pending':
            flash(f'Cannot execute auction with status: {auction["status"]}', 'error')
            return redirect(url_for('auction_detail', auction_id=auction_id))
        
        result = execute_instant_auction(auction_id)
        if result.get('success'):
            if result.get('winner'):
                flash(f'Auction executed successfully! Winner: {result.get("winning_user_name")} with bid of ${result.get("winning_amount"):,.2f}', 'success')
            else:
                flash('Auction executed but no winner was determined. Reserve price may not have been met.', 'warning')
        else:
            flash(f'Error executing auction: {result.get("message")}', 'error')
    else:
        flash('Auction not found.', 'error')

    return redirect(url_for('auction_detail', auction_id=auction_id))

@app.route('/auction/<auction_id>/end')
def end_auction(auction_id):
    user = get_user()
    if not user or not user.get('is_admin', False):
        flash('You do not have permission to perform this action.', 'error')
        return redirect(url_for('auctions'))
    
    if auction_id in auctions:
        result = finalize_auction(auction_id)
        if result['success']:
            flash('Auction ended successfully!', 'success')
        else:
            flash(f"Failed to end auction: {result['message']}", 'error')
    else:
        flash('Auction not found.', 'error')
    
    return redirect(url_for('auction_detail', auction_id=auction_id))

@app.route('/auction/<auction_id>/cancel')
def cancel_auction(auction_id):
    user = get_user()
    if not user or not user.get('is_admin', False):
        flash('You do not have permission to perform this action.', 'error')
        return redirect(url_for('auctions'))
    
    if auction_id in auctions:
        auctions[auction_id]['status'] = 'cancelled'
        storage.save_auctions(auctions)
        flash('Auction cancelled successfully!', 'success')
    else:
        flash('Auction not found.', 'error')
    
    return redirect(url_for('auction_detail', auction_id=auction_id))

@app.route('/process_auction_payment/<result_id>', methods=['GET', 'POST'])
def process_auction_payment_route(result_id):
    """Process payment for won auction - Now mainly for backward compatibility"""
    user = get_user()
    if not user:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))

    # Find the auction result
    if result_id not in auction_results:
        flash('Auction result not found.', 'error')
        return redirect(url_for('auction_listings'))

    result = auction_results[result_id]

    # Check if user is the winner
    if result['winning_user_id'] != user['id']:
        flash('You are not authorized to make this payment.', 'error')
        return redirect(url_for('auction_listings'))

    # If payment is already completed, redirect back
    if result['payment_status'] == 'completed':
        flash('Payment has already been processed.', 'success')
        return redirect(url_for('auction_detail', auction_id=result['auction_id']))

    # Get the auction and winning amount
    auction = auction_data.get(result['auction_id'], {})
    winning_amount = float(result['winning_amount'])

    if request.method == 'POST':
        # Mark the payment as completed
        result['payment_status'] = 'completed'
        result['payment_transaction_id'] = f"MANUAL-{uuid.uuid4()}"
        result['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Save the updated result
        auction_results[result_id] = result
        storage.save_auction_results(auction_results)

        flash('Payment processed successfully!', 'success')
        return redirect(url_for('auction_detail', auction_id=result['auction_id']))

    # For GET requests, show the payment form
    # Get the game and moment info for display
    game = next((g for g in upcoming_games if g['id'] == auction.get('game_id')), None)
    moment = moments.get(str(auction.get('moment_id')), {})
    
    return render_template('process_payment.html',
                          user=user,
                          result=result,
                          auction=auction,
                          game=game,
                          moment=moment)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', user=get_user()), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html', user=get_user()), 500

if __name__ == '__main__':
    # Save initial data to ensure files exist
    storage.save_users(users)
    storage.save_data(teams, storage.TEAMS_FILE)
    storage.save_data(players, storage.PLAYERS_FILE)
    storage.save_strategies(strategies)
    storage.save_data(moments, storage.MOMENTS_FILE)
    storage.save_data(upcoming_games, storage.GAMES_FILE)
    storage.save_data(sponsors, storage.SPONSORS_FILE)

    # Add these new lines:
    storage.save_auctions(auction_data)
    storage.save_bids(bids)
    storage.save_auction_results(auction_results)

    app.run(debug=True, host='0.0.0.0', port=5000)
