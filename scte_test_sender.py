#!/usr/bin/env python3
"""
SCTE Marker Test Sender
Simulates sending SCTE-35/104 markers to the auction platform for testing
"""

import socket
import json
import time
import struct
import argparse
from datetime import datetime
import random

def create_scte_packet(event_type, game_id, period, team_id, additional_metadata=None):
    """Create a simulated SCTE-35 packet with embedded JSON metadata"""
    
    # SCTE-35 header (simplified)
    table_id = 0xFC  # SCTE-35 table identifier
    section_syntax_indicator = 0
    private_indicator = 0
    section_length = 0  # Will be calculated
    protocol_version = 0
    encrypted_packet = 0
    encryption_algorithm = 0
    pts_adjustment = int(time.time() * 90000)  # Current time in 90kHz
    
    # Splice command type
    splice_command_type = 0x05  # SPLICE_INSERT
    
    # Create metadata JSON
    metadata = {
        'event_type': event_type,
        'game_id': game_id,
        'period': period,
        'team_id': team_id,
        'timestamp': datetime.now().isoformat(),
        'is_test': True
    }
    
    if additional_metadata:
        metadata.update(additional_metadata)
    
    # Convert metadata to bytes
    metadata_bytes = json.dumps(metadata).encode()
    
    # Build packet (simplified SCTE-35 structure)
    packet = bytearray()
    
    # Table ID
    packet.append(table_id)
    
    # Section syntax indicator and length (simplified)
    packet.append(0x00)
    packet.append(0x00)
    
    # Protocol version
    packet.append(protocol_version)
    
    # Padding bytes
    for _ in range(9):
        packet.append(0x00)
    
    # Splice command type at position 13
    packet.append(splice_command_type)
    
    # PTS adjustment (6 bytes, simplified)
    pts_bytes = struct.pack('>Q', pts_adjustment)[-6:]
    packet.extend(pts_bytes)
    
    # Add metadata JSON at the end
    packet.extend(metadata_bytes)
    
    return bytes(packet)

def send_scte_marker(host='localhost', port=9999, event_type='goal', 
                     game_id='test_game', period='1', team_id='NYR'):
    """Send a SCTE marker via UDP"""
    
    # Create the packet
    packet = create_scte_packet(event_type, game_id, period, team_id)
    
    # Send via UDP
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.sendto(packet, (host, port))
        print(f"Sent SCTE marker: {event_type} for {team_id} in period {period}")
        return True
    except Exception as e:
        print(f"Error sending marker: {e}")
        return False
    finally:
        sock.close()

def simulate_game_events(host='localhost', port=9999, game_id='game_001'):
    """Simulate a series of game events"""
    
    events = [
        ('goal', '1', 'NYR', {'star_player': True}),
        ('save', '1', 'BOS', None),
        ('penalty', '1', 'NYR', None),
        ('powerplay', '1', 'BOS', None),
        ('goal', '1', 'BOS', None),
        ('commercial', '1', None, None),
        ('fight', '2', 'both', None),
        ('goal', '2', 'NYR', None),
        ('save', '2', 'NYR', None),
        ('penalty', '2', 'BOS', None),
        ('replay', '2', 'NYR', {'highlight': True}),
        ('commercial', '2', None, None),
        ('goal', '3', 'BOS', None),
        ('save', '3', 'BOS', None),
        ('goal', '3', 'NYR', {'is_overtime': True}),
    ]
    
    print(f"Starting game simulation for {game_id}")
    print("=" * 50)
    
    for i, (event_type, period, team_id, metadata) in enumerate(events):
        print(f"\nEvent {i+1}/{len(events)}:")
        
        # Send the marker
        if send_scte_marker(host, port, event_type, game_id, period, team_id or 'both'):
            print(f"  ✓ {event_type.upper()} event sent")
        
        # Random delay between events (1-5 seconds)
        delay = random.uniform(1, 5)
        print(f"  Waiting {delay:.1f} seconds...")
        time.sleep(delay)
    
    print("\n" + "=" * 50)
    print("Game simulation complete!")

def main():
    parser = argparse.ArgumentParser(description='SCTE Marker Test Sender')
    parser.add_argument('--host', default='localhost', help='Target host (default: localhost)')
    parser.add_argument('--port', type=int, default=9999, help='Target UDP port (default: 9999)')
    parser.add_argument('--simulate', action='store_true', help='Run game simulation')
    parser.add_argument('--event', default='goal', help='Event type to send')
    parser.add_argument('--game', default='test_game', help='Game ID')
    parser.add_argument('--period', default='1', help='Period (1, 2, 3, OT)')
    parser.add_argument('--team', default='NYR', help='Team ID')
    parser.add_argument('--count', type=int, default=1, help='Number of markers to send')
    parser.add_argument('--delay', type=float, default=1.0, help='Delay between markers (seconds)')
    
    args = parser.parse_args()
    
    if args.simulate:
        # Run full game simulation
        simulate_game_events(args.host, args.port, args.game)
    else:
        # Send individual markers
        for i in range(args.count):
            if i > 0:
                time.sleep(args.delay)
            
            print(f"Sending marker {i+1}/{args.count}")
            send_scte_marker(
                host=args.host,
                port=args.port,
                event_type=args.event,
                game_id=args.game,
                period=args.period,
                team_id=args.team
            )
        
        print(f"\nSent {args.count} marker(s) successfully!")

if __name__ == '__main__':
    main()