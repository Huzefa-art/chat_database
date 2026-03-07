from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .llm import llm

import os
import re
import json

from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import AIMessage

from .models import ChatSession, ChatMessage
from .prompts import (
    GATE_CHECK_PROMPT,
    SQL_REACT_PROMPT,
    ANSWER_AGENT_PROMPT,
    DIRECT_REPLY_PROMPT,
)

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.settings import api_settings

User = get_user_model()


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def get_sql_db():
    db_uri = (
        f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:"
        f"{os.getenv('POSTGRES_PASSWORD')}@"
        f"{os.getenv('DB_HOST', 'localhost')}:"
        f"{os.getenv('DB_PORT', '5432')}/"
        f"{os.getenv('POSTGRES_DB')}"
    )
    return SQLDatabase.from_uri(db_uri)


def build_history_context(recent_messages: list) -> str:
    """Build a plain-text history string from recent DB messages."""
    if not recent_messages:
        return ""
    lines = []
    for msg in recent_messages:
        role = "User" if msg.role == "user" else "Assistant"
        lines.append(f"{role}: {msg.content}")
    return "\n".join(lines)


def build_agent_history(recent_messages: list, question: str) -> list:
    """Build LangGraph message list from recent DB messages + current question."""
    history = []
    for msg in recent_messages:
        if msg.role == "user":
            history.append({"role": "user", "content": msg.content})
        elif msg.role == "assistant":
            # Stripped — avoid confusing the SQL agent with old formatted answers
            history.append({"role": "assistant", "content": "Answered using the database."})
    history.append({"role": "user", "content": question})
    return history


def extract_response_tag(raw: str) -> dict:
    """
    Extract JSON from <response>...</response> tags.
    Returns dict with at minimum a 'summary' key.
    """
    match = re.search(r"<response>(.*?)</response>", raw, re.DOTALL)
    if match:
        content = match.group(1).strip()
        try:
            return json.loads(content)
        except Exception:
            return {"summary": content, "chart": {"type": None}}
    return {"summary": raw.strip(), "chart": {"type": None}}


def save_assistant_message(chat_session, final_answer: str, sql_queries: list, parsed: dict):
    """Save the assistant response to DB."""
    ChatMessage.objects.create(
        chat=chat_session,
        role="assistant",
        content=final_answer,
        response_json={
            "sql_queries": sql_queries,
            "sql_query": sql_queries[-1] if sql_queries else None,
            "summary": final_answer,
            "data": [],
            "chart": parsed.get("chart", {"type": None}),
        }
    )


def update_session_title(chat_session, question: str):
    if chat_session.title == "New Chat":
        chat_session.title = question[:80]
        chat_session.save()


def build_response(chat_id, question, final_answer, sql_queries, parsed, route):
    return Response({
        "status": "success",
        "chat_id": chat_id,
        "question": question,
        "answer": final_answer,
        "summary": final_answer,
        "data": [],
        "chart": parsed.get("chart", {"type": None}),
        "sql_queries": sql_queries,
        "sql_query": sql_queries[-1] if sql_queries else None,
        "route": route,
    })


# ─────────────────────────────────────────────────────────────────────────────
# AUTH VIEWS
# ─────────────────────────────────────────────────────────────────────────────

@api_view(["POST"])
def signup(request):
    username = request.data.get("username")
    password = request.data.get("password")
    email = request.data.get("email", "")

    if not username or not password:
        return Response({"error": "Username and password are required"}, status=400)
    if User.objects.filter(username=username).exists():
        return Response({"error": "Username already exists"}, status=400)

    user = User.objects.create_user(username=username, password=password, email=email)
    return Response({"message": "User created successfully", "user_id": user.id, "username": user.username}, status=201)


class CreateTokenView(ObtainAuthToken):
    serializer_class = AuthTokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES

    def post(self, request, *args, **kwargs):
        email_or_username = request.data.get("email") or request.data.get("username")
        password = request.data.get("password")

        user = None
        existing_user = None

        try:
            if "@" in email_or_username:
                existing_user = User.objects.get(email=email_or_username)
            else:
                existing_user = User.objects.get(username=email_or_username)
        except User.DoesNotExist:
            existing_user = None

        if existing_user:
            serializer = self.serializer_class(
                data={"username": existing_user.username, "password": password},
                context={"request": request}
            )
            try:
                serializer.is_valid(raise_exception=True)
                user = serializer.validated_data["user"]
            except Exception:
                user = None

        if user is None:
            return Response({"detail": _("Login failed.")}, status=status.HTTP_401_UNAUTHORIZED)

        token, created = Token.objects.get_or_create(user=user)

        if not getattr(user, "verified", True):
            return Response({"detail": _("Account not verified.")}, status=status.HTTP_401_UNAUTHORIZED)

        return Response({
            "token": token.key,
            "user_id": user.id,
            "email": user.email,
            "verified": user.verified,
        })


# ─────────────────────────────────────────────────────────────────────────────
# CHAT SESSION VIEWS
# ─────────────────────────────────────────────────────────────────────────────

@api_view(["POST"])
def start_chat(request):
    user_id = request.data.get("user_id")
    title = request.data.get("title", "New Chat")
    user = None

    if user_id:
        try:
            user = User.objects.get(id=user_id)
        except (User.DoesNotExist, ValueError):
            return Response({"error": f"User with ID {user_id} not found"}, status=404)

    if not user and request.user.is_authenticated:
        user = request.user

    if not user:
        return Response({"error": "Authentication required"}, status=401)

    session = ChatSession.objects.create(user=user, title=title)
    return Response({"chat_id": session.id, "title": session.title})


@api_view(["POST", "PUT", "DELETE"])
def manage_chat_session(request, chat_id=None):
    if not chat_id:
        chat_id = request.data.get("chat_id")
    if not chat_id:
        return Response({"error": "chat_id is required"}, status=400)

    try:
        session = ChatSession.objects.get(id=chat_id)
    except ChatSession.DoesNotExist:
        return Response({"error": "Invalid chat_id"}, status=404)

    if request.method == "PUT":
        title = request.data.get("title")
        if not title:
            return Response({"error": "title is required"}, status=400)
        session.title = title
        session.save()
        return Response({"message": "Updated", "chat_id": session.id, "title": session.title})

    elif request.method == "DELETE":
        session.delete()
        return Response({"message": "Deleted", "chat_id": chat_id})

    return Response({"error": "Method not allowed"}, status=405)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN CHAT VIEW
# Flow: Gate Check → SQL ReAct Agent → Answer Agent
#                 → Direct Reply (NO path)
# ─────────────────────────────────────────────────────────────────────────────

@api_view(["POST"])
def chat(request):
    try:
        question = request.data.get("question", "").strip()
        chat_id = request.data.get("chat_id")

        if not chat_id:
            return Response({"error": "chat_id is required"}, status=400)
        if not question:
            return Response({"error": "Missing 'question' in request body"}, status=400)

        # ── 1. Validate chat session ──────────────────────────────────────────
        try:
            chat_session = ChatSession.objects.get(id=chat_id)
        except ChatSession.DoesNotExist:
            return Response({"error": "Chat session not found"}, status=404)

        # ── 2. Load last 6 messages (3 Q&A pairs) ────────────────────────────
        recent_messages = list(
            chat_session.messages
            .filter(role__in=["user", "assistant"])
            .order_by("-created_at")[:6]
        )
        recent_messages.reverse()

        # ── 3. Build history representations ─────────────────────────────────
        history_context = build_history_context(recent_messages)
        agent_history = build_agent_history(recent_messages, question)

        # ── 4. Save user message ──────────────────────────────────────────────
        ChatMessage.objects.create(chat=chat_session, role="user", content=question)

        # ─────────────────────────────────────────────────────────────────────
        # STEP 1: GATE CHECK
        # Ask: is this question clear enough to run a SQL query?
        # Provides schema table list + history so follow-ups resolve correctly.
        # ─────────────────────────────────────────────────────────────────────
        gate_input = GATE_CHECK_PROMPT.format(
            history_context=history_context or "No prior conversation.",
            question=question,
        )
        gate_result = llm.invoke(gate_input).content.strip().upper()
        is_sql_query = gate_result.startswith("YES")

        print(f"[GATE CHECK] question='{question}' → '{gate_result}' → sql={is_sql_query}")

        # ─────────────────────────────────────────────────────────────────────
        # PATH: NO — not a database question
        # Direct reply handles greetings, vague, follow-ups, capability Q's
        # ─────────────────────────────────────────────────────────────────────
        if not is_sql_query:
            direct_input = DIRECT_REPLY_PROMPT.format(
                history_context=history_context or "No prior conversation.",
                question=question,
            )
            final_answer = llm.invoke(direct_input).content.strip()
            parsed = {"chart": {"type": None}}

            save_assistant_message(chat_session, final_answer, [], parsed)
            update_session_title(chat_session, question)

            return build_response(chat_id, question, final_answer, [], parsed, route="direct_reply")

        # ─────────────────────────────────────────────────────────────────────
        # PATH: YES — run the SQL ReAct agent
        # ReAct loop: Think → Write SQL → Execute → See result/error → Retry
        # ─────────────────────────────────────────────────────────────────────

        # ── STEP 2: SQL REACT AGENT ───────────────────────────────────────────
        sql_db = get_sql_db()
        tools = [QuerySQLDatabaseTool(db=sql_db)]

        # Inject history into the system prompt so the agent resolves pronouns
        system_prompt = SQL_REACT_PROMPT.format(
            history_context=(
                f"### CONVERSATION HISTORY:\n{history_context}"
                if history_context else ""
            )
        )

        agent_executor = create_react_agent(llm, tools, prompt=system_prompt)
        result = agent_executor.invoke({"messages": agent_history})
        agent_messages = result["messages"]

        # Extract all SQL queries the agent tried (including retries)
        sql_queries = [
            tool_call["args"].get("query", "")
            for msg in agent_messages
            if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None)
            for tool_call in msg.tool_calls
            if tool_call["name"] == "sql_db_query"
        ]

        # Raw result from the agent's final message
        raw_agent_answer = agent_messages[-1].content

        print(f"[SQL AGENT] queries attempted: {len(sql_queries)}")
        print(f"[SQL AGENT] final message: {raw_agent_answer[:200]}")

        # ── STEP 3: ANSWER AGENT ──────────────────────────────────────────────
        # Takes raw SQL output and formats into human-readable summary + chart
        answer_input = ANSWER_AGENT_PROMPT.format(
            question=question,
            data=raw_agent_answer,
        )
        answer_raw = llm.invoke(answer_input).content.strip()
        parsed = extract_response_tag(answer_raw)
        final_answer = parsed.get("summary", answer_raw)

        save_assistant_message(chat_session, final_answer, sql_queries, parsed)
        update_session_title(chat_session, question)

        return build_response(chat_id, question, final_answer, sql_queries, parsed, route="sql_agent")

    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({"error": "Internal server error"}, status=500)


# ─────────────────────────────────────────────────────────────────────────────
# HISTORY & SESSION LIST VIEWS
# ─────────────────────────────────────────────────────────────────────────────

@api_view(["GET"])
def load_chathistory(request):
    chat_id = request.query_params.get("chat_id")
    if not chat_id:
        return Response({"error": "chat_id is required"}, status=400)

    try:
        session = ChatSession.objects.get(id=chat_id)
    except ChatSession.DoesNotExist:
        return Response({"error": "Invalid chat_id"}, status=404)

    messages = session.messages.all().order_by("created_at")
    history_data = []

    for msg in messages:
        msg_data = {
            "role": msg.role,
            "content": msg.content,
            "summary": msg.content if msg.role == "assistant" else None,
            "data": [],
            "chart": {"type": None, "labels": [], "datasets": []},
            "chat_id": chat_id,
            "created_at": msg.created_at.isoformat(),
        }
        if msg.role == "assistant" and msg.response_json:
            msg_data.update(msg.response_json)
        history_data.append(msg_data)

    return Response({"messages": history_data})


@api_view(["GET"])
def list_chats(request):
    user_id = request.query_params.get("user_id")
    if not user_id:
        return Response({"error": "user_id is required"}, status=400)

    sessions = ChatSession.objects.filter(user_id=user_id).order_by("-updated_at")
    data = [{"id": s.id, "title": s.title, "updated_at": s.updated_at} for s in sessions]
    return Response(data)
