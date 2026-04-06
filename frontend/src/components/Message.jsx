
export default function Message({msg}){
  if(msg.role==="user") return <p>{msg.text}</p>;
  return <div>{msg.text.split("\n").map((l,i)=>
    l.startsWith("Image:")
      ? <img key={i} src={l.replace("Image:","").trim()} width="300"/>
      : <p key={i}>{l}</p>
  )}</div>;
}
