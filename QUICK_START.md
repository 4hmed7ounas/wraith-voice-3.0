# WRAITH Voice-Controlled Robot - Quick Start Guide

## 🚀 Getting Started in 5 Minutes

### Step 1: Start Robot Controller (Raspberry Pi)
```bash
# SSH into your Raspberry Pi
ssh pi@192.168.1.100

# Navigate to robot controller directory
cd /path/to/robot_controller

# Run the controller
python robot_controller.py
```

**Expected Output:**
```
 * Running on http://0.0.0.0:5000
```

### Step 2: Configure Voice Bot (PC)

**Update `.env` with your Raspberry Pi's IP address:**
```bash
ROBOT_CONTROLLER_URL=http://192.168.1.100:5000  # Change to your Pi's IP
```

**Find your Pi's IP:**
```bash
# On Raspberry Pi, run:
hostname -I
```

### Step 3: Test Connection
```bash
# On PC, run:
python test_robot_integration.py
```

**Look for:**
```
✅ PASS: Robot controller is online
✅ Tests Passed: 9
```

### Step 4: Start Voice Control
```bash
# On PC, run:
python voice-bot-deepgram.py
```

**Wait for:**
```
🤖 WRAITH Voice-Controlled Robot System Ready!
🎤 Start speaking to control WRAITH...
```

### Step 5: Test Voice Commands

**Try saying:**
1. "Move forward"
2. "Stop"
3. "Turn left"
4. "Check distance"
5. "Go faster"

---

## 🎤 Voice Commands Reference

| Command | What Robot Does | Example Phrases |
|---------|----------------|-----------------|
| **Movement** | Moves in direction for 1-5 seconds | "Move forward", "Go backward", "Turn left", "Move right for 2 seconds" |
| **Stop** | Immediately stops all motors | "Stop", "Halt", "Emergency stop" |
| **Speed** | Adjusts movement speed | "Go faster", "Slow down", "Speed up" |
| **Distance** | Reads ultrasonic sensor | "Check distance", "Any obstacles?", "How far?" |
| **Auto Mode** | Toggle autonomous navigation | "Start auto mode", "Stop auto mode" |

---

## 🔧 Configuration Quick Reference

### `.env` File Settings
```bash
# Robot Connection
ROBOT_CONTROLLER_URL=http://192.168.1.100:5000  # Your Pi's IP
ROBOT_MOVEMENT_DURATION=1.0                      # Default move time (seconds)
ROBOT_REQUEST_TIMEOUT=5.0                        # HTTP timeout (seconds)
ROBOT_MAX_DURATION=5.0                           # Max move time (safety)

# API Keys (keep existing)
GROQ_API_KEY=your_groq_key
DEEPGRAM_API_KEY=your_deepgram_key
CARTESIA_API_KEY=your_cartesia_key
```

### Common IP Addresses
- **Localhost testing:** `http://localhost:5000`
- **Same WiFi network:** `http://192.168.1.X:5000`
- **Ethernet direct:** `http://169.254.X.X:5000`

---

## ⚡ Troubleshooting (30 seconds)

### Robot doesn't move?
```bash
# Check connection
curl http://192.168.1.100:5000/
# Should return: "AutoCar API Online"
```

### Voice not recognized?
- Speak clearly and wait for silence
- Check microphone is working
- Reduce background noise

### Connection timeout?
1. Check Pi IP address: `hostname -I`
2. Update `.env` with correct IP
3. Ping the Pi: `ping 192.168.1.100`

---

## 📊 Project Structure

```
wraith-voice-3.0/
├── voice-bot-deepgram.py          # Main voice bot (run on PC)
├── robot_controller.py            # Robot control (run on Pi)
├── test_robot_integration.py      # Integration tests
├── test_movement.py               # Function call tests
├── .env                            # Configuration
├── TESTING_GUIDE.md               # Detailed testing guide
├── VOICE_ROBOT_INTEGRATION_PLAN.md # Implementation details
└── QUICK_START.md                 # This file
```

---

## 🎯 Quick Test Checklist

- [ ] Robot controller running on Pi
- [ ] Integration tests pass (9/9)
- [ ] Voice bot starts without errors
- [ ] "Move forward" command works
- [ ] "Stop" command works
- [ ] Distance sensor returns reading
- [ ] Network latency < 500ms

---

## 📞 When You Need Help

1. **Check logs** - Look for errors in console output
2. **Run tests** - `python test_robot_integration.py`
3. **Verify network** - Ping the Raspberry Pi
4. **Read guides** - `TESTING_GUIDE.md` for detailed help

---

## 🎉 You're Ready!

Your voice-controlled robot is now fully operational. Start with simple commands and gradually try more complex ones.

**Example Session:**
```
You: "Move forward"
Robot: [moves forward for 1 second]
Bot: "I've moved forward."

You: "Check distance"
Bot: "The distance to the nearest obstacle is 45 centimeters."

You: "Turn left"
Robot: [turns left for 1 second]
Bot: "Turned left."
```

**Have fun controlling your robot with voice! 🚀**
