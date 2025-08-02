'use client';

// part 1 : imports
import '../styles/globals.css';
import { Button } from "./ui/button"
import { useEffect, useState } from 'react';
import { supabase_obj } from '@/lib/supabaseClient';
import { User } from '@supabase/supabase-js';
import LoginButton from '@/components/LoginButton';
import { useRouter } from 'next/navigation';
//for routing

//part 2 : logic and data ( java/typescript zone.)


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
  
    const response = await fetch('https://bdyl3hj7je.execute-api.us-east-1.amazonaws.com/Prod/receive', {
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

  if (loading || !isClient) return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
    </div>
  );
  
  if (!user) return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
      <div className="bg-white p-8 rounded-2xl shadow-xl max-w-md w-full mx-4">
        <div className="text-center">
          <div className="mx-auto h-16 w-16 bg-indigo-100 rounded-full flex items-center justify-center mb-6">
            <svg className="h-8 w-8 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Invoice Processing</h1>
          <p className="text-gray-600 mb-6">Sign in to start processing your invoices</p>
          <LoginButton />
        </div>
      </div>
    </div>
  );
  //return <div>Welcome {user.email}</div>;
  //show the login page is proceeded by a file upload UI
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Welcome, <span className="text-indigo-600">{user.email}</span>
          </h1>
          <h2 className="text-xl text-gray-600">Upload Your Invoice</h2>
        </div>

        <div className="bg-white rounded-3xl shadow-xl p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="border-2 border-dashed border-gray-300 rounded-2xl p-12 text-center hover:border-indigo-400 hover:bg-gray-50 transition-all duration-300">
              <div className="mx-auto h-20 w-20 bg-indigo-100 rounded-full flex items-center justify-center mb-6">
                <svg className="h-10 w-10 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
              </div>
              <h3 className="text-2xl font-semibold text-gray-900 mb-2">Choose your invoice file</h3>
              <p className="text-gray-600 mb-6">Click to browse or drag and drop</p>
              
              <input type="file" name="file_upload" accept="image" className="block w-full text-sm text-gray-500 file:mr-4 file:py-3 file:px-6 file:rounded-xl file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100 file:cursor-pointer cursor-pointer" />
              
              <div className="text-sm text-gray-500 mt-4">
                <span className="font-medium">Supported formats:</span> PNG, JPG, JPEG
              </div>
            </div>

            <Button className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-semibold py-4 px-8 rounded-xl text-lg transition-all duration-300 transform hover:scale-105">
              <div className="flex items-center justify-center space-x-2">
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <span>Process Invoice</span>
              </div>
            </Button>
          </form>
        </div>

        <div className="grid md:grid-cols-3 gap-6 mt-8">
          <div className="bg-white rounded-2xl p-6 shadow-lg text-center">
            <div className="h-12 w-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">AI-Powered OCR</h3>
            <p className="text-gray-600 text-sm">Advanced Google Vision API</p>
          </div>
          
          <div className="bg-white rounded-2xl p-6 shadow-lg text-center">
            <div className="h-12 w-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="h-6 w-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">Secure Processing</h3>
            <p className="text-gray-600 text-sm">AWS infrastructure</p>
          </div>
          
          <div className="bg-white rounded-2xl p-6 shadow-lg text-center">
            <div className="h-12 w-12 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="h-6 w-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">Lightning Fast</h3>
            <p className="text-gray-600 text-sm">Process invoices quickly</p>
          </div>
        </div>
      </div>
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
