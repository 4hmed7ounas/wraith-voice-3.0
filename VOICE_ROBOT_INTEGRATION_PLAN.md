# Voice-Controlled Robot Integration Plan

## Overview
Integration plan for connecting the WRAITH voice bot (Deepgram STT + Groq LLM + Cartesia TTS) with the physical robot controller (Flask API with GPIO control).

---

## Current System Analysis

### 1. Voice Bot System (`voice-bot-deepgram.py`)
**Components:**
- **STT**: Deepgram (Speech-to-Text)
- **LLM**: Groq (llama-3.1-8b-instant) with function calling
- **TTS**: Cartesia (Text-to-Speech)
- **Current Function**: `movement(direction)` - Returns string, prints to console

**Existing Function Call Schema:**
```json
{
  "name": "movement",
  "parameters": {
    "direction": ["forward", "backward", "left", "right"]
  }
}
```

### 2. Robot Controller System (`robot_controller.py`)
**Type**: Flask REST API running on Raspberry Pi (GPIO control)

**Available Movement Functions:**
```python
move_forward(speed)   # GPIO pins 18,23,24,25
move_backward(speed)  # GPIO pins 18,23,24,25
move_left(speed)      # Differential drive - left motor backward, right forward
move_right(speed)     # Differential drive - left motor forward, right backward
stop_motors()         # Stop all motors
```

**Additional Features:**
- Speed control: `increase_speed()`, `decrease_speed()`
- Auto mode: `auto_start`, `auto_stop` (obstacle avoidance)
- Distance sensor: `get_distance()` endpoint
- Current speed: Global variable `current_speed` (default: 0.3)

**API Endpoints:**
- `POST /control` - Send commands like: `forward_start`, `forward_stop`, `backward_start`, etc.
- `GET /get_distance` - Get ultrasonic sensor reading
- `GET /get_ip` - Get robot's IP address

---

## Integration Architecture

### Option A: Direct Import (Same Machine)
```
Voice Bot → Import robot_controller functions → Direct GPIO Control
```
**Pros**: Lowest latency, no network overhead
**Cons**: Both must run on same Raspberry Pi

### Option B: HTTP Client (Network Communication) ⭐ RECOMMENDED
```
Voice Bot → HTTP Requests → Flask API → GPIO Control
```
**Pros**:
- Decoupled systems (can run on different machines)
- Robot controller can serve multiple clients
- Easier debugging and testing
- Matches existing Flask API architecture

**Cons**: Small network latency (~10-50ms)

---

## Implementation Plan

### Phase 1: HTTP Client Integration
**Goal**: Make voice bot send HTTP commands to robot controller

#### Step 1.1: Add HTTP Client to Voice Bot
- Install `httpx` or `requests` library
- Add robot controller URL configuration to `.env`:
  ```
  ROBOT_CONTROLLER_URL=http://192.168.x.x:5000
  ```

#### Step 1.2: Update Movement Function
Replace current print-only `movement()` function with actual HTTP calls:
```python
async def movement(self, direction: str) -> str:
    """Send movement command to robot via HTTP"""
    commands = {
        "forward": "forward_start",
        "backward": "backward_start",
        "left": "left_start",
        "right": "right_start"
    }

    try:
        # Send start command
        response = await http_client.post(
            f"{ROBOT_URL}/control",
            data=commands[direction]
        )

        # Wait for movement duration
        await asyncio.sleep(1.0)  # Move for 1 second

        # Send stop command
        await http_client.post(
            f"{ROBOT_URL}/control",
            data=f"{direction}_stop"
        )

        return f"Moved {direction} successfully"
    except Exception as e:
        logger.error(f"Movement error: {e}")
        return f"Failed to move {direction}"
```

#### Step 1.3: Add Movement Duration Control
Add optional parameter for movement duration:
```python
{
  "name": "movement",
  "parameters": {
    "direction": ["forward", "backward", "left", "right"],
    "duration": "optional float (default: 1.0 seconds)"
  }
}
```

### Phase 2: Enhanced Voice Commands
**Goal**: Add more robot control functions

#### Step 2.1: Speed Control Function
```python
{
  "name": "set_speed",
  "parameters": {
    "action": ["increase", "decrease", "set"],
    "value": "optional float for 'set' action"
  }
}
```

#### Step 2.2: Stop Command
```python
{
  "name": "stop",
  "description": "Immediately stop all motors"
}
```

#### Step 2.3: Query Distance
```python
{
  "name": "check_distance",
  "description": "Get distance to nearest obstacle"
}
```

#### Step 2.4: Auto Mode Control
```python
{
  "name": "auto_mode",
  "parameters": {
    "action": ["start", "stop"]
  }
}
```

### Phase 3: Safety & Error Handling

#### Step 3.1: Connection Monitoring
- Check robot controller availability on startup
- Implement retry logic with exponential backoff
- Add timeout handling (default: 5 seconds)

#### Step 3.2: Movement Safety
- Add maximum movement duration (e.g., 5 seconds)
- Emergency stop on connection loss
- Obstacle detection integration (query distance before moving)

#### Step 3.3: User Feedback
- Clear voice responses for success/failure
- Status updates during long movements
- Error explanations in simple terms

### Phase 4: Testing Strategy

#### Test 4.1: Unit Tests
```python
# test_voice_robot_integration.py
- Test HTTP connection to robot controller
- Test each movement direction
- Test stop command
- Test error handling (network failure, robot offline)
```

#### Test 4.2: Integration Tests
- Voice command → HTTP → GPIO → Movement verification
- Test with actual hardware on Raspberry Pi
- Test network latency and timeout scenarios

#### Test 4.3: Voice Recognition Tests
Test various phrasings:
- "Move forward" / "Go forward" / "Drive forward"
- "Turn left" / "Go left" / "Rotate left"
- "Stop" / "Halt" / "Emergency stop"
- "Go faster" / "Slow down"

---

## Configuration Requirements

### Environment Variables (`.env`)
```bash
# Existing
GROQ_API_KEY=xxx
DEEPGRAM_API_KEY=xxx
CARTESIA_API_KEY=xxx
GROQ_MODEL=llama-3.1-8b-instant

# New
ROBOT_CONTROLLER_URL=http://192.168.1.100:5000
ROBOT_MOVEMENT_DURATION=1.0  # seconds
ROBOT_REQUEST_TIMEOUT=5.0    # seconds
```

### Dependencies to Add
```txt
httpx>=0.24.0  # Async HTTP client
```

---

## File Structure

```
wraith-voice-3.0/
├── voice-bot-deepgram.py          # Main voice bot (UPDATE)
├── robot_controller.py            # Flask GPIO controller (NO CHANGES)
├── test_movement.py               # Basic function test (EXISTING)
├── test_voice_robot_integration.py # New integration tests (CREATE)
├── .env                            # Environment config (UPDATE)
├── requirements.txt               # Dependencies (UPDATE)
└── VOICE_ROBOT_INTEGRATION_PLAN.md # This document
```

---

## Implementation Sequence

### Minimal Viable Integration (1-2 hours)
1. ✅ Install `httpx` library
2. ✅ Add `ROBOT_CONTROLLER_URL` to `.env`
3. ✅ Update `movement()` function to send HTTP commands
4. ✅ Test with simple voice commands
5. ✅ Verify robot responds to: forward, backward, left, right

### Full Integration (4-6 hours)
1. ✅ Complete Phase 1 (HTTP Client Integration)
2. ✅ Add speed control and stop commands (Phase 2.1 - 2.2)
3. ✅ Implement safety features (Phase 3.1 - 3.2)
4. ✅ Write integration tests (Phase 4.1 - 4.2)
5. ✅ Test on actual hardware

### Advanced Features (Optional)
1. ⏳ Distance queries and obstacle awareness
2. ⏳ Auto mode voice control
3. ⏳ Multi-step commands ("Move forward then turn left")
4. ⏳ Natural language duration ("Move forward for 3 seconds")

---

## Risk Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| Network latency | Medium | Use local network, add timeout handling |
| Robot offline | High | Check availability on startup, clear error messages |
| Wrong direction mapping | High | Test thoroughly, add confirmation responses |
| Runaway robot | Critical | Max duration limits, emergency stop command |
| Voice misrecognition | Medium | Use confirmation before critical actions |

---

## Success Criteria

### Minimum Success
- ✅ Voice commands control robot movement in 4 directions
- ✅ Robot stops after reasonable duration
- ✅ Clear voice feedback on success/failure

### Full Success
- ✅ All movement commands working
- ✅ Speed control via voice
- ✅ Emergency stop command
- ✅ Safe error handling
- ✅ < 500ms latency from voice → movement

### Stretch Goals
- ✅ Natural language understanding ("Go forward a bit")
- ✅ Complex multi-step commands
- ✅ Obstacle awareness integration
- ✅ Voice-controlled autonomous mode

---

## Next Steps

**Ready to implement?** Here's what I recommend:

1. **Quick Test First**: Start with Phase 1 minimal integration
   - Update `movement()` function to send HTTP commands
   - Test with robot controller running on Raspberry Pi
   - Verify basic 4-direction control works

2. **Then Expand**: Add safety and enhanced features
   - Stop command, duration control, error handling
   - Speed control and status queries

3. **Deploy & Test**: Real-world testing
   - Test on actual robot hardware
   - Iterate based on voice recognition accuracy
   - Fine-tune movement durations

Would you like me to proceed with implementing Phase 1?
