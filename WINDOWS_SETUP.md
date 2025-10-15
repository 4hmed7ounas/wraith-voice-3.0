# Voice Bot Setup for Windows

## ⚠️ CRITICAL: Daily.co Does NOT Support Windows

**The Issue:**
The `daily-python` package **does not have Windows builds**. It only supports:
- macOS (ARM64)
- Linux (x86-64)

**This is why you got the error:**
```
ERROR: No matching distribution found for daily-python>=0.19.9
```

**Solution:** Use the **Deepgram version** instead of Daily!

---

## ✅ Recommended: Deepgram Version (Windows Compatible)

### What You'll Use:

| Component | Service | Status |
|-----------|---------|--------|
| **Audio Transport** | Local (PyAudio) | ✅ Windows compatible |
| **Speech-to-Text** | Deepgram | ✅ You have API key |
| **Language Model** | OpenAI GPT-4 | ❌ Need API key |
| **Text-to-Speech** | Cartesia | ✅ You have API key |

---

## Step-by-Step Setup

### 1. Install PyAudio (Required for Microphone Access)

**Option A: Using pipwin (Easiest)**
```bash
pip install pipwin
pipwin install pyaudio
```

**Option B: Download Pre-built Wheel**
1. Visit: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
2. Download for Python 3.12: `PyAudio‑0.2.14‑cp312‑cp312‑win_amd64.whl`
3. Install:
   ```bash
   pip install PyAudio-0.2.14-cp312-cp312-win_amd64.whl
   ```

### 2. Install Pipecat Dependencies

```bash
pip install -r requirements-deepgram.txt
```

This installs:
- `pipecat-ai[openai,deepgram,cartesia,silero]==0.0.87`
- `pyaudio>=0.2.14`

### 3. Get OpenAI API Key

1. Go to: https://platform.openai.com/api-keys
2. Sign up / Log in
3. Click "Create new secret key"
4. Copy the key (starts with `sk-proj-...`)

**Free tier:** $5 credit for new accounts

### 4. Update .env

Your `.env` already has most keys. Just add OpenAI:

```bash
OPENAI_API_KEY=sk-proj-your_actual_key_here
```

Your complete `.env`:
```bash
CARTESIA_API_KEY=sk_car_uhuozDmZUZahvQS7FqCekc
DEEPGRAM_API_KEY=c886864ca7e130733fee4306ea212483091c37fe
GEMINI_API_KEY=AIzaSyDqb0snGfu29Zri5WUaTacueg2MwHWPEKs
OPENAI_API_KEY=sk-proj-your_key_here
```

### 5. Run the Bot

```bash
python voice-bot-deepgram.py
```

**Expected Output:**
```
INFO: Starting pipeline...
INFO: 🎤 Microphone ready - start speaking!
```

Then **start talking** to your microphone!

---

## Alternative: Use Gemini Instead of OpenAI

If you don't want to use OpenAI, you can use Gemini (you already have the key).

**Edit `voice-bot-deepgram.py`** (lines 19-24):

```python
# Replace these imports:
from pipecat.services.openai.llm import OpenAILLMService

# With:
from pipecat.services.google import GoogleLLMService
```

**Then replace lines 57-60:**
```python
# OLD:
llm = OpenAILLMService(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o-mini",
)

# NEW:
llm = GoogleLLMService(
    api_key=os.getenv("GEMINI_API_KEY"),
    model="gemini-2.0-flash-exp",
)
```

**Update requirements:**
```bash
pip install pipecat-ai[google,deepgram,cartesia,silero]==0.0.87
```

---

## Architecture (Windows-Compatible)

```
Your Microphone
    ↓ (PyAudio)
LocalAudioTransport
    ↓
Deepgram STT (c886864ca7e130733fee4306ea212483091c37fe)
    ↓
OpenAI GPT-4o-mini (or Gemini)
    ↓
Cartesia TTS (sk_car_uhuozDmZUZahvQS7FqCekc)
    ↓
Your Speakers
```

---

## Why Daily Doesn't Work on Windows

**Technical Reason:**
The `daily-python` package uses native bindings to Daily's WebRTC library. These bindings are compiled for specific platforms:

- ✅ macOS ARM64 (M1/M2/M3 chips)
- ✅ Linux x86-64
- ❌ Windows (no builds available)

**From PyPI:**
```
Available wheels:
- daily_python-0.0.3-cp39-cp39-macosx_11_0_arm64.whl
- daily_python-0.0.3-cp39-cp39-manylinux_2_35_x86_64.whl
- (No Windows .whl files)
```

**What the GitHub issue says:**
> "Hopefully, `daily-python` will have support for Windows early 2025."

As of October 2025, Windows support is still not available.

---

## Comparison: What You're Giving Up

### Daily Version (macOS/Linux only):
- ✅ Web browser access
- ✅ Multi-user rooms
- ✅ Mobile app support
- ✅ One-click sharing
- ❌ Requires macOS/Linux

### Deepgram Version (Windows compatible):
- ✅ Works on Windows
- ✅ Local microphone/speaker
- ✅ You already have Deepgram key
- ❌ Local machine only (no web access)

---

## Troubleshooting

### PyAudio Won't Install

**Error:** `error: Microsoft Visual C++ 14.0 or greater is required`

**Solutions:**
1. Use `pipwin install pyaudio` (easiest)
2. Download pre-built wheel from https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
3. Install Visual Studio Build Tools (last resort)

### No Microphone Found

**Check available devices:**
```python
import pyaudio
p = pyaudio.PyAudio()
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    print(f"{i}: {info['name']}")
```

### Deepgram API Error

**Test your key:**
```bash
curl -X GET "https://api.deepgram.com/v1/projects" ^
  -H "Authorization: Token c886864ca7e130733fee4306ea212483091c37fe"
```

Should return your project info.

### OpenAI API Error

**Common issues:**
- Invalid API key (check it's correct in `.env`)
- No credits (add payment method)
- Rate limit (wait a bit)

---

## Cost Breakdown

### For 1 Hour of Conversation:

**Deepgram:**
- Cost: $0.0043/min × 60 = **$0.26/hour**
- Free tier: $200 credit = ~769 hours

**OpenAI (GPT-4o-mini):**
- Input: ~10K tokens = **$0.0015**
- Output: ~2K tokens = **$0.0012**
- Total: **~$0.003/hour**

**Cartesia:**
- ~1000 chars/min × 60 = 60K chars
- Cost: $0.05/1K chars = **$3/hour**
- Free tier: 10K chars = ~10 minutes

**Total:** ~$3.26/hour (mostly Cartesia TTS)

**Tip:** Cartesia free tier is limited. Consider using free alternatives:
- Google TTS (free, lower quality)
- Edge TTS (free, Windows built-in)
- Coqui TTS (open source, local)

---

## Quick Start (TL;DR)

```bash
# 1. Install PyAudio
pip install pipwin && pipwin install pyaudio

# 2. Install dependencies
pip install -r requirements-deepgram.txt

# 3. Get OpenAI key
# https://platform.openai.com/api-keys

# 4. Add to .env
# OPENAI_API_KEY=sk-proj-...

# 5. Run
python voice-bot-deepgram.py

# 6. Talk to your microphone!
```

---

## Files to Use on Windows

| File | Purpose | Use on Windows? |
|------|---------|-----------------|
| `voice-bot.py` | Daily + Gemini | ❌ No (Daily not supported) |
| `voice-bot-deepgram.py` | Deepgram + OpenAI | ✅ Yes (use this!) |
| `requirements.txt` | Daily dependencies | ❌ Won't work |
| `requirements-deepgram.txt` | Deepgram dependencies | ✅ Use this |

---

## Next Steps

1. ✅ Install PyAudio: `pipwin install pyaudio`
2. ✅ Install Pipecat: `pip install -r requirements-deepgram.txt`
3. ⬜ Get OpenAI API key: https://platform.openai.com/api-keys
4. ⬜ Add to `.env`: `OPENAI_API_KEY=sk-...`
5. ⬜ Run: `python voice-bot-deepgram.py`
6. ⬜ Start talking!

**Alternative:** Use Gemini instead (see "Alternative" section above)

---

## Summary

**Problem:** Daily.co doesn't support Windows

**Solution:** Use Deepgram + Local Audio instead

**What you have:**
- ✅ Deepgram API key
- ✅ Cartesia API key
- ✅ Gemini API key

**What you need:**
- ⬜ OpenAI API key (or use Gemini alternative)
- ⬜ Install PyAudio

**Result:** Working voice bot on Windows!
