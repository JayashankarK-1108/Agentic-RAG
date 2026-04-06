
import {useState, useRef} from "react";
import {sendMessage} from "../services/api";
import Message from "./Message";

export default function Chat(){
  const [messages,setMessages]=useState([]);
  const [loading,setLoading]=useState(false);
  const inputRef=useRef(null);
  
  const send=async(text)=>{
    if(!text.trim()) return;
    
    setMessages(m=>[...m,{role:"user",text}]);
    setLoading(true);
    
    try {
      const res=await sendMessage(text);
      setMessages(m=>[...m,{role:"bot",text:res.response}]);
    } catch(err) {
      setMessages(m=>[...m,{role:"bot",text:"Error: Could not get response"}]);
    } finally {
      setLoading(false);
      if(inputRef.current) inputRef.current.value="";
    }
  };
  
  const handleKeyDown=(e)=>{
    if(e.key==="Enter"&&!loading){
      send(e.target.value);
    }
  };
  
  return <>
    {messages.map((m,i)=><Message key={i} msg={m}/>)}
    {loading&&<div>Loading...</div>}
    <input ref={inputRef} onKeyDown={handleKeyDown} disabled={loading} placeholder="Type message..."/>
  </>
}
