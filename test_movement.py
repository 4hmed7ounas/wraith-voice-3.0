"""
Quick test script to verify movement function calling works
"""
import asyncio
import os
from dotenv import load_dotenv
from groq import AsyncGroq
import json

load_dotenv(override=True)

async def test_movement():
    """Test the movement function calling"""

    client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

    tools = [
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

    test_phrases = [
        "move forward",
        "go backward",
        "turn left",
        "move right"
    ]

    print("=" * 60)
    print("Testing Movement Function Calls")
    print("=" * 60)

    for phrase in test_phrases:
        print(f"\nTesting: '{phrase}'")
        print("-" * 60)

        messages = [
            {
                "role": "system",
                "content": "You are a robot assistant. When the user asks you to move, use the movement function."
            },
            {
                "role": "user",
                "content": phrase
            }
        ]

        response = await client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )

        response_message = response.choices[0].message

        if response_message.tool_calls:
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)

                print(f"[SUCCESS] Function Called: {function_name}")
                print(f"Arguments: {function_args}")
                print(f"Direction: {function_args['direction'].upper()}")
        else:
            print(f"[FAIL] No function call - Regular response: {response_message.content}")

    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_movement())
