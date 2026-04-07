
const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

export async function sendMessage(query, department = null){
  const res = await fetch(`${API_URL}/chat`,{
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify({query, department})
  });
  if(!res.ok) throw new Error(`Server error: ${res.status}`);
  return res.json();
}
