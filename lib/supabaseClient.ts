import { createClient } from '@supabase/supabase-js'; // this was what was installed

// What is createClient?
// This is a function Supabase provides that creates a connection object using:

// your Supabase URL (so it knows where your project is)

// your anon key (so it can authenticate requests)

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
//eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFrd3ZpaWNkcGJra2Fmc3R1eHhoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDkxMzM4OTIsImV4cCI6MjA2NDcwOTg5Mn0.f6AvhycerXoCdCAhvpSOLW4N5_hoFsmnL_CcA8iri0s
export const supabase_obj = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true
  }
})

//user - defined object supabase.

