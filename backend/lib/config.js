import dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const rootPath = path.resolve(__dirname, '../../.env');
const localPath = path.resolve(__dirname, '../.env');

dotenv.config({ path: rootPath });
dotenv.config({ path: localPath });
dotenv.config();

console.log('Resolving .env at:', rootPath);
console.log('Environment variables loaded. SUPABASE_URL exists:', !!process.env.SUPABASE_URL);
