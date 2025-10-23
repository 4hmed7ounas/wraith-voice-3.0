# WRAITH Voice-Controlled Robot - Testing Guide

## Overview
Complete testing guide for the voice-controlled robot integration system.

---

## Prerequisites

### Hardware Setup
1. **Raspberry Pi** with GPIO access running `robot_controller.py`
2. **Motor drivers** (BTS7960) properly connected
3. **Ultrasonic sensor** connected to GPIO pins
4. **Network connection** between PC and Raspberry Pi

### Software Requirements
```bash
# On PC (Voice Bot)
- Python 3.8+
- All dependencies from requirements.txt installed
- Microphone and speakers connected
- API keys configured in .env

# On Raspberry Pi (Robot Controller)
- Python 3.8+
- Flask, gpiozero installed
- robot_controller.py running on port 5000
```

### Configuration
Ensure `.env` file has correct robot URL:
```bash
ROBOT_CONTROLLER_URL=http://192.168.1.100:5000  # Update with your Pi's IP
ROBOT_MOVEMENT_DURATION=1.0
ROBOT_REQUEST_TIMEOUT=5.0
ROBOT_MAX_DURATION=5.0
```

---

## Testing Levels

### Level 1: Robot Controller Only (Raspberry Pi)

**Start the robot controller:**
```bash
# On Raspberry Pi
python robot_controller.py
```

**Expected output:**
```
 * Serving Flask app 'robot_controller'
 * Running on http://0.0.0.0:5000
```

**Test with curl:**
```bash
# From any machine on the network
curl http://192.168.1.100:5000/

# Expected: "AutoCar API Online"
```

---

### Level 2: HTTP Integration Tests

**Purpose:** Verify voice bot can communicate with robot controller

**Run from PC:**
```bash
cd E:\FYP\wraith-voice-3.0
.venv\Scripts\python test_robot_integration.py
```

**Expected Output:**
```
======================================================================
WRAITH Robot Integration Test Suite
======================================================================
Robot Controller URL: http://192.168.1.100:5000
Timeout: 5.0s
======================================================================

[TEST 1] Testing robot controller connection...
  ✅ PASS: Robot controller is online
     Response: AutoCar API Online

[TEST 2-5] Testing all movement directions...

[TEST] Testing forward movement...
  ✅ Start command sent: forward_start
  ✅ Stop command sent: forward_stop
  ✅ PASS: FORWARD movement test successful

[TEST] Testing backward movement...
  ✅ Start command sent: backward_start
  ✅ Stop command sent: backward_stop
  ✅ PASS: BACKWARD movement test successful

[TEST] Testing left movement...
  ✅ Start command sent: left_start
  ✅ Stop command sent: left_stop
  ✅ PASS: LEFT movement test successful

[TEST] Testing right movement...
  ✅ Start command sent: right_start
  ✅ Stop command sent: right_stop
  ✅ PASS: RIGHT movement test successful

[TEST 6] Testing speed control...
  ✅ Speed increased
  ✅ Speed decreased
  ✅ PASS: Speed control test successful

[TEST 7] Testing distance sensor...
  ✅ Distance reading: 45.23 cm
  ✅ PASS: Distance sensor test successful

[TEST 8] Testing auto mode control...
  ✅ Auto mode started
  ✅ Auto mode stopped
  ✅ PASS: Auto mode test successful

[TEST 9] Testing timeout/error handling...
  ✅ Timeout/error handled correctly
  ✅ PASS: Error handling test successful

======================================================================
TEST SUMMARY
======================================================================
✅ Tests Passed: 9
❌ Tests Failed: 0
📊 Success Rate: 100.0%
======================================================================
🎉 ALL TESTS PASSED! Voice-robot integration is ready!
======================================================================
```

**Troubleshooting Test Failures:**

| Error | Cause | Solution |
|-------|-------|----------|
| Connection timeout | Robot not running | Start `robot_controller.py` on Pi |
| Wrong IP address | Incorrect URL in .env | Update `ROBOT_CONTROLLER_URL` |
| Movement commands fail | GPIO permission issue | Run robot controller with sudo |
| Distance sensor fail | Sensor not connected | Check GPIO pins 20, 21 |

---

### Level 3: Function Calling Tests

**Purpose:** Verify Groq LLM correctly calls movement functions

**Run from PC:**
```bash
.venv\Scripts\python test_movement.py
```

**Expected Output:**
```
============================================================
Testing Movement Function Calls
============================================================

Testing: 'move forward'
------------------------------------------------------------
[SUCCESS] Function Called: movement
Arguments: {'direction': 'forward'}
Direction: FORWARD

Testing: 'go backward'
------------------------------------------------------------
[SUCCESS] Function Called: movement
Arguments: {'direction': 'backward'}
Direction: BACKWARD

Testing: 'turn left'
------------------------------------------------------------
[SUCCESS] Function Called: movement
Arguments: {'direction': 'left'}
Direction: LEFT

Testing: 'move right'
------------------------------------------------------------
[SUCCESS] Function Called: movement
Arguments: {'direction': 'right'}
Direction: RIGHT

============================================================
Test Complete!
============================================================
```

**What this tests:**
- Groq API function calling setup
- Parameter extraction from natural language
- Function schema validation

---

### Level 4: Voice Bot Integration (Full System)

**Purpose:** Test complete voice → robot movement pipeline

**Setup:**
1. Ensure robot controller is running on Raspberry Pi
2. Connect microphone and speakers to PC
3. Ensure quiet environment for speech recognition

**Run from PC:**
```bash
.venv\Scripts\python voice-bot-deepgram.py
```

**Expected Startup Output:**
```
============================================================
🤖 WRAITH Voice-Controlled Robot System Ready!
============================================================
📡 Pipeline: Deepgram STT → Groq (llama-3.1-8b-instant) → Cartesia TTS
🤖 Robot Controller: http://192.168.1.100:5000
⏱️ Movement Duration: 1.0s (max: 5.0s)
✨ Advanced autonomous service robot - FAST NUCES, Pakistan

Available Voice Commands:
  • Movement: 'move forward/backward/left/right'
  • Stop: 'stop', 'halt', 'emergency stop'
  • Speed: 'go faster', 'slow down'
  • Distance: 'check distance', 'any obstacles?'
  • Auto Mode: 'start auto mode', 'stop auto mode'

🎤 Start speaking to control WRAITH...
Press Ctrl+C to stop
============================================================
```

---

## Voice Command Test Cases

### Test Case 1: Basic Movement
**Say:** "Move forward"

**Expected Behavior:**
1. Speech recognized: "Move forward"
2. LLM calls `movement(direction="forward")`
3. Robot moves forward for 1 second
4. Robot stops
5. Voice response: "Moved forward for 1 second" or similar

**Log Output:**
```
👤 User: Move forward
🔧 Function call: movement({'direction': 'forward'})
🚀 MOVEMENT: FORWARD for 1.0s
✅ Moving forward...
✅ Movement forward completed
🤖 Bot: I've moved forward for you.
```

### Test Case 2: Movement with Duration
**Say:** "Move backward for 3 seconds"

**Expected Behavior:**
1. LLM calls `movement(direction="backward", duration=3.0)`
2. Robot moves backward for 3 seconds
3. Robot stops
4. Voice response confirms action

### Test Case 3: Emergency Stop
**Say:** "Stop" (while robot is moving)

**Expected Behavior:**
1. LLM calls `stop()`
2. All motors immediately halt
3. Voice response: "All motors stopped"

**Log Output:**
```
👤 User: Stop
🔧 Function call: stop({})
🛑 EMERGENCY STOP CALLED
✅ All motors stopped
🤖 Bot: I've stopped all motors.
```

### Test Case 4: Speed Control
**Say:** "Go faster"

**Expected Behavior:**
1. LLM calls `set_speed(action="increase")`
2. Robot speed increases by 0.1
3. Voice response confirms speed change

**Say:** "Slow down"

**Expected Behavior:**
1. LLM calls `set_speed(action="decrease")`
2. Robot speed decreases by 0.1
3. Voice response confirms speed change

### Test Case 5: Distance Check
**Say:** "Check distance" or "Any obstacles?"

**Expected Behavior:**
1. LLM calls `check_distance()`
2. Ultrasonic sensor queried
3. Voice response: "Distance to obstacle: X centimeters"

**Log Output:**
```
👤 User: Check distance
🔧 Function call: check_distance({})
📏 CHECKING DISTANCE
📏 Distance: 45.2 cm
🤖 Bot: The distance to the nearest obstacle is 45.2 centimeters.
```

### Test Case 6: Autonomous Mode
**Say:** "Start auto mode"

**Expected Behavior:**
1. LLM calls `auto_mode(action="start")`
2. Robot enters autonomous navigation
3. Robot avoids obstacles automatically
4. Voice response confirms auto mode started

**Say:** "Stop auto mode"

**Expected Behavior:**
1. LLM calls `auto_mode(action="stop")`
2. Autonomous navigation stops
3. Voice response confirms auto mode stopped

---

## Natural Language Variations

Test that the system understands different phrasings:

### Movement Commands
- ✅ "Move forward" / "Go forward" / "Drive forward"
- ✅ "Move backward" / "Go backward" / "Reverse"
- ✅ "Turn left" / "Go left" / "Rotate left"
- ✅ "Turn right" / "Go right" / "Rotate right"

### Stop Commands
- ✅ "Stop" / "Halt" / "Emergency stop" / "Stop moving"

### Speed Commands
- ✅ "Go faster" / "Speed up" / "Increase speed"
- ✅ "Slow down" / "Go slower" / "Decrease speed"

### Distance Queries
- ✅ "Check distance" / "How far?" / "Any obstacles?"
- ✅ "What's ahead?" / "Is anything in front?"

---

## Performance Benchmarks

### Target Metrics
| Metric | Target | How to Measure |
|--------|--------|----------------|
| Voice → Movement Latency | < 2s | Time from speech end to robot start |
| HTTP Request Latency | < 100ms | Check test_robot_integration.py |
| Speech Recognition Accuracy | > 90% | Test 10 commands, count successes |
| Function Call Accuracy | > 95% | LLM correctly identifies command |

### Measuring Latency
```python
import time

# In voice-bot-deepgram.py, add timing:
start_time = time.time()
# ... movement code ...
elapsed = time.time() - start_time
logger.info(f"⏱️ Total latency: {elapsed:.2f}s")
```

---

## Troubleshooting Guide

### Issue: Voice bot says "Robot connection timeout"

**Causes:**
1. Robot controller not running
2. Wrong IP address in .env
3. Network connectivity issue

**Solutions:**
```bash
# 1. Check robot controller is running
ssh pi@192.168.1.100
ps aux | grep robot_controller

# 2. Test connectivity
ping 192.168.1.100

# 3. Test HTTP endpoint
curl http://192.168.1.100:5000/

# 4. Check firewall
# On Raspberry Pi:
sudo ufw status
sudo ufw allow 5000
```

### Issue: Robot doesn't move but no errors

**Causes:**
1. Motors not enabled in robot_controller.py
2. GPIO permissions issue
3. Motor drivers not powered

**Solutions:**
```bash
# Run with sudo for GPIO access
sudo python robot_controller.py

# Check GPIO pins
gpio readall

# Verify motor driver power supply
```

### Issue: Speech not recognized correctly

**Causes:**
1. Background noise
2. Microphone quality
3. VAD settings too sensitive

**Solutions:**
```python
# In voice-bot-deepgram.py, adjust VAD:
params=VADParams(
    stop_secs=1.5,      # Increase if cutting off
    min_volume=0.85,    # Increase if too sensitive
    start_secs=0.3,
    confidence=0.8,
)
```

### Issue: Robot moves but doesn't stop

**Causes:**
1. Stop command not sent
2. Network interruption during movement
3. Exception in movement function

**Solutions:**
- Check logs for errors
- Ensure try/finally blocks send stop commands
- Test emergency stop separately

---

## Safety Checklist

Before testing with the physical robot:

- [ ] Robot on stable surface with clearance
- [ ] Emergency stop tested and working
- [ ] Maximum duration limit configured (5s)
- [ ] Obstacle sensors functional
- [ ] Network connection stable
- [ ] Someone ready to physically stop robot if needed
- [ ] No people/objects in robot's path
- [ ] Battery/power supply adequate

---

## Quick Test Procedure

**5-Minute Quick Test:**

1. **Start robot controller** (30s)
   ```bash
   ssh pi@192.168.1.100
   python robot_controller.py
   ```

2. **Run integration tests** (2 min)
   ```bash
   python test_robot_integration.py
   ```

3. **Test voice control** (2 min)
   ```bash
   python voice-bot-deepgram.py
   # Say: "Move forward"
   # Say: "Stop"
   # Say: "Turn left"
   # Say: "Check distance"
   ```

4. **Verify logs** (30s)
   - Check for errors
   - Verify function calls
   - Confirm robot responses

---

## Continuous Testing

**Run tests regularly:**
```bash
# Before each development session
python test_robot_integration.py

# After code changes
python test_movement.py

# Weekly full system test
python voice-bot-deepgram.py
# Test all voice commands systematically
```

---

## Test Results Log Template

```
Date: _____________
Tester: _____________
Robot Serial: _____________

Integration Tests (test_robot_integration.py):
  [ ] Connection test passed
  [ ] Forward movement passed
  [ ] Backward movement passed
  [ ] Left movement passed
  [ ] Right movement passed
  [ ] Speed control passed
  [ ] Distance sensor passed
  [ ] Auto mode passed
  [ ] Error handling passed

Voice Command Tests:
  [ ] "Move forward" - worked / failed
  [ ] "Stop" - worked / failed
  [ ] "Go faster" - worked / failed
  [ ] "Check distance" - worked / failed
  [ ] "Start auto mode" - worked / failed

Performance:
  Voice→Movement latency: _____ seconds
  HTTP latency: _____ ms
  Recognition accuracy: _____ %

Issues Found:
_____________________________________
_____________________________________

Notes:
_____________________________________
_____________________________________
```

---

## Next Steps After Successful Testing

1. ✅ Fine-tune movement durations for your specific robot
2. ✅ Calibrate distance sensor thresholds
3. ✅ Add custom voice commands for your use case
4. ✅ Implement multi-step command sequences
5. ✅ Add confirmation for critical commands
6. ✅ Integrate with SLAM/navigation systems

---

## Support

If tests fail and you can't resolve:
1. Check all logs in console output
2. Review `VOICE_ROBOT_INTEGRATION_PLAN.md`
3. Verify hardware connections
4. Test components individually
5. Check network connectivity

**Good luck with testing! 🚀**
