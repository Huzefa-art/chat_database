import { CONTEXT_PROMPT } from '../prompts.js';
import { extractJson, validateOutput } from './utils.js';

export async function contextAgent(question, llm, history = null) {
    const historyContext = history ? `\nChat History:\n${history}\n` : '';
    const prompt = CONTEXT_PROMPT.replace('{history_context}', historyContext).replace('{question}', question);

    try {
        const responseObj = await llm.invoke(prompt);
        const response = responseObj.content.trim();

        try {
            const cleaned = extractJson(response);
            const result = JSON.parse(cleaned);
            return validateOutput(result, [], 'answer_from_history');
        } catch (e) {
            return validateOutput({ summary: "I'm sorry, I'm having trouble processing that request right now." }, [], 'answer_from_history');
        }
    } catch (error) {
        console.error('Context agent failed:', error);
        throw error;
    }
}
