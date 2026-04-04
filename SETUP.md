# Setup Guide: ERP Analytics Chatbot (Node.js/Supabase)

## Prerequisites
- Node.js 18+
- Supabase account (supabase.com)
- Groq API key (console.groq.com)

## Step 1: Clone and Install
1. Clone the repository.
2. Run `npm install` at the root directory.
3. Run `npm run install:all` to install dependencies for both frontend and backend.

## Step 2: Supabase Configuration
1. Create a new project on Supabase.
2. Go to the **SQL Editor**.
3. Copy the contents of `supabase/schema.sql`, paste into the editor, and run it.
4. Copy the contents of `supabase/seed.sql`, paste into the editor, and run it.
5. Go to **Project Settings -> API** and copy:
   - `Project URL` (SUPABASE_URL)
   - `anon public` (SUPABASE_ANON_KEY / VITE_SUPABASE_ANON_KEY)
   - `service_role` (SUPABASE_SERVICE_ROLE_KEY) - *Keep this secret!*

## Step 3: Environment Variables
1. Copy `.env.example` to `.env` in the root (or create individual `.env` files in `backend/` and `frontend/`).
2. Fill in the values:
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `GROQ_API_KEY`
   - `VITE_API_URL=http://localhost:3000`
   - `VITE_SUPABASE_URL=<your-supabase-url>`
   - `VITE_SUPABASE_ANON_KEY=<your-anon-key>`

## Step 4: Run the Application
1. Run `npm run dev` at the root.
2. This will start:
   - **Backend**: http://localhost:3000
   - **Frontend**: http://localhost:5173
3. Open http://localhost:5173 in your browser.

## Step 5: Login
Use the demo account:
- **Username**: `demo`
- **Password**: `password123`
