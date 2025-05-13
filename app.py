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

# Budget calculation helper functions - UPDATED

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
    """Process all pending payments to completed status"""
    updates_count = 0
    
    for result_id, result in auction_results.items():
        if result.get('payment_status') == 'pending':
            result['payment_status'] = 'completed'
            result['payment_transaction_id'] = f"BACKFILL-{uuid.uuid4()}"
            result['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            auction_results[result_id] = result
            updates_count += 1
    
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
    winning_amount = winning_bid["amount"]
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

    # CHANGE: Set payment status to completed by default
    result = {
        "id": result_id,
        "auction_id": auction_id,
        "winning_bid_id": winning_bid_id,
        "winning_user_id": winning_user_id,
        "winning_strategy_id": winning_bid.get("strategy_id"),  # Store strategy ID if available
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

    # Update auction status
    auction["status"] = "completed"
    auction_data[auction_id] = auction

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
        "winning_amount": winning_amount
    }

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
            'budget': 0  # Changed from 100000 to 0
        }

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
    session.pop('user_id', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    user = get_user()
    if not user:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))

    # Debug print for budget
    print(f"\n=== DASHBOARD ACCESS ===")
    print(f"User: {user['name']} (ID: {user['id']})")
    print(f"Total Budget: ${user['total_budget']:,.2f}")
    print(f"Used Budget: ${user['used_budget']:,.2f}")
    print(f"Available Budget: ${user['available_budget']:,.2f}")

    # Get user's strategies to determine which moments have strategies
    user_strategies = {k: v for k, v in strategies.items() if v['user_id'] == user['id']}

    # Debug prints
    print(f"Number of total strategies: {len(strategies)}")
    print(f"Number of user strategies: {len(user_strategies)}")

    if user_strategies:
        print("User strategies:")
        for strat_id, strategy in user_strategies.items():
            moment_name = moments.get(strategy.get('moment_id', 0), {}).get('name', 'Unknown')
            print(f"  {strat_id}: Game {strategy.get('game_id')}, Moment: {moment_name} (ID: {strategy.get('moment_id')})")
    else:
        print("User has no strategies")
    print(f"===========================\n")

    return render_template('dashboard.html', user=user, moments=moments,
                           upcoming_games=upcoming_games, user_strategies=user_strategies)

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

    # Check if there's an existing strategy for this moment and user
    existing_strategy = None
    for strat_id, strategy in strategies.items():
        # Convert moment_id to string for comparison
        strategy_moment_id = str(strategy.get('moment_id', ''))
        if strategy_moment_id == moment_id and strategy.get('user_id') == user['id']:
            existing_strategy = dict(strategy)  # Create a copy
            existing_strategy['id'] = strat_id
            break

    if request.method == 'POST':
        # Get form data
        game_id = request.form.get('game_id')
        base_bid = request.form.get('base_bid')
        bid_increment = request.form.get('bid_increment')
        max_bid = request.form.get('max_bid')
        team_focus = request.form.get('team_focus')
        player_focus = request.form.get('player_focus')
        period_restrictions = request.form.get('period_restrictions')
        ad_content = request.form.get('ad_content')
        specific_scenario = request.form.get('specific_scenario')

        # Validate required fields
        if not all([game_id, base_bid, max_bid]):
            flash('All required fields must be filled out.', 'error')
            return redirect(url_for('setup_strategy', moment_id=moment_id, game_id=selected_game_id))

        try:
            # Convert to integers
            game_id = int(game_id)
            base_bid = int(base_bid)
            bid_increment = int(bid_increment) if bid_increment else 500
            max_bid = int(max_bid)
        except ValueError:
            flash('Invalid numeric values.', 'error')
            return redirect(url_for('setup_strategy', moment_id=moment_id, game_id=selected_game_id))

        # Check if user has sufficient available budget for max_bid
        # Now we check available budget (total - spent), not allocated budget
        if max_bid > user['available_budget']:
            flash(f'Insufficient available budget. You have ${user["available_budget"]:,.2f} available. This does not include money allocated to other strategies.', 'error')
            return redirect(url_for('setup_strategy', moment_id=moment_id, game_id=selected_game_id))

        # Generate a unique ID for the new strategy if it doesn't exist
        if existing_strategy:
            strategy_id = existing_strategy['id']
        else:
            strategy_id = str(uuid.uuid4())

        # Create or update strategy
        new_strategy = {
            'moment_id': moment_id,  # Store as string to match dictionary keys
            'game_id': game_id,
            'user_id': user['id'],
            'base_bid': base_bid,
            'bid_increment': bid_increment,
            'max_bid': max_bid,
            'team_focus': team_focus or 'both',
            'player_focus': player_focus,
            'period_restrictions': period_restrictions,
            'ad_content': ad_content,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'active'  # Default to active
        }

        # Add specific scenario for overtime/shootout goals
        if processed_moment['name'] == 'Overtime Goal/Shootout' and specific_scenario:
            new_strategy['specific_scenario'] = specific_scenario

        # Add to strategies dictionary (NO BUDGET DEDUCTION HERE)
        strategies[strategy_id] = new_strategy

        # Save changes to file
        storage.save_strategies(strategies)

        flash(f"Bidding strategy {'updated' if existing_strategy else 'created'} successfully! Money will only be spent when you win auctions.", 'success')

        # Redirect back to the game detail page if we have a game_id
        if game_id:
            return redirect(url_for('game_detail', game_id=game_id))
        else:
            return redirect(url_for('dashboard'))

    # Pass budget info to template
    return render_template('setup_strategy.html',
                          user=user,
                          moment=processed_moment,
                          moments=moments,
                          upcoming_games=upcoming_games,
                          existing_strategy=existing_strategy,
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
    for strategy in user_strategies.values():
        strategy['moment'] = moments.get(strategy['moment_id'])
        strategy['game'] = next((g for g in upcoming_games if g['id'] == strategy['game_id']), None)

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
    print(f"\n=== MY STRATEGIES ACCESS ===")
    print(f"User: {user['name']} (ID: {user['id']})")
    print(f"Number of strategies: {len(user_strategies)}")
    print(f"Number of wins: {len(user_auction_results)}")
    for strat_id, strategy in user_strategies.items():
        moment_name = strategy.get('moment', {}).get('name', 'Unknown Moment')
        game_away = strategy.get('game', {}).get('away', 'Unknown')
        game_home = strategy.get('game', {}).get('home', 'Unknown')
        print(f"  Strategy {strat_id}: {moment_name} for {game_away} @ {game_home}")
    print(f"===========================\n")

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

@app.route('/simulation')
def simulation():
    user = get_user()
    if not user:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))

    # Get user's strategies
    user_strategies = {k: v for k, v in strategies.items() if v['user_id'] == user['id']}

    return render_template('simulation.html', user=user, sponsors=sponsors, moments=moments, user_strategies=user_strategies)

@app.route('/api/simulate_auction', methods=['POST'])
def simulate_auction():
    data = request.json
    moment_id = data.get('moment_id')

    # Simulate an auction with the sponsors
    results = []
    for sponsor in sponsors:
        # Generate a random bid based on the sponsor's budget
        bid = round(random.uniform(1000, 10000), 2)
        results.append({
            'sponsor_id': sponsor['id'],
            'sponsor_name': sponsor['name'],
            'bid': bid
        })

    # Sort by bid (highest first)
    results.sort(key=lambda x: x['bid'], reverse=True)

    # Add a winning flag to the highest bidder
    if results:
        results[0]['winner'] = True

    return {'results': results}

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
    
    updates_count = process_all_pending_payments()
    
    if updates_count > 0:
        flash(f'Successfully processed {updates_count} pending payments!', 'success')
    else:
        flash('No pending payments found to process.', 'info')
    
    return redirect(url_for('admin_financials'))

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

# Auction Routes
@app.route('/auctions')
def auction_listings():
    user = get_user()
    if not user:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))

    # Get auctions by status
    active_auctions = {}
    upcoming_auctions = {}
    completed_auctions = {}

    # Current time for determining auction status
    now = datetime.now()

    for auction_id, auction in auction_data.items():
        # Check auction type
        if auction.get('auction_type') == 'instant':
            # Handle instant auctions based on their status
            if auction['status'] == 'pending':
                upcoming_auctions[auction_id] = auction
            elif auction['status'] == 'active':
                active_auctions[auction_id] = auction
            else:  # 'completed', 'cancelled', etc.
                completed_auctions[auction_id] = auction
        else:
            # Handle traditional auctions with start/end times
            try:
                # Convert string timestamps to datetime objects
                start_time = datetime.strptime(auction['start_time'], '%Y-%m-%d %H:%M:%S')
                end_time = datetime.strptime(auction['end_time'], '%Y-%m-%d %H:%M:%S')
                
                # Update auction status based on current time
                if auction['status'] != 'cancelled':
                    if now < start_time:
                        auction['status'] = 'pending'
                        upcoming_auctions[auction_id] = auction
                    elif now >= start_time and now < end_time:
                        auction['status'] = 'active'
                        active_auctions[auction_id] = auction
                    else:
                        if auction['status'] != 'completed':
                            # Auto-finalize any auction that's past end time but not marked completed
                            finalize_auction(auction_id)
                        auction['status'] = 'completed'
                        completed_auctions[auction_id] = auction
            except (KeyError, ValueError) as e:
                # Handle any missing fields or date parsing issues
                print(f"Error processing auction {auction_id}: {e}")
                if auction['status'] == 'completed' or auction['status'] == 'cancelled':
                    completed_auctions[auction_id] = auction
                else:
                    # Default to upcoming if status can't be determined
                    upcoming_auctions[auction_id] = auction

    # Pass the current datetime to template for progress calculation
    template_now = now

    return render_template('auctions.html',
                          user=user,
                          active_auctions=active_auctions,
                          upcoming_auctions=upcoming_auctions,
                          completed_auctions=completed_auctions,
                          moments=moments,
                          upcoming_games=upcoming_games,
                          now=template_now,
                          users=users)

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
    execute_immediately = 'execute_immediately' in request.form
    
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

    # Execute the auction immediately if requested
    if execute_immediately:
        result = execute_instant_auction(auction_id)
        if result.get('success'):
            if result.get('winner'):
                flash(f'Auction executed successfully! Winner: {result.get("winning_user_name")} with bid of ${result.get("winning_amount"):,.2f}', 'success')
            else:
                flash('Auction executed but no winner was determined. Reserve price may not have been met.', 'warning')
        else:
            flash(f'Error executing auction: {result.get("message")}', 'error')
    else:
        flash('Instant auction created successfully! It can be executed from the auction details page.', 'success')

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
