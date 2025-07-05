1) installed an a supbase sdk javascript library to allow communication : 
@supabase/supabase-js

This gives your app access to the Supabase JavaScript library — so you can do:

supabase.auth.signInWithOAuth()

supabase.from('invoices').insert(...)




2) to run the server : npm run dev 


---------------------------------------------------------------------------------------------
funtioning of the full stack----------------------------------------------------------------- : 
---------------------------------------------------------------------------------------------

the main landing page is app/page.tsx : its written in javascript. 


general info : 


Client side = where user interacts with the system
Server = powerful computer that stores the website's code and data


In the modern world, Client side rendering is low and only for components that require user interaction. Most of the rendering is done by the server. CSR is enabled by 'use client' and the browser does it. 

useState and useEffect are Client components that are called React Hooks.
useState = components memory
const [user, setUser] = useState(null);  //NUll = INITIAL VALUE
                                        // USER = current val
                                        //setUser = updating val

useEffect = components side jobs
checklist of tasks to do after component has been displayed.
tasks : any work that isn't directly related to drawing the component, like fetching data, setting up subscriptions, or talking to browser APIs.
Syntax: useEffect(() => { ... }, []);
The first argument () => { ... } is the "side job" you want to run.
The second argument [] is the dependency array. An empty array [] means: "Only run this side job once, right after the component first appears on the screen."