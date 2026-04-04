import { ChatGroq } from '@langchain/groq';

const apiKey = process.env.GROQ_API_KEY;
const modelName = process.env.GROQ_MODEL || 'llama-3.3-70b-versatile';

export const llm = apiKey ? new ChatGroq({
    apiKey: apiKey,
    modelName: modelName,
    temperature: 0,
}) : null;

if (!llm) {
    console.warn('⚠️  GROQ_API_KEY is missing! AI agent features will not work.');
}
