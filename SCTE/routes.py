"""
Flask routes for SCTE-optimized NHL auction platform
"""

from flask import render_template, request, redirect, url_for, flash, session, jsonify
import json
import time
import uuid
from datetime import datetime
import logging
from app import app, scte_config, scte_listener, scte_markers, scte_triggered_auctions
from app import users, teams, auction_data, bids, auction_results, strategies
from app import SCTEMarker, SCTEEventType, AuctionTriggerType, handle_scte_marker
from auction_engine import find_applicable_strategies, place_bid_from_strategy, finalize_auction

logger = logging.getLogger(__name__)

# =============================================================================
# Authentication and User Management
# =============================================================================

def get_user():
    """Get current user from session"""
    user_id = session.get('user_id')
    if user_id and user_id in users:
        return users[user_id]
    return None

@app.route('/')
def index():
    """SCTE-optimized homepage"""
    user = get_user()
    
    # Get SCTE system status
    scte_status = {
        'listener_active': scte_listener.is_listening,
        'total_markers': len(scte_markers),
        'active_auctions': len([a for a in auction_data.values() if a.get('status') == 'active']),
        'total_scte_auctions': len(scte_triggered_auctions)
    }
    
    return render_template('index.html', user=user, scte_status=scte_status)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        for user in users.values():
            if user['email'] == email and user['password'] == password:
                session['user_id'] = user['id']
                flash('Logged in successfully!', 'success')
                return redirect(url_for('dashboard'))
        
        flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    """Enhanced dashboard with SCTE metrics"""
    user = get_user()
    if not user:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))
    
    # Get user's recent activity
    user_bids = {bid_id: bid for bid_id, bid in bids.items() if bid['user_id'] == user['id']}
    user_results = {result_id: result for result_id, result in auction_results.items() 
                   if result['winner_user_id'] == user['id']}
    
    # SCTE-specific metrics
    scte_metrics = {
        'listener_status': 'Active' if scte_listener.is_listening else 'Stopped',
        'recent_markers': list(scte_markers.values())[-5:] if scte_markers else [],
        'scte_auctions_participated': len([bid for bid in user_bids.values() 
                                         if bid.get('auction_id') in scte_triggered_auctions]),
        'scte_auctions_won': len([result for result in user_results.values() 
                                if result.get('scte_triggered', False)])
    }
    
    return render_template('dashboard.html', 
                         user=user, 
                         recent_bids=list(user_bids.values())[-10:],
                         recent_wins=list(user_results.values())[-5:],
                         scte_metrics=scte_metrics)

# =============================================================================
# SCTE-Specific Routes
# =============================================================================

@app.route('/scte/dashboard')
def scte_dashboard():
    """SCTE monitoring and control dashboard"""
    user = get_user()
    if not user or not user.get('is_admin', False):
        flash('Admin access required.', 'error')
        return redirect(url_for('login'))
    
    # Get comprehensive SCTE statistics
    listener_stats = scte_listener.get_stats()
    
    active_auctions = [a for a in scte_triggered_auctions.values() if not a.get('executed_at')]
    completed_auctions = [a for a in scte_triggered_auctions.values() if a.get('executed_at')]
    
    stats = {
        'listener_status': 'Active' if scte_listener.is_listening else 'Stopped',
        'udp_port': scte_config.get('listener.udp_port'),
        'auto_execute': scte_config.get('auctions.auto_execute'),
        'total_markers': len(scte_markers),
        'total_auctions': len(scte_triggered_auctions),
        'active_auctions': len(active_auctions),
        'completed_auctions': len(completed_auctions),
        'recent_markers': list(scte_markers.values())[-10:] if scte_markers else [],
        'listener_stats': listener_stats
    }
    
    # Recent SCTE-triggered auctions with details
    recent_auctions = []
    for auction_id, scte_data in list(scte_triggered_auctions.items())[-10:]:
        auction = auction_data.get(auction_id, {})
        recent_auctions.append({
            'auction_id': auction_id,
            'scte_data': scte_data,
            'auction': auction
        })
    
    return render_template('scte_dashboard.html', 
                         user=user, 
                         stats=stats,
                         scte_config=scte_config.config,
                         recent_auctions=recent_auctions)

@app.route('/scte/config', methods=['GET', 'POST'])
def scte_configuration():
    """SCTE configuration management"""
    user = get_user()
    if not user or not user.get('is_admin', False):
        flash('Admin access required.', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            # Update listener configuration
            scte_config.set('listener.enabled', request.form.get('listener_enabled') == 'on')
            scte_config.set('listener.udp_port', int(request.form.get('udp_port', 9999)))
            
            # Update auction configuration
            scte_config.set('auctions.auto_execute', request.form.get('auto_execute') == 'on')
            scte_config.set('auctions.max_concurrent', int(request.form.get('max_concurrent', 10)))
            scte_config.set('auctions.default_duration_ms', int(request.form.get('duration_ms', 500)))
            
            # Update trigger values
            for trigger_type in ['goal_scored', 'save', 'penalty', 'fight', 'power_play']:
                base_value = request.form.get(f'{trigger_type}_value')
                if base_value:
                    scte_config.set(f'triggers.{trigger_type}.base_value', float(base_value))
            
            flash('SCTE configuration updated successfully', 'success')
            return redirect(url_for('scte_dashboard'))
            
        except Exception as e:
            flash(f'Error updating configuration: {e}', 'error')
    
    return render_template('scte_config.html', user=user, config=scte_config.config)

@app.route('/scte/listener/start', methods=['POST'])
def scte_start():
    """Start SCTE listener"""
    user = get_user()
    if not user or not user.get('is_admin', False):
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    
    try:
        success = scte_listener.start_listening()
        if success:
            return jsonify({'success': True, 'message': 'SCTE listener started successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to start SCTE listener'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/scte/listener/stop', methods=['POST'])
def scte_stop():
    """Stop SCTE listener"""
    user = get_user()
    if not user or not user.get('is_admin', False):
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    
    try:
        scte_listener.stop_listening()
        return jsonify({'success': True, 'message': 'SCTE listener stopped successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/scte/test', methods=['POST'])
def scte_test_marker():
    """Send a test SCTE marker"""
    user = get_user()
    if not user or not user.get('is_admin', False):
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    
    try:
        # Get test parameters
        data = request.get_json()
        event_type = data.get('event_type', 'goal')
        game_id = data.get('game_id', 'test_game')
        period = data.get('period', '1')
        team_id = data.get('team_id', 'NYR')
        
        # Add context modifiers for testing
        test_metadata = {
            'event_type': event_type,
            'game_id': game_id,
            'period': period,
            'team_id': team_id,
            'is_test': True,
            'timestamp': datetime.now().isoformat()
        }
        
        # Add optional context
        if data.get('is_overtime'):
            test_metadata['is_overtime'] = True
        if data.get('star_player'):
            test_metadata['star_player'] = True
        if data.get('close_game'):
            test_metadata['close_game'] = True
        
        # Create test marker
        test_marker = SCTEMarker(
            timestamp=datetime.now(),
            pts_time=int(time.time() * 90000),
            command_type=SCTEEventType.SPLICE_INSERT,
            unique_program_id=1,
            avail_num=1,
            avails_expected=1,
            duration=None,
            metadata=test_metadata,
            raw_data=b'\xFC' + json.dumps(test_metadata).encode()
        )
        
        # Handle the marker
        handle_scte_marker(test_marker)
        
        return jsonify({
            'success': True, 
            'message': f'Test {event_type} marker sent successfully',
            'marker_id': list(scte_markers.keys())[-1] if scte_markers else None
        })
        
    except Exception as e:
        logger.error(f"Error sending test marker: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/scte/markers')
def scte_markers_api():
    """Get recent SCTE markers (API)"""
    user = get_user()
    if not user or not user.get('is_admin', False):
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    
    try:
        # Get recent markers
        recent_markers = []
        for marker_id, marker in list(scte_markers.items())[-50:]:
            recent_markers.append({
                'id': marker_id,
                'timestamp': marker.timestamp.isoformat(),
                'command_type': marker.command_type.name,
                'metadata': marker.metadata,
                'pts_time': marker.pts_time
            })
        
        return jsonify({
            'success': True,
            'total': len(scte_markers),
            'markers': recent_markers,
            'listener_stats': scte_listener.get_stats()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/scte/auctions')
def scte_auctions_api():
    """Get SCTE-triggered auctions (API)"""
    user = get_user()
    if not user or not user.get('is_admin', False):
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    
    try:
        # Get SCTE auctions with details
        auctions = []
        for auction_id, scte_data in scte_triggered_auctions.items():
            auction = auction_data.get(auction_id, {})
            auctions.append({
                'auction_id': auction_id,
                'trigger_type': scte_data['trigger_type'],
                'created_at': scte_data['created_at'],
                'executed_at': scte_data.get('executed_at'),
                'estimated_value': scte_data.get('estimated_value', 0),
                'winning_amount': scte_data.get('winning_amount', 0),
                'status': auction.get('status', 'unknown'),
                'bid_count': len(auction.get('bids', [])),
                'context_score': scte_data.get('context_score', 1.0)
            })
        
        return jsonify({
            'success': True,
            'total': len(auctions),
            'auctions': sorted(auctions, key=lambda x: x['created_at'], reverse=True)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# =============================================================================
# Auction and Strategy Routes
# =============================================================================

@app.route('/auctions')
def auction_listings():
    """List auctions with SCTE indicators"""
    user = get_user()
    if not user:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))
    
    # Separate SCTE-triggered and manual auctions
    scte_auctions = []
    manual_auctions = []
    
    for auction_id, auction in auction_data.items():
        auction_copy = auction.copy()
        auction_copy['id'] = auction_id
        auction_copy['is_scte'] = auction_id in scte_triggered_auctions
        
        if auction_copy['is_scte']:
            auction_copy['scte_data'] = scte_triggered_auctions.get(auction_id, {})
            scte_auctions.append(auction_copy)
        else:
            manual_auctions.append(auction_copy)
    
    return render_template('auctions.html', 
                         user=user, 
                         scte_auctions=scte_auctions[-20:],  # Recent 20
                         manual_auctions=manual_auctions[-10:])  # Recent 10

@app.route('/strategies')
def my_strategies():
    """User's bidding strategies"""
    user = get_user()
    if not user:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))
    
    user_strategies = {sid: s for sid, s in strategies.items() if s.get('user_id') == user['id']}
    
    return render_template('strategies.html', 
                         user=user, 
                         strategies=user_strategies,
                         teams=teams,
                         trigger_types=[t.value for t in AuctionTriggerType])

# =============================================================================
# API Routes for Real-time Updates
# =============================================================================

@app.route('/api/live-stats')
def live_stats():
    """Real-time statistics for dashboard updates"""
    try:
        stats = {
            'timestamp': datetime.now().isoformat(),
            'scte': {
                'listener_active': scte_listener.is_listening,
                'total_markers': len(scte_markers),
                'packets_received': scte_listener.stats.get('packets_received', 0),
                'auctions_triggered': scte_listener.stats.get('auctions_triggered', 0)
            },
            'auctions': {
                'total': len(auction_data),
                'active': len([a for a in auction_data.values() if a.get('status') == 'active']),
                'scte_triggered': len(scte_triggered_auctions)
            }
        }
        
        return jsonify({'success': True, 'stats': stats})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# =============================================================================
# Error Handlers
# =============================================================================

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html', user=get_user()), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html', user=get_user()), 500