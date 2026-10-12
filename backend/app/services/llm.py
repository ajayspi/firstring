"""GPT-4.1 integration with function calling"""
import openai
import os
from typing import List, Dict, Any, Optional
import json

client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT_TEMPLATE = """[STATIC — cached at session start]
You are an AI phone ordering assistant for {restaurant_name}.
You take orders clearly and confirm before finalising.
Today is {date}. Current time: {time}.
Restaurant closes at {closing_time}.

[RESTAURANT CONTEXT — cached per session]
Menu: {rag_menu}
Special instructions: {ai_instructions}
Payment: Customer will receive SMS with payment link after order confirmed.

[CALL STATE — updated each turn]
Current state: {state}
Items in order: {order_items_so_far}
"""

FUNCTIONS = [
    {
        "name": "add_item",
        "description": "Add item to order",
        "parameters": {
            "type": "object",
            "properties": {
                "menu_item_id": {"type": "string"},
                "quantity": {"type": "integer", "minimum": 1},
                "modifiers": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["menu_item_id", "quantity"],
        },
    },
    {
        "name": "remove_item",
        "description": "Remove item from order",
        "parameters": {
            "type": "object",
            "properties": {
                "menu_item_id": {"type": "string"},
            },
            "required": ["menu_item_id"],
        },
    },
    {
        "name": "confirm_order",
        "description": "Confirm order and proceed to payment",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "transfer_to_human",
        "description": "Transfer call to human operator",
        "parameters": {
            "type": "object",
            "properties": {
                "reason": {"type": "string"},
            },
            "required": ["reason"],
        },
    },
]


async def generate_response(
    messages: List[Dict],
    restaurant_name: str,
    date: str,
    time: str,
    closing_time: str,
    rag_menu: str,
    ai_instructions: str,
    state: str,
    order_items: List[Dict],
) -> Dict:
    """Generate AI response with function calling"""
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        restaurant_name=restaurant_name,
        date=date,
        time=time,
        closing_time=closing_time,
        rag_menu=rag_menu,
        ai_instructions=ai_instructions,
        state=state,
        order_items_so_far=json.dumps(order_items),
    )

    response = await client.chat.completions.create(
        model="gpt-4.1",
        messages=[{"role": "system", "content": system_prompt}] + messages,
        functions=FUNCTIONS,
        function_call="auto",
        temperature=0.3,
        max_tokens=500,
    )

    return response.choices[0].message