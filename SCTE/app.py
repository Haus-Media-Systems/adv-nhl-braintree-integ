"""
SCTE-35/104 NHL Instant Replay Bidding Platform
Real-time auction system triggered by SCTE markers in video streams
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import random
import uuid
from datetime import datetime, timedelta
import os
import json
import storage
import braintree
import threading
import socket
import struct
import logging
import time
from enum import Enum
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Callable
import signal
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scte_auction.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'scte_dev_secret_key_change_in_production')

# =============================================================================
# SCTE-35/104 Core Classes and Enums
# =============================================================================

class SCTEEventType(Enum):
    """SCTE-35 Command Types"""
    SPLICE_NULL = 0x00
    SPLICE_SCHEDULE = 0x04
    SPLICE_INSERT = 0x05
    TIME_SIGNAL = 0x06
    BANDWIDTH_RESERVATION = 0x07
    PRIVATE_COMMAND = 0xFF

class AuctionTriggerType(Enum):
    """Enhanced auction triggers for hockey events"""
    GOAL_SCORED = "goal_scored"
    ASSIST = "assist"
    PENALTY = "penalty"
    SAVE = "save"
    FIGHT = "fight"
    PERIOD_END = "period_end"
    PERIOD_START = "period_start"
    POWER_PLAY = "power_play"
    POWER_PLAY_GOAL = "power_play_goal"
    SHORT_HANDED_GOAL = "short_handed_goal"
    BREAKAWAY = "breakaway"
    OVERTIME = "overtime"
    SHOOTOUT = "shootout"
    SHOOTOUT_GOAL = "shootout_goal"
    COMMERCIAL_BREAK = "commercial_break"
    INSTANT_REPLAY = "instant_replay"
    HIGHLIGHT = "highlight"
    FACEOFF = "faceoff"
    HIT = "hit"
    BLOCK = "block"
    TAKEAWAY = "takeaway"
    GIVEAWAY = "giveaway"

@dataclass
class SCTEMarker:
    """Enhanced SCTE marker with full metadata support"""
    timestamp: datetime
    pts_time: Optional[int]
    command_type: SCTEEventType
    unique_program_id: int
    avail_num: int
    avails_expected: int
    duration: Optional[int]
    metadata: Dict
    raw_data: bytes
    
    def to_dict(self):
        return {
            'timestamp': self.timestamp.isoformat(),
            'pts_time': self.pts_time,
            'command_type': self.command_type.name,
            'unique_program_id': self.unique_program_id,
            'avail_num': self.avail_num,
            'avails_expected': self.avails_expected,
            'duration': self.duration,
            'metadata': self.metadata
        }

@dataclass
class AuctionTrigger:
    """Enhanced auction trigger with detailed context"""
    trigger_id: str
    marker: SCTEMarker
    trigger_type: AuctionTriggerType
    game_id: str
    period: str
    team_id: Optional[str]
    player_ids: List[str]
    importance: str
    estimated_value: float
    metadata: Dict
    context_score: float = 1.0  # Multiplier based on game context
    
    def to_dict(self):
        return {
            'trigger_id': self.trigger_id,
            'trigger_type': self.trigger_type.value,
            'game_id': self.game_id,
            'period': self.period,
            'team_id': self.team_id,
            'player_ids': self.player_ids,
            'importance': self.importance,
            'estimated_value': self.estimated_value,
            'context_score': self.context_score,
            'metadata': self.metadata
        }

# =============================================================================
# Configuration and Data Management
# =============================================================================

class SCTEConfig:
    """Centralized SCTE configuration management"""
    
    def __init__(self):
        self.config_file = 'config/scte_config.json'
        self.load_config()
    
    def load_config(self):
        """Load configuration from file or use defaults"""
        default_config = {
            'listener': {
                'enabled': True,
                'udp_port': 9999,
                'bind_address': '0.0.0.0',
                'buffer_size': 4096,
                'timeout': 1.0
            },
            'auctions': {
                'auto_execute': True,
                'max_concurrent': 10,
                'default_duration_ms': 500,
                'min_duration_ms': 100,
                'max_duration_ms': 5000
            },
            'triggers': {
                'goal_scored': {'base_value': 5000, 'importance': 'critical', 'multiplier': 1.0},
                'assist': {'base_value': 2000, 'importance': 'high', 'multiplier': 0.4},
                'penalty': {'base_value': 1500, 'importance': 'normal', 'multiplier': 1.0},
                'save': {'base_value': 2500, 'importance': 'high', 'multiplier': 1.0},
                'fight': {'base_value': 3500, 'importance': 'high', 'multiplier': 1.2},
                'power_play': {'base_value': 2000, 'importance': 'normal', 'multiplier': 1.0},
                'power_play_goal': {'base_value': 6000, 'importance': 'critical', 'multiplier': 1.3},
                'short_handed_goal': {'base_value': 7000, 'importance': 'critical', 'multiplier': 1.5},
                'overtime': {'base_value': 4000, 'importance': 'high', 'multiplier': 1.5},
                'shootout': {'base_value': 3000, 'importance': 'high', 'multiplier': 1.2},
                'shootout_goal': {'base_value': 8000, 'importance': 'critical', 'multiplier': 2.0},
                'commercial_break': {'base_value': 500, 'importance': 'low', 'multiplier': 1.0},
                'instant_replay': {'base_value': 3000, 'importance': 'high', 'multiplier': 1.1},
                'highlight': {'base_value': 2500, 'importance': 'high', 'multiplier': 1.0}
            },
            'context_modifiers': {
                'is_overtime': 1.5,
                'is_playoffs': 2.0,
                'is_finals': 3.0,
                'star_player': 1.25,
                'rival_teams': 1.3,
                'late_period': 1.2,
                'close_game': 1.4,
                'sellout_crowd': 1.1
            },
            'monitoring': {
                'enable_metrics': True,
                'metrics_interval': 30,
                'enable_alerts': True,
                'alert_thresholds': {
                    'max_queue_size': 100,
                    'max_processing_time': 5.0,
                    'min_success_rate': 0.95
                }
            }
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                # Merge with defaults
                self.config = self._merge_configs(default_config, loaded_config)
            else:
                self.config = default_config
                self.save_config()
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            self.config = default_config
    
    def _merge_configs(self, default, loaded):
        """Recursively merge configurations"""
        for key, value in loaded.items():
            if key in default and isinstance(default[key], dict) and isinstance(value, dict):
                default[key] = self._merge_configs(default[key], value)
            else:
                default[key] = value
        return default
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def get(self, path, default=None):
        """Get configuration value by dot path (e.g., 'listener.udp_port')"""
        keys = path.split('.')
        value = self.config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    def set(self, path, value):
        """Set configuration value by dot path"""
        keys = path.split('.')
        config = self.config
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        config[keys[-1]] = value
        self.save_config()

# Initialize global configuration
scte_config = SCTEConfig()

# Configure Braintree
braintree_gateway = braintree.BraintreeGateway(
    braintree.Configuration(
        environment=braintree.Environment.Sandbox,
        merchant_id="cmw9qh963vbrbnp7",
        public_key="b4m63tfbnjh229qk",
        private_key="6dbee76c103a0c6bf6ae64a5076a9708"
    )
)

# Data storage
users = storage.load_users({
    "admin": {
        "id": "admin",
        "name": "SCTE Administrator",
        "company": "NHL SCTE Platform",
        "email": "admin@scte.com",
        "password": "admin",
        "budget": 0,
        "is_admin": True
    }
})

teams = storage.load_data('data/teams.json', {
    "NYR": {"id": "NYR", "name": "New York Rangers", "conference": "Eastern", "division": "Metropolitan"},
    "BOS": {"id": "BOS", "name": "Boston Bruins", "conference": "Eastern", "division": "Atlantic"},
    "TOR": {"id": "TOR", "name": "Toronto Maple Leafs", "conference": "Eastern", "division": "Atlantic"},
    "MTL": {"id": "MTL", "name": "Montreal Canadiens", "conference": "Eastern", "division": "Atlantic"},
    "EDM": {"id": "EDM", "name": "Edmonton Oilers", "conference": "Western", "division": "Pacific"},
    "CGY": {"id": "CGY", "name": "Calgary Flames", "conference": "Western", "division": "Pacific"}
})

# SCTE-specific data structures
scte_markers = {}
scte_triggered_auctions = {}
auction_data = storage.load_auctions({})
bids = storage.load_bids({})
auction_results = storage.load_auction_results({})
strategies = storage.load_strategies({})

# =============================================================================
# SCTE Stream Listener (Enhanced)
# =============================================================================

class SCTEStreamListener:
    """Enhanced SCTE stream listener with robust error handling"""
    
    def __init__(self):
        self.is_listening = False
        self.socket = None
        self.listener_thread = None
        self.stats = {
            'packets_received': 0,
            'packets_processed': 0,
            'packets_failed': 0,
            'markers_created': 0,
            'auctions_triggered': 0,
            'start_time': None,
            'last_packet_time': None
        }
        
    def start_listening(self):
        """Start the SCTE listener"""
        if self.is_listening:
            logger.warning("SCTE listener already running")
            return False
            
        try:
            self.is_listening = True
            self.stats['start_time'] = datetime.now()
            self.listener_thread = threading.Thread(target=self._listen_loop, daemon=True)
            self.listener_thread.start()
            
            logger.info(f"SCTE listener started on UDP port {scte_config.get('listener.udp_port')}")
            return True
        except Exception as e:
            logger.error(f"Failed to start SCTE listener: {e}")
            self.is_listening = False
            return False
    
    def stop_listening(self):
        """Stop the SCTE listener"""
        self.is_listening = False
        if self.socket:
            self.socket.close()
        if self.listener_thread and self.listener_thread.is_alive():
            self.listener_thread.join(timeout=5)
        logger.info("SCTE listener stopped")
    
    def _listen_loop(self):
        """Main listening loop"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            bind_address = scte_config.get('listener.bind_address', '0.0.0.0')
            udp_port = scte_config.get('listener.udp_port', 9999)
            
            self.socket.bind((bind_address, udp_port))
            self.socket.settimeout(scte_config.get('listener.timeout', 1.0))
            
            logger.info(f"SCTE listener bound to {bind_address}:{udp_port}")
            
            while self.is_listening:
                try:
                    data, addr = self.socket.recvfrom(scte_config.get('listener.buffer_size', 4096))
                    self.stats['packets_received'] += 1
                    self.stats['last_packet_time'] = datetime.now()
                    
                    # Process packet in separate thread to avoid blocking
                    threading.Thread(
                        target=self._process_packet,
                        args=(data, addr),
                        daemon=True
                    ).start()
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    logger.error(f"Error receiving packet: {e}")
                    self.stats['packets_failed'] += 1
                    
        except Exception as e:
            logger.error(f"Critical error in SCTE listener: {e}")
        finally:
            if self.socket:
                self.socket.close()
    
    def _process_packet(self, data: bytes, addr):
        """Process individual SCTE packet"""
        try:
            marker = self._parse_scte_data(data)
            if marker:
                self.stats['markers_created'] += 1
                handle_scte_marker(marker)
            self.stats['packets_processed'] += 1
        except Exception as e:
            logger.error(f"Error processing packet from {addr}: {e}")
            self.stats['packets_failed'] += 1
    
    def _parse_scte_data(self, data: bytes) -> Optional[SCTEMarker]:
        """Enhanced SCTE-35 packet parsing"""
        try:
            if len(data) < 14:
                return None
            
            # Basic SCTE-35 validation
            table_id = data[0]
            if table_id != 0xFC:
                return None
            
            # Extract command type
            splice_command_type = data[13] if len(data) > 13 else 0
            
            # Parse PTS time
            pts_time = None
            if len(data) > 20:
                try:
                    pts_time = struct.unpack('>Q', b'\x00\x00\x00' + data[14:20])[0]
                except:
                    pass
            
            # Extract JSON metadata
            metadata = {}
            try:
                if b'{' in data and b'}' in data:
                    json_start = data.index(b'{')
                    json_end = data.rindex(b'}') + 1
                    json_str = data[json_start:json_end].decode('utf-8')
                    metadata = json.loads(json_str)
            except:
                pass
            
            return SCTEMarker(
                timestamp=datetime.now(),
                pts_time=pts_time,
                command_type=SCTEEventType(splice_command_type),
                unique_program_id=metadata.get('program_id', 0),
                avail_num=metadata.get('avail_num', 0),
                avails_expected=metadata.get('avails_expected', 0),
                duration=metadata.get('duration'),
                metadata=metadata,
                raw_data=data
            )
            
        except Exception as e:
            logger.error(f"Error parsing SCTE data: {e}")
            return None
    
    def get_stats(self):
        """Get listener statistics"""
        stats = self.stats.copy()
        if stats['start_time']:
            uptime = datetime.now() - stats['start_time']
            stats['uptime_seconds'] = uptime.total_seconds()
            stats['packets_per_second'] = stats['packets_received'] / max(uptime.total_seconds(), 1)
        return stats

# Global SCTE listener
scte_listener = SCTEStreamListener()

# =============================================================================
# SCTE Marker Processing and Auction Logic
# =============================================================================

def handle_scte_marker(marker: SCTEMarker):
    """Enhanced SCTE marker handling with context awareness"""
    try:
        # Store marker
        marker_id = str(uuid.uuid4())
        scte_markers[marker_id] = marker
        
        logger.info(f"Processing SCTE marker: {marker.command_type.name}, metadata: {marker.metadata}")
        
        # Map to auction trigger
        trigger = create_auction_trigger(marker)
        if trigger:
            # Evaluate context and adjust trigger
            enhanced_trigger = enhance_trigger_context(trigger)
            
            # Create auction if conditions are met
            if should_create_auction(enhanced_trigger):
                auction_id = create_scte_auction(enhanced_trigger)
                if auction_id:
                    scte_listener.stats['auctions_triggered'] += 1
                    logger.info(f"Created auction {auction_id} from SCTE trigger {trigger.trigger_id}")
        
    except Exception as e:
        logger.error(f"Error handling SCTE marker: {e}")

def create_auction_trigger(marker: SCTEMarker) -> Optional[AuctionTrigger]:
    """Create auction trigger from SCTE marker with enhanced mapping"""
    try:
        metadata = marker.metadata
        event_type = metadata.get('event_type', '').lower()
        
        # Enhanced event type mapping
        trigger_mapping = {
            'goal': AuctionTriggerType.GOAL_SCORED,
            'assist': AuctionTriggerType.ASSIST,
            'penalty': AuctionTriggerType.PENALTY,
            'save': AuctionTriggerType.SAVE,
            'fight': AuctionTriggerType.FIGHT,
            'powerplay': AuctionTriggerType.POWER_PLAY,
            'pp_goal': AuctionTriggerType.POWER_PLAY_GOAL,
            'sh_goal': AuctionTriggerType.SHORT_HANDED_GOAL,
            'commercial': AuctionTriggerType.COMMERCIAL_BREAK,
            'replay': AuctionTriggerType.INSTANT_REPLAY,
            'highlight': AuctionTriggerType.HIGHLIGHT,
            'overtime': AuctionTriggerType.OVERTIME,
            'shootout': AuctionTriggerType.SHOOTOUT,
            'so_goal': AuctionTriggerType.SHOOTOUT_GOAL,
            'hit': AuctionTriggerType.HIT,
            'block': AuctionTriggerType.BLOCK
        }
        
        trigger_type = trigger_mapping.get(event_type)
        if not trigger_type:
            logger.debug(f"Unknown event type: {event_type}")
            return None
        
        # Get trigger configuration
        trigger_config = scte_config.get(f'triggers.{trigger_type.value}', {})
        
        return AuctionTrigger(
            trigger_id=str(uuid.uuid4()),
            marker=marker,
            trigger_type=trigger_type,
            game_id=metadata.get('game_id', 'unknown'),
            period=metadata.get('period', '1'),
            team_id=metadata.get('team_id'),
            player_ids=metadata.get('player_ids', []),
            importance=trigger_config.get('importance', 'normal'),
            estimated_value=trigger_config.get('base_value', 1000),
            metadata=metadata,
            context_score=1.0
        )
        
    except Exception as e:
        logger.error(f"Error creating auction trigger: {e}")
        return None

def enhance_trigger_context(trigger: AuctionTrigger) -> AuctionTrigger:
    """Enhance trigger with contextual information and value adjustments"""
    try:
        metadata = trigger.metadata
        context_modifiers = scte_config.get('context_modifiers', {})
        
        # Calculate context score multiplier
        multiplier = 1.0
        
        # Game situation modifiers
        if metadata.get('is_overtime'):
            multiplier *= context_modifiers.get('is_overtime', 1.5)
        if metadata.get('is_playoffs'):
            multiplier *= context_modifiers.get('is_playoffs', 2.0)
        if metadata.get('is_finals'):
            multiplier *= context_modifiers.get('is_finals', 3.0)
        if metadata.get('star_player'):
            multiplier *= context_modifiers.get('star_player', 1.25)
        if metadata.get('rival_teams'):
            multiplier *= context_modifiers.get('rival_teams', 1.3)
        if metadata.get('late_period'):
            multiplier *= context_modifiers.get('late_period', 1.2)
        if metadata.get('close_game'):
            multiplier *= context_modifiers.get('close_game', 1.4)
        if metadata.get('sellout_crowd'):
            multiplier *= context_modifiers.get('sellout_crowd', 1.1)
        
        # Apply trigger-specific multiplier
        trigger_config = scte_config.get(f'triggers.{trigger.trigger_type.value}', {})
        multiplier *= trigger_config.get('multiplier', 1.0)
        
        # Update trigger
        trigger.context_score = multiplier
        trigger.estimated_value = int(trigger.estimated_value * multiplier)
        
        # Adjust importance based on context
        if multiplier >= 2.0:
            trigger.importance = 'critical'
        elif multiplier >= 1.5:
            trigger.importance = 'high'
        elif multiplier <= 0.7:
            trigger.importance = 'low'
        
        return trigger
        
    except Exception as e:
        logger.error(f"Error enhancing trigger context: {e}")
        return trigger

def should_create_auction(trigger: AuctionTrigger) -> bool:
    """Determine if auction should be created based on current conditions"""
    try:
        # Check concurrent auction limit
        active_count = len([a for a in auction_data.values() if a.get('status') == 'active'])
        max_concurrent = scte_config.get('auctions.max_concurrent', 10)
        
        if active_count >= max_concurrent:
            logger.warning(f"Max concurrent auctions reached ({active_count}/{max_concurrent})")
            return False
        
        # Check importance thresholds based on current load
        if active_count > max_concurrent * 0.8:  # 80% capacity
            if trigger.importance in ['low', 'normal']:
                logger.debug(f"Skipping {trigger.importance} importance auction due to high load")
                return False
        
        # Check minimum value threshold
        min_value = scte_config.get('auctions.min_value', 100)
        if trigger.estimated_value < min_value:
            logger.debug(f"Auction value {trigger.estimated_value} below minimum {min_value}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error checking auction creation conditions: {e}")
        return False

def create_scte_auction(trigger: AuctionTrigger) -> Optional[str]:
    """Create instant auction from SCTE trigger"""
    try:
        auction_id = str(uuid.uuid4())
        
        # Calculate auction duration based on importance
        duration_ms = scte_config.get('auctions.default_duration_ms', 500)
        if trigger.importance == 'critical':
            duration_ms = min(duration_ms * 1.5, scte_config.get('auctions.max_duration_ms', 5000))
        elif trigger.importance == 'low':
            duration_ms = max(duration_ms * 0.5, scte_config.get('auctions.min_duration_ms', 100))
        
        # Create auction
        auction = {
            'id': auction_id,
            'moment_id': f"scte_{trigger.trigger_type.value}_{trigger.trigger_id[:8]}",
            'game_id': trigger.game_id,
            'status': 'active',
            'start_time': datetime.now().isoformat(),
            'end_time': (datetime.now() + timedelta(milliseconds=duration_ms)).isoformat(),
            'base_price': trigger.estimated_value,
            'reserve_price': trigger.estimated_value * 0.7,
            'increment_amount': max(trigger.estimated_value * 0.1, 50),
            'period': trigger.period,
            'team_id': trigger.team_id or 'both',
            'players': trigger.player_ids,
            'event_importance': trigger.importance,
            'scte_trigger': trigger.to_dict(),
            'created_from': 'scte_marker',
            'duration_ms': duration_ms,
            'bids': [],
            'winning_bid': None
        }
        
        # Store auction
        auction_data[auction_id] = auction
        storage.save_auctions(auction_data)
        
        # Track SCTE-triggered auction
        scte_triggered_auctions[auction_id] = {
            'trigger_id': trigger.trigger_id,
            'trigger_type': trigger.trigger_type.value,
            'marker_timestamp': trigger.marker.timestamp.isoformat(),
            'created_at': datetime.now().isoformat(),
            'estimated_value': trigger.estimated_value,
            'context_score': trigger.context_score
        }
        
        # Auto-execute if enabled
        if scte_config.get('auctions.auto_execute', True):
            # Small delay to allow strategies to register
            threading.Timer(0.1, lambda: execute_instant_auction(auction_id)).start()
        
        logger.info(f"Created SCTE auction {auction_id}: {trigger.trigger_type.value} worth ${trigger.estimated_value}")
        return auction_id
        
    except Exception as e:
        logger.error(f"Error creating SCTE auction: {e}")
        return None

def execute_instant_auction(auction_id: str):
    """Execute an instant auction with strategy-based bidding"""
    try:
        if auction_id not in auction_data:
            logger.error(f"Auction {auction_id} not found for execution")
            return {'success': False, 'message': 'Auction not found'}
        
        auction = auction_data[auction_id]
        
        # Find applicable strategies
        applicable_strategies = find_applicable_strategies(auction)
        
        if not applicable_strategies:
            logger.info(f"No applicable strategies for auction {auction_id}")
            return finalize_auction(auction_id, None, 0)
        
        # Execute bidding with all applicable strategies
        bids_placed = []
        for strategy in applicable_strategies:
            bid_result = place_bid_from_strategy(auction_id, strategy['id'])
            if bid_result.get('success'):
                bids_placed.append(bid_result)
        
        # Determine winner
        if bids_placed:
            # Find highest bid
            highest_bid = max(bids_placed, key=lambda x: x.get('amount', 0))
            return finalize_auction(auction_id, highest_bid.get('bid_id'), highest_bid.get('amount', 0))
        else:
            return finalize_auction(auction_id, None, 0)
        
    except Exception as e:
        logger.error(f"Error executing instant auction {auction_id}: {e}")
        return {'success': False, 'message': str(e)}

# ... [Continue with helper functions - truncated for length] ...