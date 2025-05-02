from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import random
import uuid
from datetime import datetime, timedelta
import os
import json
import storage  # Import the storage module

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev_secret_key_change_in_production')

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

# Budget calculation helper functions
def calculate_used_budget(user_id):
    """Calculate the total amount of budget used in all active strategies"""
    total_used = 0
    for strategy in strategies.values():
        if strategy['user_id'] == user_id:
            total_used += float(strategy.get('max_bid', 0))
    return total_used

def calculate_available_budget(user_id):
    """Calculate the available budget for a user"""
    user = users.get(user_id)
    if not user:
        return 0

    # Get the total budget from the user object
    total_budget = float(user.get('budget', 0))

    # Calculate used budget
    used_budget = calculate_used_budget(user_id)

    # Return the difference
    return max(0, total_budget - used_budget)

def debug_print_budget(user_id):
    """Print budget information for debugging"""
    user = users.get(user_id)
    if not user:
        print("User not found")
        return

    total_budget = float(user.get('budget', 0))

    print("\n=== BUDGET INFORMATION ===")
    print(f"User: {user.get('name')} (ID: {user_id})")
    print(f"Total Budget: ${total_budget:,.2f}")

    # Calculate used budget
    used_budget = 0
    print("\nActive strategies:")
    for strat_id, strategy in strategies.items():
        if strategy['user_id'] == user_id:
            max_bid = float(strategy.get('max_bid', 0))
            used_budget += max_bid
            moment_id = strategy.get('moment_id')
            moment_name = "Unknown"
            if moment_id in moments:
                moment_name = moments[moment_id]['name']
            print(f"  Strategy {strat_id}: {moment_name} - ${max_bid:,.2f}")

    print(f"\nTotal Used Budget: ${used_budget:,.2f}")
    print(f"Available Budget: ${max(0, total_budget - used_budget):,.2f}")
    print("=========================\n")

# Helper functions
def get_user():
    if 'user_id' in session:
        user_id = session['user_id']
        print(f"Getting user with ID: {user_id}")
        print(f"Available users: {list(users.keys())}")
        user = users.get(user_id)
        if user:
            # Add budget information for templates
            user['total_budget'] = float(user.get('budget', 0))
            user['used_budget'] = calculate_used_budget(user_id)
            user['available_budget'] = calculate_available_budget(user_id)
            return user
        else:
            print(f"User ID {user_id} not found in users dictionary")
    else:
        print("No user_id in session")
    return None

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

        # Create new user
        user_id = str(uuid.uuid4())
        users[user_id] = {
            'id': user_id,
            'name': name,
            'company': company,
            'email': email,
            'password': password,  # For demo, store plaintext
            'budget': 100000  # Default budget
        }

        # Save users to storage
        storage.save_users(users)

        # Debug print
        print(f"Created new user: {users[user_id]}")

        session['user_id'] = user_id
        flash('Registration successful!', 'success')
        return redirect(url_for('dashboard'))

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

    # Debug prints
    print(f"\n=== PROFILE ACCESS ===")
    print(f"User: {user['name']} (ID: {user['id']})")
    print(f"Total Budget: ${user['total_budget']:,.2f}")
    print(f"Used Budget: ${user['used_budget']:,.2f}")
    print(f"Available Budget: ${user['available_budget']:,.2f}")
    print(f"===========================\n")

    return render_template('profile.html',
                          user=user,
                          user_strategies=user_strategies,
                          upcoming_games=upcoming_games,
                          moments=moments)

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
        storage.save_users(users)

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
                          debug_data=debug_data)

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
    
    print(f"Raw moment_id from URL: {moment_id_raw}")
    print(f"Cleaned moment_id: {moment_id}")
    print(f"Available moment keys: {list(moments.keys())}")

    # Get the moment data - try using string key
    moment = moments.get(moment_id)
    print(f"Lookup result: {moment}")
    
    if not moment:
        print(f"Moment with ID {moment_id} not found in moments dictionary")
        flash(f'Moment not found. Please select a valid moment.', 'error')
        return redirect(url_for('dashboard'))
    
    # Create a new moment dictionary with id explicitly set
    processed_moment = dict(moment)  # Create a copy to avoid modifying the original
    processed_moment['id'] = moment_id  # Make sure the id field exists
    
    print(f"Processed moment for template: {processed_moment}")
    
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
            print(f"Found existing strategy: {strat_id}")
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
        
        # Add to strategies dictionary
        strategies[strategy_id] = new_strategy
        
        # Save changes to file
        storage.save_strategies(strategies)
        
        # Debug print
        print(f"{'Updated' if existing_strategy else 'Created new'} strategy: (ID: {strategy_id})")
        print(f"Strategy details: {new_strategy}")
        
        flash(f"Bidding strategy {'updated' if existing_strategy else 'created'} successfully!", 'success')
        
        # Redirect back to the game detail page if we have a game_id
        if game_id:
            return redirect(url_for('game_detail', game_id=game_id))
        else:
            return redirect(url_for('dashboard'))

    # Add debug prints right before returning the template
    print("==== TEMPLATE VARIABLES DEBUG ====")
    print(f"moment: {processed_moment}")
    print(f"moment type: {type(processed_moment)}")
    print(f"moment id: {processed_moment.get('id')}")
    print(f"moment id type: {type(processed_moment.get('id'))}")
    print(f"moment name: {processed_moment.get('name')}")
    print("=================================")
    
    # Return the template with our processed moment
    return render_template('setup_strategy.html', 
                          user=user, 
                          moment=processed_moment,  # Use the processed copy
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

    # Debug prints
    print(f"\n=== MY STRATEGIES ACCESS ===")
    print(f"User: {user['name']} (ID: {user['id']})")
    print(f"Number of strategies: {len(user_strategies)}")
    for strat_id, strategy in user_strategies.items():
        moment_name = strategy.get('moment', {}).get('name', 'Unknown Moment')
        game_away = strategy.get('game', {}).get('away', 'Unknown')
        game_home = strategy.get('game', {}).get('home', 'Unknown')
        print(f"  Strategy {strat_id}: {moment_name} for {game_away} @ {game_home}")
    print(f"===========================\n")

    return render_template('my_strategies.html', user=user, strategies=user_strategies)

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

# Removed duplicate toggle_strategy_status route

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
    
    app.run(debug=True, host='0.0.0.0', port=5000)
