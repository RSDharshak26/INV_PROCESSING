'use client';
import { useEffect, useState } from 'react';
import { supabase_obj } from '@/lib/supabaseClient';
import { User } from '@supabase/supabase-js';
import LoginButton from '@/app/components/LoginButton';

export default function HomePage() {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    const getUser = async () => {
      try {
        console.log('Checking current user...');
        const { data: { user }, error } = await supabase_obj.auth.getUser();
        if (error) throw error;
        console.log('Current user:', user);
        setUser(user);
      } catch (error) {
        console.error('Error getting user:', error);
        setUser(null);
      }
    };

    getUser();

    const { data: { subscription } } = supabase_obj.auth.onAuthStateChange((_event, session) => {
      console.log('Auth state changed:', _event, session?.user);
      setUser(session?.user ?? null);
    });

    return () => subscription.unsubscribe();
  }, []);

  if (!user) return <div><LoginButton /></div>;

  //return <div>Welcome {user.email}</div>;
  //show the login page is proceeded by a file upload UI
  
  return (
    <div style={{ padding: '2rem', textAlign: 'center' }}>
      <h1>Welcome, {user.email}</h1>
      <h2 style={{ marginTop: '1rem' }}>Upload Your Invoice</h2>
      //show a new option to upload invoice

      <input
        type="file"
        accept="application/pdf"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) {
            console.log("You selected:", file.name);
          }
        }}
        style={{ marginTop: '1.5rem' }}
      />
    </div>
  );
}


