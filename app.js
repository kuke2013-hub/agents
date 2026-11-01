"use strict";
const AGENTS=[
{id:1,name:"The Architect",role:"Coordinator",color:"#52779d",initials:"A1"},
{id:2,name:"Mad Scientist",role:"Unconventional ideas",color:"#9666b3",initials:"A2"},
{id:3,name:"The Engineer",role:"Technical systems",color:"#3e9b91",initials:"A3"},
{id:4,name:"The Investigator",role:"Research & evidence",color:"#bc8a4f",initials:"A4"},
{id:5,name:"Devil's Advocate",role:"Critical thinking",color:"#b85f6f",initials:"A5"}];
const $=id=>document.getElementById(id);
const store=sessionStorage;
const state={url:store.getItem("agent_city_url")||"",token:store.getItem("agent_city_token")||"",connected:false,messages:[],data:null,busy:false};
function el(tag,cls,text){const x=document.createElement(tag);if(cls)x.className=cls;if(text!==undefined)x.textContent=text;return x}
function stamp(s){const d=new Date(s);return Number.isNaN(d.getTime())?"":new Intl.DateTimeFormat(undefined,{hour:"2-digit",minute:"2-digit"}).format(d)}
function agent(a){return AGENTS.find(x=>x.id===a)||{name:"BOSS",role:"BOSS",color:"#425773",initials:"B"}}
function showBanner(kind,title,detail){const b=$("mode-banner");b.className="mode-banner"+(kind?" "+kind:"");b.replaceChildren();b.append(el("span","",kind==="error"?"!":"◉"));const d=el("div");d.append(el("strong","",title),el("p","",detail));b.append(d)}
function showAgents(){const target=$("agent-list");target.replaceChildren();for(const a of AGENTS){const line=el("div","agent"),av=el("div","avatar",a.initials),identity=el("div","identity"),active=el("span","status-dot");av.style.background=a.color;identity.append(el("strong","",a.name),el("small","",a.role));if(state.connected&&state.data&&state.data.autopilot&&state.data.mission&&state.data.mission.current_agent===a.id)active.classList.add("on");line.append(av,identity,active);target.append(line)}}
function showFeed(){
  const feed=$("feed"),atEnd=feed.scrollHeight-feed.scrollTop-feed.clientHeight<130;
  feed.replaceChildren();
  const rows=state.connected?state.messages.filter(m=>Number(m.author)>=1&&Number(m.author)<=5):[];
  for(const m of rows){
    const a=agent(m.author),row=el("article","message"),av=el("div","message-avatar",a.initials),main=el("div","message-main"),head=el("div","message-head");
    av.style.background=a.color;
    head.append(el("strong","",a.name),el("span","role",a.role),el("time","",stamp(m.created_at)));
    if(m.to_agent)head.append(el("span","target","@ "+agent(m.to_agent).name));
    main.append(head,el("p","message-body",m.body));
    row.append(av,main);
    feed.append(row);
  }
  if(atEnd)feed.scrollTop=feed.scrollHeight;
}
function missionView(){const d=state.data,m=d&&d.mission; $("mission-title").textContent=m?m.title:"No active mission";$("mission-description").textContent=m?m.goal:"Give your agents a shared goal to begin a real discussion.";$("turn-count").textContent=m?m.turns+" / "+m.max_turns+" turns":"0 / 20 turns";$("mission-status").textContent=m?(m.status==="active"?(d.autopilot?"Running":"Paused"):m.status):"Idle";$("mission-progress-bar").style.width=m?Math.min(100,100*m.turns/m.max_turns)+"%":"0%";$("daily-count").textContent=d?d.daily_turns+" / "+d.daily_cap+" used":"0 / 40 used";$("model-label").textContent=d?(d.model_ready?d.model:"API key missing"):"Not connected";$("autopilot-toggle").checked=!!(d&&d.autopilot);$("autopilot-toggle").disabled=!(state.connected&&d&&d.model_ready);$("mission-form").querySelector("button").disabled=!state.connected||(!!m&&m.status==="active")}
function updateView(){showAgents();showFeed();missionView();const pill=$("connection-pill");pill.classList.toggle("connected",state.connected);pill.querySelector("span").textContent=state.connected?"Backend connected":"Not connected";if(state.connected){showBanner("live",state.data&&state.data.autopilot?"Agents enabled":"Board connected · agents paused",state.data&&state.data.autopilot?"The scheduler checks for work every minute. Messages refresh here every 10 seconds.":"Messages are persistent. Enable autonomous turns to let agents reply.")}else{showBanner("","Board awaiting connection","The conversation starts empty. Only actual agent messages will appear here.")}}
async function request(path,opts={}){if(!state.url||!state.token)throw Error("Enter the Worker URL and board token first.");const url=new URL(state.url);if(url.protocol!=="https:"&&url.hostname!=="localhost"&&url.hostname!=="127.0.0.1")throw Error("Use a secure HTTPS Worker URL.");const headers={"Authorization":"Bearer "+state.token};if(opts.body)headers["Content-Type"]="application/json";const res=await fetch(url.origin+url.pathname.replace(/\/$/,"")+path,{...opts,headers,cache:"no-store"});const payload=await res.json().catch(()=>({}));if(!res.ok)throw Error(payload.error||"Request failed ("+res.status+").");return payload}
async function refresh(throwOnError=false){if(!state.url||!state.token)return;try{const [d,list]=await Promise.all([request("/api/state"),request("/api/messages")]);state.data=d;state.messages=list.messages||[];state.connected=true;updateView()}catch(e){state.connected=false;state.data=null;updateView();showBanner("error","Connection unavailable",e.message);if(throwOnError)throw e}}
async function createMission(e){e.preventDefault();if(state.busy)return;const goal=$("mission-goal").value.trim();if(goal.length<12){alert("Write at least a sentence describing the mission.");return}if(!state.connected){$("settings-dialog").showModal();$("connection-result").textContent="Connect your backend before launching a real mission.";return}state.busy=true;try{await request("/api/missions",{method:"POST",body:JSON.stringify({goal})});$("mission-goal").value="";await refresh()}catch(err){alert(err.message)}finally{state.busy=false}}
async function toggleAuto(e){if(!state.connected)return;const enabled=e.target.checked;try{await request("/api/control",{method:"POST",body:JSON.stringify({enabled})});await refresh()}catch(err){alert(err.message);await refresh()}}
async function connect(){const url=$("api-url").value.trim().replace(/\/+$/,""),token=$("board-token").value.trim();if(!url||!token){$("connection-result").textContent="Both fields are required.";return}state.url=url;state.token=token;$("connection-result").textContent="Connecting…";try{await refresh(true);store.setItem("agent_city_url",state.url);store.setItem("agent_city_token",state.token);$("connection-result").textContent="Connected successfully.";setTimeout(()=>$("settings-dialog").close(),400)}catch(e){$("connection-result").textContent=e.message}}
function disconnect(){state.url="";state.token="";state.connected=false;state.data=null;state.messages=[];store.removeItem("agent_city_url");store.removeItem("agent_city_token");$("api-url").value="";$("board-token").value="";$("settings-dialog").close();updateView()}
$("mission-form").addEventListener("submit",createMission);$("autopilot-toggle").addEventListener("change",toggleAuto);$("refresh-btn").addEventListener("click",()=>refresh());$("settings-open").addEventListener("click",()=>{$("api-url").value=state.url;$("board-token").value=state.token;$("connection-result").textContent="";$("settings-dialog").showModal()});$("connect-btn").addEventListener("click",connect);$("disconnect-btn").addEventListener("click",disconnect);
updateView();if(state.url&&state.token)refresh();setInterval(()=>{if(state.url&&state.token)refresh()},10000);
