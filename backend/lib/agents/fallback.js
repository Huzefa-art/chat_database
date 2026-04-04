import { FALLBACK_PROMPT } from '../prompts.js';
import { extractJson, validateOutput } from './utils.js';

export async function fallbackAgent(question, answer, llm, history = null, intent = null) {
    const summary = (answer.summary || "").toLowerCase();
    const isError = summary.includes("error") || summary.includes("could not generate");

    if (intent === "clarify") return answer;

    let isNoData = summary.includes("relevant data") || summary.includes("no data") || !answer.data || (Array.isArray(answer.data) && answer.data.length === 0);
    if (intent === "answer_from_history") isNoData = false;

    if (!isNoData && !isError) return answer;

    const qLower = question.toLowerCase().trim();
    if (["yes", "ok", "tell me about it", "go ahead", "sure"].includes(qLower)) return answer;

    const historyContext = history ? `\nChat History:\n${history}` : '';
    const prompt = FALLBACK_PROMPT.replace('{question}', question).replace('{history_context}', historyContext);

    try {
        const responseObj = await llm.invoke(prompt);
        const response = responseObj.content.trim();

        try {
            const cleaned = extractJson(response);
            const fallbackResult = JSON.parse(cleaned);
            fallbackResult.data = answer.data || [];
            if (answer.sql) fallbackResult.sql = answer.sql;
            return validateOutput(fallbackResult, fallbackResult.data, intent);
        } catch (e) {
            return answer;
        }
    } catch (error) {
        return answer;
    }
}
