/* Educational surface print, not an ordering code or a universal maker rule. */
(function(root){
 'use strict';
 const same=(a,b)=>Math.abs(a-b)<=Math.max(1e-12,Math.abs(a)*1e-10);
 function encode(value,profile='three'){
  if(!['three','four','underline'].includes(profile))throw new RangeError('Unknown marking example');
  if(!Number.isFinite(value)||value<=0)return null;
  const underline=profile==='underline',digits=profile==='four'?3:2,length=digits+1;
  if(underline){
   // Stackpole RMCF/RMCP 0603, E24-only values, date codes >= 2025-04-01.
   const normalized=value/10**(Math.floor(Math.log10(value))-1);
   if(value<.1||value>1e6||![10,11,12,13,15,16,18,20,22,24,27,30,33,36,39,43,47,51,56,62,68,75,82,91].some(n=>same(n,normalized))||[10,11,13,15,20,75].some(n=>same(n,normalized)))return null;
  }
  const result=(code,kind)=>({code,ohms:value,kind,underline,profile});
  // R occupies the decimal point, including sub-ohm examples such as R10.
  if(value<(profile==='four'?100:10)){
   for(let places=1;places<=3;places++){
    const decimal=value.toFixed(places),code=decimal.replace(/^0\./,'R').replace('.','R');
    if(code.length<=length&&same(Number(decimal),value))return result(code.padEnd(length,'0'),'R小数点码');
   }
  }
  // Encode this selected rule exactly. Never round the lab value to fit it.
  for(let exponent=0;exponent<=7;exponent++){
   const significant=Math.round(value/10**exponent);
   if(significant>=10**(digits-1)&&significant<10**digits&&same(significant*10**exponent,value))return result(String(significant)+exponent,(digits+1)+'位数字码');
  }
  return null;
 }
 const glyphs={
  '0':['01110','10001','10011','10101','11001','10001','01110'],
  '1':['00100','01100','00100','00100','00100','00100','01110'],
  '2':['01110','10001','00001','00010','00100','01000','11111'],
  '3':['11110','00001','00001','01110','00001','00001','11110'],
  '4':['00010','00110','01010','10010','11111','00010','00010'],
  '5':['11111','10000','10000','11110','00001','00001','11110'],
  '6':['01110','10000','10000','11110','10001','10001','01110'],
  '7':['11111','00001','00010','00100','01000','01000','01000'],
  '8':['01110','10001','10001','01110','10001','10001','01110'],
  '9':['01110','10001','10001','01111','00001','00001','01110'],
  'R':['11110','10001','10001','11110','10100','10010','10001']
 };
 function attach(faces,value,materials,profile='three'){
  const mark=encode(value,profile);if(!mark)return faces;
  const cover=faces.filter(f=>f.id==='cover');
  const top=Math.max(...cover.flatMap(f=>f.p.map(p=>p[1])));
  const face=cover.find(f=>f.p.every(p=>same(p[1],top)));
  if(!face)return faces;
  const xs=face.p.map(p=>p[0]),zs=face.p.map(p=>p[2]);
  const cx=(Math.min(...xs)+Math.max(...xs))/2,cz=(Math.min(...zs)+Math.max(...zs))/2;
  const columns=mark.code.length*6-1,cell=1.05/columns,depth=.44/7,ink=[];
  for(const [index,char] of [...mark.code].entries())for(const [row,line] of glyphs[char].entries())for(let col=0;col<5;col++)if(line[col]==='1'){
   const x=cx-1.05/2+(index*6+col)*cell,z=cz-.22+row*depth;
   ink.push([[x,top,z],[x+cell*.92,top,z],[x+cell*.92,top,z+depth*.92],[x,top,z+depth*.92]]);
  }
  // Render inside this face's paint pass, so nearer faces hide the print naturally.
  const bounds=()=>{const points=ink.flat(),x=points.map(p=>p[0]),z=points.map(p=>p[2]);return {left:Math.min(...x),right:Math.max(...x),back:Math.min(...z),front:Math.max(...z)};};
  if(mark.underline){const b=bounds();ink.push([[b.left,top,b.front+.04],[b.right,top,b.front+.04],[b.right,top,b.front+.065],[b.left,top,b.front+.065]]);}
  // Centre the visible print, including its underline, not the glyph grid's
  // unequal side bearings. Material markers move aside instead of moving ink.
  const b=bounds(),dx=cx-(b.left+b.right)/2,dz=cz-(b.back+b.front)/2;
  for(const quad of ink)for(const point of quad){point[0]+=dx;point[2]+=dz;}
  face.ink=ink;face.inkColor=materials?'#14283e':'#f6f8fb';face.markingCode=mark.code;face.markingUnderline=mark.underline;
  return faces;
 }
 const api=Object.freeze({encode,attach});if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.TrainingResistorMarking=api;
})(typeof window==='undefined'?globalThis:window);
