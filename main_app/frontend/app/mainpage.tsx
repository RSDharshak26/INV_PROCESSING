'use client';

import '../styles/globals.css';
import { Button } from "./ui/button"
import { useEffect, useState } from 'react';
import { supabase_obj } from '@/lib/supabaseClient';
import { User } from '@supabase/supabase-js';
import LoginButton from '@/components/LoginButton';
import { useRouter } from 'next/navigation';
//for routing 


export default function HomePage() {
  const [loading,setloading] = useState(true);
  const [isClient,setisClient] = useState(false);
  const router = useRouter();
  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => { //handleSubmit is a custom event handler. async returns a promise. async enables await. 
    e.preventDefault();
    const form = e.currentTarget; // html element that event listener is attached to 
    const fileInput = form.elements.namedItem('file_upload') as HTMLInputElement;
    const file = fileInput.files?.[0];   // get the File
    
    if (!file) {
      alert("Please select a file first.");
      return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    console.log("handleSubmit fired"); 
    //fetch does two things:
    // Sends an HTTP request to the URL you give (here http://…/receive).
    // Returns a Promise that resolves to a Response object once the server replies.
  
    const response = await fetch('https://pd8768jjsc.execute-api.us-east-1.amazonaws.com/Prod/receive', {
      method: 'POST',
      body: formData        // no headers, browser adds them
    });
    
    const result = await response.json(); // instead of json you can use text, blob, formdata etc,

    console.log("console result",result.status)
    if (result.status === "success") { // status is inbuilt 
      // Redirect to results page with the processed image and extracted text
      const params = new URLSearchParams({
        img: result.processed_image,
        text: result.extracted_text || ''
      });
      router.push(`/results?${params.toString()}`);
    } else {
      alert("Processing failed. Please try again.");
    }
  };  

// ================================================================================= HANDLE SUBMIT OVER ========================================
// =============================================================================================================================================
// =============================================================================================================================================
// =============================================================================================================================================
// ============================================================================================================================================= 

  const [user, setUser] = useState<User | null>(null);
  useEffect(() => {

    setisClient(true);
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
      } finally {setloading(false)}
    };

    getUser();

    const { data: { subscription } } = supabase_obj.auth.onAuthStateChange((_event, session) => {
      console.log('Auth state changed:', _event, session?.user);
      setUser(session?.user ?? null); // subscription is event driven
    });

    return () => subscription.unsubscribe();
  }, []); // [] is the dependency array . empty = no dependency and runs only once. 

  if (loading || !isClient) return <div>loading....</div>;
  if (!user) return <div><LoginButton /></div>;
  //return <div>Welcome {user.email}</div>;
  //show the login page is proceeded by a file upload UI
  
  return (
    <div style={{ padding: '2rem', textAlign: 'center' }}>
      <h1>Welcome, {user.email}</h1>
      <h2 style={{ marginTop: '1rem' }}>Upload Your Invoice</h2>

      
      <form onSubmit={handleSubmit}>

      
      <input type="file" name = "file_upload" accept="image" />

      <Button className="bg-blue-500 text-white p-4 rounded">Submit</Button>
      </form>    


      


    </div>
  );
}

//<form> is an HTML element that groups inputs and a submit button.
//call the JavaScript function named handleSubmit
//onSubmit={…}—is your event listener.


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


// useEffect is Your Friend: Anything that should only run on the client goes in useEffect. The server ignores effects.