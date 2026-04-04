import { CLARIFICATION_PROMPT } from '../prompts.js';
import { extractBetweenTags, validateOutput } from './utils.js';

export async function clarificationAgent(question, llm, history = null) {
    const historyContext = history ? `\nChat History:\n${history}` : '';
    const prompt = CLARIFICATION_PROMPT.replace('{history_context}', historyContext).replace('{question}', question);

    try {
        const responseObj = await llm.invoke(prompt);
        const responseText = responseObj.content.trim();
        const questionText = extractBetweenTags(responseText);

        return validateOutput({ summary: questionText }, [], 'clarify');
    } catch (error) {
        console.error('Clarification agent failed:', error);
        throw error;
    }
}
