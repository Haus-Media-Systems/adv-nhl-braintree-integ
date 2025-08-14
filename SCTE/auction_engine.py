"""
SCTE-optimized auction engine
Handles the core auction logic optimized for real-time SCTE triggers
"""

import uuid
import json
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

def find_applicable_strategies(auction: Dict) -> List[Dict]:
    """Find strategies that apply to this auction"""
    from app import strategies, teams, users
    
    applicable_strategies = []
    moment_id = auction.get('moment_id')
    game_id = auction.get('game_id')
    period = auction.get('period')
    team_id = auction.get('team_id')
    event_importance = auction.get('event_importance', 'normal')
    players = auction.get('players', [])
    
    for strategy_id, strategy in strategies.items():
        if not strategy.get('enabled', True):
            continue
            
        user_id = strategy.get('user_id')
        if user_id not in users:
            continue
            
        user = users[user_id]
        if user.get('budget', 0) <= 0:
            continue
        
        # Check strategy criteria
        matches = True
        
        # Team matching
        strategy_teams = strategy.get('teams', [])
        if strategy_teams and team_id and team_id not in strategy_teams and 'all' not in strategy_teams:
            matches = False
        
        # Period matching
        strategy_periods = strategy.get('periods', [])
        if strategy_periods and period not in strategy_periods and 'all' not in strategy_periods:
            matches = False
        
        # Event importance matching
        strategy_importance = strategy.get('event_importance', [])
        if strategy_importance and event_importance not in strategy_importance and 'all' not in strategy_importance:
            matches = False
        
        # Player matching
        strategy_players = strategy.get('players', [])
        if strategy_players and players:
            player_match = any(player in strategy_players for player in players)
            if not player_match and 'all' not in strategy_players:
                matches = False
        
        # Budget check
        max_bid = strategy.get('max_bid', 0)
        if max_bid <= 0:
            matches = False
            
        if matches:
            applicable_strategies.append(strategy)
    
    return applicable_strategies

def place_bid_from_strategy(auction_id: str, strategy_id: str) -> Dict:
    """Place a bid based on strategy configuration"""
    from app import strategies, users, auction_data, bids
    
    try:
        if strategy_id not in strategies:
            return {'success': False, 'message': 'Strategy not found'}
        
        strategy = strategies[strategy_id]
        user_id = strategy.get('user_id')
        
        if user_id not in users:
            return {'success': False, 'message': 'User not found'}
        
        user = users[user_id]
        
        if auction_id not in auction_data:
            return {'success': False, 'message': 'Auction not found'}
        
        auction = auction_data[auction_id]
        
        # Calculate bid amount based on strategy
        base_price = auction.get('base_price', 1000)
        max_bid = strategy.get('max_bid', 0)
        bid_strategy = strategy.get('bid_strategy', 'conservative')
        
        if bid_strategy == 'aggressive':
            bid_amount = min(max_bid, base_price * 1.5)
        elif bid_strategy == 'moderate':
            bid_amount = min(max_bid, base_price * 1.2)
        else:  # conservative
            bid_amount = min(max_bid, base_price * 1.05)
        
        # Ensure minimum bid
        bid_amount = max(bid_amount, base_price)
        
        if bid_amount > user.get('budget', 0):
            return {'success': False, 'message': 'Insufficient budget'}
        
        # Create bid
        bid_id = str(uuid.uuid4())
        bid = {
            'id': bid_id,
            'auction_id': auction_id,
            'user_id': user_id,
            'amount': bid_amount,
            'timestamp': datetime.now().isoformat(),
            'strategy_id': strategy_id,
            'type': 'strategy_auto'
        }
        
        # Store bid
        bids[bid_id] = bid
        auction['bids'].append(bid_id)
        
        logger.info(f"Strategy {strategy_id} placed bid {bid_id} for ${bid_amount}")
        
        return {
            'success': True,
            'bid_id': bid_id,
            'amount': bid_amount,
            'message': 'Bid placed successfully'
        }
        
    except Exception as e:
        logger.error(f"Error placing bid from strategy {strategy_id}: {e}")
        return {'success': False, 'message': str(e)}

def finalize_auction(auction_id: str, winning_bid_id: Optional[str] = None, winning_amount: float = 0) -> Dict:
    """Finalize an auction and create result record"""
    from app import auction_data, auction_results, bids, users, scte_triggered_auctions
    
    try:
        if auction_id not in auction_data:
            return {'success': False, 'message': 'Auction not found'}
        
        auction = auction_data[auction_id]
        auction['status'] = 'completed'
        auction['end_time'] = datetime.now().isoformat()
        
        if winning_bid_id and winning_bid_id in bids:
            winning_bid = bids[winning_bid_id]
            auction['winning_bid'] = winning_bid_id
            
            # Create auction result
            result_id = str(uuid.uuid4())
            result = {
                'id': result_id,
                'auction_id': auction_id,
                'moment_id': auction.get('moment_id'),
                'game_id': auction.get('game_id'),
                'winner_user_id': winning_bid['user_id'],
                'winning_amount': winning_amount,
                'timestamp': datetime.now().isoformat(),
                'payment_status': 'pending',
                'scte_triggered': auction_id in scte_triggered_auctions
            }
            
            auction_results[result_id] = result
            
            # Update SCTE tracking
            if auction_id in scte_triggered_auctions:
                scte_triggered_auctions[auction_id]['executed_at'] = datetime.now().isoformat()
                scte_triggered_auctions[auction_id]['winning_amount'] = winning_amount
                scte_triggered_auctions[auction_id]['result_id'] = result_id
            
            logger.info(f"Auction {auction_id} won by user {winning_bid['user_id']} for ${winning_amount}")
            
            return {
                'success': True,
                'winner_user_id': winning_bid['user_id'],
                'winning_amount': winning_amount,
                'result_id': result_id,
                'message': 'Auction completed successfully'
            }
        else:
            # No winning bid
            logger.info(f"Auction {auction_id} completed with no bids")
            
            if auction_id in scte_triggered_auctions:
                scte_triggered_auctions[auction_id]['executed_at'] = datetime.now().isoformat()
                scte_triggered_auctions[auction_id]['winning_amount'] = 0
            
            return {
                'success': True,
                'winner_user_id': None,
                'winning_amount': 0,
                'message': 'Auction completed with no bids'
            }
            
    except Exception as e:
        logger.error(f"Error finalizing auction {auction_id}: {e}")
        return {'success': False, 'message': str(e)}