# Wraith Voice 3.0 - Comprehensive Project Analysis

## Project Overview

**Project Name:** Wraith Voice 3.0
**Project Type:** AI-Powered Real-time Voice/Video Chatbot
**Location:** E:\FYP\wraith-voice-3.0
**Version Control:** Not a git repository (currently)
**Platform:** Windows (win32)
**Primary Language:** Python

---

## Executive Summary

Wraith Voice 3.0 is a real-time AI chatbot application that enables voice and video interactions with users through multiple AI backends. The project is built on the **Pipecat AI framework** and supports both OpenAI's GPT-4 and Google's Gemini AI models. It features an animated robot avatar, real-time audio/video communication via Daily.co, and text-to-speech capabilities using ElevenLabs.

This appears to be a Final Year Project (FYP) implementation demonstrating advanced AI integration with real-time communication technologies.

---

## Technology Stack

### Core Framework
- **Pipecat AI** (v0.0.82+): Main framework for building conversational AI pipelines
  - Handles audio/video streaming
  - Pipeline architecture for processing frames
  - RTVI (Real-Time Voice Interface) support
  - WebRTC transport layer

### AI Services

#### 1. **Language Models**
- **OpenAI GPT-4** (gpt-4o): Primary conversational AI
- **Google Gemini**: Multimodal Live model with speech-to-speech capabilities
  - Voice options: Aoede, Charon, Fenrir, Kore, Puck

#### 2. **Speech Services**
- **ElevenLabs**: Text-to-speech synthesis (used with OpenAI bot)
  - Voice ID: pNInz6obpgDQGcFmaJgB
- **Deepgram**: Speech recognition/transcription capabilities (API key present)
- **Cartesia**: Additional audio processing (API key present)

#### 3. **Voice Activity Detection**
- **Silero VAD Analyzer**: Detects when users start/stop speaking

### Communication Infrastructure
- **Daily.co**: WebRTC platform for real-time audio/video transport
  - Room-based architecture
  - Transcription enabled
  - Participant management

### Python Dependencies
```
pipecat-ai[daily,elevenlabs,openai,silero,google,runner]>=0.0.82
```

### Additional Libraries
- **python-dotenv**: Environment variable management
- **loguru**: Advanced logging
- **Pillow (PIL)**: Image processing for avatar animations

---

## Project Structure

```
wraith-voice-3.0/
├── bot-openai.py          # OpenAI GPT-4 bot implementation
├── bot-gemini.py          # Google Gemini bot implementation
├── .env                   # API keys and configuration (ACTIVE)
├── env.example            # Environment template
├── requirements.txt       # Python dependencies
├── .gitignore            # Git ignore rules
├── README.md             # Main documentation
├── README-Server.md      # Server setup guide
└── assets/               # Robot animation sprites (MISSING - referenced but not present)
    └── robot01.png to robot25.png (expected)
```

---

## Configuration Details

### Environment Variables (Active)

The project uses three API keys currently configured in `.env`:

1. **CARTESIA_API_KEY**: `sk_car_uhuozDmZUZahvQS7FqCekc`
2. **DEEPGRAM_API_KEY**: `c886864ca7e130733fee4306ea212483091c37fe`
3. **GEMINI_API_KEY**: `AIzaSyDqb0snGfu29Zri5WUaTacueg2MwHWPEKs`

**Missing Keys (Required for full functionality):**
- DAILY_API_KEY
- OPENAI_API_KEY
- ELEVENLABS_API_KEY
- DAILY_SAMPLE_ROOM_URL (optional)
- DAILY_SAMPLE_ROOM_TOKEN (optional)

### Expected Configuration Template (from env.example)

```ini
DAILY_SAMPLE_ROOM_URL=https://yourdomain.daily.co/yourroom
DAILY_SAMPLE_ROOM_TOKEN=9c8...
DAILY_API_KEY=7df...
OPENAI_API_KEY=sk-PL...
GOOGLE_API_KEY=AIza...
ELEVENLABS_API_KEY=aeb...
BOT_IMPLEMENTATION= # Options: 'openai' or 'gemini'
```

---

## Architecture & Implementation

### Pipeline Architecture

Both bots use a **frame-based processing pipeline** where data flows through sequential processors:

#### OpenAI Bot Pipeline
```
Input (Daily Transport)
    ↓
RTVI Processor
    ↓
Context Aggregator (User)
    ↓
OpenAI LLM Service (GPT-4)
    ↓
ElevenLabs TTS Service
    ↓
Talking Animation Processor
    ↓
Output (Daily Transport)
    ↓
Context Aggregator (Assistant)
```

#### Gemini Bot Pipeline
```
Input (Daily Transport)
    ↓
RTVI Processor
    ↓
Context Aggregator (User)
    ↓
Gemini Multimodal Live Service
    ↓
Talking Animation Processor
    ↓
Output (Daily Transport)
    ↓
Context Aggregator (Assistant)
```

**Key Difference:** Gemini bot has built-in speech synthesis, so it doesn't need a separate TTS service.

---

## Core Components Breakdown

### 1. Bot Implementations (bot-openai.py & bot-gemini.py)

#### Shared Features:
- **Animated Avatar System**: 25-frame robot animation
  - Loads sprites from `assets/robot01.png` to `robot25.png`
  - Creates smooth loop by reversing frames (50 total frames)
  - Two states: quiet (static) and talking (animated)

- **TalkingAnimation Class**: Custom FrameProcessor
  - Monitors `BotStartedSpeakingFrame` and `BotStoppedSpeakingFrame`
  - Switches between static and animated avatar states
  - Maintains internal `_is_talking` state

- **RTVI Integration**: Real-Time Voice Interface
  - Handles client ready events
  - Sets bot ready state
  - Triggers initial conversation

- **Event Handlers**:
  - `on_client_connected`: Starts transcription capture
  - `on_client_disconnected`: Gracefully cancels pipeline
  - `on_client_ready`: Initiates conversation with LLMRunFrame

#### OpenAI Bot Specific (bot-openai.py:102-208)
- **LLM Configuration**:
  - Model: GPT-4o (latest OpenAI multimodal model)
  - System prompt: Defines bot as "Chatbot, a friendly, helpful robot"
  - Instruction to keep responses brief and audio-friendly
  - Auto-introduction on startup

- **TTS Configuration**:
  - Service: ElevenLabs
  - Voice ID: pNInz6obpgDQGcFmaJgB (specific voice character)

#### Gemini Bot Specific (bot-gemini.py:100-202)
- **LLM Configuration**:
  - Model: Gemini Multimodal Live
  - Voice: "Puck" (other options: Aoede, Charon, Fenrir, Kore)
  - Native speech-to-speech (no separate TTS needed)
  - Same conversational prompt as OpenAI bot

### 2. Transport Layer (DailyTransport)

**Configuration Parameters:**
- Audio Input: Enabled
- Audio Output: Enabled
- Video Output: Enabled (1024x576 resolution)
- VAD Analyzer: Silero (for voice activity detection)
- Transcription: Enabled
- Bot Name: "Pipecat Bot"

**Purpose:**
- Manages WebRTC connections via Daily.co
- Handles real-time audio/video streaming
- Captures participant transcriptions
- Provides event-driven architecture

### 3. Context Management

- **OpenAILLMContext**: Manages conversation history
- **Context Aggregator**: Splits into user and assistant flows
  - User aggregator: Collects user inputs before LLM
  - Assistant aggregator: Collects bot responses after output

### 4. Pipeline Task Configuration

**Features Enabled:**
- Metrics: General performance tracking
- Usage Metrics: AI service usage tracking
- RTVI Observer: Monitors RTVI events

---

## Missing Components & Issues

### Critical Missing Elements:

1. **Assets Directory**:
   - Referenced: `assets/robot01.png` through `robot25.png`
   - Status: Directory not found
   - Impact: Bot will crash on startup when trying to load animation sprites
   - Line References: bot-openai.py:52-58, bot-gemini.py:50-56

2. **API Keys**:
   - Missing: DAILY_API_KEY (required for transport)
   - Missing: OPENAI_API_KEY (required for OpenAI bot)
   - Missing: ELEVENLABS_API_KEY (required for OpenAI bot TTS)

3. **Client Implementations**:
   - README references multiple client options (Android, iOS, JavaScript, React, React Native)
   - None are present in current directory
   - Expected location: `client/` directory (missing)

4. **Server Directory Structure**:
   - README suggests bots should be in `server/` subdirectory
   - Current structure: Flat (bots in root)
   - Indicates this might be a simplified/stripped version

---

## System Prompts & Bot Personality

Both bots share the same conversational directive:

**System Prompt:**
```
"You are Chatbot, a friendly, helpful robot. Your goal is to demonstrate
your capabilities in a succinct way. Your output will be converted to
audio so don't include special characters in your answers. Respond to
what the user said in a creative and helpful way, but keep your
responses brief. Start by introducing yourself."
```

**Key Characteristics:**
- Friendly and helpful tone
- Brief, concise responses
- Audio-optimized (no special characters)
- Self-introduction on startup
- Creative but focused answers

---

## Execution Flow

### Startup Sequence:

1. **Environment Loading**: Load .env file with API keys
2. **Sprite Loading**: Load 25 PNG images from assets folder
3. **Animation Prep**: Create 50-frame loop (forward + reverse)
4. **Transport Init**: Setup Daily.co connection with room URL/token
5. **Service Init**: Initialize AI service (OpenAI or Gemini) + TTS
6. **Pipeline Build**: Construct processing pipeline
7. **Task Creation**: Create PipelineTask with observers
8. **Initial Frame**: Queue quiet_frame (static avatar)
9. **Event Setup**: Register connection/disconnection handlers
10. **Runner Start**: Launch PipelineRunner

### Runtime Flow:

1. **Client Connection**: User joins Daily.co room
2. **RTVI Ready**: Client signals ready state
3. **Bot Ready**: Bot responds with ready state
4. **Initial Greeting**: Bot queues LLMRunFrame to introduce itself
5. **Conversation Loop**:
   - User speaks → VAD detects → Transcription
   - Audio frames → Context aggregator
   - LLM generates response
   - TTS converts to audio (OpenAI) / Native audio (Gemini)
   - Animation switches to talking state
   - Audio output to user
   - Animation returns to quiet state
6. **Disconnection**: User leaves → Pipeline cancels gracefully

---

## Code Quality & Practices

### Strengths:
- **Well-documented**: Comprehensive docstrings and comments
- **Type hints**: Uses type annotations (Frame, FrameDirection, etc.)
- **Async/await**: Proper asynchronous programming
- **Event-driven**: Clean event handler architecture
- **Modular**: Separated concerns (animation, transport, LLM)
- **Error handling**: Graceful disconnection handling
- **Licensing**: BSD 2-Clause License (2024-2025 Daily)

### Potential Improvements:
- **Error handling**: No try/catch for sprite loading
- **Configuration validation**: No checks for missing API keys
- **Asset verification**: No fallback if images missing
- **Logging**: Limited error logging (only client connection/disconnection)
- **Environment validation**: Should verify all required env vars on startup

---

## Use Cases & Applications

### Demonstrated Capabilities:
1. **Voice Assistants**: Real-time conversational AI
2. **Customer Service Bots**: Automated support with visual avatar
3. **Educational Tools**: Interactive learning companions
4. **Accessibility**: Voice-driven interfaces
5. **Prototyping**: Testing AI model capabilities (OpenAI vs Gemini)

### Target Platforms (from README):
- Web browsers (JavaScript, React)
- Mobile (React Native, Android, iOS)
- Daily Prebuilt rooms (instant deployment)

---

## Security Considerations

### Exposed Credentials:
⚠️ **WARNING**: The `.env` file contains active API keys that should NOT be committed to version control:
- Cartesia API key exposed
- Deepgram API key exposed
- Gemini API key exposed

### Recommendations:
1. **Rotate all exposed API keys immediately**
2. **Add .env to .gitignore** (already present but ensure it's respected)
3. **Use secret management** for production deployments
4. **Implement API key validation** at runtime
5. **Add rate limiting** to prevent API abuse

---

## Performance Characteristics

### Video Output:
- Resolution: 1024x576 pixels
- Format: Sequential sprite animation (50 frames)
- Frame switching based on speech state

### Audio Processing:
- Real-time bidirectional streaming
- Voice Activity Detection (Silero)
- Transcription enabled (for better context)

### Metrics:
- Performance metrics enabled
- Usage metrics enabled
- Allows monitoring of:
  - Pipeline throughput
  - AI service latency
  - Token usage
  - Frame processing times

---

## Dependencies & Requirements

### Python Version:
- **Minimum**: Python 3.10+

### System Requirements (from README):
- Python 3.10+
- Node.js 16+ (for client implementations - not present)
- Modern web browser with WebRTC support

### API Service Requirements:
- Daily.co account (WebRTC platform)
- OpenAI account (for GPT-4 bot)
- Google AI account (for Gemini bot)
- ElevenLabs account (for OpenAI TTS)
- Optional: Deepgram, Cartesia accounts

---

## Development Setup Instructions

### Current Status:
Based on README-Server.md, the setup process should be:

1. **Environment Configuration**:
   ```bash
   cp env.example .env
   # Edit .env to add missing API keys
   ```

2. **Virtual Environment**:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

3. **Asset Preparation**:
   - Need to create/add `assets/` directory
   - Add robot01.png through robot25.png sprite images

4. **Run Bot**:
   ```bash
   python bot-openai.py --transport daily
   # OR
   python bot-gemini.py --transport daily
   ```

### Alternative with uv:
```bash
uv sync
uv run bot-openai.py --transport daily
```

---

## Troubleshooting Notes

### Known Issues (from README-Server.md):

**SSL Certificate Error:**
```
aiohttp.client_exceptions.ClientConnectorCertificateError:
Cannot connect to host api.daily.co:443 ssl:True
```

**Solution (macOS):**
```bash
/Applications/Python\ 3.12/Install\ Certificates.command
```

**Solution (Windows):**
- Install/update certifi package
- May need to run Python installer to repair SSL certificates

---

## Project Purpose & Context

### Final Year Project (FYP) Indicators:
- Located in `E:\FYP\` directory
- Version 3.0 suggests iterative development
- Demonstrates multiple AI integrations
- Comprehensive documentation
- Multiple client options (scalability demonstration)

### Educational Value:
- **AI Integration**: Shows practical LLM implementation
- **Real-time Communication**: WebRTC and streaming audio/video
- **Pipeline Architecture**: Frame-based processing patterns
- **Async Programming**: Modern Python async/await patterns
- **Multi-service Integration**: Combining multiple APIs
- **Animation/UX**: Visual feedback systems

---

## Comparison: OpenAI vs Gemini Implementations

| Feature | OpenAI Bot | Gemini Bot |
|---------|-----------|------------|
| **Model** | GPT-4o | Gemini Multimodal Live |
| **Speech Synthesis** | ElevenLabs (external) | Built-in |
| **Voice Options** | 1 (ElevenLabs voice) | 5 (Aoede, Charon, Fenrir, Kore, Puck) |
| **Pipeline Stages** | 9 processors | 8 processors (no TTS) |
| **Multimodal** | Yes (text/audio) | Yes (text/audio/speech-to-speech) |
| **API Cost** | OpenAI + ElevenLabs | Google Gemini only |
| **Latency** | Higher (2 services) | Lower (integrated TTS) |
| **Code Lines** | 209 lines | 203 lines |

---

## Pipecat Framework Deep Dive

### What is Pipecat?
Pipecat is a framework for building voice and multimodal conversational AI applications. It provides:

1. **Frame-based Architecture**: All data (audio, video, text, control signals) flows as frames
2. **Pipeline Processing**: Linear or branching data flows
3. **Transport Abstraction**: Supports multiple communication backends (Daily, WebRTC, etc.)
4. **Service Integration**: Pre-built connectors for major AI services
5. **RTVI Standard**: Real-Time Voice Interface protocol

### Frame Types Used in Project:
- **OutputImageRawFrame**: Raw image data for avatar
- **SpriteFrame**: Animated sequence of images
- **BotStartedSpeakingFrame**: Control signal for animation
- **BotStoppedSpeakingFrame**: Control signal for animation
- **LLMRunFrame**: Triggers LLM processing

### Pipeline Params:
- **enable_metrics**: Tracks processing performance
- **enable_usage_metrics**: Tracks AI service usage/costs

---

## Animation System Details

### Sprite Loading Process:
```python
# Load 25 frames
for i in range(1, 26):
    full_path = os.path.join(script_dir, f"assets/robot0{i}.png")
    with Image.open(full_path) as img:
        sprites.append(OutputImageRawFrame(
            image=img.tobytes(),
            size=img.size,
            format=img.format
        ))
```

### Animation Loop:
```python
# Original: frames 1-25
# Flipped: frames 25-1
# Total: 50 frames for smooth loop
flipped = sprites[::-1]
sprites.extend(flipped)
```

### State Management:
- **quiet_frame**: `sprites[0]` - First frame (static)
- **talking_frame**: `SpriteFrame(images=sprites)` - All 50 frames
- Switches automatically based on speaking events

---

## RTVI (Real-Time Voice Interface) Integration

### Purpose:
- Standardized protocol for voice AI interactions
- Manages client-bot synchronization
- Event-driven state management

### Events Used:
1. **on_client_ready**: Client UI is ready to interact
   - Response: `rtvi.set_bot_ready()`
   - Action: Queue initial LLM run

2. **on_client_connected**: New participant joins
   - Action: Start transcription capture
   - Logging: Connection event

3. **on_client_disconnected**: Participant leaves
   - Action: Cancel pipeline task
   - Logging: Disconnection event

### Configuration:
```python
rtvi = RTVIProcessor(config=RTVIConfig(config=[]))
```
- Empty config suggests default settings
- Observer pattern for monitoring

---

## Future Enhancements & Possibilities

### Immediate Needs:
1. **Add missing assets** (robot sprite images)
2. **Complete API key configuration**
3. **Implement client applications**
4. **Add error handling** for missing dependencies
5. **Create setup validation script**

### Potential Features:
1. **Multi-language Support**: Extend beyond English/Spanish
2. **Custom Avatars**: User-selectable or uploadable sprites
3. **Emotion Detection**: Vary animation based on sentiment
4. **Screen Sharing**: Add visual context to conversations
5. **Recording**: Save conversation transcripts
6. **Analytics Dashboard**: Track usage patterns
7. **A/B Testing**: Compare OpenAI vs Gemini performance
8. **Webhook Integration**: Trigger external actions
9. **Database Integration**: Persistent conversation history
10. **Authentication**: Secure access control

---

## API Service Analysis

### Currently Configured:
1. **Cartesia**: Audio/speech synthesis (alternative to ElevenLabs)
2. **Deepgram**: Advanced speech recognition
3. **Gemini**: Google's multimodal AI

### Required but Missing:
1. **Daily.co**: WebRTC infrastructure (CRITICAL)
2. **OpenAI**: GPT-4 access (for OpenAI bot)
3. **ElevenLabs**: TTS for OpenAI bot

### Service Purposes:

**Cartesia**:
- Real-time voice synthesis
- Low-latency audio generation
- Alternative to ElevenLabs

**Deepgram**:
- Speech-to-text transcription
- Real-time streaming ASR (Automatic Speech Recognition)
- Enhanced accuracy

**Gemini**:
- Multimodal AI (text, audio, images)
- Native speech-to-speech
- Google's latest model

**Daily.co** (missing):
- WebRTC platform
- Room-based video conferencing
- Critical for transport layer

**OpenAI** (missing):
- GPT-4o language model
- Multimodal capabilities
- High-quality responses

**ElevenLabs** (missing):
- Premium TTS
- Natural-sounding voices
- Emotional inflection

---

## Licensing & Attribution

**License**: BSD 2-Clause License
**Copyright**: 2024–2025, Daily
**SPDX-License-Identifier**: BSD-2-Clause

### Implications:
- Free to use, modify, distribute
- Must retain copyright notice
- No warranty provided
- Attribution required

---

## Git Configuration Analysis

### Current Status:
- **Not a git repository** (no .git folder)
- `.gitignore` present and configured
- Suggests version control not initialized yet

### .gitignore Coverage:
- Python artifacts (\_\_pycache\_\_, .pyc files)
- Virtual environments (.venv, venv)
- Environment files (.env)
- Node modules (for client apps)
- IDE configs (.vscode, .idea)
- Build artifacts
- Log files

**Recommendation**: Initialize git and make initial commit (after rotating exposed API keys)

---

## Conclusion

### Project Assessment:

**Strengths:**
- ✅ Modern tech stack (Pipecat, GPT-4, Gemini)
- ✅ Clean, well-documented code
- ✅ Dual AI backend support
- ✅ Production-ready architecture
- ✅ Event-driven design
- ✅ Scalable pipeline structure

**Weaknesses:**
- ❌ Missing critical assets (robot sprites)
- ❌ Incomplete API configuration
- ❌ No client implementations present
- ❌ Exposed API keys in .env
- ❌ No version control initialized
- ❌ Limited error handling

**Overall Status:**
This is a **partially complete** FYP project demonstrating strong architectural design and AI integration skills. The core server logic is production-quality, but the project needs asset files and proper configuration to run. It showcases understanding of:
- Real-time communication
- AI service integration
- Asynchronous programming
- Pipeline architecture
- Multi-platform deployment strategies

### Next Steps for Completion:
1. Create/add robot animation sprites
2. Obtain and configure missing API keys
3. Test both OpenAI and Gemini bots
4. Implement at least one client (JavaScript recommended for simplicity)
5. Initialize git repository
6. Add comprehensive error handling
7. Create deployment documentation
8. Consider adding unit tests

---

## Technical Specifications Summary

| Specification | Value |
|--------------|-------|
| **Language** | Python 3.10+ |
| **Framework** | Pipecat AI 0.0.82+ |
| **AI Models** | GPT-4o, Gemini Multimodal Live |
| **TTS** | ElevenLabs, Gemini Native |
| **Transport** | Daily.co WebRTC |
| **VAD** | Silero |
| **Animation** | 50-frame sprite loop |
| **Video Resolution** | 1024x576 |
| **Architecture** | Frame-based pipeline |
| **License** | BSD 2-Clause |
| **Platform** | Cross-platform (Windows, macOS, Linux) |

---

**Document Generated**: 2025-10-07
**Analysis Type**: Comprehensive Code Review & Architecture Analysis
**Project Version**: 3.0
**Status**: Development (Incomplete)
