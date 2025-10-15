# Voice-Only Chatbot - Wraith Voice 3.0

A streamlined voice chatbot using Gemini AI and Cartesia TTS.

## Overview

This voice bot provides a simple conversation flow:

```
User Speech → Speech-to-Text → Gemini LLM → Text-to-Speech (Cartesia) → Audio Output
```

**No video, no animations, just pure voice interaction.**

## Features

- ✅ Real-time voice conversation
- ✅ Google Gemini AI for intelligent responses
- ✅ Cartesia TTS for natural-sounding speech
- ✅ Voice Activity Detection (Silero VAD)
- ✅ Automatic speech-to-text transcription
- ✅ Low latency audio streaming

## Requirements

- Python 3.10+
- Daily.co API key (for WebRTC transport)
- Google Gemini API key (for AI)
- Cartesia API key (for TTS)

## Setup

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (macOS/Linux)
source .venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy template
cp env.example .env

# Edit .env and add your API keys
```

**Required API Keys:**
- `DAILY_API_KEY` - Get from https://daily.co
- `GEMINI_API_KEY` - Get from https://ai.google.dev
- `CARTESIA_API_KEY` - You already have this: `sk_car_uhuozDmZUZahvQS7FqCekc`

### 3. Run the Bot

```bash
python voice-bot.py --transport daily
```

## How It Works

### Pipeline Flow

```
1. Audio Input (Daily Transport)
   ↓
2. RTVI Processor (client sync)
   ↓
3. Context Aggregator (user messages)
   ↓
4. Gemini LLM (generates response)
   ↓
5. Cartesia TTS (converts to speech)
   ↓
6. Audio Output (Daily Transport)
   ↓
7. Context Aggregator (assistant messages)
```

### Key Components

**Speech-to-Text:**
- Handled automatically by Daily's transcription feature
- Enabled with `transcription_enabled=True`

**Language Model:**
- Google Gemini Multimodal Live API
- Configured for conversational, concise responses

**Text-to-Speech:**
- Cartesia TTS service
- Default voice ID: `a0e99841-438c-4a64-b679-ae501e7d6091`

**Voice Activity Detection:**
- Silero VAD Analyzer
- Detects when user starts/stops speaking

## Configuration

### Cartesia Voice Options

Change the voice by modifying `voice_id` in `voice-bot.py:44`:

```python
tts = CartesiaTTSService(
    api_key=os.getenv("CARTESIA_API_KEY"),
    voice_id="your_preferred_voice_id",  # Change this
)
```

Visit [Cartesia Voices](https://play.cartesia.ai/voices) to explore options.

### System Prompt

Modify the bot's personality by editing the message in `voice-bot.py:62-67`:

```python
messages = [
    {
        "role": "user",
        "content": "Your custom system prompt here...",
    },
]
```

## Connecting a Client

### Option 1: Daily Prebuilt (Quickest)

1. Run the bot
2. Bot will output a room URL
3. Open URL in browser
4. Allow microphone access
5. Start talking!

### Option 2: Custom Client

Create a simple HTML client using Daily's JavaScript SDK:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Voice Bot Client</title>
    <script src="https://unpkg.com/@daily-co/daily-js"></script>
</head>
<body>
    <button id="join">Join Call</button>
    <button id="leave">Leave Call</button>

    <script>
        const callFrame = window.DailyIframe.createFrame({
            iframeStyle: { display: 'none' }
        });

        document.getElementById('join').onclick = async () => {
            await callFrame.join({ url: 'YOUR_ROOM_URL_HERE' });
        };

        document.getElementById('leave').onclick = async () => {
            await callFrame.leave();
        };
    </script>
</body>
</html>
```

## Troubleshooting

### Bot doesn't start

**Check API keys:**
```bash
# Verify .env file has all required keys
cat .env
```

**Check dependencies:**
```bash
pip install --upgrade -r requirements.txt
```

### No audio output

**Verify Cartesia API key:**
- Test at https://play.cartesia.ai
- Confirm key has sufficient credits

**Check Daily room:**
- Ensure audio is enabled in room settings
- Check browser microphone permissions

### SSL Certificate Error

**Windows:**
```bash
pip install --upgrade certifi
```

**macOS:**
```bash
/Applications/Python\ 3.12/Install\ Certificates.command
```

## Project Structure

```
wraith-voice-3.0/
├── voice-bot.py           # Main voice bot (USE THIS)
├── bot-openai.py          # Old OpenAI bot (deprecated)
├── bot-gemini.py          # Old Gemini bot with video (deprecated)
├── requirements.txt       # Python dependencies
├── .env                   # Your API keys (DO NOT COMMIT)
├── env.example            # Template for .env
└── VOICE_BOT_README.md    # This file
```

## API Costs

**Gemini:**
- Free tier: 15 requests/minute
- Paid: ~$0.00025 per 1K characters

**Cartesia:**
- Free tier: 10K characters/month
- Paid: $0.05 per 1K characters

**Daily:**
- Free tier: 10K minutes/month
- Paid: $0.004 per minute

## Next Steps

1. ✅ Get Daily API key from https://daily.co
2. ✅ Update .env with DAILY_API_KEY
3. ✅ Run: `python voice-bot.py --transport daily`
4. ✅ Connect via browser to test
5. ⬜ Customize system prompt
6. ⬜ Build custom client UI
7. ⬜ Deploy to cloud

## Differences from Original

**Removed:**
- ❌ Video output
- ❌ Animated robot avatar
- ❌ PIL/Image dependencies
- ❌ Sprite frame loading
- ❌ TalkingAnimation processor
- ❌ ElevenLabs TTS

**Added:**
- ✅ Cartesia TTS integration
- ✅ Simplified pipeline
- ✅ Audio-only transport
- ✅ Cleaner code structure

## Support

**Documentation:**
- Pipecat: https://docs.pipecat.ai
- Gemini: https://ai.google.dev/docs
- Cartesia: https://docs.cartesia.ai
- Daily: https://docs.daily.co

**Issues:**
- Check logs for error messages
- Verify API keys are valid
- Ensure all dependencies installed
- Test network connectivity

## License

BSD 2-Clause License - Copyright (c) 2024–2025, Daily
