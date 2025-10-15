# Voice Bot with Deepgram (No Daily.co)

## Overview

This version uses **Deepgram for STT** instead of Daily.co:

```
Microphone → Deepgram STT → OpenAI/Gemini LLM → Cartesia TTS → Speaker
```

**What changed:**
- ❌ Removed: Daily.co (WebRTC transport + transcription)
- ✅ Added: Deepgram STT (dedicated speech-to-text)
- ✅ Added: LocalAudioTransport (direct microphone/speaker access)
- ⚠️ Changed: Using OpenAI instead of Gemini (Gemini requires Daily transport)

---

## Why This Approach?

### Pros:
- ✅ **You already have Deepgram API key**: `c886864ca7e130733fee4306ea212483091c37fe`
- ✅ **No Daily.co needed**: Direct local audio access
- ✅ **More control**: Choose your own STT, LLM, TTS
- ✅ **Simpler architecture**: Fewer services to coordinate

### Cons:
- ❌ **Local only**: Runs on your machine (not web-accessible)
- ❌ **Needs OpenAI key**: Gemini Multimodal Live requires Daily transport
- ❌ **PyAudio complexity**: Can be tricky to install on Windows

---

## Architecture Comparison

### OLD (with Daily):
```
User Browser (WebRTC)
    ↓
Daily.co (STT included)
    ↓
Gemini LLM
    ↓
Cartesia TTS
    ↓
Daily.co (audio out)
    ↓
User Browser
```

### NEW (with Deepgram):
```
Your Microphone
    ↓
LocalAudioTransport
    ↓
Deepgram STT
    ↓
OpenAI LLM
    ↓
Cartesia TTS
    ↓
Your Speakers
```

---

## Setup Instructions

### 1. Install PyAudio (Windows)

PyAudio is needed for microphone/speaker access.

**Option A: Using pipwin (easiest)**
```bash
pip install pipwin
pipwin install pyaudio
```

**Option B: Download wheel manually**
1. Go to https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
2. Download: `PyAudio‑0.2.14‑cp312‑cp312‑win_amd64.whl` (for Python 3.12)
3. Install:
   ```bash
   pip install PyAudio‑0.2.14‑cp312‑cp312‑win_amd64.whl
   ```

**Option C: Build from source (requires Visual Studio)**
```bash
pip install pyaudio
```

### 2. Install Dependencies

```bash
pip install -r requirements-deepgram.txt
```

### 3. Configure API Keys

Edit `.env`:
```bash
# Required
DEEPGRAM_API_KEY=c886864ca7e130733fee4306ea212483091c37fe
OPENAI_API_KEY=your_openai_key_here
CARTESIA_API_KEY=sk_car_uhuozDmZUZahvQS7FqCekc

# Not needed for Deepgram version
# DAILY_API_KEY=
# GEMINI_API_KEY=
```

**Note:** You need an OpenAI API key. Get one at https://platform.openai.com/api-keys

### 4. Run the Bot

```bash
python voice-bot-deepgram.py
```

**Expected output:**
```
INFO: Starting pipeline...
INFO: 🎤 Microphone ready - start speaking!
```

Then just **start talking** to your microphone!

---

## API Keys Needed

| Service | Purpose | You Have It? | Where to Get |
|---------|---------|--------------|--------------|
| **Deepgram** | Speech-to-Text | ✅ Yes | https://deepgram.com |
| **OpenAI** | Language Model | ❌ Need this | https://platform.openai.com |
| **Cartesia** | Text-to-Speech | ✅ Yes | https://cartesia.ai |

**You only need to get OpenAI API key!**

---

## Can We Use Gemini Instead of OpenAI?

**Short answer:** Not easily with local audio transport.

**Why:**
- Gemini Multimodal Live is designed to work with Daily's WebRTC transport
- It handles audio directly (speech-to-speech)
- Using it with local audio would require custom integration

**Options:**
1. **Use OpenAI GPT-4o-mini** (recommended - fast and cheap)
2. **Use regular Gemini API** (text-only, not Multimodal Live)
3. **Stick with Daily + Gemini** (as in original voice-bot.py)

---

## Using Regular Gemini API (Text-Only)

If you want to avoid OpenAI, you can use standard Gemini:

**Change in voice-bot-deepgram.py (lines 57-60):**

```python
# Replace OpenAI LLM with:
from pipecat.services.google import GoogleLLMService

llm = GoogleLLMService(
    api_key=os.getenv("GEMINI_API_KEY"),
    model="gemini-2.0-flash-exp",
)
```

Then update `.env`:
```bash
GEMINI_API_KEY=AIzaSyDqb0snGfu29Zri5WUaTacueg2MwHWPEKs
```

**Install Google support:**
```bash
pip install pipecat-ai[google]==0.0.87
```

---

## Troubleshooting

### PyAudio Installation Fails

**Error:** `error: Microsoft Visual C++ 14.0 or greater is required`

**Solution:**
1. Use pipwin: `pip install pipwin && pipwin install pyaudio`
2. Or download pre-built wheel from https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio

### No Microphone Detected

**Check:**
```python
import pyaudio
p = pyaudio.PyAudio()
for i in range(p.get_device_count()):
    print(p.get_device_info_by_index(i))
```

### Deepgram API Error

**Check key validity:**
```bash
curl -X GET "https://api.deepgram.com/v1/projects" \
  -H "Authorization: Token YOUR_DEEPGRAM_KEY"
```

### OpenAI API Error

**Get API key:**
1. Go to https://platform.openai.com/api-keys
2. Create new secret key
3. Add to `.env`

---

## Cost Comparison

### Deepgram:
- **Free tier:** $200 credit (≈33 hours of audio)
- **Paid:** $0.0043/minute ($0.26/hour)

### OpenAI (GPT-4o-mini):
- **Input:** $0.150 / 1M tokens (very cheap)
- **Output:** $0.600 / 1M tokens

### Cartesia:
- **Free tier:** 10K characters/month
- **Paid:** $0.05 / 1K characters

**Total cost for 1 hour of conversation:** ~$1-2

---

## Which Version Should You Use?

### Use **Deepgram Version** (voice-bot-deepgram.py) if:
- ✅ You want local testing only
- ✅ You don't want to deal with Daily.co
- ✅ You already have Deepgram API key
- ✅ You're okay using OpenAI for LLM

### Use **Daily Version** (voice-bot.py) if:
- ✅ You want web/mobile access
- ✅ You want to use Gemini Multimodal Live
- ✅ You need multi-user support
- ✅ You want one-click browser access

---

## File Structure

```
wraith-voice-3.0/
├── voice-bot.py                 # Daily + Gemini (original)
├── voice-bot-deepgram.py        # Deepgram + OpenAI (NEW)
├── requirements.txt             # For Daily version
├── requirements-deepgram.txt    # For Deepgram version (NEW)
├── DEEPGRAM_SETUP.md           # This file
└── .env                        # API keys
```

---

## Quick Start (TL;DR)

```bash
# 1. Install PyAudio
pip install pipwin && pipwin install pyaudio

# 2. Install dependencies
pip install -r requirements-deepgram.txt

# 3. Get OpenAI API key
# Visit: https://platform.openai.com/api-keys

# 4. Add to .env
echo "OPENAI_API_KEY=sk-..." >> .env

# 5. Run
python voice-bot-deepgram.py

# 6. Start talking to your microphone!
```

---

## Summary

**What you get:**
- 🎤 Deepgram STT (you already have the key!)
- 🤖 OpenAI LLM (need to get key)
- 🔊 Cartesia TTS (you already have the key!)
- 💻 Local audio (no browser needed)

**Trade-off:**
- Works only on your local machine
- Can't share via web link (like Daily allows)
- Need to install PyAudio (can be tricky on Windows)

**But:** Much simpler if you just want local voice testing!
