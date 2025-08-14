#!/usr/bin/env python3
"""
Advanced SCTE Marker Test Sender
Professional-grade testing utility for SCTE-35/104 marker simulation
"""

import socket
import json
import time
import struct
import argparse
from datetime import datetime, timedelta
import random
import threading
import logging
from typing import Dict, List, Optional
import sys
import signal

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SCTESender:
    """Advanced SCTE marker sender with realistic game simulation"""
    
    def __init__(self, host='localhost', port=9999):
        self.host = host
        self.port = port
        self.running = False
        self.stats = {
            'markers_sent': 0,
            'start_time': None,
            'last_marker_time': None
        }
        
    def create_scte_packet(self, event_type: str, metadata: Dict) -> bytes:
        """Create a realistic SCTE-35 packet with embedded metadata"""
        
        # SCTE-35 header structure
        table_id = 0xFC  # SCTE-35 table identifier
        section_syntax_indicator = 0
        private_indicator = 0
        section_length = 0
        protocol_version = 0
        encrypted_packet = 0
        encryption_algorithm = 0
        pts_adjustment = int(time.time() * 90000)  # Current time in 90kHz
        
        # Splice command type based on event
        command_mapping = {
            'goal': 0x05,           # SPLICE_INSERT
            'save': 0x06,           # TIME_SIGNAL
            'penalty': 0x05,        # SPLICE_INSERT
            'commercial': 0x05,     # SPLICE_INSERT
            'replay': 0x06,         # TIME_SIGNAL
            'fight': 0x05,          # SPLICE_INSERT
            'powerplay': 0x06,      # TIME_SIGNAL
            'period_end': 0x05,     # SPLICE_INSERT
            'period_start': 0x05,   # SPLICE_INSERT
        }
        
        splice_command_type = command_mapping.get(event_type, 0x05)
        
        # Enhanced metadata
        enhanced_metadata = {
            'event_type': event_type,
            'timestamp': datetime.now().isoformat(),
            'pts_time': pts_adjustment,
            'sender': 'scte_test_sender_v2',
            **metadata
        }
        
        # Convert metadata to bytes
        metadata_bytes = json.dumps(enhanced_metadata).encode()
        
        # Build SCTE-35 packet
        packet = bytearray()
        
        # Basic SCTE-35 header
        packet.append(table_id)
        packet.append(0x00)  # Section syntax indicator + reserved + section length high
        packet.append(len(metadata_bytes) + 20)  # Section length low (approximate)
        packet.append(protocol_version)
        
        # Reserved bytes and flags
        for _ in range(9):
            packet.append(0x00)
        
        # Splice command type at position 13
        packet.append(splice_command_type)
        
        # PTS adjustment (6 bytes)
        pts_bytes = struct.pack('>Q', pts_adjustment)[-6:]
        packet.extend(pts_bytes)
        
        # Splice command length and command data (simplified)
        packet.append(0x00)  # Command length
        
        # Add metadata JSON
        packet.extend(metadata_bytes)
        
        return bytes(packet)
    
    def send_marker(self, event_type: str, metadata: Dict) -> bool:
        """Send a single SCTE marker"""
        try:
            packet = self.create_scte_packet(event_type, metadata)
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(packet, (self.host, self.port))
            sock.close()
            
            self.stats['markers_sent'] += 1
            self.stats['last_marker_time'] = datetime.now()
            
            logger.info(f"Sent {event_type} marker: {metadata.get('description', '')}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending marker: {e}")
            return False
    
    def simulate_live_game(self, game_config: Dict):
        """Simulate a complete live hockey game with realistic timing"""
        
        logger.info(f"Starting live game simulation: {game_config['home_team']} vs {game_config['away_team']}")
        self.running = True
        self.stats['start_time'] = datetime.now()
        
        # Game setup
        home_team = game_config['home_team']
        away_team = game_config['away_team']
        game_id = game_config.get('game_id', f"game_{int(time.time())}")
        
        # Game state
        period = 1
        period_time = 0  # Seconds into period
        score = {'home': 0, 'away': 0}
        power_plays = []
        
        try:
            # Pre-game
            self.send_marker('period_start', {
                'game_id': game_id,
                'period': 'pre',
                'home_team': home_team,
                'away_team': away_team,
                'description': 'Pre-game show starting'
            })
            
            time.sleep(2)
            
            # Simulate 3 periods + potential overtime
            for current_period in range(1, 4):
                if not self.running:
                    break
                    
                logger.info(f"Starting Period {current_period}")
                
                # Period start
                self.send_marker('period_start', {
                    'game_id': game_id,
                    'period': str(current_period),
                    'home_team': home_team,
                    'away_team': away_team,
                    'score_home': score['home'],
                    'score_away': score['away'],
                    'description': f'Period {current_period} starting'
                })
                
                # Simulate period events (20 minutes = 1200 seconds, but we'll compress time)
                period_duration = game_config.get('period_duration_seconds', 60)  # Compressed time
                period_start_time = time.time()
                
                while (time.time() - period_start_time) < period_duration and self.running:
                    # Random event probability
                    event_roll = random.random()
                    
                    if event_roll < 0.05:  # 5% chance per interval
                        # Goal!
                        scoring_team = random.choice([home_team, away_team])
                        if scoring_team == home_team:
                            score['home'] += 1
                        else:
                            score['away'] += 1
                        
                        # Determine goal type
                        goal_type = 'goal'
                        importance = 'critical'
                        
                        if power_plays and random.random() < 0.3:
                            goal_type = 'pp_goal'
                            importance = 'critical'
                        elif random.random() < 0.1:
                            goal_type = 'sh_goal'
                            importance = 'critical'
                        
                        self.send_marker(goal_type, {
                            'game_id': game_id,
                            'period': str(current_period),
                            'team_id': scoring_team,
                            'score_home': score['home'],
                            'score_away': score['away'],
                            'star_player': random.random() < 0.3,
                            'close_game': abs(score['home'] - score['away']) <= 1,
                            'late_period': (time.time() - period_start_time) > (period_duration * 0.8),
                            'description': f"{scoring_team} scores! {score['home']}-{score['away']}"
                        })
                        
                        # Replay likely after goal
                        time.sleep(1)
                        self.send_marker('replay', {
                            'game_id': game_id,
                            'period': str(current_period),
                            'team_id': scoring_team,
                            'event_type': 'goal_replay',
                            'highlight': True,
                            'description': 'Goal replay'
                        })
                        
                    elif event_roll < 0.15:  # 10% chance for save
                        goalie_team = random.choice([home_team, away_team])
                        self.send_marker('save', {
                            'game_id': game_id,
                            'period': str(current_period),
                            'team_id': goalie_team,
                            'spectacular': random.random() < 0.4,
                            'breakaway': random.random() < 0.2,
                            'description': f"Great save by {goalie_team} goalie"
                        })
                        
                    elif event_roll < 0.25:  # 10% chance for penalty
                        penalty_team = random.choice([home_team, away_team])
                        penalty_type = random.choice(['minor', 'major', 'misconduct'])
                        
                        self.send_marker('penalty', {
                            'game_id': game_id,
                            'period': str(current_period),
                            'team_id': penalty_team,
                            'penalty_type': penalty_type,
                            'description': f"{penalty_type.title()} penalty to {penalty_team}"
                        })
                        
                        # Start power play
                        if penalty_type == 'minor':
                            power_plays.append({
                                'team': away_team if penalty_team == home_team else home_team,
                                'start_time': time.time(),
                                'duration': 120  # 2 minutes compressed
                            })
                            
                            self.send_marker('powerplay', {
                                'game_id': game_id,
                                'period': str(current_period),
                                'team_id': away_team if penalty_team == home_team else home_team,
                                'description': f"Power play for {'away' if penalty_team == home_team else 'home'}"
                            })
                    
                    elif event_roll < 0.28:  # 3% chance for fight
                        self.send_marker('fight', {
                            'game_id': game_id,
                            'period': str(current_period),
                            'team_id': 'both',
                            'rivalry': random.random() < 0.4,
                            'description': "Fight breaks out!"
                        })
                    
                    # Check expired power plays
                    power_plays = [pp for pp in power_plays 
                                 if (time.time() - pp['start_time']) < pp['duration']]
                    
                    # Wait between events
                    time.sleep(random.uniform(2, 8))
                
                # Period end
                self.send_marker('period_end', {
                    'game_id': game_id,
                    'period': str(current_period),
                    'score_home': score['home'],
                    'score_away': score['away'],
                    'description': f"End of Period {current_period}"
                })
                
                # Intermission
                if current_period < 3:
                    self.send_marker('commercial', {
                        'game_id': game_id,
                        'period': 'intermission',
                        'duration': 1800,  # 18 minutes
                        'description': f"Intermission after Period {current_period}"
                    })
                    
                    time.sleep(3)  # Compressed intermission
            
            # Check for overtime
            if score['home'] == score['away'] and game_config.get('allow_overtime', True):
                logger.info("Game tied, starting overtime")
                
                self.send_marker('overtime', {
                    'game_id': game_id,
                    'period': 'OT',
                    'score_home': score['home'],
                    'score_away': score['away'],
                    'description': "Overtime starting"
                })
                
                # Simulate overtime (compressed)
                overtime_duration = 20  # Compressed OT
                ot_start = time.time()
                
                while (time.time() - ot_start) < overtime_duration and self.running:
                    if random.random() < 0.1:  # Higher goal probability in OT
                        winner = random.choice([home_team, away_team])
                        if winner == home_team:
                            score['home'] += 1
                        else:
                            score['away'] += 1
                        
                        self.send_marker('goal', {
                            'game_id': game_id,
                            'period': 'OT',
                            'team_id': winner,
                            'score_home': score['home'],
                            'score_away': score['away'],
                            'is_overtime': True,
                            'game_winner': True,
                            'description': f"OVERTIME WINNER! {winner} wins {score['home']}-{score['away']}"
                        })
                        break
                    
                    time.sleep(2)
                
                # If still tied, shootout
                if score['home'] == score['away']:
                    logger.info("Still tied, starting shootout")
                    
                    self.send_marker('shootout', {
                        'game_id': game_id,
                        'period': 'SO',
                        'description': "Shootout starting"
                    })
                    
                    # Simulate shootout rounds
                    for round_num in range(1, 4):  # Best of 3 initially
                        for team in [home_team, away_team]:
                            if random.random() < 0.4:  # 40% goal rate
                                self.send_marker('so_goal', {
                                    'game_id': game_id,
                                    'period': 'SO',
                                    'team_id': team,
                                    'round': round_num,
                                    'description': f"Shootout goal by {team}, round {round_num}"
                                })
                            
                            time.sleep(1)
                    
                    # Determine winner (simplified)
                    winner = random.choice([home_team, away_team])
                    self.send_marker('so_goal', {
                        'game_id': game_id,
                        'period': 'SO',
                        'team_id': winner,
                        'game_winner': True,
                        'description': f"SHOOTOUT WINNER! {winner} wins in shootout"
                    })
            
            logger.info(f"Game simulation complete. Final score: {home_team} {score['home']} - {away_team} {score['away']}")
            
        except KeyboardInterrupt:
            logger.info("Game simulation interrupted by user")
        except Exception as e:
            logger.error(f"Error in game simulation: {e}")
        finally:
            self.running = False
    
    def send_batch_markers(self, events: List[Dict], delay_range=(1, 3)):
        """Send a batch of markers with random delays"""
        self.running = True
        
        for i, event in enumerate(events):
            if not self.running:
                break
                
            logger.info(f"Sending event {i+1}/{len(events)}: {event['type']}")
            
            self.send_marker(event['type'], event['metadata'])
            
            if i < len(events) - 1:  # Don't delay after last event
                delay = random.uniform(*delay_range)
                time.sleep(delay)
        
        self.running = False
    
    def stress_test(self, duration_seconds=60, events_per_second=2):
        """Stress test the SCTE system with high-frequency markers"""
        logger.info(f"Starting stress test: {events_per_second} events/sec for {duration_seconds} seconds")
        
        self.running = True
        start_time = time.time()
        event_types = ['goal', 'save', 'penalty', 'hit', 'block']
        
        while (time.time() - start_time) < duration_seconds and self.running:
            event_type = random.choice(event_types)
            
            self.send_marker(event_type, {
                'game_id': 'stress_test',
                'period': '1',
                'team_id': random.choice(['NYR', 'BOS']),
                'test_type': 'stress',
                'sequence': self.stats['markers_sent']
            })
            
            time.sleep(1.0 / events_per_second)
        
        logger.info(f"Stress test complete. Sent {self.stats['markers_sent']} markers")
        self.running = False
    
    def get_stats(self):
        """Get sender statistics"""
        stats = self.stats.copy()
        if stats['start_time']:
            uptime = datetime.now() - stats['start_time']
            stats['uptime_seconds'] = uptime.total_seconds()
            if stats['uptime_seconds'] > 0:
                stats['markers_per_second'] = stats['markers_sent'] / stats['uptime_seconds']
        return stats

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    logger.info("Received interrupt signal, stopping...")
    if 'sender' in globals():
        sender.running = False
    sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description='Advanced SCTE Marker Test Sender')
    parser.add_argument('--host', default='localhost', help='Target host')
    parser.add_argument('--port', type=int, default=9999, help='Target UDP port')
    
    # Operation modes
    parser.add_argument('--single', action='store_true', help='Send single marker')
    parser.add_argument('--simulate', action='store_true', help='Simulate live game')
    parser.add_argument('--stress', action='store_true', help='Run stress test')
    parser.add_argument('--batch', action='store_true', help='Send batch of predefined events')
    
    # Single marker options
    parser.add_argument('--event', default='goal', help='Event type')
    parser.add_argument('--team', default='NYR', help='Team ID')
    parser.add_argument('--period', default='1', help='Period')
    
    # Simulation options
    parser.add_argument('--home-team', default='NYR', help='Home team')
    parser.add_argument('--away-team', default='BOS', help='Away team')
    parser.add_argument('--period-duration', type=int, default=60, help='Period duration in seconds (compressed)')
    
    # Stress test options
    parser.add_argument('--duration', type=int, default=60, help='Test duration in seconds')
    parser.add_argument('--rate', type=float, default=2.0, help='Events per second')
    
    args = parser.parse_args()
    
    # Set up signal handling
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create sender
    global sender
    sender = SCTESender(args.host, args.port)
    
    try:
        if args.simulate:
            # Live game simulation
            game_config = {
                'home_team': args.home_team,
                'away_team': args.away_team,
                'period_duration_seconds': args.period_duration,
                'allow_overtime': True
            }
            sender.simulate_live_game(game_config)
            
        elif args.stress:
            # Stress test
            sender.stress_test(args.duration, args.rate)
            
        elif args.batch:
            # Batch events
            events = [
                {'type': 'goal', 'metadata': {'team_id': 'NYR', 'period': '1', 'star_player': True}},
                {'type': 'save', 'metadata': {'team_id': 'BOS', 'period': '1', 'spectacular': True}},
                {'type': 'penalty', 'metadata': {'team_id': 'NYR', 'period': '1', 'penalty_type': 'minor'}},
                {'type': 'powerplay', 'metadata': {'team_id': 'BOS', 'period': '1'}},
                {'type': 'fight', 'metadata': {'team_id': 'both', 'period': '2'}},
                {'type': 'replay', 'metadata': {'team_id': 'NYR', 'period': '2', 'highlight': True}}
            ]
            sender.send_batch_markers(events)
            
        else:
            # Single marker
            metadata = {
                'game_id': f'test_{int(time.time())}',
                'period': args.period,
                'team_id': args.team,
                'description': f'Test {args.event} event'
            }
            sender.send_marker(args.event, metadata)
        
        # Print final stats
        stats = sender.get_stats()
        logger.info(f"Final stats: {stats}")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()