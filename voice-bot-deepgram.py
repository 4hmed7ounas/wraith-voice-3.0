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


class GroqProcessor(FrameProcessor):
    """Custom processor that calls Groq API directly"""

    def __init__(self, api_key: str, model: str = "llama-3.1-8b-instant"):
        super().__init__()

        # Initialize Groq client
        self.client = AsyncGroq(api_key=api_key)
        self.model = model

        # Define available functions for function calling
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "movement",
                    "description": "Controls the robot's movement in a specified direction. Use this when the user asks to move forward, backward, left, or right.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "direction": {
                                "type": "string",
                                "enum": ["forward", "backward", "left", "right"],
                                "description": "The direction to move the robot"
                            }
                        },
                        "required": ["direction"]
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
- Movement control via voice commands (forward, backward, left, right)
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
- When the user asks you to move, use the movement function to control the robot"""
            }
        ]

        # Transcription buffering to avoid partial responses
        self.last_transcription_text = ""
        self.transcription_task = None

        logger.info(f"✅ Groq {model} initialized with movement function")

    def movement(self, direction: str) -> str:
        """Handle movement commands"""
        logger.info(f"🚀 MOVEMENT FUNCTION CALLED: Moving {direction.upper()}")
        print(f"\n{'='*50}")
        print(f"🤖 ROBOT MOVING: {direction.upper()}")
        print(f"{'='*50}\n")
        return f"Moving {direction}"

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

                    # Execute the function
                    if function_name == "movement":
                        function_response = self.movement(function_args["direction"])

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
        language="hi",
        # Balanced endpointing for responsive yet accurate transcription
        params={
            "endpointing": 300,  # Wait 300ms before finalizing (good balance)
            "interim_results": False,  # Disable interim results completely
        }
    )

    # LLM (Our custom Groq processor)
    llm = GroqProcessor(
        api_key=os.getenv("GROQ_API_KEY"),
        model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")  # Use env variable or default
    )

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
            llm,                    # Our Gemini: Text → Response Text
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

    logger.info("🤖 WRAITH Voice Assistant Ready!")
    logger.info(f"📡 Pipeline: Deepgram STT → Groq ({llm.model}) → Cartesia TTS")
    logger.info("✨ Advanced autonomous service robot - FAST NUCES, Pakistan")
    logger.info("🎤 Start speaking to interact with WRAITH...")
    logger.info("Press Ctrl+C to stop")

    await runner.run(task)


if __name__ == "__main__":
    asyncio.run(main())
