#
# WRAITH Voice Bot with Direct Groq API Integration
#
# Features:
# - Groq LLM for ultra-fast inference with high rate limits
# - Fragment filtering to prevent partial transcription responses
# - Balanced pause detection (1s) for responsive conversation
# - Anti-hallucination and anti-repetition system prompts
# - Deepgram STT with 300ms endpointing for quick responses
# - WRAITH robot identity with professional, concise responses
# - Noise-resistant VAD (min_volume=0.75, confidence=0.8)
#

import os
import asyncio
import json
import httpx
from dotenv import load_dotenv
from loguru import logger
from groq import AsyncGroq

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.frames.frames import Frame, TranscriptionFrame, InterimTranscriptionFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.services.cartesia.tts import CartesiaTTSService
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.transports.local.audio import LocalAudioTransport, LocalAudioTransportParams

load_dotenv(override=True)

# Robot Controller Configuration
ROBOT_URL = os.getenv("ROBOT_CONTROLLER_URL", "http://localhost:5000")
ROBOT_MOVEMENT_DURATION = float(os.getenv("ROBOT_MOVEMENT_DURATION", "1.0"))
ROBOT_REQUEST_TIMEOUT = float(os.getenv("ROBOT_REQUEST_TIMEOUT", "5.0"))
ROBOT_MAX_DURATION = float(os.getenv("ROBOT_MAX_DURATION", "5.0"))


class GroqProcessor(FrameProcessor):
    """Custom processor that calls Groq API directly with robot control integration"""

    def __init__(self, api_key: str, model: str = "llama-3.1-8b-instant"):
        super().__init__()

        # Initialize Groq client
        self.client = AsyncGroq(api_key=api_key)
        self.model = model

        # Initialize HTTP client for robot control
        self.http_client = httpx.AsyncClient(timeout=ROBOT_REQUEST_TIMEOUT)
        self.robot_available = False

        # Define available functions for function calling
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "movement",
                    "description": "Controls the robot's movement in a specified direction. Use this when the user asks to move forward, backward, left, or right. Optionally specify duration in seconds.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "direction": {
                                "type": "string",
                                "enum": ["forward", "backward", "left", "right"],
                                "description": "The direction to move the robot"
                            },
                            "duration": {
                                "type": "number",
                                "description": "Optional duration in seconds (default: 1.0, max: 5.0)"
                            }
                        },
                        "required": ["direction"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "stop",
                    "description": "Immediately stops all robot motors. Use when user says stop, halt, or emergency stop.",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "set_speed",
                    "description": "Adjusts the robot's movement speed. Use when user asks to go faster, slower, or set specific speed.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "enum": ["increase", "decrease"],
                                "description": "Whether to increase or decrease speed"
                            }
                        },
                        "required": ["action"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "check_distance",
                    "description": "Gets the distance to the nearest obstacle using the ultrasonic sensor. Use when user asks about obstacles or distance.",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "auto_mode",
                    "description": "Controls autonomous obstacle avoidance mode. Use when user asks to enable/disable auto mode or autonomous navigation.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "enum": ["start", "stop"],
                                "description": "Start or stop autonomous mode"
                            }
                        },
                        "required": ["action"]
                    }
                }
            }
        ]

        # Chat history with WRAITH system prompt
        self.messages = [
            {
                "role": "system",
                "content": """You are WRAITH, an advanced autonomous service robot developed by three Robotics students - Ahmed Younas, Zaid Shabbir, and Abdul Hannan from Lahore, Pakistan. You represent cutting-edge Pakistani innovation in robotics.

Your capabilities include:
- Advanced SLAM and Machine Learning algorithms for precise autonomous navigation
- Complex indoor environment mapping using integrated LiDAR, depth cameras, and IMUs
- Efficient guest guidance with clear, concise directions
- Secure object transportation with optimized pathfinding
- Natural voice and text-based interaction with professional communication
- Location assistance for disoriented individuals
- Dual-mode operation: manual teleoperation and fully autonomous functioning
- Remote control through a dedicated mobile application
- Voice-controlled movement: forward, backward, left, right with adjustable duration
- Speed control: increase/decrease speed on command
- Emergency stop functionality
- Ultrasonic distance sensor for obstacle detection
- Autonomous obstacle avoidance mode
- You represent technological excellence from Pakistan, developed at FAST NUCES

You are currently operating in voice interaction mode, providing professional assistance through conversation.

CRITICAL RESPONSE GUIDELINES:
- Keep responses brief: 1-2 sentences maximum for voice interaction
- Be direct and conversational, avoid verbose explanations
- NEVER repeat information you just mentioned in previous responses
- NEVER hallucinate facts, capabilities, or features you don't have
- If you don't know something, simply say "I don't have that information"
- Don't make up technical specifications, locations, or details
- Stay factual and grounded - only state what you actually know
- Avoid listing your capabilities repeatedly unless specifically asked
- Each response should add NEW information, not rehash previous statements
- Listen to context: if the user already knows something, don't repeat it
- Be natural and human-like in conversation tone
- Acknowledge when you're uncertain rather than inventing details

FUNCTION CALLING INSTRUCTIONS:
- Use the 'movement' function when user asks to move in any direction
- Use the 'stop' function when user says stop, halt, or emergency stop
- Use the 'set_speed' function when user asks to go faster or slower
- Use the 'check_distance' function when user asks about obstacles or distance
- Use the 'auto_mode' function when user wants autonomous navigation on/off"""
            }
        ]

        # Transcription buffering to avoid partial responses
        self.last_transcription_text = ""
        self.transcription_task = None

        logger.info(f"✅ Groq {model} initialized with robot control functions")

    async def check_robot_connection(self) -> bool:
        """Check if robot controller is available"""
        try:
            response = await self.http_client.get(f"{ROBOT_URL}/", timeout=2.0)
            self.robot_available = response.status_code == 200
            if self.robot_available:
                logger.info(f"✅ Robot controller connected at {ROBOT_URL}")
            return self.robot_available
        except Exception as e:
            logger.warning(f"⚠️ Robot controller not available: {e}")
            self.robot_available = False
            return False

    async def movement(self, direction: str, duration: float = None) -> str:
        """Handle movement commands with HTTP control"""
        if duration is None:
            duration = ROBOT_MOVEMENT_DURATION

        # Safety: Limit maximum duration
        duration = min(duration, ROBOT_MAX_DURATION)

        logger.info(f"🚀 MOVEMENT: {direction.upper()} for {duration}s")

        # Map direction to robot commands
        commands = {
            "forward": "forward",
            "backward": "backward",
            "left": "left",
            "right": "right"
        }

        if direction not in commands:
            return f"Invalid direction: {direction}"

        try:
            # Send start command
            start_cmd = f"{commands[direction]}_start"
            response = await self.http_client.post(
                f"{ROBOT_URL}/control",
                content=start_cmd
            )

            if response.status_code != 200:
                logger.error(f"Failed to start movement: {response.text}")
                return f"Failed to move {direction}"

            logger.info(f"✅ Moving {direction}...")

            # Wait for specified duration
            await asyncio.sleep(duration)

            # Send stop command
            stop_cmd = f"{commands[direction]}_stop"
            await self.http_client.post(
                f"{ROBOT_URL}/control",
                content=stop_cmd
            )

            logger.info(f"✅ Movement {direction} completed")
            return f"Moved {direction} for {duration} seconds"

        except httpx.TimeoutException:
            logger.error("⏱️ Robot connection timeout")
            return "Robot connection timeout"
        except Exception as e:
            logger.error(f"❌ Movement error: {e}")
            return f"Movement failed: {str(e)}"

    async def stop(self) -> str:
        """Emergency stop - immediately halt all motors"""
        logger.info("🛑 EMERGENCY STOP CALLED")

        try:
            # Send stop commands for all directions
            stop_commands = ["forward_stop", "backward_stop", "left_stop", "right_stop"]

            for cmd in stop_commands:
                await self.http_client.post(
                    f"{ROBOT_URL}/control",
                    content=cmd,
                    timeout=2.0
                )

            logger.info("✅ All motors stopped")
            return "All motors stopped"

        except Exception as e:
            logger.error(f"❌ Stop error: {e}")
            return f"Stop command failed: {str(e)}"

    async def set_speed(self, action: str) -> str:
        """Adjust robot speed"""
        logger.info(f"⚡ SPEED CONTROL: {action}")

        try:
            cmd = "speed+" if action == "increase" else "speed-"
            response = await self.http_client.post(
                f"{ROBOT_URL}/control",
                content=cmd
            )

            if response.status_code == 200:
                logger.info(f"✅ Speed {action}d")
                return f"Speed {action}d"
            else:
                return f"Failed to {action} speed"

        except Exception as e:
            logger.error(f"❌ Speed control error: {e}")
            return f"Speed control failed: {str(e)}"

    async def check_distance(self) -> str:
        """Query ultrasonic distance sensor"""
        logger.info("📏 CHECKING DISTANCE")

        try:
            response = await self.http_client.get(f"{ROBOT_URL}/get_distance")

            if response.status_code == 200:
                data = response.json()
                distance = data.get('distance', 0)
                logger.info(f"📏 Distance: {distance} cm")
                return f"Distance to obstacle: {distance:.1f} centimeters"
            else:
                return "Failed to read distance sensor"

        except Exception as e:
            logger.error(f"❌ Distance check error: {e}")
            return f"Distance check failed: {str(e)}"

    async def auto_mode(self, action: str) -> str:
        """Control autonomous obstacle avoidance mode"""
        logger.info(f"🤖 AUTO MODE: {action}")

        try:
            cmd = "auto_start" if action == "start" else "auto_stop"
            response = await self.http_client.post(
                f"{ROBOT_URL}/control",
                content=cmd
            )

            if response.status_code == 200:
                logger.info(f"✅ Auto mode {action}ed")
                return f"Autonomous mode {action}ed"
            else:
                return f"Failed to {action} auto mode"

        except Exception as e:
            logger.error(f"❌ Auto mode error: {e}")
            return f"Auto mode control failed: {str(e)}"

    async def _process_complete_transcription(self, user_text: str):
        """Process a complete transcription after ensuring it's not a fragment"""
        try:
            # Add user message to history
            self.messages.append({"role": "user", "content": user_text})

            # Call Groq API with function calling
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                temperature=0.7,
                max_tokens=150,
                tools=self.tools,
                tool_choice="auto",
            )

            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            # Handle function calls
            if tool_calls:
                # Add the assistant's response with tool calls to history
                self.messages.append(response_message)

                # Process each tool call
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)

                    logger.info(f"🔧 Function call: {function_name}({function_args})")

                    # Execute the appropriate function
                    function_response = ""

                    if function_name == "movement":
                        direction = function_args["direction"]
                        duration = function_args.get("duration", None)
                        function_response = await self.movement(direction, duration)

                    elif function_name == "stop":
                        function_response = await self.stop()

                    elif function_name == "set_speed":
                        action = function_args["action"]
                        function_response = await self.set_speed(action)

                    elif function_name == "check_distance":
                        function_response = await self.check_distance()

                    elif function_name == "auto_mode":
                        action = function_args["action"]
                        function_response = await self.auto_mode(action)

                    else:
                        function_response = f"Unknown function: {function_name}"

                    # Add function response to history
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": function_response,
                    })

                # Get final response from the model after function execution
                second_response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=self.messages,
                    temperature=0.7,
                    max_tokens=150,
                )

                bot_text = second_response.choices[0].message.content
                logger.info(f"🤖 Bot: {bot_text}")

                # Add final assistant response to history
                self.messages.append({"role": "assistant", "content": bot_text})

            else:
                # No function call, regular response
                bot_text = response_message.content
                logger.info(f"🤖 Bot: {bot_text}")

                # Add assistant response to history
                self.messages.append({"role": "assistant", "content": bot_text})

            # Keep history manageable (last 10 messages + system)
            if len(self.messages) > 21:
                self.messages = [self.messages[0]] + self.messages[-20:]

            # Push response as new text frame
            from pipecat.frames.frames import TextFrame
            await self.push_frame(TextFrame(text=bot_text))

        except Exception as e:
            logger.error(f"Groq error: {e}")
            from pipecat.frames.frames import TextFrame
            await self.push_frame(TextFrame(text="Sorry, I encountered an error."))

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        # IMPORTANT: Only process FINAL transcriptions, not interim ones
        if isinstance(frame, TranscriptionFrame) and not isinstance(frame, InterimTranscriptionFrame):
            user_text = frame.text.strip()

            # Skip empty or very short transcriptions (likely fragments)
            word_count = len(user_text.split())
            if not user_text or word_count < 2:
                logger.debug(f"⏭️ Skipping short transcription: '{user_text}'")
                await self.push_frame(frame, direction)
                return

            # Skip if it's the same as the last transcription (duplicate)
            if user_text == self.last_transcription_text:
                logger.debug(f"⏭️ Skipping duplicate transcription: '{user_text}'")
                await self.push_frame(frame, direction)
                return

            # Check if this looks like a sentence fragment by checking for incomplete patterns
            # Skip single words or fragments like "You're", "Can.", "Robot."
            ends_with_sentence = user_text.endswith(('.', '!', '?'))
            if word_count < 3 and not ends_with_sentence:
                logger.debug(f"⏭️ Skipping likely fragment: '{user_text}' ({word_count} words)")
                await self.push_frame(frame, direction)
                return

            self.last_transcription_text = user_text
            logger.info(f"👤 User: {user_text}")

            await self._process_complete_transcription(user_text)

        else:
            # Pass through all other frames (including interim transcriptions)
            await self.push_frame(frame, direction)


async def main():
    """
    Voice bot with direct Gemini API integration
    """

    # Transport with adjusted VAD for longer pauses
    transport = LocalAudioTransport(
        LocalAudioTransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_enabled=True,
            vad_analyzer=SileroVADAnalyzer(
                # Balanced for noisy environments - responsive yet noise-resistant
                params=VADParams(
                    stop_secs=1.0,      # Wait 1 second of silence before stopping (balanced)
                    min_volume=0.75,    # Higher volume threshold to ignore background noise
                    start_secs=0.3,     # Reduced: Faster speech detection (was 0.4s)
                    confidence=0.8,     # High confidence to reduce false positives
                )
            ),
        )
    )

    # STT (Speech to Text)
    stt = DeepgramSTTService(
        api_key=os.getenv("DEEPGRAM_API_KEY"),
        model="nova-2",
        language="en",
        # Balanced endpointing for responsive yet accurate transcription
        params={
            "endpointing": 300,  # Wait 300ms before finalizing (good balance)
            "interim_results": False,  # Disable interim results completely
        }
    )

    # LLM (Our custom Groq processor with robot control)
    llm = GroqProcessor(
        api_key=os.getenv("GROQ_API_KEY"),
        model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")  # Use env variable or default
    )

    # Check robot controller connection
    logger.info(f"🔍 Checking robot controller at {ROBOT_URL}...")
    robot_connected = await llm.check_robot_connection()

    if robot_connected:
        logger.info("✅ Robot controller is online and ready")
    else:
        logger.warning("⚠️ Robot controller not available - voice commands will report errors")
        logger.warning("   Make sure robot_controller.py is running on the Raspberry Pi")

    # TTS (Text to Speech) with extended timeout for slow connections
    tts = CartesiaTTSService(
        api_key=os.getenv("CARTESIA_API_KEY"),
        voice_id="a0e99841-438c-4a64-b679-ae501e7d6091",
    )

    # Simple pipeline
    pipeline = Pipeline(
        [
            transport.input(),      # Microphone input
            stt,                    # Deepgram: Audio → Text
            llm,                    # Our Groq: Text → Response Text (with robot control)
            tts,                    # Cartesia: Text → Audio
            transport.output(),     # Speaker output
        ]
    )

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            allow_interruptions=True,
            enable_metrics=True,
            enable_usage_metrics=False,  # Reduce overhead
        ),
    )

    runner = PipelineRunner()

    logger.info("=" * 60)
    logger.info("🤖 WRAITH Voice-Controlled Robot System Ready!")
    logger.info("=" * 60)
    logger.info(f"📡 Pipeline: Deepgram STT → Groq ({llm.model}) → Cartesia TTS")
    logger.info(f"🤖 Robot Controller: {ROBOT_URL}")
    logger.info(f"⏱️ Movement Duration: {ROBOT_MOVEMENT_DURATION}s (max: {ROBOT_MAX_DURATION}s)")
    logger.info("✨ Advanced autonomous service robot - FAST NUCES, Pakistan")
    logger.info("")
    logger.info("Available Voice Commands:")
    logger.info("  • Movement: 'move forward/backward/left/right'")
    logger.info("  • Stop: 'stop', 'halt', 'emergency stop'")
    logger.info("  • Speed: 'go faster', 'slow down'")
    logger.info("  • Distance: 'check distance', 'any obstacles?'")
    logger.info("  • Auto Mode: 'start auto mode', 'stop auto mode'")
    logger.info("")
    logger.info("🎤 Start speaking to control WRAITH...")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 60)

    try:
        await runner.run(task)
    finally:
        # Cleanup: close HTTP client
        await llm.http_client.aclose()
        logger.info("✅ Cleaned up resources")


if __name__ == "__main__":
    asyncio.run(main())
