'use client';

import '../styles/globals.css';
import { Button } from "./ui/button"
import { useEffect, useState } from 'react';
import { supabase_obj } from '@/lib/supabaseClient';
import { User } from '@supabase/supabase-js';
import LoginButton from '@/components/LoginButton';

export default function HomePage() {
  const [user, setUser] = useState<User | null>(null);
  useEffect(() => {
    const getUser = async () => {
      try {
        console.log('Checking current user...');
        //const { data: { user }, error } = await supabase_obj.auth.getUser(); // await means pause until you get a return object 
        const response = await supabase_obj.auth.getUser();
        const user  = response.data.user;
        const error = response.error;
        if (error) throw error;
        console.log('Current user:', user);
        setUser(user); // queues a state change which means react schedules a re-render
      } catch (error) {
        console.error('Error getting user:', error);
        setUser(null);
      }
    };

    getUser();

    const { data: { subscription } } = supabase_obj.auth.onAuthStateChange((_event, session) => {
      console.log('Auth state changed:', _event, session?.user);
      setUser(session?.user ?? null); // subscription is event driven
    });

    return () => subscription.unsubscribe();
  }, []); // [] is the dependency array . empty = no dependency and runs only once. 

  if (!user) return <div><LoginButton /></div>;

  //return <div>Welcome {user.email}</div>;
  //show the login page is proceeded by a file upload UI
  
  return (
    <div style={{ padding: '2rem', textAlign: 'center' }}>
      <h1>Welcome, {user.email}</h1>
      <h2 style={{ marginTop: '1rem' }}>Upload Your Invoice</h2>
      //show a brand nicce  new option to upload invoice
      <Button>Click me</Button>
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



// USE EFFECT AND USE STATE ARE CALLED REACT HOOKS =============================================
// USE STATE allows component to remember information between RENDERS 
// because everytime a page renders the memory of variables is lost
// for example,  whether user has logged on or not

// USE EFFECT allows to run code at specific times in components library. 
// example : data change, first appearance ( can mention logic )
// useEffect runs after the component is first rendered (mounted).

//export default  ==============================================================================
//export default: This means you are making this function the "main thing" exported from the file. 
//Other files can import it easily.


//Component ==============================================================================
//A component is a function that returns what you want to show on the screen (the UI).

// RETURN in React ===========================================================================
//In React, the return value of a component is not a single variable or value.
// Instead, it returns a description of what the UI should look like.
// This description is written in JSX (JavaScript XML), which looks like HTML but is actually JavaScript.


// async ===========================================================================
// async on a function declaration means “this function will return a Promise, 
// and inside it I can use await to pause execution until another Promise resolves.