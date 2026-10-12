"""LiveKit Agents pipeline"""
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli
from livekit import api
import os
from app.services.stt import stt_stream
from app.services.tts import tts_stream
from app.services.llm import generate_response, FUNCTIONS
import json


async def entrypoint(ctx: JobContext):
    """Main LiveKit agent entrypoint"""
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    
    # Get call metadata
    room = ctx.room
    metadata = json.loads(room.metadata) if room.metadata else {}
    restaurant_id = metadata.get("restaurant_id")
    call_sid = metadata.get("call_sid")
    caller_number = metadata.get("caller_number")

    # TODO: Fetch restaurant config from Supabase
    restaurant_name = "Mama's Pizzeria"
    closing_time = "22:00"
    ai_instructions = "Be friendly and efficient"
    
    # State machine
    state = "GREETING"
    order_items = []
    
    # Greeting
    greeting = f"Hi! Welcome to {restaurant_name}. What can I get you?"
    async for chunk in tts_stream(greeting):
        await ctx.room.local_participant.publish_audio(chunk)
    
    state = "TAKING_ORDER"
    
    # Main conversation loop
    async for event in ctx.room.events():
        if event.type == "audio":
            # Process STT
            pass
        elif event.type == "transcript":
            user_text = event.transcript
            
            # Generate LLM response
            messages = [{"role": "user", "content": user_text}]
            llm_response = await generate_response(
                messages=messages,
                restaurant_name=restaurant_name,
                date="2026-09-21",
                time="14:30",
                closing_time=closing_time,
                rag_menu="Menu items...",
                ai_instructions=ai_instructions,
                state=state,
                order_items=[],
            )
            
            if llm_response.function_call:
                # Handle function calls
                pass
            else:
                # Speak response
                async for chunk in tts_stream(llm_response.content):
                    await ctx.room.local_participant.publish_audio(chunk)


def main():
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))


if __name__ == "__main__":
    main()