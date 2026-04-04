# StackBlitz Deployment Guide

Follow these steps to run this project in StackBlitz.

## 1. Import to StackBlitz
1. Push this project to a GitHub repository if it's not already.
2. Open `https://stackblitz.com/github/[your-username]/[your-repo-name]`.

## 2. Set Environment Variables
1. In StackBlitz, go to **Project Settings -> Environment Variables**.
2. Add the following variables:
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `GROQ_API_KEY`
   - `VITE_SUPABASE_URL`
   - `VITE_SUPABASE_ANON_KEY`
   - `VITE_API_URL`: Initially set this to a placeholder.

## 3. Configure VITE_API_URL
1. Run `npm run dev`.
2. Look at the **Ports** tab in StackBlitz.
3. Find the URL for port **3000** (the backend).
4. Update `VITE_API_URL` in the environment variables to this exact URL (e.g., `https://node-1234.webcontainer.io`).
5. Restart the dev server or refresh the frontend.

## 4. Database Setup
Ensure you have already run `schema.sql` and `seed.sql` in your Supabase SQL editor as described in `SETUP.md`.

## 5. Single Command
The project is configured with npm workspaces. Running `npm run dev` starts both the frontend and backend concurrently.
