# How to Create a Video Feed with SCTE Markers (Simple Guide)

## Making a Video Stream with Special Signals

### What You're Building (Like a TV Channel)

Imagine you're making your own TV channel that shows hockey games. You need to add special invisible "beeps" that tell computers when exciting things happen!

### The Basic Parts You Need:

1. **A Camera** (or video file) - This is your hockey game video
2. **An Encoder** - This is like a machine that packages your video for the internet
3. **SCTE Inserter** - This adds the special "beeps" (markers) to your video
4. **A Streaming Server** - This sends your video to viewers

## Simple Step-by-Step Setup

### Step 1: Get Your Video Ready
```bash
# If you have a video file of a hockey game:
# hockey_game.mp4
```

### Step 2: Stream with OBS Studio (Free & Easy)
1. Download OBS Studio (it's free!)
2. Add your video or camera as a "Source"
3. Set up streaming to a local server

### Step 3: Use FFmpeg to Add SCTE Markers
Here's a simple script that creates a stream AND adds markers:

```bash
#!/bin/bash
# stream_with_markers.sh

# Start streaming your video
ffmpeg -re -i hockey_game.mp4 \
  -c:v libx264 \
  -f mpegts \
  udp://localhost:8000 &

# Every 30 seconds, send a "goal" marker
while true; do
  sleep 30
  python scte_test_sender.py --event goal --team NYR
done
```

## Even Simpler: Use a Webcam Feed

Create this Python file:

```python
# simple_stream_with_events.py
import cv2
import time
import random
import socket
import json
import threading

def send_scte_marker(event_type):
    """Send a marker to your auction system"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Create a simple message
    message = {
        'event_type': event_type,
        'game_id': 'live_game_001',
        'timestamp': time.time()
    }
    
    # Make it look like SCTE
    packet = b'\xFC' + json.dumps(message).encode()
    sock.sendto(packet, ('localhost', 9999))
    print(f"📡 Sent {event_type} signal!")

def simulate_game_events():
    """Pretend game events are happening"""
    events = ['goal', 'save', 'penalty', 'fight']
    
    while True:
        # Wait random time (10-60 seconds)
        time.sleep(random.randint(10, 60))
        
        # Pick a random event
        event = random.choice(events)
        send_scte_marker(event)

# Start the event simulator
event_thread = threading.Thread(target=simulate_game_events)
event_thread.daemon = True
event_thread.start()

# Start your "broadcast"
print("🎥 Broadcasting started! Events will trigger randomly...")
print("Press Ctrl+C to stop")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n📺 Broadcast ended!")
```

## The Simplest Test Setup

1. **Start your auction app:**
```bash
python app_scte.py
```

2. **Login as admin** and go to the SCTE dashboard
   - Username: `admin@gmail.com`
   - Password: `admin`
   - Navigate to: `http://localhost:5000/scte/dashboard`

3. **Click "Start Listener"** - Now it's waiting for signals!

4. **Run the simple broadcaster:**
```bash
python simple_stream_with_events.py
```

## What Happens (Like Magic! ✨)

1. Your "broadcast" runs
2. Every so often, it sends a signal saying "GOAL!" or "SAVE!"
3. Your auction system hears the signal
4. It instantly starts an auction for that moment
5. People's pre-set bids compete automatically
6. Winner gets their ad shown during the replay!

## Try This Fun Experiment

Be the referee and call the plays yourself!

1. Run the auction app
2. Open the SCTE dashboard
3. Use the test sender to be the "referee":

```bash
# You're the referee - call the plays!
python scte_test_sender.py --event goal   # "GOAL!"
python scte_test_sender.py --event fight  # "FIGHT!"
python scte_test_sender.py --event save   # "GREAT SAVE!"
```

Watch the dashboard light up with auctions every time you "call a play"!

## Creating a More Realistic Stream

### Option 1: Using VLC to Stream
```bash
# Stream a video file with VLC
vlc hockey_game.mp4 --sout '#rtp{dst=239.0.0.1,port=5004,mux=ts}'

# Then trigger events manually or with a script
python scte_test_sender.py --event goal
```

### Option 2: Using Python OpenCV
```python
# stream_with_manual_triggers.py
import cv2
import socket
import json
import keyboard  # pip install keyboard

def send_event(event_type):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    message = {
        'event_type': event_type,
        'game_id': 'live_stream',
        'period': '1',
        'team_id': 'NYR'
    }
    packet = b'\xFC' + json.dumps(message).encode()
    sock.sendto(packet, ('localhost', 9999))
    print(f"Sent: {event_type}")

print("Streaming... Press keys to trigger events:")
print("G = Goal | S = Save | P = Penalty | F = Fight")

# Set up keyboard triggers
keyboard.add_hotkey('g', lambda: send_event('goal'))
keyboard.add_hotkey('s', lambda: send_event('save'))
keyboard.add_hotkey('p', lambda: send_event('penalty'))
keyboard.add_hotkey('f', lambda: send_event('fight'))

# Keep running
keyboard.wait('esc')
```

## Real Professional Setup (Advanced)

When big TV companies do this, they use:

- **Elemental Live** - Professional encoder ($$$)
- **Evertz** or **Imagine** SCTE inserters
- **Wowza** or **AWS MediaLive** for streaming
- **SCTE-35 injectors** that read from automation systems

But your simple setup works the same way - just like a toy train set works like a real train, just smaller!

## Quick Reference: Event Types and Values

| Event | Marker Type | Base Auction Value |
|-------|-------------|-------------------|
| Goal | `goal` | $5,000 |
| Save | `save` | $2,500 |
| Penalty | `penalty` | $1,500 |
| Fight | `fight` | $3,500 |
| Power Play | `powerplay` | $2,000 |
| Commercial | `commercial` | $500 |
| Instant Replay | `replay` | $3,000 |

## Testing Checklist

- [ ] Start `app_scte.py`
- [ ] Login as admin
- [ ] Navigate to SCTE Dashboard
- [ ] Click "Start Listener"
- [ ] Send test marker using test sender
- [ ] Verify marker appears in dashboard
- [ ] Verify auction is created
- [ ] Check auction executes if auto-execute is on

## Troubleshooting

### "No markers received"
- Check the UDP port (default 9999) is not blocked
- Verify the listener is started in the dashboard
- Try sending a test marker from the dashboard UI

### "Auctions not triggering"
- Check auto-execute is enabled
- Verify the event_type matches supported types
- Check you haven't hit the max concurrent auctions limit

### "Connection refused"
- Make sure `app_scte.py` is running
- Check you're sending to the right port (9999)
- Verify localhost/127.0.0.1 is correct

## Fun Ideas to Try

1. **Sports Bar Mode**: Set up a tablet showing the dashboard while watching a game, manually trigger events as they happen
2. **Training Mode**: Have friends watch a game recording and compete to trigger events fastest
3. **Auto-Replay**: Use video analysis to detect goals automatically (advanced!)

That's it! You're basically a TV broadcaster now! 📺🏒