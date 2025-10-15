# Voice Bot Setup Guide

## Understanding the Components

### Speech-to-Text (STT)

**What we're using:** Daily.co's built-in transcription service

**How it works:**
1. User speaks into microphone
2. Daily.co WebRTC captures audio
3. Daily automatically transcribes speech to text
4. Text is sent to your bot via `transport.capture_participant_transcription()`

**Why Daily?** It handles:
- Audio streaming (WebRTC)
- Speech-to-text conversion
- Voice activity detection
- Multiple participants
- Cross-platform support (web, mobile, desktop)

**You don't need a separate STT service** - Daily does it all!

### What Daily.co Does

Daily.co is a **WebRTC platform** that provides:

1. **Audio Transport**: Real-time audio streaming
2. **Transcription**: Automatic speech-to-text
3. **Room Management**: Virtual "rooms" where users connect
4. **Multi-platform**: Works in browsers, iOS, Android, etc.

**In voice-bot.py:**
- Line 108: `transcription_enabled=True` - Enables automatic STT
- Line 132: `await transport.capture_participant_transcription()` - Captures the text

### Architecture Flow

```
User speaks
    ↓
Daily.co captures audio (WebRTC)
    ↓
Daily.co transcribes to text (automatic STT)
    ↓
Text → Gemini LLM
    ↓
Gemini generates response text
    ↓
Cartesia TTS converts to audio
    ↓
Audio → Daily.co → User hears it
```

---

## Getting Daily.co API Key

### Step 1: Create Account

1. Go to https://dashboard.daily.co/u/signup
2. Sign up (free tier: 10,000 minutes/month)
3. Verify email

### Step 2: Get API Key

1. Go to https://dashboard.daily.co/developers
2. Click **"Create API key"**
3. Copy the key (starts with a long string)
4. Add to `.env`:
   ```
   DAILY_API_KEY=your_key_here
   ```

### Step 3: Test Your Key

```bash
# Test API key works
curl -H "Authorization: Bearer YOUR_DAILY_API_KEY" https://api.daily.co/v1/
```

Should return: `{"info":"Daily.co REST API"}`

---

## Complete Installation

### 1. Fix the Dependency Error

The error you got is because pip can't resolve `pipecat-ai` dependencies.

**Solution:** I've updated `requirements.txt` to specify exact versions.

```bash
pip install -r requirements.txt
```

If still fails, try:
```bash
pip install --upgrade pip
pip install daily-python==0.19.9
pip install pipecat-ai[cartesia,google,silero,runner]==0.0.87
```

### 2. Configure API Keys

Edit `.env`:
```bash
# Required
DAILY_API_KEY=your_daily_key_here
GEMINI_API_KEY=AIzaSyDqb0snGfu29Zri5WUaTacueg2MwHWPEKs
CARTESIA_API_KEY=sk_car_uhuozDmZUZahvQS7FqCekc

# Optional (for development)
DAILY_SAMPLE_ROOM_URL=
DAILY_SAMPLE_ROOM_TOKEN=
```

### 3. Run the Bot

```bash
python voice-bot.py --transport daily
```

**Expected output:**
```
INFO: Starting bot...
INFO: Creating Daily room...
INFO: Room URL: https://yourcompany.daily.co/abc-123
INFO: Waiting for participant...
```

### 4. Connect as User

**Option A: Browser (simplest)**
1. Copy the room URL from bot output
2. Open in Chrome/Firefox
3. Allow microphone access
4. Start speaking!

**Option B: Test with Daily Prebuilt**
1. Go to https://app.daily.co
2. Create a test room
3. Join the room
4. Give room URL to bot via `DAILY_SAMPLE_ROOM_URL`

---

## Why the Error Happened

**The error:**
```
ERROR: Cannot install pipecat-ai>=0.0.82 because these package
versions have conflicting dependencies.
```

**Reason:**
- `pipecat-ai[daily]` requires `daily-python~=0.19.9`
- Using `>=0.0.82` caused pip to check ALL versions (0.82, 0.83, 0.84, 0.85, 0.86, 0.87)
- Each version has slightly different dependency requirements
- Pip couldn't find a combination that satisfies all constraints

**Fix:**
Pin to specific version: `==0.0.87` (latest stable)

---

## Testing Without Daily (Alternative)

If you want to test without Daily:

### Option 1: Use Console Transport (Text-only)

```python
# Add at top of voice-bot.py
from pipecat.transports.console.transport import ConsoleTransport

# Replace DailyTransport with:
transport = ConsoleTransport()
```

This lets you type text instead of speaking (no STT/TTS).

### Option 2: Use Local Audio (No Daily)

You'd need:
- Local microphone input (PyAudio)
- Local STT service (Deepgram/Whisper)
- Local speaker output

But this is **much more complex** - Daily makes it easy!

---

## Common Issues

### Issue: "Invalid API key"
**Solution:** Double-check your Daily API key:
- Go to https://dashboard.daily.co/developers
- Regenerate key if needed
- Make sure no extra spaces in `.env`

### Issue: "Room not found"
**Solution:** Bot creates rooms automatically. If using custom room:
- Verify `DAILY_SAMPLE_ROOM_URL` is correct
- Check room hasn't expired (Daily rooms expire after 24h by default)

### Issue: "No audio output"
**Solution:**
- Check Cartesia API key has credits
- Verify browser microphone permissions
- Check bot logs for TTS errors

### Issue: Bot hears itself talking
**Solution:** Daily handles echo cancellation automatically, but if issue persists:
- Check transport settings
- Ensure `audio_in_enabled` and `audio_out_enabled` are separate

---

## API Keys Summary

| Service | Purpose | Where to Get | Cost |
|---------|---------|--------------|------|
| **Daily.co** | Audio transport + STT | https://daily.co | Free: 10K min/mo |
| **Gemini** | AI responses | https://ai.google.dev | Free: 15 req/min |
| **Cartesia** | Text-to-speech | https://cartesia.ai | Free: 10K chars/mo |

---

## Next Steps

1. **Get Daily API key** → https://dashboard.daily.co/developers
2. **Add to .env**
3. **Run:** `pip install -r requirements.txt`
4. **Start bot:** `python voice-bot.py --transport daily`
5. **Test:** Open room URL in browser and speak

---

## How STT Works in Detail

### Code Location: voice-bot.py

**Line 108:** Enable transcription
```python
params=DailyParams(
    transcription_enabled=True,  # This enables STT
)
```

**Line 132:** Capture transcribed text
```python
await transport.capture_participant_transcription(participant["id"])
```

**What happens internally:**
1. Daily receives audio PCM data
2. Daily sends to transcription service
3. Text comes back as transcription events
4. Pipecat converts to text frames
5. Frames flow through pipeline to LLM

**You never see the STT step** - it's automatic!

---

## Daily.co Free Tier Limits

- ✅ 10,000 minutes/month
- ✅ Unlimited rooms
- ✅ 100 participants per room
- ✅ Recording & transcription included
- ✅ HIPAA compliant
- ✅ No credit card required

**Perfect for development and testing!**

---

## Architecture Comparison

### What You DON'T Need:

❌ Separate STT service (Deepgram, Whisper, AssemblyAI)
❌ WebRTC infrastructure setup
❌ Audio encoding/decoding
❌ NAT traversal / STUN/TURN servers
❌ Signaling server

### What Daily Provides:

✅ WebRTC transport (audio streaming)
✅ Built-in transcription (STT)
✅ Room management
✅ Multi-platform SDKs
✅ Echo cancellation
✅ Noise suppression
✅ Automatic gain control

**Daily = Audio infrastructure + STT in one service**

---

## Quick Start (TL;DR)

```bash
# 1. Fix dependencies
pip install -r requirements.txt

# 2. Get Daily key
# Visit: https://dashboard.daily.co/developers

# 3. Add to .env
echo "DAILY_API_KEY=your_key_here" >> .env

# 4. Run
python voice-bot.py --transport daily

# 5. Open room URL in browser and talk!
```

That's it! Daily handles all the STT automatically.
