# Architecture Overview: ERP Analytics Chatbot

## Agent Pipeline
The chatbot uses a modular agent architecture to handle natural language queries about ERP data.

\`\`\`
User Query
    |
    v
Analyze Intent (Router Agent)
    |
    +---- "clarify" ----------> Clarification Agent (Ask follow-up)
    |
    +---- "run_sql" ----------> SQL Agent (Generate & Exec SQL)
    |                               |
    |                               v
    |                          Validate Result & Detect Charts
    |
    +---- "answer_from_history" -> Context Agent (Conversational)
    |
    v
Fallback Layer (If no data found/Error)
    |
    v
Structured JSON Response (Summary + Data + Chart)
\`\`\`

## Key Components

### Backend (Node.js/Express)
- **Routes**: Handle API requests for auth, chat creation, and message processing.
- **Agents**: LangChain-powered micro-agents using `llama3-70b-8192`.
- **Database**: Supabase client for persistence and raw SQL execution via `exec_sql` RPC.

### Database Schema (Supabase)
The database contains two main areas:
1. **ERP Data**: Vendors, Items, POs, Invoices, Inventory, Finance, Approvals.
2. **Chat System**: Users, Chat Sessions, Chat Messages (history).

### Session Management
- Chat history is stored in the `chat_message` table.
- Each message is linked to a `chat_session`.
- The last 10 messages are retrieved for context in each agent call.

### Chart Detection
The SQL Agent uses a specific prompt (`SQL_FORMATTING_PROMPT`) to decide if the data should be rendered as a `line`, `bar`, or `pie` chart based on the query result shape.
