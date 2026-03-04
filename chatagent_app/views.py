from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .services import (
    run_sql, analyze_query_intent, 
    sql_agent, clarification_agent, context_agent,
    fallback_agent
)
from .llm import llm
from .models import ChatSession, ChatMessage
from django.contrib.auth import authenticate, get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.settings import api_settings

User = get_user_model()




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
    """Create a new auth token for user."""

    serializer_class = AuthTokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES

    def post(self, request, *args, **kwargs):
        email_or_username = request.data.get("email") or request.data.get("username")
        password = request.data.get("password")

        print(f"[CreateTokenView] Received login request for: {email_or_username}")

        user = None
        existing_user = None
        
        # 1. Check local database
        try:
            # Try lookup by email or username
            if "@" in email_or_username:
                existing_user = User.objects.get(email=email_or_username)
            else:
                existing_user = User.objects.get(username=email_or_username)
        except User.DoesNotExist:
            existing_user = None

        # 2. Authenticate local user
        if existing_user:
            print(f"[CreateTokenView] Local user detected: {existing_user.username}. Using ModelBackend.")
            serializer = self.serializer_class(
                data={'username': existing_user.username, 'password': password},
                context={'request': request}
            )
            try:
                serializer.is_valid(raise_exception=True)
                user = serializer.validated_data['user']
            except Exception as e:
                print(f"[CreateTokenView] Auth failed: {e}")
                user = None

        if user is None:
            print(f"[CreateTokenView] Login failed for {email_or_username}")
            return Response({
                'detail': _('Login failed. Please check your username and password.')
            }, status=status.HTTP_401_UNAUTHORIZED)

        # 3. Token and Verification
        token, created = Token.objects.get_or_create(user=user)
        print(f"[CreateTokenView] Token {'created' if created else 'retrieved'}: {token.key}")

        if not getattr(user, 'verified', True):
            print(f"[CreateTokenView] User verified={user.verified}, denying access.")
            return Response({
                'detail': _('Your account is not verified. Please contact your administrator.')
            }, status=status.HTTP_401_UNAUTHORIZED)

        print(f"[CreateTokenView] Login success for {user.username}. Returning token.")
        return Response({
            'token': token.key,
            'user_id': user.id,
            'email': user.email,
            'verified': user.verified
        })

@api_view(["POST"])
def start_chat(request):
    """
    Creates a new chat session and returns the chat_id.
    """
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
         return Response({"error": "Authentication required to start a chat"}, status=401)
        
    session = ChatSession.objects.create(user=user, title=title)
    return Response({"chat_id": session.id, "title": session.title})

@api_view(["POST", "PUT", "DELETE"])
def manage_chat_session(request, chat_id=None):
    """
    Manages a specific chat session (Update Title, Delete).
    For creation, use start_chat via POST.
    """
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
            return Response({"error": "title is required for update"}, status=400)
        session.title = title
        session.save()
        return Response({"message": "Chat title updated", "chat_id": session.id, "title": session.title})

    elif request.method == "DELETE":
        session.delete()
        return Response({"message": "Chat session deleted", "chat_id": chat_id})

    return Response({"error": "Method not allowed"}, status=405)

@api_view(["POST"])
def chat(request):
    question = request.data.get("question")
    chat_id = request.data.get("chat_id")
    
    # 1. Handle Session (Required)
    if not chat_id:
        return Response({"error": "chat_id is required"}, status=400)
        
    try:
        session = ChatSession.objects.get(id=chat_id)
    except ChatSession.DoesNotExist:
        return Response({"error": "Invalid chat_id"}, status=400)

    # Update Title if it's the first message
    if session.title == "New Chat" and question:
        session.title = question[:50]
        session.save()

    # 2. Retrieve History (Last 10 messages for context)
    history_objs = session.messages.all().order_by('-created_at')[:10][::-1]
    history_text = "\n".join([f"{msg.role.capitalize()}: {msg.content}" for msg in history_objs])

    # Save User Message
    ChatMessage.objects.create(chat=session, role="user", content=question)

    # 3. Modular Agent Orchestration
    # First Step: Router Agent decides the intent
    intent = analyze_query_intent(question, llm, history=history_text)
    
    # Dispatch based on intent
    if intent == "run_sql":
        # Structured Query -> SQL Agent
        answer = sql_agent(question, llm, history=history_text)
    elif intent == "clarify":
        # Ambiguous Query -> Clarification Agent
        answer = clarification_agent(question, llm, history=history_text)
    elif intent == "rate_limit":
        # Global Rate Limit hit in Router
        answer = {
            "summary": "I'm currently hitting usage limits. Please try again in a few minutes.",
            "data": [],
            "chart": {"type": None}
        }
    else:
        answer = context_agent(question, llm, history=history_text)

    # 4. Fallback Layer: Catch unhelpful responses
    answer = fallback_agent(question, answer, llm, history=history_text, intent=intent)

    # 5. Final Processing and Logging
    answer["chat_id"] = chat_id
    ChatMessage.objects.create(
        chat=session, 
        role="assistant", 
        content=answer.get("summary", ""), 
        response_json=answer
    )

    return Response(answer)

@api_view(["GET"])
def load_chathistory(request):
    """
    Returns the full history of a chat session in a structured format.
    """
    chat_id = request.query_params.get("chat_id")
    if not chat_id:
        return Response({"error": "chat_id is required"}, status=400)
    
    try:
        session = ChatSession.objects.get(id=chat_id)
    except ChatSession.DoesNotExist:
        return Response({"error": "Invalid chat_id"}, status=404)
    
    messages = session.messages.all().order_by('created_at')
    
    history_data = []
    for msg in messages:
        msg_data = {
            "role": msg.role,
            "content": msg.content,
            "summary": msg.content if msg.role == "assistant" else None,
            "data": [],
            "chart": {"type": None, "labels": [], "datasets": []},
            "chat_id": chat_id,
            "created_at": msg.created_at.isoformat()
        }
        if msg.role == "assistant" and msg.response_json:
            # Update with stored structured data
            msg_data.update(msg.response_json)
        
        history_data.append(msg_data)
            
    return Response({"messages": history_data})

@api_view(["GET"])
def list_chats(request):
    """
    Returns all chat sessions for a specific user.
    """
    user_id = request.query_params.get("user_id")
    if not user_id:
        return Response({"error": "user_id is required"}, status=400)
    
    sessions = ChatSession.objects.filter(user_id=user_id).order_by('-updated_at')
    data = [{"id": s.id, "title": s.title, "updated_at": s.updated_at} for s in sessions]
    
    return Response(data)
