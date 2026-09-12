import * as THREE from './vendor/three/build/three.module.js'
import {CHARACTERS,birthdayName,birthdayGreeting} from './garden-characters.mjs?v=3'

export function addGardenPeople({scene,group,ball,rod,mesh,sphere,boxGeo,cylinder,cone,surprise,callbacks,burst,onMessage,softNotes,textSign,getTime,partyState={}}) {
 // Merge rigid details by material inside each character, keeping arms articulated.
 function consolidate(g){const sets=new Map();for(const o of [...g.children])if(o.isMesh){const key=o.material.uuid;if(!sets.has(key))sets.set(key,[]);sets.get(key).push(o)}
 for(const items of sets.values()){if(items.length<2)continue;const pos=[],normal=[],uv=[];for(const o of items){o.updateMatrix();const geo=(o.geometry.index?o.geometry.toNonIndexed():o.geometry.clone());geo.applyMatrix4(o.matrix);pos.push(...geo.attributes.position.array);normal.push(...geo.attributes.normal.array);if(geo.attributes.uv)uv.push(...geo.attributes.uv.array);else uv.push(...new Array(geo.attributes.position.count*2).fill(0));geo.dispose();g.remove(o)}const geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));geo.setAttribute('normal',new THREE.Float32BufferAttribute(normal,3));geo.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));mesh(g,geo,items[0].material)} }
 function flower(g,p,color,size=.12){for(let i=0;i<5;i++)ball(g,color,[p[0]+Math.cos(i*1.256)*size,p[1]+Math.sin(i*1.256)*size,p[2]],[size*.8,size*.8,.045]);ball(g,'#ffe576',p,[size*.5,size*.5,.055])}
 function glasses(g,color,dark=false,top=false){const y=top?2.18:1.92,z=top?.06:.31;for(const s of [-1,1]){const ring=mesh(g,new THREE.TorusGeometry(.11,.018,6,12),color,[s*.14,y,z],[1.1,.8,1]);if(top)ring.rotation.x=-.8;if(dark)ball(g,'#164759',[s*.14,y,z-.009],[.105,.075,.02])}rod(g,[-.035,y,z],[.035,y,z],.014,color)}
 for(const d of CHARACTERS){const {x,z}=d,name=birthdayName(d.file),g=group(scene,[x,.25,z]);g.name=`Birthday_${name.replaceAll(' ','_')}`;const scale=d.scale||1.12;g.scale.setScalar(scale)
 const skin='#eac49f';for(const s of [-1,1]){rod(g,[s*.18,.12,0],[s*.18,.8,0],.14,d.pants||'#27627c');ball(g,'#d7f4e2',[s*.18,.1,.06],[.18,.10,.25]);ball(g,skin,[s*.32,1.84,0],[.07,.12,.10])}
 ball(g,d.shirt,[0,1.12,0],[.4,.5,.25]);ball(g,skin,[0,1.88,0],[.32,.37,.30]);ball(g,skin,[0,1.83,.30],[.045,.055,.045]);
 for(const s of [-1,1]){ball(g,'#244953',[s*.115,1.93,.278],[.029,.035,.025]);ball(g,'#ffffff',[s*.11,1.943,.299],[.008,.011,.008])}
 // A small curved smile belongs to the same friendly toy-like face language.
 const smile=mesh(g,new THREE.TorusGeometry(.09,.009,5,12,Math.PI),'#a16c60',[0,1.77,.29]);smile.rotation.z=Math.PI
 const capY=d.style==='buzz'?2.09:2.075,capH=d.style==='buzz'?.14:.23
 if(d.style==='balding'){for(const s of [-1,1])ball(g,d.hair,[s*.27,2.0,-.04],[.095,.16,.22])}else ball(g,d.hair,[0,capY,-.035],[.34,capH,.31])
 if(['long','shoulder','curly'].includes(d.style)){const long=d.style!=='shoulder';ball(g,d.hair,[0,long?1.64:1.78,-.20],[.34,long?.51:.35,.17]);for(const s of [-1,1]){if(d.style==='curly'){for(let i=0;i<6;i++)ball(g,i%3===0?'#c39d5d':d.hair,[s*(.29+Math.sin(i)*.025),2.06-i*.14,.01],[.10,.12,.12])}else ball(g,d.hair,[s*.29,long?1.65:1.79,.01],[.10,long?.49:.31,.17])}}
 if(['spiky','pixie'].includes(d.style))for(let i=0;i<7;i++){const a=i*2.4,o=ball(g,i%3===0?(d.style==='pixie'?'#fff3dc':'#b39156'):d.hair,[Math.sin(a)*.20,2.18+Math.cos(i)*.035,Math.cos(a)*.16],[.11,.16,.075]);o.rotation.z=-.4+i*.1}
 if(d.style==='braided'){ball(g,d.hair,[.08,2.10,-.25],[.23,.22,.19]);for(let i=0;i<8;i++){const a=i/7*Math.PI;ball(g,i%2?'#806447':d.hair,[Math.cos(a)*.29,2.04+Math.sin(a)*.18,.04],[.075,.075,.10])}}
 if(d.highlights)for(const s of [-1,1]){const o=ball(g,'#d4c19a',[s*.23,2.03,.18],[.05,.20,.045]);o.rotation.z=s*.5}
 if(d.beard){ball(g,d.hair,[0,1.67,.16],[.26,.14,.18]);for(const s of [-1,1])ball(g,d.hair,[s*.23,1.76,.16],[.08,.17,.13])}
 if(d.moustache)for(const s of [-1,1])ball(g,d.hair,[s*.075,1.785,.305],[.105,.048,.038])
 if(d.bow){mesh(g,boxGeo,'#f8fcf4',[0,1.35,.235],[.20,.45,.04]);for(const s of [-1,1]){const o=ball(g,'#162e3f',[s*.075,1.51,.27],[.085,.05,.035]);o.rotation.z=s*.3}}
 if(d.glasses)glasses(g,'#282d41');if(d.sunglasses)glasses(g,d.sunglasses,true);if(d.topGlasses)glasses(g,'#26352f',true,true)
 if(d.hat){mesh(g,cylinder,'#223e43',[0,2.18,0],[.47,.045,.37]);mesh(g,cylinder,'#223e43',[0,2.34,-.02],[.3,.32,.25]);mesh(g,cylinder,'#48645c',[0,2.23,-.02],[.308,.06,.258])}
 if(d.flower)flower(g,[-.32,2.1,.11],d.flower,.13)
 if(d.crown){for(let i=0;i<5;i++)flower(g,[(i-2)*.17,2.24+Math.sin(i)*.07,.07],['#40b9eb','#ff68ad','#ffe34f','#9669d3','#ff857c'][i],.12);for(let i=0;i<3;i++){const o=ball(g,i%2?'#a362d1':'#ef67b1',[(i-1)*.13,2.65,-.09],[.055,.38,.055]);o.rotation.z=(i-1)*.3}}
 if(d.lei)for(let i=0;i<11;i++){const a=i/10*Math.PI;ball(g,['#ed6eaf','#ffe160','#a7dd6e','#71cde8'][i%4],[Math.cos(a)*.27,1.43-Math.sin(a)*.37,.24],[.075,.07,.055])}
 if(d.necklace){for(let i=0;i<7;i++){const a=i/6*Math.PI;ball(g,'#54c7e2',[Math.cos(a)*.22,1.48-Math.sin(a)*.18,.24],[.033,.04,.025])}}
 if(d.hood){const o=mesh(g,new THREE.TorusGeometry(.28,.075,6,16,Math.PI),'#b8d6d5',[0,1.43,-.03]);o.rotation.x=Math.PI/2}
 if(d.freckles)for(const s of [-1,1])for(let i=0;i<3;i++)ball(g,'#986f52',[s*(.13+i*.04),1.82+(i%2)*.035,.27],[.01,.009,.009])
 const arms=[-1,1].map(s=>{const a=group(g,[s*.35,1.45,0]);rod(a,[0,0,0],[s*.12,-.55,.06],.10,d.shirt);ball(a,skin,[s*.12,-.57,.06],[.12,.13,.11]);if(d.stripe)rod(a,[s*.08,-.05,.07],[s*.17,-.49,.11],.025,d.stripe);return a});let until=0
 consolidate(g);surprise(name,`${name}: Happy Birthday Sammy`,g,()=>{until=getTime()+5;burst([x,2.6,z],'#ff82bc');onMessage(birthdayGreeting(d.file));softNotes([330,440,554])})
 // At the party, everyone jumps to their own beat (phase-offset by x, like a real crowd) with both arms thrown up.
 callbacks.push(t=>{const partying=partyState.active
 g.rotation.y=partying?Math.sin(t*6+x)*.05:Math.sin(t*.4+x)*.07
 g.position.y=partying?.25+Math.abs(Math.sin(t*7+x*2))*.55:.25+Math.sin(t*1.4+x)*.025
 arms[1].rotation.z=partying?2.4+Math.sin(t*10+x)*.4:(t<until?2.3+Math.sin(t*9)*.3:Math.sin(t+x)*.06)
 arms[0].rotation.z=partying?-2.4+Math.sin(t*10+x+1)*.4:Math.sin(t+x)*.05})
 textSign(name,[x,(d.crown?3.5:2.95)*scale,z],name.length>15?3.6:name.length>9?2.5:1.8)
 }
}
