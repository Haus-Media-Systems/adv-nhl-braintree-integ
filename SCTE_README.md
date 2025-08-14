# SCTE-35/104 Integration for NHL Auction Platform

This is a fork of the NHL Instant Replay Bidding Platform that integrates SCTE-35/104 marker detection to trigger real-time auctions based on video stream events.

## Overview

SCTE-35/104 markers are industry-standard signals embedded in video streams to indicate events like commercial breaks, program boundaries, and custom metadata. This integration uses these markers to automatically trigger instant auctions when specific game events occur.

## Features

- **Real-time SCTE marker detection** via UDP listener
- **Automatic auction triggering** based on marker metadata
- **Event-to-auction mapping** for different game moments:
  - Goals → High-value auctions ($5,000 base)
  - Saves → Medium-value auctions ($2,500 base)
  - Penalties → Standard auctions ($1,500 base)
  - Fights → High-interest auctions ($3,500 base)
  - Power plays → Enhanced auctions ($2,000 base)
  - Commercial breaks → Lower-value auctions ($500 base)
  - Instant replays → Premium auctions ($3,000 base)
- **SCTE monitoring dashboard** for administrators
- **Test marker sender** for development and testing
- **Configurable auction parameters** based on event importance

## Installation

1. Install the same requirements as the base application:
```bash
pip install -r requirements.txt
```

2. Run the SCTE-enabled version:
```bash
python app_scte.py
```

## Configuration

The SCTE integration can be configured through:

1. **Web Interface**: Navigate to `/scte/config` when logged in as admin
2. **Default Settings** in `app_scte.py`:
```python
scte_config = {
    'enabled': True,
    'udp_port': 9999,
    'auto_execute': True,
    'max_concurrent_auctions': 10,
    'auction_duration_ms': 500,
}
```

## Usage

### Starting the SCTE Listener

1. Log in as an administrator
2. Navigate to `/scte/dashboard`
3. Click "Start Listener" to begin monitoring for SCTE markers

### Sending Test Markers

Use the included test sender script:

```bash
# Send a single test marker
python scte_test_sender.py --event goal --team NYR --period 1

# Simulate a full game with various events
python scte_test_sender.py --simulate

# Send multiple markers with delay
python scte_test_sender.py --count 5 --delay 2 --event save
```

### SCTE Marker Format

The system expects SCTE markers with embedded JSON metadata:

```json
{
    "event_type": "goal",
    "game_id": "game_001",
    "period": "2",
    "team_id": "NYR",
    "player_ids": ["player_123"],
    "is_overtime": false,
    "is_playoffs": false,
    "star_player": true
}
```

## API Endpoints

### SCTE-Specific Routes

- `GET /scte/dashboard` - SCTE monitoring dashboard (admin only)
- `POST /scte/start` - Start the SCTE listener
- `POST /scte/stop` - Stop the SCTE listener
- `GET/POST /scte/config` - Configure SCTE settings
- `POST /scte/test` - Send a test SCTE marker
- `GET /scte/markers` - Get list of received markers (JSON)
- `GET /scte/auctions` - Get list of SCTE-triggered auctions (JSON)

## How It Works

1. **SCTE Listener**: A UDP socket listens on port 9999 for incoming SCTE-35 packets
2. **Marker Parsing**: Packets are parsed to extract command type and embedded metadata
3. **Event Mapping**: Metadata is analyzed to determine the auction trigger type
4. **Auction Creation**: An instant auction is created with parameters based on the event
5. **Auto-Execution**: If enabled, the auction executes immediately (500ms duration)
6. **Strategy Matching**: User strategies automatically bid based on their configurations
7. **Result Processing**: Winners are determined and payments are processed

## Testing

### Manual Testing

1. Start the Flask application:
```bash
python app_scte.py
```

2. Log in as admin (username: admin@gmail.com, password: admin)

3. Navigate to SCTE Dashboard: http://localhost:5000/scte/dashboard

4. Start the SCTE listener

5. In another terminal, send test markers:
```bash
python scte_test_sender.py --event goal --team NYR
```

6. Watch the dashboard update with received markers and triggered auctions

### Automated Testing

Run the game simulation to test multiple events:
```bash
python scte_test_sender.py --simulate
```

This will send a sequence of game events with random delays, simulating a real game.

## Integration with Video Streams

To integrate with actual video streams:

1. Configure your video encoder to send SCTE-35 markers to the platform's UDP port
2. Ensure markers include the required JSON metadata in the private data section
3. Map your event detection system to the supported event types
4. Adjust auction values and importance levels based on your requirements

## Monitoring

The SCTE dashboard provides real-time monitoring of:
- Listener status and configuration
- Received SCTE markers with timestamps
- Triggered auctions and their status
- Success rates and statistics

## Troubleshooting

### Listener Won't Start
- Check if port 9999 is available: `lsof -i :9999`
- Ensure you have admin privileges
- Check firewall settings

### No Markers Received
- Verify UDP packets are reaching the server: `tcpdump -i any -n port 9999`
- Check the marker format matches SCTE-35 specification
- Ensure metadata is properly JSON-encoded

### Auctions Not Triggering
- Verify event_type in metadata matches supported types
- Check max_concurrent_auctions limit hasn't been reached
- Ensure auto_execute is enabled for instant auctions

## Security Considerations

- The UDP listener binds to all interfaces (0.0.0.0) - consider restricting to specific IPs
- Validate and sanitize all incoming SCTE marker data
- Implement rate limiting to prevent auction flooding
- Use authentication for production deployments

## Future Enhancements

- Support for SCTE-104 (API-based triggers)
- Machine learning for dynamic auction value adjustment
- Multi-stream support for concurrent games
- WebSocket updates for real-time dashboard
- Integration with actual broadcast systems
- Support for HLS/DASH manifest manipulation

## License

Same as the parent project - for demonstration and educational purposes.