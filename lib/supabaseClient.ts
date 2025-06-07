import { createClient } from '@supabase/supabase-js'; // this was what was installed

// What is createClient?
// This is a function Supabase provides that creates a connection object using:

// your Supabase URL (so it knows where your project is)

// your anon key (so it can authenticate requests)

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase_obj = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true
  }
})

//user - defined object supabase.

