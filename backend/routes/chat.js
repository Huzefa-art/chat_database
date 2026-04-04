import express from 'express';
import { supabase } from '../lib/supabase.js';
import { llm } from '../lib/llm.js';
import { analyzeQueryIntent } from '../lib/agents/router.js';
import { sqlAgent } from '../lib/agents/sqlAgent.js';
import { clarificationAgent } from '../lib/agents/clarification.js';
import { contextAgent } from '../lib/agents/context.js';
import { fallbackAgent } from '../lib/agents/fallback.js';

const router = express.Router();

router.use((req, res, next) => {
    if (!supabase) {
        return res.status(500).json({ error: 'Supabase is not configured. Please check your .env file.' });
    }
    next();
});

router.post('/create-chat', async (req, res) => {
    const { user_id, title = 'New Chat' } = req.body;

    if (!user_id) {
        return res.status(401).json({ error: 'Authentication required to start a chat' });
    }

    const { data, error } = await supabase
        .from('chat_session')
        .insert([{ user_id, title }])
        .select()
        .single();

    if (error) return res.status(500).json({ error: error.message });
    res.json({ chat_id: data.id, title: data.title });
});

router.put('/update-chat/:chat_id', async (req, res) => {
    const { chat_id } = req.params;
    const { title } = req.body;

    if (!title) return res.status(400).json({ error: 'title is required for update' });

    const { data, error } = await supabase
        .from('chat_session')
        .update({ title, updated_at: new Date() })
        .eq('id', chat_id)
        .select()
        .single();

    if (error) return res.status(404).json({ error: 'Invalid chat_id' });
    res.json({ message: 'Chat title updated', chat_id: data.id, title: data.title });
});

router.delete('/delete-chat/:chat_id', async (req, res) => {
    const { chat_id } = req.params;
    const { error } = await supabase.from('chat_session').delete().eq('id', chat_id);
    if (error) return res.status(404).json({ error: 'Invalid chat_id' });
    res.json({ message: 'Chat session deleted', chat_id });
});

router.get('/list-chats', async (req, res) => {
    const { user_id } = req.query;
    if (!user_id) return res.status(400).json({ error: 'user_id is required' });

    const { data, error } = await supabase
        .from('chat_session')
        .select('id, title, updated_at')
        .eq('user_id', user_id)
        .order('updated_at', { ascending: false });

    if (error) return res.status(500).json({ error: error.message });
    res.json(data);
});

router.get('/load-chathistory', async (req, res) => {
    const { chat_id } = req.query;
    if (!chat_id) return res.status(400).json({ error: 'chat_id is required' });

    const { data: messages, error } = await supabase
        .from('chat_message')
        .select('*')
        .eq('chat_id', chat_id)
        .order('created_at', { ascending: true });

    if (error) return res.status(404).json({ error: 'Invalid chat_id' });

    const historyData = messages.map(msg => ({
        role: msg.role,
        content: msg.content,
        summary: msg.role === 'assistant' ? msg.content : null,
        data: [],
        chart: { type: null, labels: [], datasets: [] },
        chat_id,
        created_at: msg.created_at,
        ...(msg.role === 'assistant' && msg.response_json ? msg.response_json : {})
    }));

    res.json({ messages: historyData });
});

router.post('/send-message', async (req, res) => {
    const { question, chat_id } = req.body;

    if (!chat_id) return res.status(400).json({ error: 'chat_id is required' });

    const { data: session, error: sessError } = await supabase
        .from('chat_session')
        .select('*')
        .eq('id', chat_id)
        .single();

    if (sessError || !session) return res.status(400).json({ error: 'Invalid chat_id' });

    if (session.title === 'New Chat' && question) {
        await supabase
            .from('chat_session')
            .update({ title: question.substring(0, 50) })
            .eq('id', chat_id);
    }

    const { data: historyObjs } = await supabase
        .from('chat_message')
        .select('role, content')
        .eq('chat_id', chat_id)
        .order('created_at', { ascending: false })
        .limit(10);

    const historyText = historyObjs ? historyObjs.reverse().map(m => `${m.role.charAt(0).toUpperCase() + m.role.slice(1)}: ${m.content}`).join('\n') : '';

    await supabase.from('chat_message').insert([{ chat_id, role: 'user', content: question }]);

    const intent = await analyzeQueryIntent(question, llm, historyText);

    let answer;
    if (intent === 'run_sql') {
        answer = await sqlAgent(question, llm, historyText);
    } else if (intent === 'clarify') {
        answer = await clarificationAgent(question, llm, historyText);
    } else if (intent === 'rate_limit') {
        answer = {
            summary: "I'm currently hitting usage limits. Please try again in a few minutes.",
            data: [],
            chart: { type: null }
        };
    } else {
        answer = await contextAgent(question, llm, historyText);
    }

    answer = await fallbackAgent(question, answer, llm, historyText, intent);

    answer.chat_id = chat_id;
    await supabase.from('chat_message').insert([{
        chat_id,
        role: 'assistant',
        content: answer.summary || '',
        response_json: answer
    }]);

    res.json(answer);
});

export default router;
