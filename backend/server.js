import './lib/config.js';
import express from 'express';
import cors from 'cors';
import morgan from 'morgan';
import authRoutes from './routes/auth.js';
import chatRoutes from './routes/chat.js';

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(morgan('dev'));

// Routes
app.use('/', authRoutes);
app.use('/', chatRoutes);

// Health check
app.get('/health', (req, res) => {
    res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Error handling
app.use((err, req, res, next) => {
    console.error('SERVER ERROR:', err);
    res.status(500).json({ error: err.message || 'Something went wrong!' });
});

app.listen(PORT, () => {
    console.log(`Backend server running on port ${PORT}`);
});
