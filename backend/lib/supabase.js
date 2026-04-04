import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.SUPABASE_URL;
const supabaseServiceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

export const supabase = (supabaseUrl && supabaseServiceRoleKey)
  ? createClient(supabaseUrl, supabaseServiceRoleKey)
  : null;

if (!supabase) {
  console.warn('⚠️  Supabase environment variables are missing! Database features will not work.');
  console.warn('Please check your .env file and ensure SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are set.');
}
