import re
import json
from django.db import connection
from pgvector.django import L2Distance
from .models import ERPVectorDocument

from .prompts import ROUTER_PROMPT, SQL_GENERATION_PROMPT, SQL_FORMATTING_PROMPT, CLARIFICATION_PROMPT, CONTEXT_PROMPT

from decimal import Decimal
from datetime import date, datetime

def _serialize_data(obj):
    """
    Recursively converts non-serializable objects (Decimal, date, datetime) 
    into JSON-friendly formats.
    """
    if isinstance(obj, list):
        return [_serialize_data(i) for i in obj]
    if isinstance(obj, dict):
        return {k: _serialize_data(v) for k, v in obj.items()}
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    return obj

def safe_llm_invoke(llm, prompt):
    """
    Wrapper around llm.invoke to catch rate limits and other errors.
    Returns a mock response object with 'content' attribute.
    """
    try:
        return llm.invoke(prompt)
    except Exception as e:
        error_msg = str(e).lower()
        if "429" in error_msg or "rate_limit" in error_msg or "rate limit" in error_msg:
            # Create a mock response object that agents can handle
            class MockResponse:
                def __init__(self, content):
                    self.content = content
            
            # Return a special marker that agents will check for
            return MockResponse("RATE_LIMIT_EXCEEDED")
        raise e

def run_sql(query):
    """
    Executes a SELECT query on the ERP database and serializes the result.
    """
    clean_query = query.strip().upper()
    if not (clean_query.startswith("SELECT") or clean_query.startswith("WITH")):
         raise PermissionError("Only SELECT and WITH queries are allowed for security reasons.")
         
    with connection.cursor() as cursor:
        cursor.execute(query)
        columns = [col[0] for col in cursor.description]
        raw_results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return _serialize_data(raw_results)

def analyze_query_intent(question, llm, history=None):
    """
    Query Analyzer Agent (Router): Decides which agent should handle the question.
    """
    history_context = f"\nChat History:\n{history}" if history else ""
    
    prompt = ROUTER_PROMPT.format(history_context=history_context, question=question)
    response_obj = safe_llm_invoke(llm, prompt)
    response = response_obj.content.strip().lower()
    
    if "rate_limit_exceeded" in response:
        return "rate_limit"
    
    # Cleanup response in case of extra text
    if "run_sql" in response: return "run_sql"
    if "clarify" in response: return "clarify"
    return "answer_from_history"

def extract_json(test_str):
    """
    Robustly extracts JSON from a string that might contain chatter or markdown blocks.
    """
    # 1. Try markdown code blocks first
    match = re.search(r'```(?:json)?\n?(.*?)\n?```', test_str, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    # 2. Try to find the first '{' and last '}'
    start = test_str.find('{')
    end = test_str.rfind('}')
    if start != -1 and end != -1 and end > start:
        return test_str[start:end+1].strip()
        
    return test_str.strip()

def extract_between_tags(text, tag="response"):
    """
    Extracts content between XML-like tags.
    """
    pattern = f"<{tag}>(.*?)</{tag}>"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()

def extract_sql(test_str):
    """
    Extracts SQL query from LLM output, handling markdown or plain text chatter.
    """
    # Try markdown block first
    match = re.search(r'```(?:sql|postgresql|)?\n?(.*?)\n?```', test_str, re.I | re.DOTALL)
    if match:
        return match.group(1).strip()
    
    # Try to find SELECT or WITH ... up to the last semicolon or end of string
    sql_match = re.search(r'((?:SELECT|WITH)\s+.*)', test_str, re.I | re.DOTALL)
    if sql_match:
        sql = sql_match.group(1).strip()
        # Remove trailing junk if any (common with chatter after SQL)
        if ";" in sql:
            sql = sql.split(";")[0] + ";"
        return sql
        
    return test_str.strip()

def extract_json(test_str):
    """
    Robustly extracts JSON from a string that might contain chatter or markdown blocks.
    """
    # 1. Try tags first
    content = extract_between_tags(test_str)
    
    # 2. Try markdown code blocks
    match = re.search(r'```(?:json)?\n?(.*?)\n?```', content, re.DOTALL)
    if match:
        content = match.group(1).strip()
    
    # 3. Try to find the first '{' and last '}'
    start = content.find('{')
    end = content.rfind('}')
    if start != -1 and end != -1 and end > start:
        return content[start:end+1].strip()
        
    return content.strip()

def validate_output(result, raw_data=None, intent=None):
    """
    Business Logic Guard: Ensures the AI result is sensible, 
    matches the actual data, and follows strict schema rules.
    """
    if not isinstance(result, dict):
        result = {"summary": str(result)}

    # 1. Schema Enforcement
    result.setdefault("summary", "No summary provided.")
    result.setdefault("data", raw_data if raw_data is not None else [])
    result.setdefault("chart", {"type": None, "labels": [], "datasets": []})
    
    # Ensure chart structure is complete even if nested keys are missing
    if not isinstance(result["chart"], dict): result["chart"] = {"type": None}
    result["chart"].setdefault("type", None)
    result["chart"].setdefault("labels", [])
    result["chart"].setdefault("datasets", [])

    # 2. Empty Data Handling
    data_is_empty = not raw_data or (isinstance(raw_data, list) and len(raw_data) == 0)
    
    # NEW: Skip overwrite if intent is naturally data-less (clarification or conversation)
    skip_overwrite = intent in ["clarify", "answer_from_history"] or "rate limit" in result["summary"].lower()

    if data_is_empty and not skip_overwrite:
        # If no data found, ensure summary reflects this and chart is disabled
        lower_summary = result["summary"].lower()
        if "found" in lower_summary or "here is" in lower_summary or "based on" in lower_summary:
            result["summary"] = "I couldn't find any relevant data for your request."
        result["chart"]["type"] = None
        result["data"] = []

    # 3. Chart Sanity Checks
    chart_type = str(result["chart"].get("type", "")).lower()
    
    # Rule: Pie charts need at least 2 data points to make sense
    if chart_type == "pie" and len(raw_data) < 2:
        result["chart"]["type"] = "table"
        
    # Rule: Line charts usually need multiple points for a trend
    if chart_type == "line" and len(raw_data) < 2:
        result["chart"]["type"] = "table"
        
    # Rule: Change 'null' string to None type for frontend consistency
    if chart_type == "null" or chart_type == "none":
        result["chart"]["type"] = None

    return result


def generate_sql_from_llm(question, llm, history=None):
    """
    Helper to generate SQL from LLM using the standardized prompt and extraction logic.
    Used by sql_agent and evaluation scripts.
    """
    history_context = f"\nConversation History:\n{history}\n" if history else ""
    prompt = SQL_GENERATION_PROMPT.format(history_context=history_context, question=question)
    response_obj = safe_llm_invoke(llm, prompt)
    response = response_obj.content.strip()
    return extract_sql(response)

def sql_agent(question, llm, history=None):
    """
    SQL Agent: Generates SQL, executes it, and formats results into structured JSON.
    """
    # 1. Generate SQL
    sql = generate_sql_from_llm(question, llm, history)
    
    if "RATE_LIMIT_EXCEEDED" in sql:
        return validate_output({"summary": "I'm currently hitting usage limits. Please try again in a few minutes."}, [], intent="run_sql")

    if not (sql.upper().startswith("SELECT") or sql.upper().startswith("WITH")):
        return validate_output({"summary": "I could not generate a valid query for that."}, [], intent="run_sql")

    # 2. Run SQL
    try:
        data = run_sql(sql)
    except Exception as e:
        return validate_output({"summary": f"Database error: {str(e)}"}, [], intent="run_sql")

    # 3. Format Response
    format_prompt = SQL_FORMATTING_PROMPT.format(data=data, question=question)
    response_obj = safe_llm_invoke(llm, format_prompt)
    final_response = response_obj.content.strip()
    
    # NEW: Programmatic fallback for simple time-series to bypass LLM if rate limited
    if "RATE_LIMIT_EXCEEDED" in final_response and data:
        # Check if we have typical month/value keys
        first_row = data[0]
        date_key = next((k for k in first_row.keys() if "month" in k.lower() or "date" in k.lower()), None)
        value_key = next((k for k in first_row.keys() if "value" in k.lower() or "total" in k.lower() or "amount" in k.lower() or "sum" in k.lower()), None)
        
        if date_key and value_key:
            labels = [str(row[date_key])[:7] if "T" in str(row[date_key]) else str(row[date_key]) for row in data]
            dataset_data = [row[value_key] for row in data]
            return validate_output({
                "summary": f"I've retrieved the requested trend data. Total value reached its peak of {max(dataset_data)}.",
                "chart": {
                    "type": "line",
                    "labels": labels,
                    "datasets": [{"label": value_key.replace("_", " ").title(), "data": dataset_data}]
                },
                "sql": sql
            }, data, intent="run_sql")

    if "RATE_LIMIT_EXCEEDED" in final_response:
        return validate_output({"summary": "I'm currently hitting usage limits. Please try again in a few minutes."}, data, intent="run_sql")

    try:
        cleaned = extract_json(final_response)
        result = json.loads(cleaned)
        result["sql"] = sql
        return validate_output(result, data, intent="run_sql")
    except Exception as e:
        return validate_output({
            "summary": "I found the data you requested. Please see the list below.", 
            "sql": sql
        }, data, intent="run_sql")

def clarification_agent(question, llm, history=None):
    """
    Clarification Agent: Asks follow-up questions to resolve ambiguity.
    """
    history_context = f"\nChat History:\n{history}" if history else ""
    prompt = CLARIFICATION_PROMPT.format(history_context=history_context, question=question)
    response_obj = safe_llm_invoke(llm, prompt)
    response_text = response_obj.content.strip()
    
    if "RATE_LIMIT_EXCEEDED" in response_text:
        return validate_output({"summary": "I'm currently hitting usage limits. Please try again in a few minutes."}, [], intent="clarify")
    
    question_text = extract_between_tags(response_text)
    
    # Fallback if it returned JSON despite instructions
    if question_text.startswith('{'):
        try:
            data = json.loads(question_text)
            question_text = data.get("summary", question_text)
        except: pass

    return validate_output({"summary": question_text}, [], intent="clarify")

def context_agent(question, llm, history=None, search_func=None):
    """
    Context / Direct Answer Agent: Handles conversational logic and RAG.
    """
    history_context = f"\nChat History:\n{history}\n" if history else ""
    
    # Optional RAG
    rag_context = ""
    if search_func:
        from .utils.embeddings import generate_embedding
        try:
            emb = generate_embedding(question)
            docs = search_func(emb)
            rag_context = "\nReference Docs:\n" + "\n".join([d.content for d in docs])
        except: pass

    prompt = CONTEXT_PROMPT.format(history_context=history_context, rag_context=rag_context, question=question)
    response_obj = safe_llm_invoke(llm, prompt)
    response = response_obj.content.strip()
    
    if "RATE_LIMIT_EXCEEDED" in response:
        return validate_output({"summary": "I'm currently hitting usage limits. Please try again in a few minutes."}, [], intent="answer_from_history")

    try:
        cleaned = extract_json(response)
        result = json.loads(cleaned)
        return validate_output(result, [], intent="answer_from_history")
    except:
        return validate_output({"summary": "I'm sorry, I'm having trouble processing that request right now."}, [], intent="answer_from_history")

def fallback_agent(question, answer, llm, history=None, intent=None):
    """
    Fallback Agent: Catches unhelpful "no data" or "error" responses and makes them helpful.
    """
    from .prompts import FALLBACK_PROMPT
    
    # Check if the answer is considered a "failure"
    summary = answer.get("summary", "").lower()
    is_error = "error" in summary or "could not generate" in summary
    
    # NEW logic: skip fallback for 'clarify' intent as it's already a conversational guide
    if intent == "clarify":
         return answer

    # Greetings (answer_from_history) should NOT trigger the 'no data' fallback
    is_no_data = "relevant data" in summary or "no data" in summary or not answer.get("data")
    if intent == "answer_from_history":
        is_no_data = False # Don't fallback based on data content for conversation
    
    # If it's a valid data response or intentional conversation, don't intervene
    if not is_no_data and not is_error:
        return answer

    # Detect if user is saying "yes", "ok", etc. after a suggestion - don't fallback again
    q_lower = question.lower().strip()
    if q_lower in ["yes", "ok", "tell me about it", "tell me about", "go ahead", "yes please", "sure"]:
        return answer
        
    # If it's a "failure", invoke the fallback LLM
    history_context = f"\nChat History:\n{history}" if history else ""
    prompt = FALLBACK_PROMPT.format(
        question=question,
        history_context=history_context
    )
    
    response_obj = safe_llm_invoke(llm, prompt)
    response = response_obj.content.strip()
    
    if "RATE_LIMIT_EXCEEDED" in response:
        return answer # Return original failed answer if fallback also hits rate limit

    try:
        cleaned = extract_json(response)
        fallback_result = json.loads(cleaned)
        
        # Merge the old data (likely empty) into the new helpful summary
        fallback_result["data"] = answer.get("data", [])
        if "sql" in answer:
            fallback_result["sql"] = answer["sql"]
            
        return validate_output(fallback_result, fallback_result["data"], intent=intent)
    except:
        # If fallback fails, return the original answer
        return answer

def vector_search(query_embedding, top_k=3):
    return ERPVectorDocument.objects.order_by(
        L2Distance('embedding', query_embedding)
    )[:top_k]
