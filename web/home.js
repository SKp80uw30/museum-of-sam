import { STAGES, clamp, ease, lerp, timeline } from './home-journey.mjs'

const canvas = document.querySelector('#world'), ctx = canvas.getContext('2d', { alpha:false })
const panels = Object.fromEntries(['welcome','journey','reveal','portals'].map(id=>[id,document.getElementById(id)]))
const announce = document.querySelector('#announcement')
const motion = matchMedia('(prefers-reduced-motion: reduce)')
let reduced = motion.matches, W=0,H=0,DPR=1, room, state='welcome', elapsed=0,last=0,stageShown=-1, hover=-1
let stars=[], galaxy=[], words=[], textFrom=[], portals=[]
let living=null, gardenPaused=false, partyGame=null
const images=['reef','forest','jumping-castle','gallery'].map(name=>{const im=new Image();im.onload=()=>{if(W&&!living)buildRoom()};im.src=`./home-assets/${name}.png`;return im})
let seed=92016
function rand(){seed=(seed*1664525+1013904223)>>>0;return seed/4294967296}
for(let i=0;i<1300;i++)stars.push({x:rand(),y:rand(),r:.3+rand()*1.2,a:.15+rand()*.75,p:rand()*6.28})
for(let i=0;i<6200;i++){
 const r=Math.pow(rand(),.65),arm=i%4,angle=r*9+arm*Math.PI/2+(rand()-.5)*(.45+r*.5)
 galaxy.push({x:Math.cos(angle)*r,y:Math.sin(angle)*r,z:(rand()-.5)*(.07+.1*r),a:.1+rand()*.55,c:rand()})
}
function path(c,points,fill,stroke){c.beginPath();points.forEach(([x,y],i)=>i?c.lineTo(x,y):c.moveTo(x,y));c.closePath();if(fill){c.fillStyle=fill;c.fill()}if(stroke){c.strokeStyle=stroke;c.stroke()}}
function rect(c,x,y,w,h,color){c.fillStyle=color;c.fillRect(x,y,w,h)}
function glow(c,x,y,r,color,alpha=1){c.save();c.globalAlpha*=alpha;const g=c.createRadialGradient(x,y,0,x,y,r);g.addColorStop(0,color);g.addColorStop(1,'transparent');c.fillStyle=g;c.fillRect(x-r,y-r,r*2,r*2);c.restore()}
function arch(c,x,y,w,h){const r=w/2;c.beginPath();c.moveTo(x,y+h);c.lineTo(x,y+r);c.arc(x+r,y+r,r,Math.PI,0);c.lineTo(x+w,y+h);c.closePath()}
function drawCover(c,img,x,y,w,h){if(!img.complete||!img.naturalWidth)return;const k=Math.max(w/img.width,h/img.height);c.drawImage(img,x+(w-img.width*k)/2,y+(h-img.height*k)/2,img.width*k,img.height*k)}
function getPortals(){if(W<=650){const x=.12*W,gap=.0988*W,w=.3306*W,y=.29*H,h=.266*H;return [0,1,2,3].map(i=>({x:x+(i%2)*(w+gap),y:y+Math.floor(i/2)*(.294*H),w,h}))}const w=.16948*W,gap=.02736*W;return [0,1,2,3].map(i=>({x:.12*W+i*(w+gap),y:.4*H,w,h:.42*H}))}
function buildRoom(){
 room=document.createElement('canvas');room.width=Math.round(W*DPR);room.height=Math.round(H*DPR);const c=room.getContext('2d');c.scale(DPR,DPR);portals=getPortals()
 const wall=c.createLinearGradient(0,0,0,H);wall.addColorStop(0,'#ded5c4');wall.addColorStop(.52,'#f3eddf');wall.addColorStop(1,'#b4a78c');rect(c,0,0,W,H,wall)
 // A shallow, symmetrical salon: warm plaster, a recessed ceiling and stone floor.
 path(c,[[0,0],[W,0],[W*.9,H*.13],[W*.1,H*.13]],'#cbc1ae')
 path(c,[[W*.035,0],[W*.965,0],[W*.87,H*.095],[W*.13,H*.095]],'#e6ddca')
 c.lineWidth=2;path(c,[[W*.06,0],[W*.94,0],[W*.86,H*.08],[W*.14,H*.08]],null,'#fff4cc')
 glow(c,W/2,H*.085,W*.5,'#fff4cb',.55)
 path(c,[[0,0],[W*.08,H*.14],[W*.08,H*.82],[0,H]],'#d8cebc')
 path(c,[[W,0],[W*.92,H*.14],[W*.92,H*.82],[W,H]],'#cfc4b1')
 const floor=c.createLinearGradient(0,H*.79,0,H);floor.addColorStop(0,'#ded4c1');floor.addColorStop(1,'#f0e8d8');rect(c,0,H*.82,W,H*.18,floor)
 c.strokeStyle='#ad9c7d44';c.lineWidth=1
 for(let i=-5;i<10;i++){c.beginPath();c.moveTo(W/2+(i-2)*W*.10,H*.82);c.lineTo(W/2+(i-2)*W*.23,H);c.stroke()}
 for(const y of [.84,.88,.945]){c.beginPath();c.moveTo(0,H*y);c.lineTo(W,H*y);c.stroke()}
 path(c,[[W*.27,H],[W*.40,H*.84],[W*.60,H*.84],[W*.73,H]],'#98856a')
 path(c,[[W*.285,H],[W*.405,H*.845],[W*.595,H*.845],[W*.715,H]],'#bcab8f')
 // Fine horizontal fibres in the soft runner.
 for(let i=0;i<65;i++){const y=.85+i*.15/65,t=(y-.84)/.16;c.globalAlpha=.12;c.strokeStyle=i%2?'#fff2d6':'#6c5d47';c.beginPath();c.moveTo(W*(.405-.12*t),H*y);c.lineTo(W*(.595+.12*t),H*y);c.stroke()}c.globalAlpha=1
 rect(c,W*.08,H*.817,W*.84,4,'#f8f1e5');rect(c,W*.08,H*.822,W*.84,2,'#a8997d')
 portals.forEach((p,i)=>{
 c.save();c.shadowColor='#59452e44';c.shadowBlur=25;c.shadowOffsetY=12;arch(c,p.x-10,p.y-10,p.w+20,p.h+12);c.fillStyle='#e9dfcb';c.fill();c.restore()
 c.lineWidth=2;arch(c,p.x-5,p.y-5,p.w+10,p.h+6);c.strokeStyle='#fdf6e6';c.stroke();arch(c,p.x,p.y,p.w,p.h);c.fillStyle=['#17464b','#345043','#9b863d','#8e8270'][i];c.fill()
 c.save();arch(c,p.x,p.y,p.w,p.h);c.clip();drawCover(c,images[i],p.x,p.y,p.w,p.h);const shade=c.createLinearGradient(p.x,p.y,p.x+p.w,p.y);shade.addColorStop(0,'#0008');shade.addColorStop(.28,'#0000');shade.addColorStop(.72,'#0000');shade.addColorStop(1,'#0007');rect(c,p.x,p.y,p.w,p.h,shade);rect(c,p.x,p.y,p.w,p.h,'#d8b76a10');c.restore()
 c.lineWidth=3;arch(c,p.x,p.y,p.w,p.h);c.strokeStyle='#a08b62';c.stroke()
 // Soft reflection catches the threshold rather than mirroring the full scene.
 if(W>650){c.save();c.translate(0,(p.y+p.h)*2+3);c.scale(1,-1);c.globalAlpha=.075;drawCover(c,images[i],p.x,p.y,p.w,p.h);c.restore()}
 })
 // Paired bronze wall lamps, keeping the centre calm for the greeting.
 for(const x of [.045,.955]){rect(c,W*x-3,H*.45,6,H*.10,'#8b7651');glow(c,W*x,H*.43,W*.065,'#fff5c7',.65);rect(c,W*x-8,H*.445,16,3,'#fff4cf')}
 // Architectural vignette.
 const vignette=c.createRadialGradient(W/2,H*.4,W*.2,W/2,H*.4,W*.8);vignette.addColorStop(0,'transparent');vignette.addColorStop(1,'#4c341c35');rect(c,0,0,W,H,vignette)
}
function makeWords(){
 const c=document.createElement('canvas');c.width=1100;c.height=240;const a=c.getContext('2d');a.fillStyle='#fff';a.textAlign='center';a.font='italic 164px Georgia';a.fillText('This much!',550,172)
 const data=a.getImageData(0,0,c.width,c.height).data;words=[];textFrom=[]
 for(let y=20;y<210;y+=4)for(let x=0;x<1100;x+=4)if(data[(y*1100+x)*4+3]>140){words.push({x:(x-550)/1100,y:(y-110)/1100,p:rand()*6.28});textFrom.push({x:rand()*2-1,y:rand()*2-1})}
}
makeWords()
function resize(){W=innerWidth;H=innerHeight;DPR=Math.min(devicePixelRatio||1,2);canvas.width=Math.round(W*DPR);canvas.height=Math.round(H*DPR);ctx.setTransform(DPR,0,0,DPR,0,0);buildRoom();living?.resize();render()}
addEventListener('resize',resize)
function drawRoom(scale=1,alpha=1){ctx.save();ctx.globalAlpha=alpha;ctx.translate(W/2,H/2);ctx.scale(scale,scale);ctx.drawImage(room,-W/2,-H/2,W,H);ctx.restore()}
function background(t){rect(ctx,0,0,W,H,'#060914');glow(ctx,W*.66,H*.40,W*.48,'#1b163d',.65);glow(ctx,W*.27,H*.6,W*.32,'#073744',.28);ctx.save();for(const s of stars){ctx.globalAlpha=s.a*(.7+.3*Math.sin(t*.3+s.p));ctx.fillStyle=s.p>4?'#d7c4a3':'#dfe9ff';ctx.beginPath();ctx.arc(s.x*W,s.y*H,s.r,0,Math.PI*2);ctx.fill()}ctx.restore()}
// Hand-drawn geographic silhouettes, deliberately illustrative rather than a map service.
const aus=[[-.48,.06],[-.46,-.14],[-.39,-.22],[-.31,-.23],[-.23,-.33],[-.12,-.37],[-.04,-.31],[.02,-.38],[.11,-.34],[.15,-.17],[.24,-.27],[.30,-.48],[.34,-.37],[.38,-.19],[.46,.04],[.45,.24],[.34,.39],[.22,.43],[.09,.28],[-.02,.27],[-.13,.18],[-.32,.22],[-.43,.27],[-.49,.21]]
function australia(scale,alpha,t){ctx.save();ctx.translate(W/2,H*.46);const size=Math.min(W*.78,H*.85)*scale;ctx.scale(size,size);ctx.globalAlpha=alpha;glow(ctx,0,0,.68,'#234556',.8);ctx.lineWidth=.002;path(ctx,aus,'#bdb18f','#eed4a4');path(ctx,[[.25,.47],[.32,.48],[.29,.56],[.25,.54]],'#c4b79b');ctx.strokeStyle='#796e5360';for(let i=0;i<18;i++){ctx.beginPath();ctx.ellipse(0,.02,.06+i*.023,.04+i*.019,-.2,0,6.28);ctx.save();path(ctx,aus);ctx.clip();ctx.stroke();ctx.restore()}
 glow(ctx,.27,.37,.06,'#ffe6a3',1);ctx.fillStyle='#fff5da';ctx.beginPath();ctx.arc(.27,.37,.005,0,6.28);ctx.fill();ctx.strokeStyle='#fff0c6';ctx.beginPath();ctx.arc(.27,.37,.015+.006*Math.sin(t*2),0,6.28);ctx.stroke();ctx.restore()}
const continents=[[[113,-22],[114,-34],[130,-32],[138,-36],[148,-39],[153,-28],[145,-15],[142,-11],[137,-16],[131,-12],[123,-15]],[[45,10],[40,30],[25,37],[10,35],[-15,28],[-17,12],[2,5],[12,-5],[18,-35],[31,-30],[40,-12],[50,0]],[[0,40],[10,58],[30,70],[60,72],[95,78],[130,65],[160,60],[178,52],[140,40],[121,20],[110,5],[100,10],[80,8],[65,25],[45,35],[25,40]], [[-168,65],[-135,70],[-105,72],[-60,50],[-80,25],[-100,17],[-115,30],[-130,50]],[[-80,10],[-58,7],[-35,-6],[-48,-28],[-67,-55],[-75,-30]],[[48,-14],[50,-20],[46,-26],[44,-18]],[[167,-35],[177,-39],[169,-47],[166,-44]],[[130,0],[150,-5],[152,-10],[138,-8]]]
function earth(scale,alpha,t){const r=Math.min(W*.29,H*.32)*scale,cx=W/2,cy=H*.46;ctx.save();ctx.globalAlpha=alpha;glow(ctx,cx,cy,r*1.18,'#348be0',.55);const sea=ctx.createRadialGradient(cx-r*.38,cy-r*.4,r*.05,cx,cy,r);sea.addColorStop(0,'#4586a8');sea.addColorStop(.55,'#1b4e7b');sea.addColorStop(.9,'#10293f');sea.addColorStop(1,'#071728');ctx.beginPath();ctx.arc(cx,cy,r,0,6.28);ctx.fillStyle=sea;ctx.fill();ctx.save();ctx.clip();const lon0=125+(reduced?0:t*1.1),lat0=-15
 function project(lon,lat){const l=(lon-lon0)*Math.PI/180,p=lat*Math.PI/180,p0=lat0*Math.PI/180;return [cx+r*Math.cos(p)*Math.sin(l),cy-r*(Math.sin(p)*Math.cos(p0)-Math.cos(p)*Math.cos(l)*Math.sin(p0)),Math.sin(p)*Math.sin(p0)+Math.cos(p)*Math.cos(l)*Math.cos(p0)]}
 continents.forEach(poly=>{const pp=poly.map(([a,b])=>project(a,b));if(pp.every(p=>p[2]<0))return;path(ctx,pp.map(p=>[p[0],p[1]]),'#7e9370')})
 ctx.strokeStyle='#e9f4f744';ctx.lineWidth=Math.max(.4,r*.009);for(let j=0;j<15;j++){ctx.beginPath();ctx.ellipse(cx+Math.sin(j*7)*r*.5,cy+(j/15-.5)*r*1.7,r*(.22+((j*7)%5)*.08),r*.028,j*.1,0,Math.PI*1.5);ctx.stroke()}
 const shade=ctx.createLinearGradient(cx-r,0,cx+r,0);shade.addColorStop(0,'#0000');shade.addColorStop(.5,'#0001');shade.addColorStop(1,'#020610e8');rect(ctx,cx-r,cy-r,r*2,r*2,shade);ctx.restore();ctx.strokeStyle='#8fd7ff77';ctx.lineWidth=1;ctx.beginPath();ctx.arc(cx,cy,r,0,6.28);ctx.stroke();ctx.restore()}
function solar(scale,alpha,t){ctx.save();ctx.globalAlpha=alpha;ctx.translate(W/2,H*.46);const u=Math.min(W*.46,H*.43)*scale;ctx.scale(u,u);ctx.rotate(-.18);ctx.lineWidth=.0014
 const colors=['#c9bdb1','#e9b974','#74bed8','#bf7754','#ccb693','#d5c7a0','#9ccccb','#688ac2'];for(let i=7;i>=0;i--){const r=.16+i*.11;ctx.strokeStyle='#afbcd330';ctx.beginPath();ctx.ellipse(0,0,r,r*.46,0,0,6.28);ctx.stroke();const a=i*2.43+(reduced?0:t*.014/(i+1)),x=Math.cos(a)*r,y=Math.sin(a)*r*.46;const pr=[.007,.012,.013,.01,.029,.025,.019,.018][i];ctx.fillStyle=colors[i];ctx.beginPath();ctx.arc(x,y,pr,0,6.28);ctx.fill();if(i===5){ctx.strokeStyle='#c9b792a0';ctx.lineWidth=.008;ctx.beginPath();ctx.ellipse(x,y,.046,.013,-.2,0,6.28);ctx.stroke()}}
 glow(ctx,0,0,.21,'#ef9d43',.75);glow(ctx,0,0,.09,'#ffe6a1',1);ctx.fillStyle='#fff2c6';ctx.beginPath();ctx.arc(0,0,.046,0,6.28);ctx.fill();ctx.restore()}
function milkyway(scale,alpha,t,x=W/2,y=H*.46,angle=-.4){ctx.save();ctx.globalAlpha=alpha;ctx.translate(x,y);ctx.rotate(angle);const u=Math.min(W*.43,H*.46)*scale;ctx.scale(u,u);glow(ctx,0,0,1.1,'#34427a',.25);glow(ctx,0,0,.3,'#ecc49a',.7);for(const p of galaxy){ctx.globalAlpha=alpha*p.a;ctx.fillStyle=p.c>.7?'#edceab':'#a2badf';ctx.fillRect(p.x,p.y*.5+p.z,.0028,.0028)}ctx.restore()}
function universe(scale,alpha,t){ctx.save();ctx.globalAlpha=alpha;ctx.translate(W/2,H*.46);ctx.scale(scale,scale);for(let i=0;i<85;i++){const a=i*2.399,r=Math.sqrt(i/85),x=Math.cos(a)*r*W*.57,y=Math.sin(a)*r*H*.47;ctx.save();ctx.translate(x,y);ctx.rotate(i*1.7);ctx.scale(1,.28+(i%4)*.1);glow(ctx,0,0,6+(i%9)*2,i%3?'#7795bc':'#eacaa0',.5);ctx.fillStyle='#e9d6b9';ctx.globalAlpha=alpha*.7;ctx.fillRect(-1,-1,2,2);ctx.restore()}ctx.restore()}
function starWords(morph,t){const size=Math.min(W*.87,1100),cy=H*.47;ctx.save();for(let i=0;i<words.length;i++){const p=words[i],f=textFrom[i],m=ease(morph);const x=lerp(W/2+f.x*W*.6,W/2+p.x*size,m),y=lerp(H/2+f.y*H*.6,cy+p.y*size,m);ctx.globalAlpha=(.48+.5*Math.pow(Math.sin(p.p+t*.6),2))*clamp(morph*3);ctx.fillStyle=i%5?'#fff1d6':'#b7d9ff';ctx.beginPath();ctx.arc(x,y,(W<650?.65:1.05)*(i%11?1:1.7),0,6.28);ctx.fill();if(i%49===0&&m>.8){ctx.globalAlpha*=.2;ctx.fillRect(x-4,y-.4,8,.8);ctx.fillRect(x-.4,y-4,.8,8)}}ctx.restore()}
function visual(index,scale,alpha,t){if(index===0)drawRoom(scale,alpha);else if(index===1)australia(scale,alpha,t);else if(index===2)earth(scale,alpha,t);else if(index===3)solar(scale,alpha,t);else if(index===4)milkyway(scale,alpha,t);else universe(scale,alpha,t)}
function render(){if(!W||!room)return
 if(state==='welcome'||state==='portals'){drawRoom();if(state==='welcome'){const g=ctx.createLinearGradient(0,0,0,H*.7);g.addColorStop(0,'#f2eadbcc');g.addColorStop(.68,'#f2eadbbd');g.addColorStop(1,'#f2eadb00');rect(ctx,0,0,W,H*.7,g)}if(state==='portals'&&hover>=0){const p=portals[hover];ctx.save();ctx.shadowBlur=22;ctx.shadowColor='#ffdf97';ctx.lineWidth=2;ctx.strokeStyle='#fff0bf';arch(ctx,p.x,p.y,p.w,p.h);ctx.stroke();ctx.restore()}return}
 background(elapsed)
 if(state==='journey'){const p=timeline(elapsed,reduced),e=ease(p.local);if(p.stage<5){if(reduced){visual(p.stage,1,1-ease((p.local-.35)/.3),elapsed);visual(p.stage+1,1,ease((p.local-.4)/.3),elapsed)}else{visual(p.stage+1,lerp(1.65,1,e),ease((p.local-.10)/.55),elapsed);visual(p.stage,Math.exp(-e*3.9),1-ease((p.local-.7)/.3),elapsed)}}else{universe(lerp(1,.55,e),1-e,elapsed);starWords(e,elapsed)}
 document.querySelector('#progress').style.transform=`scaleX(${clamp((p.stage+p.local)/5)})`
 if(p.stage!==stageShown){stageShown=p.stage;document.querySelector('#scale-number').textContent=p.stage===0?'OUR LOVE STARTS HERE':p.stage===5?'AND EVEN THAT ISN’T BIG ENOUGH':'AND STILL, WE LOVE YOU MORE';document.querySelector('#scale-name').textContent=STAGES[p.stage][0];document.querySelector('#scale-detail').textContent=STAGES[p.stage][1];document.querySelectorAll('.story-milestones li').forEach((item,i)=>{item.classList.toggle('passed',i<p.stage);if(i===p.stage)item.setAttribute('aria-current','step');else item.removeAttribute('aria-current')});announce.textContent='We love you '+STAGES[p.stage].join(' ')}
 if(p.done)setState('reveal')
 }else if(state==='reveal'){starWords(1,reduced?0:elapsed)}else if(state==='returning'){const e=ease(elapsed/(reduced?.6:2.6));ctx.save();ctx.globalAlpha=1-e;starWords(1,elapsed);ctx.restore();drawRoom(reduced?1:lerp(.04,1,e),e);if(e>=1)setState('portals')}
}
function setState(next){if(next==='journey'){closeGardenMenu();document.querySelector('#garden-toast').hidden=true;clearTimeout(toastTimer)}if(next==='journey'&&living){const snap=living.snapshot();room=document.createElement('canvas');room.width=Math.round(W*DPR);room.height=Math.round(H*DPR);room.getContext('2d').drawImage(snap.canvas,snap.left,0,snap.width,snap.canvas.height,0,0,room.width,room.height)}living?.setActive(next==='welcome'||next==='portals');partyGame?.setActive(next==='welcome'||next==='portals');state=next;elapsed=0;document.body.dataset.state=next;Object.entries(panels).forEach(([k,p])=>{p.hidden=k!==next});if(next==='journey'){stageShown=-1;document.querySelector('#skip').focus({preventScroll:true})}else if(next==='reveal'){announce.textContent='This much! More than all of that. And more every day.';document.querySelector('#return').focus({preventScroll:true})}else if(next==='portals'){history.replaceState(null,'','?home=portals');announce.textContent='Welcome home, Sam. Choose one of four museum portals.';document.querySelector('.portal-links a').focus({preventScroll:true})}render()}
document.querySelector('#begin').addEventListener('click',()=>setState('journey'))
document.querySelector('#skip').addEventListener('click',()=>setState('reveal'))
document.querySelector('#return').addEventListener('click',()=>setState('returning'))
document.querySelector('#replay').addEventListener('click',()=>{history.replaceState(null,'',location.pathname);setState('journey')})
document.querySelectorAll('.portal-links a').forEach((link,i)=>{link.addEventListener('pointerenter',()=>{hover=i;render()});link.addEventListener('pointerleave',()=>{hover=-1;render()});link.addEventListener('focus',()=>{hover=i;render()});link.addEventListener('blur',()=>{hover=-1;render()})})
motion.addEventListener('change',event=>{reduced=event.matches;living?.setReduced(reduced);if(state==='journey')setState('reveal');else render()})
// Pause the cinematic while the tab is hidden; coming back never skips the gift.
document.addEventListener('visibilitychange',()=>{last=0})
function frame(now){const delta=last?Math.min((now-last)/1000,.1):0;last=now;if(!document.hidden&&living&&(state==='welcome'||state==='portals'))living.draw(delta);if(!document.hidden&&['journey','reveal','returning'].includes(state)){if(!(reduced&&state==='reveal')){elapsed+=delta;render()}}requestAnimationFrame(frame)}
resize();if(new URLSearchParams(location.search).get('home')==='portals')setState('portals');requestAnimationFrame(frame)
if ('serviceWorker' in navigator) {
  addEventListener('load',()=>navigator.serviceWorker.register('./sw.js').catch(()=>{}))
}
addEventListener('keydown',event=>{if(event.key==='Escape'&&state==='journey')setState('reveal')})

// The birthday film remains independent of the garden renderer. A WebGL failure
// leaves the invitation and destinations usable through the original fallback.
let toastTimer=null
function gardenMessage(message){const toast=document.querySelector('#garden-toast');toast.querySelector('span').textContent=message;toast.hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>{toast.hidden=true},6000)}
if(typeof WebGLRenderingContext!=='undefined'){
 import('./living-home.js?v=party1').then(({createLivingHome})=>{
  living=createLivingHome({container:document.querySelector('#living-pan'),onMessage:gardenMessage,reducedMotion:reduced})
  document.body.classList.add('living-ready');living.resize(true);living.setActive(state==='welcome'||state==='portals')
  const actions=document.querySelector('#garden-actions')
  living.hotspots.forEach(({id,label})=>{const button=document.createElement('button');button.textContent=label;button.dataset.surprise=id;button.addEventListener('click',()=>{living.trigger(id);if(matchMedia('(max-width:700px)').matches)closeGardenMenu()});actions.append(button)})
  console.info('Living garden ready:',JSON.stringify(living.stats()))
 }).catch(error=>{console.error('Living garden could not start',error);document.body.classList.add('garden-unavailable');gardenMessage('The garden couldn’t open on this device. Your birthday journey and the four worlds are still ready.')})
}else{
 document.body.classList.add('garden-unavailable')
}
const gardenMenu=document.querySelector('#garden-menu'),gardenScrim=document.querySelector('#garden-scrim'),gardenDiscover=document.querySelector('#garden-discover')
function openGardenMenu(){gardenMenu.classList.add('open');gardenMenu.inert=false;gardenScrim.classList.add('open');gardenDiscover.setAttribute('aria-expanded','true');gardenMenu.querySelector('button')?.focus()}
function closeGardenMenu(returnFocus){if(!gardenMenu.classList.contains('open'))return;gardenMenu.classList.remove('open');gardenMenu.inert=true;gardenScrim.classList.remove('open');gardenDiscover.setAttribute('aria-expanded','false');if(returnFocus)gardenDiscover.focus()}
gardenDiscover.addEventListener('click',()=>{gardenMenu.classList.contains('open')?closeGardenMenu(true):openGardenMenu()})
gardenScrim.addEventListener('click',()=>closeGardenMenu())
document.querySelector('#garden-menu-close').addEventListener('click',()=>closeGardenMenu(true))
document.querySelector('#garden-motion').addEventListener('click',()=>{gardenPaused=!gardenPaused;living?.setPaused(gardenPaused);const button=document.querySelector('#garden-motion');button.setAttribute('aria-pressed',String(gardenPaused));button.textContent=gardenPaused?'Let it live':'Pause garden'})
document.querySelector('#garden-toast button').addEventListener('click',()=>{document.querySelector('#garden-toast').hidden=true;clearTimeout(toastTimer)})
addEventListener('keydown',event=>{if(event.key==='Escape')closeGardenMenu(true)})

document.querySelectorAll('#garden-pan-controls button').forEach((button,i)=>button.addEventListener('click',()=>document.querySelector('#living-pan').scrollBy({left:(i?1:-1)*innerWidth*.7,behavior:reduced?'instant':'smooth'})))

// "Party": ten seconds of nightclub lights/lasers (CSS, #party-overlay), every
// character jumping (living.party() flips a shared flag their own per-frame
// callbacks already watch — see living-home.js/garden-people.js), and a randomly
// picked Spotify song from whoever's nominated one in characters/messages.txt
// (extracted to party-songs.json by tools/prepare_party_songs.py).
let partySongsPromise=null,partyActive=false,spotifyIframeApiPromise=null
function loadPartySongs(){
 partySongsPromise??=fetch('./party-songs.json').then(r=>r.ok?r.json():[]).catch(()=>[])
 return partySongsPromise
}
function loadSpotifyIframeApi(){
 spotifyIframeApiPromise??=new Promise(resolve=>{
  window.onSpotifyIframeApiReady=IFrameAPI=>resolve(IFrameAPI)
  const tag=document.createElement('script');tag.src='https://open.spotify.com/embed/iframe-api/v1';tag.async=true
  document.body.append(tag)
 })
 return spotifyIframeApiPromise
}
// `music:false` is the PARTY-puzzle finale: the video already has its own
// audio, so the lights run over the top of it in silence rather than fighting
// a Spotify track.
async function startParty({duration=10000,music=true}={}){
 if(partyActive)return
 if(!living){gardenMessage('Just a moment — the garden is still waking up.');return}
 if(!living.party(duration))return
 partyActive=true
 const button=document.querySelector('#garden-party');button.disabled=true
 document.body.classList.add('party-mode')
 let mount=null,controller=null
 if(music){
  const songs=await loadPartySongs()
  if(songs.length){
   const pick=songs[Math.floor(Math.random()*songs.length)]
   gardenMessage(`🎉 Party time! Playing ${pick.character}’s pick…`)
   try{
    const IFrameAPI=await loadSpotifyIframeApi()
    const player=document.querySelector('#party-player');player.hidden=false
    mount=document.createElement('div');player.append(mount)
    IFrameAPI.createController(mount,{uri:`spotify:track:${pick.trackId}`,width:'100%',height:'152'},c=>{controller=c;c.addListener('ready',()=>c.play())})
   }catch(error){console.error('Party music could not start',error)}
  }else{
   gardenMessage('🎉 Party time! Nominate a song in characters/messages.txt for next time.')
  }
 }
 setTimeout(()=>{
  document.body.classList.remove('party-mode')
  partyActive=false;button.disabled=false
  controller?.pause();controller?.destroy?.()
  const player=document.querySelector('#party-player');player.hidden=true;mount?.remove()
 },duration)
}
document.querySelector('#garden-party').addEventListener('click',()=>startParty())

// The PARTY letter puzzle owns its own tiles, boxes and video panel; all it
// needs from here is the toast and, on the fifth correct letter, thirty
// seconds of the nightclub lights playing over the top of the big finish.
import('./party-letters.js?v=1').then(({createPartyGame})=>{
 partyGame=createPartyGame({onMessage:gardenMessage,onSolved:()=>startParty({duration:30000,music:false})})
 partyGame?.setActive(state==='welcome'||state==='portals')
}).catch(error=>console.error('PARTY puzzle could not start',error))
