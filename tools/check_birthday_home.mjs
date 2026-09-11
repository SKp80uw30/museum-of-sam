import assert from 'node:assert/strict'
import fs from 'node:fs'
import vm from 'node:vm'
import { STAGES, clamp, ease, lerp, timeline } from '../web/home-journey.mjs'
// Timeline boundaries, including the shorter reduced-motion alternative.
for(const reduced of [false,true]){
 const step=reduced?1.5:6
 for(let i=0;i<6;i++){assert.equal(timeline(i*step,reduced).stage,i);assert.equal(timeline(i*step,reduced).local,0)}
 assert.equal(timeline(step*6,reduced).done,true)
 assert.equal(timeline(step*6,reduced).progress,1)
 assert.equal(timeline(-3,reduced).stage,0)
}
const root=new URL('../',import.meta.url), html=fs.readFileSync(new URL('web/home.html',root),'utf8')
for(const scene of ['reef','forest','jumping_castle','gallery_home'])assert(html.includes(`./index.html?scene=${scene}`))
for(const f of ['reef','forest','jumping-castle','gallery'])assert(fs.existsSync(new URL(`web/home-assets/${f}.png`,root)))
// Run actual controller against a small DOM/canvas stub: this checks state and
// focus behavior, not pixels or browser compatibility.
const ids=new Map(),links=Array.from({length:4},()=>element()),milestones=Array.from({length:6},()=>element())
function element(){return {classList:{toggle(){}},attributes:{},setAttribute(k,v){this.attributes[k]=v},removeAttribute(k){delete this.attributes[k]},hidden:false,style:{},dataset:{},listeners:{},textContent:'',addEventListener(k,f){this.listeners[k]=f},focus(){this.focused=true}}}
function get(id){if(!ids.has(id))ids.set(id,element());return ids.get(id)}
const context=new Proxy({createLinearGradient:()=>({addColorStop(){}}),createRadialGradient:()=>({addColorStop(){}}),getImageData:()=>({data:new Uint8ClampedArray(1100*240*4)})},{get:(o,k)=>k in o?o[k]:()=>{}})
const document={hidden:false,body:element(),querySelector:s=>s==='.portal-links a'?links[0]:get(s),querySelectorAll:s=>s==='.story-milestones li'?milestones:links,getElementById:id=>get('#'+id),createElement:()=>({getContext:()=>context}),addEventListener(){}}
get('#world').getContext=()=>context
const location={search:'',pathname:'/web/home.html'}
const sandbox={console,navigator:{},document,location,history:{replaceState(...a){this.url=a[2]}},innerWidth:1440,innerHeight:900,devicePixelRatio:1,Image:class{complete=false},matchMedia:()=>({matches:false,addEventListener(){}}),addEventListener(){},requestAnimationFrame(){},URLSearchParams,STAGES,clamp,ease,lerp,timeline}
vm.createContext(sandbox)
const src=fs.readFileSync(new URL('web/home.js',root),'utf8').replace(/^import[^\n]*\n/,'')
vm.runInContext(src,sandbox)
const run=s=>vm.runInContext(s,sandbox)
assert.equal(run('state'),'welcome')
get('#begin').listeners.click();assert.equal(run('state'),'journey');assert(get('#skip').focused)
for(let i=0;i<6;i++){run(`elapsed=${i*6+.1};render()`);assert.equal(run('stageShown'),i);assert.equal(milestones[i].attributes['aria-current'],'step');assert.equal(milestones.filter(m=>m.attributes['aria-current']).length,1);assert(get('#announcement').textContent.startsWith('We love you more than'))}
run('elapsed=36;render()');assert.equal(run('state'),'reveal');assert(get('#return').focused)
get('#return').listeners.click();assert.equal(run('state'),'returning');run('elapsed=3;render()');assert.equal(run('state'),'portals');assert(links[0].focused)
get('#replay').listeners.click();assert.equal(run('state'),'journey');get('#skip').listeners.click();assert.equal(run('state'),'reveal')
run('innerWidth=390;innerHeight=844;resize()');assert.equal(run('portals.length'),4)
run('reduced=true;setState("journey");elapsed=9;render()');assert.equal(run('state'),'reveal')
console.log('PASS: six stages, timing endpoints, reduced motion, begin/skip/replay/return, portal destinations/assets, focus and responsive controller setup. Browser/pixel verification still required.')
