// Reproducible, offline runtime bundle from pinned, build-only npm dependencies.
// npm install --prefix <build-dir> --no-audit --no-fund three@0.160.1 esbuild@0.25.0
import {createRequire} from 'node:module';
import {readFileSync,writeFileSync,mkdirSync,copyFileSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
if(!process.argv[2])throw new Error('Supply isolated build directory');
const dependencies=resolve(process.argv[2],'node_modules'),require=createRequire(resolve(dependencies,'package.json'));
const three=JSON.parse(readFileSync(resolve(dependencies,'three/package.json'),'utf8'));
if(three.version!=='0.160.1')throw new Error('Unexpected Three version');
const esbuild=require('esbuild');if(esbuild.version!=='0.25.0')throw new Error('Unexpected bundler version');
const dest=resolve(root,'training_web/vendor');mkdirSync(dest,{recursive:true});
await esbuild.build({stdin:{contents:"export {Scene,Group,Mesh,BoxGeometry,CylinderGeometry,SphereGeometry,TorusGeometry,PlaneGeometry,ExtrudeGeometry,Shape,Path,TubeGeometry,CatmullRomCurve3,MeshStandardMaterial,MeshBasicMaterial,ShadowMaterial,WebGLRenderer,PerspectiveCamera,AmbientLight,HemisphereLight,DirectionalLight,PointLight,Texture,CanvasTexture,Vector3,Vector2,Raycaster,Color,SRGBColorSpace,PCFSoftShadowMap,ACESFilmicToneMapping,DoubleSide,PMREMGenerator} from 'three'; export {RoomEnvironment} from 'three/examples/jsm/environments/RoomEnvironment.js';",resolveDir:resolve(process.argv[2]),sourcefile:'training-three.js'},bundle:true,format:'iife',globalName:'TrainingThree',minify:true,legalComments:'inline',outfile:resolve(dest,'training-three.min.js')});
copyFileSync(resolve(dependencies,'three/LICENSE'),resolve(dest,'three-LICENSE.txt'));
writeFileSync(resolve(dest,'README.md'),'# Training 3D runtime\n\nThree.js 0.160.1, MIT; bundled with esbuild 0.25.0 using tools/build_training_playground_vendor.mjs. Served inline; no runtime CDN or package downloads. Only renderer/geometry/material/camera classes used by the interactive board are exported.\n');
