// Package the generated source texture; SVG controls come unchanged from Heroicons.
import {createRequire} from 'node:module';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),build=process.argv[2],source=process.argv[3];
if(!build||!source)throw new Error('Supply isolated build directory (sharp@0.33.5) and generated PCB source PNG');
const require=createRequire(resolve(build,'node_modules/package.json')),sharp=require('sharp');
const dest=resolve(root,'training_web/assets');mkdirSync(dest,{recursive:true});
await sharp(resolve(source)).resize(768,768,{fit:'inside'}).webp({quality:76}).toFile(resolve(dest,'playground-pcb.webp'));
for(const file of ['pause.svg','play.svg','arrow-path.svg','LICENSE']){
 const path=file==='LICENSE'?'LICENSE':'optimized/24/outline/'+file;
 const response=await fetch('https://raw.githubusercontent.com/tailwindlabs/heroicons/v2.2.0/'+path);
 if(!response.ok)throw new Error('Cannot read pinned Heroicons '+file);
 writeFileSync(resolve(dest,file==='LICENSE'?'heroicons-LICENSE.txt':'playground-'+file),await response.text());
}
writeFileSync(resolve(dest,'playground-assets.md'),'# Playground assets\n\nPCB solder-mask texture: generated with the built-in image-generation tool from the selected first Fruition mock as material reference. No circuit, text or components were baked into the texture. Original generation exec-992f897d-19ef-4ade-8c03-86b72e6bac24.png; production WebP is an optimized encoding.\n\nControl icons: unchanged Heroicons v2.2.0 24px outline (MIT), from the pinned official tailwindlabs/heroicons repository. Hardware, markings, arrows and choice previews are real runtime 3D meshes/textures, not pre-rendered loop videos.\n');
