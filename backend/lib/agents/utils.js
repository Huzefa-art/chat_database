export function extractBetweenTags(text, tag = 'response') {
    const pattern = new RegExp(`<${tag}>(.*?)</${tag}>`, 's');
    const match = text.match(pattern);
    return match ? match[1].trim() : text.trim();
}

export function extractSql(testStr) {
    // Try markdown block first
    const markdownMatch = testStr.match(/```(?:sql|postgresql|)?\n?(.*?)\n?```/is);
    if (markdownMatch) {
        return markdownMatch[1].trim();
    }

    // Try to find SELECT or WITH ... up to the last semicolon or end of string
    const sqlMatch = testStr.match(/((?:SELECT|WITH)\s+.*)/is);
    if (sqlMatch) {
        let sql = sqlMatch[1].trim();
        if (sql.includes(';')) {
            sql = sql.split(';')[0] + ';';
        }
        return sql;
    }

    return testStr.trim();
}

export function extractJson(testStr) {
    // 1. Try tags first
    let content = extractBetweenTags(testStr);

    // 2. Try markdown code blocks
    const markdownMatch = content.match(/```(?:json)?\n?(.*?)\n?```/is);
    if (markdownMatch) {
        content = markdownMatch[1].trim();
    }

    // 3. Try to find the first '{' and last '}'
    const start = content.indexOf('{');
    const end = content.lastIndexOf('}');
    if (start !== -1 && end !== -1 && end > start) {
        return content.substring(start, end + 1).trim();
    }

    return content.trim();
}

export function serializeData(obj) {
    return JSON.parse(JSON.stringify(obj, (key, value) =>
        typeof value === 'bigint' ? value.toString() : value
    ));
}

export function validateOutput(result, rawData = null, intent = null) {
    if (typeof result !== 'object' || result === null) {
        result = { summary: String(result) };
    }

    result.summary = result.summary || 'No summary provided.';
    result.data = rawData || result.data || [];
    result.chart = result.chart || { type: null, labels: [], datasets: [] };

    if (typeof result.chart !== 'object') result.chart = { type: null };
    result.chart.type = result.chart.type || null;
    result.chart.labels = result.chart.labels || [];
    result.chart.datasets = result.chart.datasets || [];

    const dataIsEmpty = !rawData || (Array.isArray(rawData) && rawData.length === 0);
    const skipOverwrite = ['clarify', 'answer_from_history'].includes(intent) ||
        (result.summary && result.summary.toLowerCase().includes('rate limit'));

    if (dataIsEmpty && !skipOverwrite) {
        const lowerSummary = result.summary.toLowerCase();
        if (lowerSummary.includes('found') || lowerSummary.includes('here is') || lowerSummary.includes('based on')) {
            result.summary = "I couldn't find any relevant data for your request.";
        }
        result.chart.type = null;
        result.data = [];
    }

    // Chart Sanity Checks
    const chartType = String(result.chart.type || '').toLowerCase();
    const rawDataLength = Array.isArray(rawData) ? rawData.length : 0;

    if (chartType === 'pie' && rawDataLength < 2) {
        result.chart.type = 'table';
    }
    if (chartType === 'line' && rawDataLength < 2) {
        result.chart.type = 'table';
    }
    if (['null', 'none'].includes(chartType)) {
        result.chart.type = null;
    }

    return result;
}
