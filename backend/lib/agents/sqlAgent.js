import { SQL_GENERATION_PROMPT, SQL_FORMATTING_PROMPT } from '../prompts.js';
import { extractSql, extractJson, validateOutput } from './utils.js';
import { supabase } from '../supabase.js';

async function runSql(query) {
    const { data, error } = await supabase.rpc('exec_sql', { query_text: query });

    if (error) {
        console.error('Database error:', error);
        throw new Error(error.message);
    }
    return data;
}

export async function sqlAgent(question, llm, history = null) {
    const historyContext = history ? `\nConversation History:\n${history}\n` : '';
    const prompt = SQL_GENERATION_PROMPT.replace('{history_context}', historyContext).replace('{question}', question);

    try {
        const responseObj = await llm.invoke(prompt);
        const sql = extractSql(responseObj.content.trim());

        if (!sql.toUpperCase().startsWith('SELECT') && !sql.toUpperCase().startsWith('WITH')) {
            return validateOutput({ summary: "I could not generate a valid query for that." }, [], 'run_sql');
        }

        const data = await runSql(sql);

        const formatPrompt = SQL_FORMATTING_PROMPT.replace('{data}', JSON.stringify(data)).replace('{question}', question);
        const formatResponseObj = await llm.invoke(formatPrompt);
        const finalResponse = formatResponseObj.content.trim();

        try {
            const cleaned = extractJson(finalResponse);
            const result = JSON.parse(cleaned);
            result.sql = sql;
            return validateOutput(result, data, 'run_sql');
        } catch (e) {
            return validateOutput({
                summary: "I found the data you requested. Please see the list below.",
                sql: sql
            }, data, 'run_sql');
        }
    } catch (error) {
        console.error('SQL Agent failed:', error);
        return validateOutput({ summary: `I encountered an error while searching for the data: ${error.message}` }, [], 'run_sql');
    }
}
