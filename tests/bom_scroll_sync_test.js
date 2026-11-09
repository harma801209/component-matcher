// Execute the shipped frontend with asynchronous, browser-like scroll events.
// No browser/account/network is involved; fixtures contain no real BOM data.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const html=fs.readFileSync(path.join(__dirname,'../bom_comparison_table/index.html'),'utf8');
const script=html.match(/<script>([\s\S]*?)<\/script>/)[1];

function fixture(coalesce=false){
  const queue=[],messages=[],writes=[];
  let activeWrap=null,incoming=null,resizeCallback;
  class Node{
    constructor(id,width=600,content=2000){
      this.id=id;this.clientWidth=width;this.scrollWidth=content;this.x=0;
      this.style={};this.events={};this.dataset={};this.scrollTop=0;
      this.classList={toggle(){},remove(){},add(){}};
    }
    get scrollLeft(){return this.x;}
    set scrollLeft(value){
      const next=Math.max(0,Math.min(Number(value),this.scrollWidth-this.clientWidth));
      if(next===this.x)return;
      this.x=next;writes.push({node:this.id,value:next,user:Boolean(this.byUser)});
      if(!coalesce||!queue.some(event=>event.node===this))queue.push({node:this});
    }
    addEventListener(type,fn){(this.events[type]??=[]).push(fn);}
    setAttribute(){}
    getBoundingClientRect(){return {height:this.id==='table-top-scroll'?16:200};}
    querySelector(selector){return selector==='thead'?null:null;}
    querySelectorAll(){return [];}
    replaceChildren(){if(this.id==='table-root')activeWrap=null;}
    append(node){if(node?.id?.startsWith('wrap'))activeWrap=node;}
  }
  const ids=['table-root','compare-selection','compare-message','compare-run','table-top-scroll',
    'table-top-scroll-spacer','compare-result','compare-summary','compare-issues','compare-empty',
    'compare-pages','compare-page','compare-prev','compare-next'];
  const nodes=Object.fromEntries(ids.map(id=>[id,new Node(id)]));
  const root=nodes['table-root'],top=nodes['table-top-scroll'];
  root.querySelector=selector=>selector==='.bom-result-table-wrap'?activeWrap:null;
  const windowEvents={};
  const parent={postMessage(value){messages.push(value);}};
  const window={parent,location:{origin:'https://fixture.invalid'},
    addEventListener(type,fn){(windowEvents[type]??=[]).push(fn);}};
  const context={window,document:{getElementById:id=>nodes[id],querySelector:()=>new Node('toolbar')},
    DOMParser:class{parseFromString(){return {querySelectorAll:()=>[],querySelector:()=>incoming};}},
    ResizeObserver:class{constructor(fn){resizeCallback=fn;}observe(){}},console,Set,WeakMap,Date};
  vm.runInNewContext(script,context,{filename:'shipped-bom-comparison.js'});
  let renderCount=0;
  function render(wrap){
    incoming=wrap;
    for(const fn of windowEvents.message)fn({source:parent,origin:window.location.origin,
      data:{type:'streamlit:render',args:{revision:'same',headers:[],table_html:'fixture-'+(++renderCount)}}});
  }
  const wrap=new Node('wrap-1');render(wrap);
  function user(node,value){node.byUser=true;node.scrollLeft=value;node.byUser=false;}
  function next(){const event=queue.shift();assert.ok(event,'expected queued scroll');
    for(const fn of event.node.events.scroll||[])fn({target:event.node});}
  function flush(){let count=0;while(queue.length){assert.ok(++count<100,'scroll feedback did not settle');next();}}
  flush();writes.length=0;
  return {wrap,top,user,next,flush,queue,writes,messages,resize:()=>resizeCallback(),
    replacement(){const node=new Node('wrap-'+(++renderCount));render(node);return node;}};
}

let scenarios=0;
for(const coalesce of [false,true]){
  for(const fromTop of [false,true]){
    const f=fixture(coalesce),source=fromTop?f.top:f.wrap,target=fromTop?f.wrap:f.top;
    f.user(source,100);f.next(); // queues an echo from the linked scrollbar
    assert.equal(target.scrollLeft,100);
    f.user(source,180);         // pointer moves before that echo is delivered
    f.next();                  // stale programmatic echo must not rewind pointer
    assert.equal(source.scrollLeft,180,'linked scroll event rewound an active drag');
    f.flush();assert.equal(source.scrollLeft,180);assert.equal(target.scrollLeft,180);
    assert.ok(!f.messages.some(message=>message.type==='streamlit:setComponentValue'));
    scenarios++;
  }
  {
    const f=fixture(coalesce);
    f.user(f.wrap,100);f.next();f.user(f.top,260);f.flush();
    assert.equal(f.wrap.scrollLeft,260,'real input on linked bar must not be discarded');
    assert.equal(f.top.scrollLeft,260);scenarios++;
  }
  {
    const f=fixture(coalesce);
    f.user(f.wrap,100);f.next();f.user(f.wrap,180);f.resize();f.next();
    // A resize can queue another linked event before the previous echo lands.
    if(!coalesce){
      const pendingSource=f.queue.shift();f.user(f.wrap,240);f.next();
      assert.equal(f.wrap.scrollLeft,240,'second delayed echo rewound active drag');
      f.queue.unshift(pendingSource);
    }
    f.flush();assert.equal(f.top.scrollLeft,f.wrap.scrollLeft);scenarios++;
  }
  {
    const f=fixture(coalesce);
    for(const value of [20.25,40.5,79.75,200.25,600.5,1399.75,1400,0]){
      f.user(f.wrap,value);f.resize();f.flush();
      assert.equal(f.wrap.scrollLeft,value);
      assert.ok(Math.abs(f.top.scrollLeft-value)<=.5,'linked fractional position exceeded rounding tolerance');
    }
    scenarios++;
  }
  {
    const f=fixture(coalesce);
    f.top.scrollWidth=1998; // zoom/rounding: linked range can be slightly shorter
    f.user(f.wrap,1400);f.flush();
    assert.equal(f.wrap.scrollLeft,1400,'clamping the linked bar must not move the table back');
    assert.equal(f.top.scrollLeft,1398);scenarios++;
  }
  {
    const f=fixture(coalesce);
    f.user(f.wrap,100);const stale=f.queue.shift();
    const current=f.replacement();f.flush();f.user(current,400);f.flush();
    f.queue.push(stale);f.flush();
    assert.equal(current.scrollLeft,400,'detached table event must not move current table');
    assert.equal(f.top.scrollLeft,400);scenarios++;
  }
}
console.log(JSON.stringify({passed:true,scenarios}));
