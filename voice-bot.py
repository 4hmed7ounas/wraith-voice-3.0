#
# Copyright (c) 2024–2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""Voice-Only Chatbot Implementation.

This module implements a streamlined voice chatbot with:
- Speech-to-text (automatic via transport)
- Gemini AI for language understanding and response generation
- Text-to-speech using Cartesia
- Voice activity detection

Flow: User Speech → STT → Gemini LLM → Cartesia TTS → Audio Output
"""

import os

from dotenv import load_dotenv
from loguru import logger
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.frames.frames import LLMRunFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.processors.frameworks.rtvi import RTVIConfig, RTVIObserver, RTVIProcessor
from pipecat.runner.types import RunnerArguments
from pipecat.services.cartesia.tts import CartesiaTTSService
from pipecat.services.gemini_multimodal_live.gemini import GeminiMultimodalLiveLLMService
from pipecat.transports.base_transport import BaseTransport
from pipecat.transports.daily.transport import DailyParams, DailyTransport

load_dotenv(override=True)


async def run_bot(transport: BaseTransport):
    """Main bot execution function.

    Sets up and runs the voice bot pipeline:
    1. User speaks (captured by transport)
    2. Speech automatically converted to text (Daily transcription)
    3. Text sent to Gemini LLM for processing
    4. Gemini generates response text
    5. Cartesia converts text to speech
    6. Audio output to user
    """

    # Initialize Cartesia text-to-speech service
    tts = CartesiaTTSService(
        api_key=os.getenv("CARTESIA_API_KEY"),
        voice_id="a0e99841-438c-4a64-b679-ae501e7d6091",  # Cartesia default voice
    )

    # Initialize Gemini LLM service
    llm = GeminiMultimodalLiveLLMService(
        api_key=os.getenv("GEMINI_API_KEY"),
        # Note: Not using Gemini's built-in TTS, will use Cartesia instead
    )

    messages = [
        {
            "role": "user",
            "content": "You are a friendly, helpful voice assistant. Your responses will be converted to speech, so keep them natural and conversational. Don't use special characters or formatting. Be concise but helpful. Start by introducing yourself briefly.",
        },
    ]

    # Set up conversation context
    context = OpenAILLMContext(messages)
    context_aggregator = llm.create_context_aggregator(context)

    # RTVI for client synchronization
    rtvi = RTVIProcessor(config=RTVIConfig(config=[]))

    # Voice-only pipeline (no video/animation)
    pipeline = Pipeline(
        [
            transport.input(),  # Audio input from user
            rtvi,  # Client sync
            context_aggregator.user(),  # Collect user context
            llm,  # Gemini processes and generates response
            tts,  # Cartesia converts to speech
            transport.output(),  # Audio output
            context_aggregator.assistant(),  # Collect assistant context
        ]
    )

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
        observers=[RTVIObserver(rtvi)],
    )

    @rtvi.event_handler("on_client_ready")
    async def on_client_ready(rtvi):
        await rtvi.set_bot_ready()
        # Start the conversation
        await task.queue_frames([LLMRunFrame()])

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, participant):
        logger.info(f"Client connected: {participant['id']}")
        # Enable transcription for speech-to-text
        await transport.capture_participant_transcription(participant["id"])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info("Client disconnected")
        await task.cancel()

    runner = PipelineRunner(handle_sigint=False)

    await runner.run(task)


async def bot(runner_args: RunnerArguments):
    """Main bot entry point."""

    transport = DailyTransport(
        runner_args.room_url,
        runner_args.token,
        "Voice Assistant",
        params=DailyParams(
            audio_in_enabled=True,  # Receive user audio
            audio_out_enabled=True,  # Send bot audio
            video_out_enabled=False,  # No video output
            vad_analyzer=SileroVADAnalyzer(),  # Voice activity detection
            transcription_enabled=True,  # Enable STT
        ),
    )

    await run_bot(transport)


if __name__ == "__main__":
    from pipecat.runner.run import main

    main()
