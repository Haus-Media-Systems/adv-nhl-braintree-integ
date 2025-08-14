# SCTE NHL Auction Platform

A production-ready, SCTE-35/104 integrated NHL instant replay bidding platform that triggers real-time auctions based on video stream markers.

## 🚀 Features

### SCTE Integration
- **Real-time SCTE-35/104 marker detection** via UDP listener
- **Automatic auction triggering** based on marker metadata
- **Context-aware pricing** with dynamic value adjustments
- **Professional-grade error handling** and monitoring
- **Configurable event mappings** and thresholds

### Auction System
- **Millisecond auction execution** (500ms default)
- **Strategy-based automated bidding** 
- **Concurrent auction management** (configurable limits)
- **Payment processing** via Braintree integration
- **Comprehensive auction analytics**

### Event Types Supported
| Event | Base Value | Importance | Context Multipliers |
|-------|------------|------------|-------------------|
| Goal Scored | $5,000 | Critical | Overtime (+50%), Playoffs (+100%) |
| Power Play Goal | $6,000 | Critical | Star Player (+25%) |
| Short-handed Goal | $7,000 | Critical | Rivalry (+30%) |
| Shootout Goal | $8,000 | Critical | Close Game (+40%) |
| Spectacular Save | $2,500 | High | Late Period (+20%) |
| Fight | $3,500 | High | Finals (+200%) |
| Instant Replay | $3,000 | High | |
| Penalty | $1,500 | Normal | |
| Power Play | $2,000 | Normal | |
| Commercial Break | $500 | Low | |

## 📁 Directory Structure

```
SCTE/
├── main.py              # Application entry point
├── app.py               # Core Flask application with SCTE classes
├── routes.py            # Flask routes and API endpoints
├── auction_engine.py    # Auction logic and strategy processing
├── storage.py           # Data persistence utilities
├── braintree_config.py  # Payment processing configuration
├── requirements.txt     # Python dependencies
├── README.md           # This file
├── config/
│   └── scte_config.json # SCTE system configuration
├── data/               # JSON data files
├── templates/          # HTML templates
│   ├── base.html       # Base template with SCTE indicators
│   ├── index.html      # Homepage with system status
│   ├── scte_dashboard.html
│   └── ...
├── static/             # CSS, JS, images
├── tools/
│   └── scte_sender.py  # Advanced testing utility
└── logs/              # Application logs
```

## 🛠 Installation & Setup

### Prerequisites
- Python 3.8+
- Virtual environment (recommended)
- Network access for UDP port 9999
- Braintree sandbox account

### Quick Start

```bash
# Navigate to SCTE directory
cd SCTE

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create required directories
mkdir -p logs config

# Start the application
python main.py
```

The application will start on `http://localhost:5000` with SCTE listener auto-enabled.

### Environment Variables

```bash
export FLASK_DEBUG=True          # Enable debug mode
export FLASK_HOST=0.0.0.0        # Bind address
export FLASK_PORT=5000           # Port number
export SECRET_KEY=your_secret    # Flask secret key
```

## ⚙️ Configuration

### SCTE Configuration
The system uses `config/scte_config.json` for configuration:

```json
{
  "listener": {
    "enabled": true,
    "udp_port": 9999,
    "bind_address": "0.0.0.0",
    "buffer_size": 4096,
    "timeout": 1.0
  },
  "auctions": {
    "auto_execute": true,
    "max_concurrent": 10,
    "default_duration_ms": 500,
    "min_duration_ms": 100,
    "max_duration_ms": 5000
  },
  "triggers": {
    "goal_scored": {
      "base_value": 5000,
      "importance": "critical",
      "multiplier": 1.0
    }
    // ... other trigger configurations
  },
  "context_modifiers": {
    "is_overtime": 1.5,
    "is_playoffs": 2.0,
    "star_player": 1.25,
    "close_game": 1.4
  }
}
```

### Web Configuration
Access `/scte/config` as admin to modify settings through the web interface.

## 🧪 Testing

### Manual Testing with Web Interface
1. Start the application: `python main.py`
2. Login as admin (`admin@scte.com` / `admin`)
3. Navigate to SCTE Dashboard
4. Use "Send Test Marker" to simulate events

### Command Line Testing

```bash
# Send single test marker
python tools/scte_sender.py --event goal --team NYR

# Simulate complete game
python tools/scte_sender.py --simulate --home-team NYR --away-team BOS

# Stress test the system
python tools/scte_sender.py --stress --duration 60 --rate 5

# Send batch of events
python tools/scte_sender.py --batch
```

### SCTE Marker Format
The system expects SCTE-35 packets with JSON metadata:

```json
{
  "event_type": "goal",
  "game_id": "nyr_vs_bos_20250114",
  "period": "2",
  "team_id": "NYR",
  "player_ids": ["player_123"],
  "is_overtime": false,
  "is_playoffs": true,
  "star_player": true,
  "close_game": true,
  "timestamp": "2025-01-14T20:30:45.123Z"
}
```

## 📊 Monitoring & Analytics

### Real-time Dashboard
- **SCTE Listener Status**: Active/inactive with packet statistics
- **Live Auction Feed**: Active auctions and recent completions
- **Performance Metrics**: Markers per second, success rates
- **System Health**: Queue sizes, processing times

### API Endpoints
- `GET /api/live-stats` - Real-time system statistics
- `GET /scte/markers` - Recent SCTE markers (admin)
- `GET /scte/auctions` - SCTE-triggered auctions (admin)

### Logging
Comprehensive logging to `logs/scte_auction.log`:
- SCTE marker processing
- Auction creation and execution
- Error tracking and debugging
- Performance metrics

## 🔗 Integration Guide

### Broadcast System Integration

#### Elemental Live/MediaLive
```yaml
# SCTE-35 Output Configuration
scte35_source: markers
output_format: udp
destination: your-auction-server:9999
metadata_insertion: json_private_data
```

#### Wowza Streaming Engine
```xml
<!-- StreamingEngine.xml -->
<SCTEOutput>
  <Enabled>true</Enabled>
  <UDPHost>your-auction-server</UDPHost>
  <UDPPort>9999</UDPPort>
  <MetadataFormat>json</MetadataFormat>
</SCTEOutput>
```

#### Custom UDP Integration
```python
import socket
import json

def send_scte_marker(event_data):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Create SCTE-35 packet with JSON metadata
    metadata = json.dumps(event_data).encode()
    packet = b'\xFC' + b'\x00' * 19 + metadata
    
    sock.sendto(packet, ('auction-server', 9999))
    sock.close()

# Example usage
send_scte_marker({
    'event_type': 'goal',
    'game_id': 'live_game_001',
    'team_id': 'NYR',
    'period': '2'
})
```

## 🚀 Production Deployment

### Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000 9999/udp

CMD ["python", "main.py"]
```

### Systemd Service
```ini
[Unit]
Description=SCTE NHL Auction Platform
After=network.target

[Service]
Type=simple
User=scte
WorkingDirectory=/opt/scte-auction
ExecStart=/opt/scte-auction/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### Load Balancer Configuration
```nginx
upstream scte_auction {
    server 127.0.0.1:5000;
    server 127.0.0.1:5001;
}

server {
    listen 80;
    server_name scte-auction.example.com;
    
    location / {
        proxy_pass http://scte_auction;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# UDP load balancing for SCTE markers
stream {
    upstream scte_udp {
        server 127.0.0.1:9999;
        server 127.0.0.1:9998;
    }
    
    server {
        listen 9999 udp;
        proxy_pass scte_udp;
    }
}
```

## 🔧 Troubleshooting

### Common Issues

#### SCTE Listener Won't Start
```bash
# Check port availability
sudo lsof -i :9999

# Check permissions
sudo ufw allow 9999/udp

# Verify configuration
grep -A 5 "listener" config/scte_config.json
```

#### No Markers Received
```bash
# Test UDP connectivity
nc -u localhost 9999 < test_marker.bin

# Monitor network traffic
sudo tcpdump -i any -n port 9999

# Check logs
tail -f logs/scte_auction.log | grep -i marker
```

#### Auctions Not Triggering
```bash
# Verify auto-execute setting
grep "auto_execute" config/scte_config.json

# Check concurrent auction limits
curl http://localhost:5000/api/live-stats

# Test with known good marker
python tools/scte_sender.py --event goal
```

### Performance Tuning

#### High-Frequency Markers
```json
{
  "listener": {
    "buffer_size": 8192,
    "timeout": 0.1
  },
  "auctions": {
    "max_concurrent": 20,
    "default_duration_ms": 250
  }
}
```

#### Resource Optimization
```python
# Increase worker threads
export FLASK_RUN_OPTIONS="--threaded"

# Enable garbage collection tuning
export PYTHONOPTIMIZE=1

# Adjust logging level
export LOG_LEVEL=WARNING
```

## 📈 Scaling Considerations

### Multi-Instance Deployment
- Use Redis for shared state
- Implement proper load balancing
- Consider database clustering
- Monitor UDP packet distribution

### High Availability
- Deploy across multiple availability zones
- Implement health checks
- Use database replication
- Monitor system metrics

## 🔐 Security

### Network Security
- Restrict UDP port access to trusted sources
- Use VPN/private networks for marker traffic
- Implement rate limiting
- Monitor for anomalous traffic

### Application Security
- Regular security updates
- Input validation and sanitization
- HTTPS/TLS encryption
- Database connection security

## 📞 Support

### Documentation
- API Reference: `/docs` endpoint
- Configuration Guide: See `config/` directory
- Integration Examples: `tools/` directory

### Monitoring
- Health Check: `GET /health`
- Metrics: `GET /metrics`
- Logs: `logs/scte_auction.log`

---

**Built for Production** • **SCTE-35/104 Compliant** • **Real-time Performance** • **Scalable Architecture**