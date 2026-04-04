import { ROUTER_PROMPT } from '../prompts.js';

export async function analyzeQueryIntent(question, llm, history = null) {
    const historyContext = history ? `\nChat History:\n${history}` : '';
    const prompt = ROUTER_PROMPT.replace('{history_context}', historyContext).replace('{question}', question);

    try {
        const responseObj = await llm.invoke(prompt);
        const response = responseObj.content.trim().toLowerCase();

        if (response.includes('run_sql')) return 'run_sql';
        if (response.includes('clarify')) return 'clarify';
        return 'answer_from_history';
    } catch (error) {
        console.error('Intent analysis failed:', error);
        if (error.message.toLowerCase().includes('rate_limit')) return 'rate_limit';
        throw error;
    }
}
