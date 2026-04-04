import express from 'express';
import { supabase } from '../lib/supabase.js';

const router = express.Router();

router.use((req, res, next) => {
    if (!supabase) {
        return res.status(500).json({ error: 'Supabase is not configured. Please check your .env file.' });
    }
    next();
});

router.post('/signup', async (req, res) => {
    const { username, password, email } = req.body;

    if (!username || !password) {
        return res.status(400).json({ error: 'Username and password are required' });
    }

    const { data, error } = await supabase
        .from('auth_user')
        .insert([{ username, password, email }])
        .select()
        .single();

    if (error) {
        if (error.code === '23505') {
            return res.status(400).json({ error: 'Username already exists' });
        }
        return res.status(500).json({ error: error.message });
    }

    res.status(201).json({ message: 'User created successfully', user_id: data.id, username: data.username });
});

router.post('/login', async (req, res) => {
    const { username, email, password } = req.body;
    const loginIdentifier = username || email;

    if (!loginIdentifier || !password) {
        return res.status(400).json({ error: 'Username/Email and password are required' });
    }

    const { data: user, error } = await supabase
        .from('auth_user')
        .select('*')
        .or(`username.eq.${loginIdentifier},email.eq.${loginIdentifier}`)
        .eq('password', password)
        .single();

    if (error || !user) {
        return res.status(401).json({ detail: 'Login failed. Please check your username and password.' });
    }

    if (!user.verified) {
        return res.status(401).json({ detail: 'Your account is not verified. Please contact your administrator.' });
    }

    res.json({
        token: 'mock-token-' + user.id,
        user_id: user.id,
        email: user.email,
        username: user.username,
        verified: user.verified
    });
});

export default router;
