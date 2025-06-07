'use client';
import React from 'react';
import { supabase_obj } from '@/lib/supabaseClient';

//A .tsx file is a TypeScript + JSX file.
//JSX = JavaScript + HTML-like syntax (example below).
//Defines a React component named LoginButton.


export default function LoginButton() {
  const handleLogin = async () => {
    console.log('Starting login process...');
    const { data, error } = await supabase_obj.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: `${window.location.origin}/auth/callback`
      }
    });
    
    if (error) {
      console.error('Login error:', error.message);
      return;
    }
    
    console.log('Login successful:', data);
  };
//This is your JSX (HTML inside JS) that renders the button.
  return (
    <button onClick={handleLogin} className="px-4 py-2 bg-blue-600 text-white">
      Sign in with Google
    </button>
  );
}
