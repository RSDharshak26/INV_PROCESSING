1) installed an a supbase sdk javascript library to allow communication : 
@supabase/supabase-js

This gives your app access to the Supabase JavaScript library — so you can do:

supabase.auth.signInWithOAuth()

supabase.from('invoices').insert(...)