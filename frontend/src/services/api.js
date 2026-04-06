
export async function sendMessage(query){
  const res = await fetch("http://localhost:8000/chat",{
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify({query})
  });
  return res.json();
}
