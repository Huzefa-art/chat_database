# Deployment Guide

## Project Structure

This is a full-stack application with:
- **Frontend**: React + TypeScript with Vite (in `/frontend`)
- **Backend**: Django REST API (in root directory)
- **Database**: Supabase PostgreSQL

## Frontend Deployment (Vercel/Netlify)

### Vercel

The project includes a `vercel.json` configuration for automatic deployment:

1. Connect your repository to Vercel
2. Environment variables are automatically configured from Supabase
3. Build command: `npm run build`
4. Output directory: `frontend/dist`

### Local Build

```bash
npm run build
```

This will:
1. Install all dependencies (root and frontend)
2. Build the frontend with TypeScript and Vite
3. Output to `frontend/dist`

### Preview

```bash
npm run preview
```

## Backend Deployment

The backend is a Django REST API that connects to Supabase PostgreSQL.

### Local Setup

1. Install Python dependencies:
```bash
pip install -r requirements.txt --break-system-packages
```

2. Run migrations:
```bash
python3 manage.py migrate
```

3. Start the development server:
```bash
python3 manage.py runserver 0.0.0.0:8000
```

### Environment Variables Required

- `VITE_SUPABASE_URL` - Supabase project URL
- `VITE_SUPABASE_ANON_KEY` - Supabase anonymous key
- `GROQ_API_KEY` - GROQ API key for LLM
- `GROQ_MODEL` - LLM model (default: llama3-8b-8192)

## Database

The application uses Supabase PostgreSQL. Connection details are configured in:
- `config/settings.py` - Django database configuration
- Database migrations are handled by Django ORM

## Key Features

### Live Query Visualizer
- Access at `/visualizer`
- Interactive database schema explorer
- Real-time query execution pipeline
- Mock data with simulated async delays

### ERP Analytics Chat
- Natural language queries about ERP data
- LLM-powered responses
- Chat history and sessions
- Real-time data retrieval

## Development

### Frontend Development

```bash
cd frontend
npm run dev
```

This starts the Vite dev server with hot module replacement.

### Full Stack Development

```bash
# Terminal 1: Frontend
npm run dev

# Terminal 2: Backend
python3 manage.py runserver

# Terminal 3: (Optional) Vite preview
npm run preview
```

## Build Files

After running `npm run build`:
- Frontend build output: `frontend/dist/`
- Ready for static hosting (Vercel, Netlify, etc.)
- No backend deployment needed for frontend-only hosting
- Backend API can be deployed separately

## Troubleshooting

### Build Fails
- Ensure Node.js version ≥ 18
- Run `npm run install:all` to ensure all dependencies are installed
- Check that `package.json` exists in both root and frontend directories

### Database Connection Issues
- Verify Supabase credentials in environment variables
- Check that Supabase project is active
- Ensure network can reach Supabase servers

### Frontend Not Loading
- Check `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` are set
- Verify Supabase project is accessible
- Check browser console for errors
