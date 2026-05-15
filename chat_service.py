"""
ChatService — Python/Flask equivalent of chats.service.ts.

Implements the same LangGraph state machine architecture:
  START → agent node → (tool_calls?) → tools node → agent node → END

Key design decisions mirrored from the original TypeScript:
  - Same graph topology (agent + tools nodes, conditional edges)
  - MongoDBSaver for conversation checkpointing (thread_id persistence)
  - Google Gemini via langchain-google-genai
  - Pydantic OrderSchema instead of Zod for the create_order tool
  - Same JSON response envelope: message, current_order, suggestions, progress
"""

import os
import re
import json
import logging
from typing import Annotated, Sequence

from pymongo import MongoClient
from pymongo.collection import Collection

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.mongodb import MongoDBSaver

from pydantic import BaseModel as PydanticBaseModel
from typing_extensions import TypedDict

from orders import OrderSchema, get_order_schema_description
from drinks import DrinkSchema
from menu_data import DRINKS
from summaries import (
    create_drink_item_summary,
    create_sweeteners_summary,
    create_available_milks_summary,
    create_syrups_summary,
    create_sizes_summary,
    available_toppings_summary,
)

logger = logging.getLogger(__name__)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
MONGO_URI = os.getenv("MONGO_URI", "")
DATABASE_NAME = "drinks_db"
ORDERS_COLLECTION = "orders"


# ─────────────────────────────────────────────
# LangGraph State
# Equivalent to the Annotation.Root({ messages }) in the TypeScript version.
# add_messages reducer appends new messages to the list rather than replacing.
# ─────────────────────────────────────────────
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]


# ─────────────────────────────────────────────
# System prompt builder
# Equivalent to the ChatPromptTemplate.fromMessages([{ role: 'system', content: `...` }])
# constructed inside callModal() in the original TypeScript.
# ─────────────────────────────────────────────
def build_system_prompt() -> str:
    drinks_summary = "\n".join(
        f"  - {create_drink_item_summary(drink)}" for drink in DRINKS
    )
    order_schema_desc = get_order_schema_description()
    drink_schema_fields = "\n".join(
        f"  - {field}" for field in DrinkSchema.model_fields.keys()
    )

    return f"""
You are a helpful assistant that helps users order drinks from Starbucks.
Your job is to take the user's request and fill in any missing details based on how a complete order should look.
A complete order follows this structure:
{order_schema_desc}

**TOOLS**
You have access to a "create_order" tool.
Use this tool when the user confirms the final order.
After calling the tool, inform the user whether the order was successfully created or if it failed.

**DRINK DETAILS**
Each drink has its own set of properties such as size, milk, syrup, sweetener, and toppings.
Drink schema fields: {drink_schema_fields}

You must ask for any missing details before creating the order.
If the user requests a modification that is not supported for the selected drink, tell them it is not possible.
If the user asks for something unrelated to drink orders, politely tell them you can only assist with drink orders.

**AVAILABLE OPTIONS**
List of available drinks and their allowed modifications:
{drinks_summary}

{create_sweeteners_summary()}

{available_toppings_summary()}

{create_available_milks_summary()}

{create_syrups_summary()}

{create_sizes_summary()}

If the user's query is unclear, tell them that the request is not clear.

**ORDER CONFIRMATION**
Once the order is ready, you must ask the user to confirm it.
If they confirm, immediately call the "create_order" tool.
Only respond after the tool completes, indicating success or failure.

**FRONTEND RESPONSE FORMAT**
You MUST wrap every response in a JSON block like this:

```json
{{
  "message": "Your conversational message to the user",
  "current_order": {{
    "drink": null,
    "size": null,
    "milk": null,
    "syrup": null,
    "sweeteners": null,
    "toppings": null,
    "quantity": null
  }},
  "suggestions": ["Option A", "Option B"],
  "progress": "in_progress"
}}
```

Set "progress" to "completed" once the order is successfully created.
Use null for any order fields not yet filled in.
Never omit the JSON block.

**IMPORTANT RULES**
- Be friendly, use emojis, and add a touch of humor ☕
- Use null for unfilled fields
- Never omit the JSON tracking block
"""


# ─────────────────────────────────────────────
# ChatService class
# Equivalent to the @Injectable() ChatService in chats.service.ts
# ─────────────────────────────────────────────
class ChatService:
    """
    Orchestrates the LangGraph conversational agent.
    Maintains a single MongoClient for the app lifetime (same pattern as the
    module-level `client` in chats.service.ts).
    """

    def __init__(self):
        self._mongo_client = MongoClient(MONGO_URI)
        self._db = self._mongo_client[DATABASE_NAME]
        self._orders_collection: Collection = self._db[ORDERS_COLLECTION]

    # ── Tool definition ──────────────────────────────────────────────────────
    # Equivalent to the `orderTool = tool(async ({ order }) => { ... })` block.
    # Decorated with @tool so LangGraph can bind it to the model.
    def _make_order_tool(self):
        orders_col = self._orders_collection

        @tool
        def create_order(
            drink: str,
            size: str,
            milk: str,
            syrup: str,
            sweeteners: str,
            toppings: str,
            quantity: int,
        ) -> str:
            """
            Creates a new drink order in the MongoDB database.
            Call this tool only when the user has confirmed their final order.

            Args:
                drink: The name of the drink (e.g. Latte, Cappuccino)
                size: The drink size (e.g. Tall, Grande, Venti)
                milk: The milk type (e.g. Oat Milk, Whole Milk)
                syrup: The syrup flavor (e.g. Vanilla Syrup, None)
                sweeteners: The sweetener (e.g. Stevia, None)
                toppings: The topping (e.g. Whipped Cream, None)
                quantity: Number of drinks (1-10)
            """
            try:
                # Validate via Pydantic before inserting (mirrors Mongoose schema validation)
                order = OrderSchema(
                    drink=drink,
                    size=size,
                    milk=milk,
                    syrup=syrup,
                    sweeteners=sweeteners,
                    toppings=toppings,
                    quantity=quantity,
                )
                orders_col.insert_one(order.model_dump())
                logger.info(f"Order created: {order.model_dump()}")
                return "Order created successfully"
            except Exception as e:
                logger.error(f"Failed to create order: {e}")
                return f"Failed to create the order: {str(e)}"

        return create_order

    # ── Agent node ───────────────────────────────────────────────────────────
    # Equivalent to the `callModal` async function in chats.service.ts.
    def _make_agent_node(self, llm_with_tools):
        system_prompt = build_system_prompt()

        async def call_model(state: AgentState):
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                MessagesPlaceholder(variable_name="messages"),
            ])
            formatted = await prompt.ainvoke({"messages": state["messages"]})
            result = await llm_with_tools.ainvoke(formatted)
            return {"messages": [result]}

        return call_model

    # ── Routing logic ────────────────────────────────────────────────────────
    # Equivalent to `shouldContinue` in chats.service.ts.
    @staticmethod
    def _should_continue(state: AgentState):
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return END

    # ── JSON extraction ──────────────────────────────────────────────────────
    # Equivalent to `extractJsonResponse()` in chats.service.ts.
    @staticmethod
    def _extract_json_response(content: str) -> dict:
        """
        Extracts the JSON block the model wraps its response in.
        Falls back to a structured error envelope if parsing fails.
        """
        if isinstance(content, list):
            # Gemini sometimes returns a list of content parts
            content = " ".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in content
            )

        match = re.search(r"```json\s*([\s\S]*?)\s*```", content, re.IGNORECASE)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError as e:
                logger.error(f"JSON parse error: {e}\nRaw: {match.group(1)}")

        # Try parsing the whole response as JSON (no fences)
        try:
            return json.loads(content.strip())
        except json.JSONDecodeError:
            pass

        # Return a fallback envelope so the frontend always gets valid JSON
        return {
            "message": content,
            "current_order": None,
            "suggestions": [],
            "progress": "in_progress",
        }

    # ── Main public method ───────────────────────────────────────────────────
    # Equivalent to `chatWithAgent({ thread_id, query })` in chats.service.ts.
    def chat_with_agent(self, *, thread_id: str, query: str) -> dict:
        """
        Runs the LangGraph state machine for one turn of conversation.
        The MongoDBSaver checkpointer persists the full message history
        keyed by thread_id, so every call automatically resumes from
        where the previous turn left off.
        """
        import asyncio

        async def _run():
            order_tool = self._make_order_tool()
            tools = [order_tool]

            llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                temperature=0,
                google_api_key=GOOGLE_API_KEY,
            ).bind_tools(tools)

            agent_node = self._make_agent_node(llm)
            tools_node = ToolNode(tools)

            # Build the graph — mirrors the StateGraph construction in chats.service.ts
            graph = (
                StateGraph(AgentState)
                .add_node("agent", agent_node)
                .add_node("tools", tools_node)
                .add_edge(START, "agent")
                .add_conditional_edges("agent", self._should_continue)
                .add_edge("tools", "agent")
                .compile(
                    checkpointer=MongoDBSaver(
                        client=self._mongo_client,
                        db_name=DATABASE_NAME,
                    )
                )
            )

            final_state = await graph.ainvoke(
                {"messages": [HumanMessage(content=query)]},
                config={
                    "configurable": {"thread_id": thread_id},
                    "recursion_limit": 15,
                },
            )

            last_message: AIMessage = final_state["messages"][-1]
            return self._extract_json_response(last_message.content)

        # Run the async graph in a fresh event loop (Flask is sync by default)
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(asyncio.run, _run())
                    return future.result()
            else:
                return loop.run_until_complete(_run())
        except RuntimeError:
            return asyncio.run(_run())
