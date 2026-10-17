(function(){try{var s=JSON.parse(localStorage.getItem('apuntia.settings.v1')||'{}');var t=s.theme||'system';var d=t==='dark'||(t==='system'&&matchMedia('(prefers-color-scheme: dark)').matches);document.documentElement.dataset.theme=d?'dark':'light';}catch(e){}})();
'use strict';



const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

/* ---------- Iconos (trazo tipo Lucide, en línea) ---------- */
const ICONS={
 home:'<path d="M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/>',
 book:'<path d="M2 4h6a4 4 0 0 1 4 4v13a3 3 0 0 0-3-3H2z"/><path d="M22 4h-6a4 4 0 0 0-4 4v13a3 3 0 0 1 3-3h7z"/>',
 star:'<path d="m12 2.5 2.9 6 6.6.9-4.8 4.6 1.2 6.5L12 17.4l-5.9 3.1 1.2-6.5L2.5 9.4l6.6-.9z"/>',
 sliders:'<path d="M3 6h9M18 6h3M3 12h3M12 12h9M3 18h11M20 18h1"/><circle cx="15" cy="6" r="3"/><circle cx="9" cy="12" r="3"/><circle cx="17" cy="18" r="3"/>',
 image:'<rect x="3" y="3" width="18" height="18" rx="3"/><circle cx="9" cy="9" r="1.8"/><path d="m21 15-4.5-4.5L5 21"/>',
 camera:'<path d="M4 8h3l1.6-2.4h6.8L17 8h3a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1z"/><circle cx="12" cy="13.5" r="3.8"/>',
 sparkles:'<path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z"/><path d="M19 15v4M17 17h4M5 17v3M3.5 18.5h3"/>',
 search:'<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
 copy:'<rect x="9" y="9" width="12" height="12" rx="2"/><path d="M5 15H4a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v1"/>',
 pdf:'<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M12 12v5M9.5 14.5 12 17l2.5-2.5"/>',
 volume:'<path d="M11 5 6 9H3v6h3l5 4z"/><path d="M15.5 8.5a5 5 0 0 1 0 7M18.5 5.5a9 9 0 0 1 0 13"/>',
 stop:'<rect x="6" y="6" width="12" height="12" rx="2"/>',
 refresh:'<path d="M20 11a8 8 0 0 0-14.5-4M4 4v4h4"/><path d="M4 13a8 8 0 0 0 14.5 4M20 20v-4h-4"/>',
 trash:'<path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3"/>',
 check:'<path d="m5 12.5 4.5 4.5L19 7.5"/>',
 x:'<path d="M6 6l12 12M18 6 6 18"/>',
 plus:'<path d="M12 5v14M5 12h14"/>',
 moon:'<path d="M20 14.5A8 8 0 0 1 9.5 4 8 8 0 1 0 20 14.5z"/>',
 sun:'<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
 eye:'<path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
 arrowLeft:'<path d="M19 12H5M11 6l-6 6 6 6"/>',
 tag:'<path d="M3 4h8.5L21 13.5a1.5 1.5 0 0 1 0 2.1l-5.4 5.4a1.5 1.5 0 0 1-2.1 0L3 11.5z"/><circle cx="7.5" cy="8.5" r="1.4"/>',
 bulb:'<path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-3.5 10.9c.6.5 1 1.2 1 2.1h5c0-.9.4-1.6 1-2.1A6 6 0 0 0 12 3z"/>',
 layers:'<path d="m12 3 9 5-9 5-9-5z"/><path d="m3 13 9 5 9-5"/>',
 scan:'<path d="M4 8V5a1 1 0 0 1 1-1h3M16 4h3a1 1 0 0 1 1 1v3M20 16v3a1 1 0 0 1-1 1h-3M8 20H5a1 1 0 0 1-1-1v-3M4 12h16"/>',
 alert:'<path d="M12 3 2 20h20z"/><path d="M12 10v4M12 17.5v.01"/>',
 list:'<path d="M9 6h12M9 12h12M9 18h12"/><circle cx="4.5" cy="6" r="1"/><circle cx="4.5" cy="12" r="1"/><circle cx="4.5" cy="18" r="1"/>',
 formula:'<path d="M18 5H7l6 7-6 7h11"/>',
 text:'<path d="M5 6h14M5 12h14M5 18h9"/>',
 target:'<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4"/>'
};
const ic=(n,s=20)=>`<svg class="ic" width="${s}" height="${s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONS[n]||''}</svg>`;
function hydrate(root=document){
  $$('[data-i]',root).forEach(el=>{el.innerHTML=ic(el.dataset.i,+el.dataset.s||20);el.removeAttribute('data-i');});
  let k=0;
  $$('[data-logo]',root).forEach(el=>{
    const id='lg'+(k++)+Math.random().toString(36).slice(2,5);
    el.innerHTML=`<svg viewBox="0 0 48 48" aria-hidden="true"><defs><linearGradient id="${id}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#12b886"/><stop offset="1" stop-color="#4f6df5"/></linearGradient></defs><rect width="48" height="48" rx="14" fill="url(#${id})"/><rect x="5" y="5" width="38" height="38" rx="10" fill="none" stroke="rgba(255,255,255,.22)" stroke-width="1.5"/><path d="M14 36 24 13l10 23" fill="none" stroke="#fff" stroke-width="3.6" stroke-linecap="round" stroke-linejoin="round"/><path d="M18.5 29h11" stroke="#fff" stroke-width="3.2" stroke-linecap="round"/><circle cx="24" cy="12.5" r="3" fill="#ffd666"/><path d="M36.5 8.5l1 2.5 2.5 1-2.5 1-1 2.5-1-2.5-2.5-1 2.5-1z" fill="#ffd666"/><circle cx="11" cy="14" r="1.6" fill="#fff" opacity=".8"/><circle cx="12" cy="40" r="1.2" fill="#fff" opacity=".6"/></svg>`;
    el.removeAttribute('data-logo');
  });
}

/* ---------- Datos: materias, detecciones, contenido simulado ---------- */
const SUBJECTS={'Física':{e:'📘',c:'#4c8dff'},'Cálculo':{e:'📗',c:'#22c08a'},'Programación':{e:'📙',c:'#ff9f43'},'Química':{e:'🧪',c:'#b06cff'},'Biología':{e:'🧬',c:'#2fc4d8'},'Historia':{e:'🏛️',c:'#d98c5f'},'Otra':{e:'📓',c:'#8a98a8'}};
const subj=n=>SUBJECTS[n]||SUBJECTS.Otra;
const DTYPE={title:{l:'Título',c:'#ffd666'},text:{l:'Texto',c:'#6aa7ff'},formula:{l:'Fórmula',c:'#ff7ab8'},diagram:{l:'Diagrama',c:'#34e0a1'},list:{l:'Lista',c:'#ff9f5a'}};
const DET=[
 {t:'title',x:5,y:4,w:54,h:13},{t:'text',x:5,y:21,w:56,h:8},{t:'text',x:5,y:30,w:50,h:8},
 {t:'formula',x:5,y:41,w:39,h:14},{t:'list',x:5,y:59,w:39,h:29},{t:'diagram',x:52,y:40,w:43,h:49},{t:'text',x:52,y:21,w:43,h:15}
];
const CONTENT={
 physics:{subject:'Física',title:'Segunda Ley de Newton',
  summary:'La segunda ley de Newton establece la relación entre la fuerza aplicada, la masa y la aceleración de un objeto.',
  formula:'F = m × a',formulaNote:'La fuerza neta es igual a la masa multiplicada por la aceleración.',
  list:{title:'Variables',items:[{k:'F',v:'Fuerza',u:'newton (N)'},{k:'m',v:'Masa',u:'kilogramo (kg)'},{k:'a',v:'Aceleración',u:'m/s²'}]},
  concepts:['Fuerza','Masa','Aceleración'],
  diagram:'Un bloque de masa m sobre una superficie. La fuerza F actúa hacia la derecha y produce una aceleración a en la misma dirección.',
  example:{q:'Una caja de 10 kg recibe una fuerza neta de 50 N. ¿Qué aceleración adquiere?',steps:['a = F / m','a = 50 N / 10 kg','a = 5 m/s²']},
  tldr:'La fuerza neta sobre un cuerpo es proporcional a su aceleración, y la masa es la constante de proporcionalidad: F = m × a.',
  explain:'Imagina empujar un carrito de supermercado vacío y luego uno lleno, con la misma fuerza. El vacío (menos masa) acelera mucho más. Eso es la segunda ley de Newton: con la misma fuerza, más masa significa menos aceleración. Por eso F = m × a: si conoces dos de las tres cantidades, puedes calcular la tercera.',
  remember:['La fuerza y la aceleración tienen la misma dirección.','Se usa la fuerza neta (la suma de todas las fuerzas).','Si la fuerza neta es 0, la aceleración es 0.']},
 calculus:{subject:'Cálculo',title:'Derivadas',
  summary:'La derivada mide qué tan rápido cambia una función en un punto; geométricamente, es la pendiente de la recta tangente a su gráfica.',
  formula:'d/dx (xⁿ) = n · xⁿ⁻¹',formulaNote:'Regla de la potencia: se baja el exponente multiplicando y se resta uno.',
  list:{title:'Reglas básicas',items:[{k:'(x²)′',v:'2x'},{k:'(sen x)′',v:'cos x'},{k:'(eˣ)′',v:'eˣ'}]},
  concepts:['Razón de cambio','Pendiente de la tangente','Regla de la potencia','Límite'],
  diagram:'Una curva con una recta tangente en un punto. La pendiente de la tangente es el valor de la derivada en ese punto.',
  example:{q:'Deriva f(x) = 3x⁴.',steps:['f′(x) = 3 · 4x⁴⁻¹','f′(x) = 12x³']},
  tldr:'La derivada es la razón de cambio instantánea de una función y se interpreta como la pendiente de su recta tangente.',
  explain:'Piensa en el velocímetro de un auto: no te dice cuánto has recorrido, sino qué tan rápido cambia tu posición en este instante. La derivada es ese «velocímetro» para cualquier función. Con la regla de la potencia puedes calcularla rápido: bajas el exponente y le restas uno.',
  remember:['La derivada de una constante es 0.','La derivada de x es 1.','Derivar es lineal: (f + g)′ = f′ + g′.']},
 programming:{subject:'Programación',title:'Estructuras de datos',
  summary:'Una estructura de datos es una forma organizada de almacenar y acceder a la información para que los programas sean más eficientes.',
  formula:'push / pop = O(1)',formulaNote:'Insertar y quitar elementos del tope de una pila toma tiempo constante.',
  list:{title:'Estructuras vistas',items:[{k:'Arreglo',v:'acceso por índice'},{k:'Lista enlazada',v:'nodos con apuntador'},{k:'Pila',v:'LIFO'},{k:'Cola',v:'FIFO'}]},
  concepts:['LIFO','FIFO','Complejidad O(1)','Nodo'],
  diagram:'Una pila vertical con tres elementos. «push» inserta por arriba y «pop» retira el elemento que está en el tope.',
  example:{q:'Haces push(1), push(2), push(3) y luego pop(). ¿Qué elemento sale?',steps:['La pila queda [1, 2, 3]','pop() retira el tope','Sale el 3 (último en entrar, primero en salir)']},
  tldr:'Las estructuras de datos organizan la información; la pila usa LIFO y la cola usa FIFO, ambas con operaciones O(1).',
  explain:'Una pila es como una columna de platos: solo puedes poner o quitar el de arriba. Una cola es como la fila del cine: el primero que llega es el primero en entrar. Elegir la estructura correcta hace que tu programa sea más rápido y más fácil de entender.',
  remember:['Pila = LIFO, Cola = FIFO.','Los arreglos dan acceso directo por índice.','Elige la estructura según las operaciones que más usarás.']}
};
const BOARDS={
 physics:{title:'Segunda Ley de Newton',lines:['La fuerza neta que actúa sobre un cuerpo','es igual a su masa por su aceleración.'],side:['Unidad: 1 N = 1 kg·m/s²','más masa → menos aceleración'],formula:'F = m · a',list:['F → fuerza','m → masa','a → aceleración'],diagram:'physics'},
 calculus:{title:'Derivadas',lines:['La derivada mide la razón de cambio','instantánea de una función.'],side:[],formula:'d/dx (xⁿ) = n·xⁿ⁻¹',list:['(x²)′ = 2x','(sen x)′ = cos x','(eˣ)′ = eˣ'],diagram:'calculus'},
 programming:{title:'Estructuras de datos',lines:['Una estructura de datos organiza la','información para usarla con eficiencia.'],side:['Pila  →  LIFO','Cola  →  FIFO'],formula:'push / pop = O(1)',list:['Arreglo','Lista enlazada','Pila (LIFO)','Cola (FIFO)'],diagram:'stack'}
};

/* ---------- Pizarrones de ejemplo dibujados en canvas (con estética de tiza) ---------- */
function rng(seed){let a=0;for(const ch of seed)a=(a*31+ch.charCodeAt(0))>>>0;return()=>{a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296}}
const _bc={};
function boardURL(kind){
  if(_bc[kind]) return _bc[kind];
  const B=BOARDS[kind]||BOARDS.physics, W=1200, H=750;
  const c=document.createElement('canvas'); c.width=W; c.height=H;
  const g=c.getContext('2d'), R=rng(kind), jit=()=>(R()-.5)*1.6, CH='#f4f1e6';
  const bg=g.createLinearGradient(0,0,W,H); bg.addColorStop(0,'#1d4d44'); bg.addColorStop(1,'#0e2d28');
  g.fillStyle=bg; g.fillRect(0,0,W,H);
  for(let i=0;i<30;i++){const x=R()*W,y=R()*H,r=60+R()*180,rg=g.createRadialGradient(x,y,0,x,y,r);rg.addColorStop(0,'rgba(255,255,255,.045)');rg.addColorStop(1,'rgba(255,255,255,0)');g.fillStyle=rg;g.fillRect(x-r,y-r,r*2,r*2);}
  for(let i=0;i<1400;i++){g.fillStyle=`rgba(255,255,255,${R()*.07})`;g.fillRect(R()*W,R()*H,1+R()*2,1+R()*2);}
  const seg=(x1,y1,x2,y2,col=CH,w=4)=>{g.save();g.strokeStyle=col;g.lineWidth=w;g.lineCap='round';g.shadowColor=col;g.shadowBlur=3;g.globalAlpha=.88;const n=Math.max(1,Math.round(Math.hypot(x2-x1,y2-y1)/22));g.beginPath();g.moveTo(x1,y1);for(let i=1;i<=n;i++)g.lineTo(x1+(x2-x1)*i/n+(i<n?jit():0),y1+(y2-y1)*i/n+(i<n?jit():0));g.stroke();g.restore();};
  const poly=(p,col,w)=>{for(let i=0;i<p.length-1;i++)seg(p[i][0],p[i][1],p[i+1][0],p[i+1][1],col,w);};
  const arrow=(x1,y1,x2,y2,col,w=5)=>{seg(x1,y1,x2,y2,col,w);const a=Math.atan2(y2-y1,x2-x1),L=22;seg(x2,y2,x2-L*Math.cos(a-.5),y2-L*Math.sin(a-.5),col,w);seg(x2,y2,x2-L*Math.cos(a+.5),y2-L*Math.sin(a+.5),col,w);};
  const rect=(x,y,w,h,col,lw=4)=>poly([[x,y],[x+w,y],[x+w,y+h],[x,y+h],[x,y-1]],col,lw);
  const txt=(s,x,y,size,col,maxW,align='left')=>{let z=size;const f=q=>`700 ${q}px Caveat,"Segoe Print","Bradley Hand",cursive`;g.font=f(z);while(g.measureText(s).width>maxW&&z>16){z-=2;g.font=f(z);}g.textAlign=align;g.textBaseline='alphabetic';g.save();g.fillStyle=col;g.shadowColor=col;g.shadowBlur=3;g.globalAlpha=.94;g.fillText(s,x,y);g.globalAlpha=.3;g.fillText(s,x+.9,y+.7);g.restore();return g.measureText(s).width;};
  // título + subrayado ondulado
  const tw=txt(B.title,60,108,92,'#ffe08a',620);
  const up=[];for(let x=60;x<=60+Math.min(tw,620);x+=24)up.push([x,124+(((x-60)/24|0)%2?4:-2)]);poly(up,'#ffe08a',3);
  // texto
  txt(B.lines[0],60,195,44,CH,660); txt(B.lines[1],60,262,44,CH,600);
  B.side.forEach((s,i)=>txt(s,630,192+i*54,40,i?'#bfe3ff':'#ffb3c7',500));
  // fórmula enmarcada
  rect(62,312,452,98,'#9be7ff',3.5); txt(B.formula,288,384,70,'#c7f4ff',410,'center');
  // lista
  B.list.forEach((s,i)=>txt('• '+s,66,492+i*56,46,'#f7e9b0',440));
  // diagramas
  if(B.diagram==='physics'){
    rect(780,470,170,120,CH,5); txt('m',865,556,76,CH,100,'center');
    [[815,602],[915,602]].forEach(([x,y])=>{for(let a=0;a<6.4;a+=.5)seg(x+14*Math.cos(a),y+14*Math.sin(a),x+14*Math.cos(a+.5),y+14*Math.sin(a+.5),CH,4);});
    seg(660,618,1110,618,CH,4);
    arrow(955,530,1105,530,'#ffd666'); txt('F',1030,505,56,'#ffd666',60,'center');
    arrow(790,660,945,660,'#4ee8b0'); txt('a',985,672,56,'#4ee8b0',60,'center');
  }else if(B.diagram==='calculus'){
    arrow(680,640,1120,640,CH,4); arrow(680,640,680,320,CH,4);
    const cv=[];for(let t=0;t<=1.001;t+=.04)cv.push([700+t*380,640-t*t*270]);poly(cv,'#9be7ff',5);
    seg(820,635,1040,447,'#ffd666',5);
    g.save();g.fillStyle='#ff7ab8';g.shadowColor='#ff7ab8';g.shadowBlur=6;g.beginPath();g.arc(928,543,9,0,7);g.fill();g.restore();
    txt('f(x)',728,372,52,'#9be7ff',140); txt('tangente',1030,430,46,'#ffd666',170,'center');
  }else{
    [[560,640],[480,560],[400,480]].forEach((r,i)=>{rect(800,r[0]-80,200,80,CH,5);txt(String(i+1),900,r[0]-22,56,i===2?'#ffd666':CH,60,'center');});
    arrow(900,322,900,392,'#4ee8b0'); txt('push',930,356,46,'#4ee8b0',110);
    arrow(1090,446,1090,350,'#ff9f5a'); txt('pop',1090,332,46,'#ff9f5a',100,'center');
    txt('tope',700,478,46,'#ffd666',110); arrow(796,462,740,462,'#ffd666',4);
  }
  // marco de madera
  g.strokeStyle='#8a6a43'; g.lineWidth=26; g.strokeRect(0,0,W,H);
  g.strokeStyle='rgba(0,0,0,.35)'; g.lineWidth=3; g.strokeRect(13,13,W-26,H-26);
  return _bc[kind]=c.toDataURL('image/jpeg',.82);
}

/* ---------- Estado y almacenamiento ---------- */
const KEY='apuntia.notes.v1', SKEY='apuntia.settings.v1';
const MONTHS=['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre'];
const fmtDate=iso=>{const[y,m,d]=iso.split('-').map(Number);return `${d} ${MONTHS[m-1]} ${y}`;};
const todayISO=()=>{const d=new Date();return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;};
const state={view:'home',from:'home',libMode:'all',notes:[],current:null,token:0,job:null,speaking:false,
  lib:{q:'',subject:'all',sort:'recent',group:false},settings:{theme:'system',rate:1,fast:false,simError:false},lastDeleted:null};

function makeDetections(kind){
  return DET.filter((d,i)=>!(i===6&&!BOARDS[kind].side.length)).map(d=>({...d,conf:Math.round(90+Math.random()*9)}));
}
function newNote(kind,extra={}){
  const n=JSON.parse(JSON.stringify(CONTENT[kind]));
  return Object.assign(n,{id:'n'+Date.now().toString(36)+Math.random().toString(36).slice(2,6),kind,date:todayISO(),tags:[],fav:false,
    detections:makeDetections(kind),conf:Math.round(93+Math.random()*5),organized:false,showTldr:false,showExplain:false},extra);
}
function seed(){
  return [
    newNote('physics',{id:'s-fisica',date:'2026-10-05',board:'physics',tags:['mecánica','parcial 1']}),
    newNote('calculus',{id:'s-calculo',date:'2026-10-03',board:'calculus',fav:true,tags:['límites']}),
    newNote('programming',{id:'s-prog',date:'2026-10-01',board:'programming',tags:['estructuras']})
  ];
}
function loadNotes(){try{const r=localStorage.getItem(KEY);if(r===null)return seed();const a=JSON.parse(r);return Array.isArray(a)?a:seed();}catch{return seed();}}
function persist(){try{localStorage.setItem(KEY,JSON.stringify(state.notes));return true;}catch{toast('No hay espacio para guardar. Elimina apuntes antiguos e inténtalo de nuevo.');return false;}}
function loadSettings(){try{Object.assign(state.settings,JSON.parse(localStorage.getItem(SKEY)||'{}'));}catch{}}
function saveSettings(){try{localStorage.setItem(SKEY,JSON.stringify(state.settings));}catch{}}
const imgOf=n=>n.board?boardURL(n.board):n.img;

/* ---------- Utilidades UI ---------- */
function toast(msg,act){
  const t=document.createElement('div');t.className='toast';
  t.innerHTML=`<span>${esc(msg)}</span>`;
  if(act){const b=document.createElement('button');b.textContent=act.label;b.onclick=()=>{act.fn();t.remove();};t.appendChild(b);}
  $('#toasts').appendChild(t);
  setTimeout(()=>t.remove(),act?7000:3800);
}
function confirmDlg({title,text,ok='Aceptar',cancel='Cancelar',danger=false}){
  return new Promise(res=>{
    const d=$('#confirmDlg');$('#cdTitle').textContent=title;$('#cdText').textContent=text;
    $('#cdOk').textContent=ok;$('#cdCancel').textContent=cancel;
    $('#cdOk').classList.toggle('danger',danger);$('#cdOk').classList.toggle('primary',!danger);
    d.returnValue='';d.addEventListener('close',()=>res(d.returnValue==='ok'),{once:true});d.showModal();
  });
}
function typeInto(el,text,speed=16){
  clearInterval(el._t);el.textContent='';el.classList.add('typing');let i=0;
  el._t=setInterval(()=>{i+=2;el.textContent=text.slice(0,i);if(i>=text.length){clearInterval(el._t);el.classList.remove('typing');el.textContent=text;}},speed);
}
const tween=(from,to,ms,token,cb)=>new Promise(res=>{
  const t0=performance.now();
  (function f(t){if(token!==state.token)return res(false);const k=Math.min(1,(t-t0)/ms);cb(from+(to-from)*(k<.5?2*k*k:1-Math.pow(-2*k+2,2)/2));k<1?requestAnimationFrame(f):res(true);})(t0);
});

/* ---------- Tema ---------- */
const mq=matchMedia('(prefers-color-scheme: dark)');
function isDark(){const t=state.settings.theme;return t==='dark'||(t==='system'&&mq.matches);}
function applyTheme(){
  document.documentElement.dataset.theme=isDark()?'dark':'light';
  $$('[data-theme-toggle]').forEach(b=>{const dark=isDark();const ico=b.querySelector('.ic')?.parentElement;if(ico)ico.innerHTML=ic(dark?'sun':'moon',20);const t=b.querySelector('.tt');if(t)t.textContent=dark?'Modo claro':'Modo oscuro';b.setAttribute('aria-label',dark?'Cambiar a modo claro':'Cambiar a modo oscuro');});
  const r=$(`input[name=theme][value=${state.settings.theme}]`);if(r)r.checked=true;
}
mq.addEventListener('change',applyTheme);

/* ---------- Navegación ---------- */
const PAGE_TITLES={home:'Inicio',proc:'Analizando…',result:'Apunte',library:'Mis apuntes',favs:'Favoritos',settings:'Configuración'};
function go(v,opts={}){
  if(!opts.force&&state.view==='result'&&v!=='result'&&state.current&&!state.current.saved){
    confirmDlg({title:'¿Salir sin guardar?',text:'Este apunte todavía no está guardado. Si sales ahora, se descartará.',ok:'Salir sin guardar',cancel:'Seguir aquí',danger:true}).then(ok=>{if(ok)go(v,{force:true});});
    return;
  }
  if(state.view==='proc'&&v!=='proc'&&v!=='result')state.token++;
  if(state.view==='result'&&v!=='result'&&state.speaking){speechSynthesis.cancel();state.speaking=false;}
  if(v==='library')state.libMode='all';
  if(v==='favs')state.libMode='favs';
  state.view=v;
  const sec=(v==='favs')?'library':v;
  $$('.view').forEach(s=>s.hidden=s.dataset.view!==sec);
  const key=v==='proc'?'home':(v==='result'?(state.from||'home'):v);
  $$('[data-nav]').forEach(b=>b.dataset.nav===key?b.setAttribute('aria-current','page'):b.removeAttribute('aria-current'));
  if(v==='library'||v==='favs')renderLibrary();
  if(v==='home')renderHome();
  document.title=`${PAGE_TITLES[v]} · APUNTIA`;
  window.scrollTo(0,0);
  const h=$('.view:not([hidden]) [data-focus]');if(h)h.focus({preventScroll:true});
}
function updateBadges(){
  $$('[data-count=all]').forEach(e=>e.textContent=state.notes.length);
  $$('[data-count=favs]').forEach(e=>e.textContent=state.notes.filter(n=>n.fav).length);
}

/* ---------- Tarjetas y biblioteca ---------- */
function cardHTML(n,i=0){
  const S=subj(n.subject);
  return `<article class="ncard" data-id="${esc(n.id)}" style="--i:${i}">
    <div class="thumb" data-act="open">
      <img src="${imgOf(n)}" alt="Miniatura del pizarrón: ${esc(n.title)}" loading="lazy">
      <button class="favbtn" data-act="fav" aria-pressed="${!!n.fav}" aria-label="${n.fav?'Quitar de favoritos':'Marcar como favorito'}: ${esc(n.title)}">${ic('star',20)}</button>
      <span class="chip subj" style="--sc:${S.c}">${S.e} ${esc(n.subject)}</span>
    </div>
    <div class="nbody">
      <h3>${esc(n.title)}</h3>
      <p class="meta"><span>📅 ${fmtDate(n.date)}</span><span>🔎 ${n.detections.length} elementos detectados</span></p>
      ${n.tags.length?`<div class="tags">${n.tags.map(t=>`<span class="chip">#${esc(t)}</span>`).join('')}</div>`:''}
    </div>
    <div class="nfoot">
      <button class="btn primary sm" data-act="open">Abrir</button>
      <button class="icon-btn sm" data-act="del" aria-label="Eliminar apunte: ${esc(n.title)}">${ic('trash',18)}</button>
    </div>
  </article>`;
}
function emptyArt(){
  return `<svg class="art" viewBox="0 0 220 150" fill="none" aria-hidden="true"><rect x="14" y="10" width="192" height="110" rx="12" fill="#0f332d" stroke="#8a6a43" stroke-width="7"/><path d="M40 44h70M40 62h100M40 80h54" stroke="#f4f1e6" stroke-width="3" stroke-linecap="round" stroke-dasharray="2 7" opacity=".6"/><rect x="132" y="70" width="50" height="34" rx="8" fill="#ffd666"/><circle cx="157" cy="87" r="9" fill="#2b2000"/><circle cx="157" cy="87" r="4" fill="#ffd666"/><path d="M168 26l3 7 7 3-7 3-3 7-3-7-7-3 7-3z" fill="#4ee8b0"/><rect x="40" y="124" width="140" height="10" rx="5" fill="#7b5a37"/></svg>`;
}
function emptyHTML(kind){
  if(kind==='none')return `<div class="empty">${emptyArt()}<h3>Sin apuntes todavía</h3><p>Toma una foto de tu primer pizarrón y deja que APUNTIA haga el resto.</p><div class="row"><button class="btn primary" data-go-photo>${ic('camera',18)}Tomar foto</button><button class="btn" data-go-load>${ic('image',18)}Cargar imagen</button></div></div>`;
  if(kind==='favs')return `<div class="empty">${emptyArt()}<h3>Aún no tienes favoritos</h3><p>Toca la estrella ⭐ de un apunte para tenerlo siempre a mano.</p><div class="row"><button class="btn primary" data-go-library>Ver mis apuntes</button></div></div>`;
  return `<div class="empty"><h3>Sin resultados</h3><p>No encontramos apuntes que coincidan con tu búsqueda o filtro.</p><div class="row"><button class="btn" data-clear-filters>Limpiar filtros</button></div></div>`;
}
function renderHome(){
  const el=$('#homeRecent');
  if(!state.notes.length){el.innerHTML=`<div class="sec-head"><div><h2>Tus apuntes</h2></div></div>${emptyHTML('none')}`;return;}
  const recent=[...state.notes].sort((a,b)=>b.date.localeCompare(a.date)).slice(0,3);
  el.innerHTML=`<div class="sec-head"><div><h2>Continúa estudiando</h2><p>Tus apuntes más recientes</p></div><button class="btn sm" data-go-library>Ver todos</button></div><div class="grid">${recent.map((n,i)=>cardHTML(n,i)).join('')}</div>`;
}
function renderLibrary(){
  const fav=state.libMode==='favs';
  $('#libTitle').textContent=fav?'Favoritos':'Mis apuntes';
  const base=state.notes.filter(n=>!fav||n.fav);
  $('#libSub').textContent=fav?`${base.length} ${base.length===1?'apunte favorito':'apuntes favoritos'}`:`${base.length} ${base.length===1?'apunte guardado':'apuntes guardados'} · tu biblioteca visual`;
  // filtros por materia
  const subs=[...new Set(base.map(n=>n.subject))];
  if(state.lib.subject!=='all'&&!subs.includes(state.lib.subject))state.lib.subject='all';
  $('#filters').innerHTML=[`<button class="fchip" data-subj="all" aria-pressed="${state.lib.subject==='all'}">Todas (${base.length})</button>`,
    ...subs.map(s=>`<button class="fchip" data-subj="${esc(s)}" aria-pressed="${state.lib.subject===s}">${subj(s).e} ${esc(s)} (${base.filter(n=>n.subject===s).length})</button>`)].join('');
  $('#filters').hidden=!base.length;
  // búsqueda y orden
  const q=state.lib.q.trim().toLowerCase();
  let list=base.filter(n=>(state.lib.subject==='all'||n.subject===state.lib.subject)&&(!q||[n.title,n.subject,n.summary,...n.tags,...n.concepts].join(' ').toLowerCase().includes(q)));
  const s=state.lib.sort;
  list=list.map((n,i)=>[n,i]).sort((A,B)=>{const a=A[0],b=B[0];
    if(s==='az')return a.title.localeCompare(b.title,'es')||A[1]-B[1];
    if(s==='items')return b.detections.length-a.detections.length||A[1]-B[1];
    return b.date.localeCompare(a.date)||A[1]-B[1];}).map(x=>x[0]);
  const body=$('#libBody');
  if(!list.length){body.innerHTML=emptyHTML(!state.notes.length?'none':(fav&&!base.length?'favs':'filter'));return;}
  if(state.lib.group){
    const groups={};list.forEach(n=>(groups[n.subject]=groups[n.subject]||[]).push(n));
    body.innerHTML=Object.entries(groups).map(([k,arr])=>`<h2 class="group-title">${subj(k).e} ${esc(k)} <small>${arr.length} ${arr.length===1?'apunte':'apuntes'}</small></h2><div class="grid">${arr.map((n,i)=>cardHTML(n,i)).join('')}</div>`).join('');
  }else body.innerHTML=`<div class="grid">${list.map((n,i)=>cardHTML(n,i)).join('')}</div>`;
}
function openNote(id,from){
  const n=state.notes.find(x=>x.id===id);if(!n)return;
  state.from=from||(state.view==='home'?'home':state.libMode);
  showResult({note:n,saved:true});
}
function toggleFav(n){n.fav=!n.fav;persist();updateBadges();toast(n.fav?'Añadido a favoritos ⭐':'Quitado de favoritos');}
async function deleteNote(id){
  const i=state.notes.findIndex(x=>x.id===id);if(i<0)return false;
  const n=state.notes[i];
  const ok=await confirmDlg({title:'¿Eliminar este apunte?',text:`«${n.title}» se eliminará de Mis apuntes.`,ok:'Eliminar',cancel:'Cancelar',danger:true});
  if(!ok)return false;
  state.notes.splice(i,1);persist();updateBadges();
  state.lastDeleted={n,i};
  toast('Apunte eliminado',{label:'Deshacer',fn:()=>{const d=state.lastDeleted;if(!d)return;state.notes.splice(d.i,0,d.n);persist();updateBadges();state.lastDeleted=null;if(state.view==='library'||state.view==='favs')renderLibrary();if(state.view==='home')renderHome();toast('Apunte restaurado');}});
  return true;
}
document.addEventListener('click',async e=>{
  const card=e.target.closest('.ncard');
  if(card){
    const id=card.dataset.id,act=e.target.closest('[data-act]')?.dataset.act;
    if(act==='open')openNote(id);
    else if(act==='fav'){const n=state.notes.find(x=>x.id===id);toggleFav(n);if(state.view==='home')renderHome();else renderLibrary();$(`.ncard[data-id="${id}"] [data-act=fav]`)?.focus();}
    else if(act==='del'){await deleteNote(id);if(state.view==='home')renderHome();else renderLibrary();}
    return;
  }
  if(e.target.closest('[data-go-photo]'))startPhoto();
  else if(e.target.closest('[data-go-load]'))$('#fileIn').click();
  else if(e.target.closest('[data-go-library]'))go('library');
  else if(e.target.closest('[data-clear-filters]')){state.lib.q='';state.lib.subject='all';$('#q').value='';renderLibrary();}
  const nav=e.target.closest('[data-nav]');if(nav)go(nav.dataset.nav);
  if(e.target.closest('[data-theme-toggle]')){state.settings.theme=isDark()?'light':'dark';saveSettings();applyTheme();}
});
$('#q').addEventListener('input',e=>{state.lib.q=e.target.value;renderLibrary();});
$('#sort').addEventListener('change',e=>{state.lib.sort=e.target.value;renderLibrary();});
$('#groupBtn').addEventListener('click',e=>{state.lib.group=!state.lib.group;e.currentTarget.setAttribute('aria-pressed',state.lib.group);renderLibrary();});
$('#filters').addEventListener('click',e=>{const b=e.target.closest('[data-subj]');if(!b)return;state.lib.subject=b.dataset.subj;renderLibrary();});
$('#libNew').addEventListener('click',()=>go('home'));

/* ---------- Cargar imagen / cámara ---------- */
function showHomeError(msg){$('#homeErrMsg').textContent=msg;$('#homeErr').hidden=false;if(state.view!=='home')go('home',{force:true});window.scrollTo(0,0);}
$('#homeErrX').addEventListener('click',()=>$('#homeErr').hidden=true);
async function shrink(file){
  const url=URL.createObjectURL(file);
  try{
    const img=await new Promise((res,rej)=>{const i=new Image();i.onload=()=>res(i);i.onerror=rej;i.src=url;});
    const s=Math.min(1,1100/Math.max(img.naturalWidth,img.naturalHeight));
    const c=document.createElement('canvas');c.width=Math.round(img.naturalWidth*s);c.height=Math.round(img.naturalHeight*s);
    c.getContext('2d').drawImage(img,0,0,c.width,c.height);
    return c.toDataURL('image/jpeg',.74);
  }finally{URL.revokeObjectURL(url);}
}
async function handleFile(file){
  if(!file)return;
  $('#homeErr').hidden=true;
  if(!file.type.startsWith('image/'))return showHomeError('Ese archivo no es una imagen. Usa una fotografía en formato JPG, PNG o WEBP.');
  if(file.size>15*1024*1024)return showHomeError('La imagen pesa más de 15 MB. Prueba con una fotografía más ligera.');
  try{const img=await shrink(file);startProcessing({img,name:file.name});}
  catch{showHomeError('No pudimos abrir la imagen. Puede estar dañada o estar en un formato no compatible (como HEIC). Prueba con JPG o PNG.');}
}
$('#btnLoad').addEventListener('click',()=>$('#fileIn').click());
$('#fileIn').addEventListener('change',e=>{handleFile(e.target.files[0]);e.target.value='';});
$('#camIn').addEventListener('change',e=>{handleFile(e.target.files[0]);e.target.value='';});
$('#btnDemo').addEventListener('click',()=>startProcessing({board:'physics',kind:'physics',name:'ejemplo'}));
const drop=$('#drop');
['dragenter','dragover'].forEach(ev=>drop.addEventListener(ev,e=>{e.preventDefault();drop.classList.add('dropping');}));
['dragleave','drop'].forEach(ev=>drop.addEventListener(ev,e=>{e.preventDefault();if(ev==='dragleave'&&drop.contains(e.relatedTarget))return;drop.classList.remove('dropping');}));
drop.addEventListener('drop',e=>handleFile(e.dataTransfer.files[0]));

let camStream=null,camMode='sim';
function startPhoto(){
  const mobile=/Android|iPhone|iPad|iPod/i.test(navigator.userAgent)&&matchMedia('(pointer:coarse)').matches;
  if(mobile){$('#camIn').click();return;} // en móviles se abre la cámara nativa
  openCamera();
}
async function openCamera(){
  const d=$('#camDlg'),v=$('#camVideo'),f=$('#camFake'),m=$('#camMsg');
  v.hidden=true;f.hidden=true;m.textContent='Solicitando acceso a la cámara…';d.showModal();
  try{
    if(!navigator.mediaDevices?.getUserMedia)throw new Error('sin cámara');
    camStream=await navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:'environment'}},audio:false});
    v.srcObject=camStream;await v.play();v.hidden=false;camMode='live';m.textContent='Alinea el pizarrón dentro del marco';
  }catch{
    camMode='sim';f.src=boardURL('physics');f.hidden=false;m.textContent='Cámara no disponible: usando una vista simulada con un pizarrón de ejemplo';
  }
}
function closeCamera(){camStream?.getTracks().forEach(t=>t.stop());camStream=null;const v=$('#camVideo');v.srcObject=null;if($('#camDlg').open)$('#camDlg').close();}
$('#btnPhoto').addEventListener('click',startPhoto);
$('#camClose').addEventListener('click',closeCamera);
$('#camDlg').addEventListener('close',()=>{camStream?.getTracks().forEach(t=>t.stop());camStream=null;});
$('#camGallery').addEventListener('click',()=>{closeCamera();$('#fileIn').click();});
$('#camShot').addEventListener('click',async()=>{
  const fl=$('#camFlash');fl.classList.remove('go');void fl.offsetWidth;fl.classList.add('go');
  await sleep(220);
  if(camMode==='live'){
    const v=$('#camVideo'),c=document.createElement('canvas'),s=Math.min(1,1100/Math.max(v.videoWidth,v.videoHeight));
    c.width=Math.round(v.videoWidth*s);c.height=Math.round(v.videoHeight*s);c.getContext('2d').drawImage(v,0,0,c.width,c.height);
    const img=c.toDataURL('image/jpeg',.74);closeCamera();startProcessing({img,name:'foto-camara'});
  }else{closeCamera();startProcessing({board:'physics',kind:'physics',name:'ejemplo'});}
});

/* ---------- Procesamiento simulado de IA ---------- */
const STEPS=[
 {e:'🔍',t:'Analizando imagen',s:'Mejorando contraste y corrigiendo perspectiva'},
 {e:'✏️',t:'Reconociendo escritura',s:'Transcribiendo texto manuscrito'},
 {e:'📐',t:'Detectando fórmulas y diagramas',s:'Localizando símbolos, ecuaciones y dibujos'},
 {e:'🧠',t:'Interpretando contenido',s:'Relacionando conceptos y definiciones'},
 {e:'📝',t:'Organizando apuntes',s:'Estructurando título, resumen y fórmulas'}
];
function pickKind(name=''){
  if(/calc|deriv|integr|mate|limit/i.test(name))return 'calculus';
  if(/prog|dato|code|codig|algor|estruct|sistem/i.test(name))return 'programming';
  if(/fis|newton|fuerza|phys/i.test(name))return 'physics';
  let i=0;try{i=+localStorage.getItem('apuntia.rot')||0;localStorage.setItem('apuntia.rot',i+1);}catch{}
  return ['physics','calculus','programming'][i%3];
}
function setStep(i,s){const li=$$('#steps .step')[i];if(li)li.dataset.s=s;}
function setP(p){p=Math.round(p);$('#pfill').style.width=p+'%';$('#pPct').textContent=p+'%';$('#pbar').setAttribute('aria-valuenow',p);}
async function startProcessing(job){
  const token=++state.token;state.job=job;
  job.kind=job.kind||pickKind(job.name);
  $('#procImg').src=job.board?boardURL(job.board):job.img;
  $('#procImgWrap').classList.remove('err');
  $('#procTitle').textContent='Analizando tu pizarrón...';
  $('#procSub').textContent='Esto tomará unos segundos. No cierres esta pantalla.';
  $('#steps').innerHTML=STEPS.map(s=>`<li class="step" data-s="pending"><span class="s-ic" aria-hidden="true">${s.e}</span><div><b>${s.t}</b><small>${s.s}</small></div><span class="s-st" aria-hidden="true"></span></li>`).join('');
  $('#found').innerHTML='<span>Elementos detectados:</span>';
  $('#procErr').hidden=true;$('#procActions').hidden=false;setP(0);
  go('proc',{force:true});
  const k=state.settings.fast?.3:1, durs=[1100,1600,1600,1300,1100].map(d=>d*k), per=100/STEPS.length;
  const reveal=[[],['title','text'],['formula','diagram'],['list'],[]];
  for(let i=0;i<STEPS.length;i++){
    setStep(i,'active');
    if(i===1&&state.settings.simError){
      if(!await tween(i*per,i*per+per*.55,durs[i]*.55,token,setP))return;
      state.settings.simError=false;saveSettings();syncSettingsUI();
      setStep(i,'error');$('#procImgWrap').classList.add('err');
      $('#procTitle').textContent='Algo salió mal';$('#procSub').textContent='El análisis se detuvo mientras reconocíamos la escritura.';
      $('#procActions').hidden=true;$('#procErr').hidden=false;$('#procRetry').focus();return;
    }
    if(!await tween(i*per,(i+1)*per,durs[i],token,setP))return;
    setStep(i,'done');
    reveal[i].forEach(t=>{$('#found').insertAdjacentHTML('beforeend',`<span class="chip" style="border-color:${DTYPE[t].c}">${DTYPE[t].l}</span>`);});
  }
  await sleep(300*k+100);if(token!==state.token)return;
  let note,saved=false;
  const old=job.reprocess;
  if(old){
    note=newNote(old.kind||job.kind,{id:old.id,date:old.date,tags:old.tags,fav:old.fav,img:old.img,board:old.board,conf:Math.min(99,(old.conf||95)+1)});
    saved=state.notes.some(n=>n.id===old.id);
    if(saved){const i=state.notes.findIndex(n=>n.id===old.id);state.notes[i]=note;persist();}
  }else note=newNote(job.kind,job.board?{board:job.board}:{img:job.img});
  state.from=state.from||'home';
  showResult({note,saved});
  toast(old?'Imagen procesada de nuevo ✓':'¡Listo! Revisa tu apunte y guárdalo.');
}
$('#procCancel').addEventListener('click',()=>{go('home',{force:true});toast('Análisis cancelado');});
$('#procBack').addEventListener('click',()=>go('home',{force:true}));
$('#procRetry').addEventListener('click',()=>startProcessing(state.job));
$('#procOther').addEventListener('click',()=>{go('home',{force:true});$('#fileIn').click();});

/* ---------- Resultado ---------- */
function showResult(cur){
  state.current=cur;const n=cur.note;
  if(!cur.saved)state.from='home';
  $('#boardImg').src=imgOf(n);
  $('#boardImg').alt=`Fotografía original del pizarrón: ${n.title}`;
  $('#resSub').textContent=cur.saved?`Guardado · ${fmtDate(n.date)}`:'Revisa el apunte generado y guárdalo en tu biblioteca';
  $('#resConf').textContent=`🎯 Confianza ${n.conf}% · contenido simulado`;
  buildBoxes(n);renderNote();go('result',{force:true});
  const b=$('#board');b.classList.add('scanning');setTimeout(()=>b.classList.remove('scanning'),1700);
}
function buildBoxes(n){
  $('#board').classList.remove('nodet');$('#toggleDet').setAttribute('aria-pressed','true');
  $('#boxes').innerHTML=n.detections.map((d,i)=>{const t=DTYPE[d.t];
    return `<div class="box" data-type="${d.t}" style="left:${d.x}%;top:${d.y}%;width:${d.w}%;height:${d.h}%;--c:${t.c};--d:${(.5+i*.16).toFixed(2)}s"><b>${t.l} ${d.conf}%</b></div>`;}).join('');
  const counts={};n.detections.forEach(d=>counts[d.t]=(counts[d.t]||0)+1);
  $('#legend').innerHTML=Object.entries(counts).map(([t,c])=>`<button class="lg" data-type="${t}" aria-pressed="true" style="--c:${DTYPE[t].c}"><i></i>${DTYPE[t].l} · ${c}</button>`).join('');
}
$('#toggleDet').addEventListener('click',e=>{const on=e.currentTarget.getAttribute('aria-pressed')!=='true';e.currentTarget.setAttribute('aria-pressed',on);$('#board').classList.toggle('nodet',!on);});
$('#legend').addEventListener('click',e=>{const b=e.target.closest('.lg');if(!b)return;const on=b.getAttribute('aria-pressed')!=='true';b.setAttribute('aria-pressed',on);$$(`.box[data-type=${b.dataset.type}]`).forEach(x=>x.classList.toggle('off',!on));});
function setHL(type){
  $$('#boxes .box').forEach(b=>{b.classList.toggle('dim',!!type&&b.dataset.type!==type);b.classList.toggle('hl',!!type&&b.dataset.type===type);});
  $$('#noteRoot .sec').forEach(s=>s.classList.toggle('hl',!!type&&s.dataset.ref===type));
}
$('#boxes').addEventListener('mouseover',e=>{const b=e.target.closest('.box');if(b)setHL(b.dataset.type);});
$('#boxes').addEventListener('mouseleave',()=>setHL(null));
$('#boxes').addEventListener('click',e=>{const b=e.target.closest('.box');if(!b)return;const s=$(`#noteRoot .sec[data-ref=${b.dataset.type}]`);if(s){s.scrollIntoView({behavior:'smooth',block:'center'});s.classList.remove('flash');void s.offsetWidth;s.classList.add('flash');}});
$('#noteRoot').addEventListener('mouseover',e=>{const s=e.target.closest('.sec');if(s)setHL(s.dataset.ref);});
$('#noteRoot').addEventListener('mouseleave',()=>setHL(null));
$('#resBack').addEventListener('click',()=>go(state.current?.saved?(state.from==='favs'?'favs':'library'):'home'));

function sec(ref,icon,head,inner,num){
  return `<section class="sec" data-ref="${ref}"><h2>${num?`<span class="num">${num}</span>`:ic(icon,16)}${head}</h2>${inner}</section>`;
}
function renderNote(){
  const {note:n,saved}=state.current,S=subj(n.subject);
  const varsHTML=`<ul class="vars">${n.list.items.map(it=>`<li><span class="k">${esc(it.k)}</span><span class="arr">→</span><span class="v">${esc(it.v)}</span>${it.u?`<span class="u">${esc(it.u)}</span>`:''}</li>`).join('')}</ul>`;
  const formulaHTML=`<div class="formula"><code>${esc(n.formula)}</code><p>${esc(n.formulaNote)}</p></div>`;
  const conceptsHTML=`<div class="concepts">${n.concepts.map(c=>`<span class="chip">${esc(c)}</span>`).join('')}</div>`;
  const diagramHTML=`<div class="diagram"><span class="di" aria-hidden="true">📐</span><p>${esc(n.diagram)}</p></div>`;
  let body='';
  if(n.showTldr)body+=`<aside class="ai-box" id="tldrBox"><b>${ic('sparkles',16)}Resumen rápido</b><p id="tldrP">${esc(n.tldr)}</p></aside>`;
  if(!n.organized){
    body+=sec('text','text','Resumen',`<p class="body">${esc(n.summary)}</p>`)
      +sec('formula','formula','Fórmula',formulaHTML)
      +sec('list','list',esc(n.list.title),varsHTML)
      +sec('text','tag','Conceptos principales',conceptsHTML)
      +sec('diagram','scan','Diagrama detectado',diagramHTML);
  }else{
    body+=`<div class="banner">${ic('sparkles',18)}<span>Apunte reorganizado como <b>esquema de estudio</b>.</span></div>`
      +sec('text','','Idea clave',`<p class="body">${esc(n.summary)}</p>`,1)
      +sec('formula','','Fórmula',formulaHTML,2)
      +sec('list','',esc(n.list.title),varsHTML,3)
      +sec('diagram','','Diagrama',diagramHTML,4)
      +sec('text','','Ejemplo resuelto',`<div class="example"><p><b>${esc(n.example.q)}</b></p><ol>${n.example.steps.map(s=>`<li>${esc(s)}</li>`).join('')}</ol></div>`,5)
      +sec('text','','Para recordar',`<ul class="remember">${n.remember.map(r=>`<li>${esc(r)}</li>`).join('')}</ul>`,6)
      +sec('text','','Conceptos principales',conceptsHTML,7);
  }
  if(n.showExplain)body+=`<aside class="ai-box" id="explBox"><b>${ic('bulb',16)}Explícame este tema</b><p id="explP">${esc(n.explain)}</p></aside>`;
  const subjOpts=Object.keys(SUBJECTS).map(k=>`<option value="${k}" ${k===n.subject?'selected':''}>${SUBJECTS[k].e} ${k}</option>`).join('');
  $('#noteRoot').innerHTML=`<article class="note-card" id="noteCard">
    <div class="print-head">APUNTIA — Apuntes Inteligentes</div>
    <div class="note-meta">
      <span class="chip subj subj-sel" id="subjChip" style="--sc:${S.c}"><label><span class="sr-only">Materia</span><select id="subjSel">${subjOpts}</select></label></span>
      <span class="note-sub">📅 ${fmtDate(n.date)} · 🔎 ${n.detections.length} elementos detectados</span>
    </div>
    <h2 class="note-title" id="noteTitle" contenteditable="true" spellcheck="false" role="textbox" aria-label="Título del apunte (editable)">${esc(n.title)}</h2>
    <div class="taglist no-print" id="taglist">${n.tags.map(t=>`<span class="chip">#${esc(t)}<button data-act="rmtag" data-tag="${esc(t)}" aria-label="Quitar etiqueta ${esc(t)}">×</button></span>`).join('')}<input class="tag-in" id="tagIn" placeholder="+ etiqueta" maxlength="24" aria-label="Añadir etiqueta"></div>
    <div class="toolbar" role="toolbar" aria-label="Acciones del apunte">
      <button class="tbtn" data-act="fav" aria-pressed="${!!n.fav}">${ic('star',17)}Favorito</button>
      <button class="tbtn" data-act="copy">${ic('copy',17)}Copiar</button>
      <button class="tbtn" data-act="pdf">${ic('pdf',17)}PDF</button>
      <button class="tbtn" data-act="speak">${ic(state.speaking?'stop':'volume',17)}${state.speaking?'Detener':'Leer'}</button>
      <button class="tbtn" data-act="tldr">${ic('sparkles',17)}Resumir</button>
      <button class="tbtn" data-act="explain">${ic('bulb',17)}Explicar</button>
      <button class="tbtn" data-act="reprocess">${ic('refresh',17)}Reprocesar</button>
      ${saved?`<button class="tbtn danger" data-act="delete">${ic('trash',17)}Eliminar</button>`:''}
    </div>
    ${body}
    <div class="savebar">
      <button class="btn" data-act="improve">${ic('sparkles',18)}✨ Mejorar / reorganizar apunte</button>
      <button class="btn primary" data-act="save">${saved?ic('check',18)+'Guardado · ver Mis apuntes':ic('check',18)+'Guardar apunte'}</button>
    </div>
  </article>`;
}
const touch=()=>{if(state.current?.saved){persist();updateBadges();}};
function noteText(n){
  return [n.title,`${n.subject} · ${fmtDate(n.date)}`,'','Resumen:',n.summary,'','Fórmula: '+n.formula,n.formulaNote,'',n.list.title+':',...n.list.items.map(i=>`- ${i.k} → ${i.v}${i.u?' ('+i.u+')':''}`),'','Conceptos principales: '+n.concepts.join(', '),'','Diagrama: '+n.diagram].join('\n');
}
async function copyText(t){try{await navigator.clipboard.writeText(t);}catch{const a=document.createElement('textarea');a.value=t;a.style.position='fixed';a.style.opacity='0';document.body.appendChild(a);a.select();document.execCommand('copy');a.remove();}}
function speakNote(n){
  if(!('speechSynthesis' in window))return toast('Tu navegador no admite la lectura en voz alta.');
  if(state.speaking){speechSynthesis.cancel();state.speaking=false;renderNote();return;}
  const u=new SpeechSynthesisUtterance(`${n.title}. ${n.summary}. Fórmula: ${n.formula}. ${n.formulaNote}. Conceptos principales: ${n.concepts.join(', ')}.`);
  u.lang='es-MX';u.rate=state.settings.rate;
  const v=speechSynthesis.getVoices().find(v=>/^es/i.test(v.lang));if(v)u.voice=v;
  u.onend=u.onerror=()=>{state.speaking=false;if(state.view==='result')renderNote();};
  speechSynthesis.cancel();speechSynthesis.speak(u);state.speaking=true;renderNote();
}
async function aiThink(label,ms=1300){
  const card=$('#noteCard');card.classList.add('thinking');
  card.insertAdjacentHTML('afterbegin',`<div class="think-pill" role="status">${ic('sparkles',18)}${label}</div>`);
  await sleep(state.settings.fast?ms*.4:ms);
}
$('#noteRoot').addEventListener('click',async e=>{
  const b=e.target.closest('[data-act]');if(!b||!state.current)return;
  const cur=state.current,n=cur.note;
  switch(b.dataset.act){
    case 'fav':{n.fav=!n.fav;touch();updateBadges();renderNote();$('#noteRoot [data-act=fav]').focus();toast(n.fav?'Añadido a favoritos ⭐':'Quitado de favoritos');break;}
    case 'copy':await copyText(noteText(n));toast('Apunte copiado al portapapeles 📋');break;
    case 'pdf':toast('Elige «Guardar como PDF» en el cuadro de impresión');setTimeout(()=>print(),500);break;
    case 'speak':speakNote(n);break;
    case 'tldr':{
      if(n.showTldr){n.showTldr=false;touch();renderNote();break;}
      await aiThink('Resumiendo…',900);n.showTldr=true;touch();renderNote();
      const p=$('#tldrP');typeInto(p,n.tldr);$('#tldrBox').scrollIntoView({behavior:'smooth',block:'center'});break;}
    case 'explain':{
      if(n.showExplain){n.showExplain=false;touch();renderNote();break;}
      await aiThink('Preparando una explicación…',1200);n.showExplain=true;touch();renderNote();
      typeInto($('#explP'),n.explain,12);$('#explBox').scrollIntoView({behavior:'smooth',block:'center'});break;}
    case 'improve':{
      await aiThink('Reorganizando tus apuntes…',1600);
      n.organized=!n.organized;touch();renderNote();
      toast(n.organized?'Apunte reorganizado como esquema de estudio ✨':'Apunte restaurado al formato estándar');break;}
    case 'reprocess':{
      const ok=await confirmDlg({title:'¿Volver a procesar la imagen?',text:'La IA analizará de nuevo el pizarrón y reemplazará el contenido generado.',ok:'Procesar de nuevo',cancel:'Cancelar'});
      if(ok)startProcessing({img:n.img,board:n.board,kind:n.kind,name:'reproceso',reprocess:n});break;}
    case 'save':{
      if(cur.saved){go(state.from==='favs'?'favs':'library',{force:true});break;}
      state.notes.unshift(n);
      if(persist()){cur.saved=true;updateBadges();renderNote();$('#resSub').textContent=`Guardado · ${fmtDate(n.date)}`;toast('Apunte guardado en Mis apuntes ✓',{label:'Ver',fn:()=>go('library',{force:true})});}
      else state.notes.shift();
      break;}
    case 'delete':{
      const ok=await deleteNote(n.id);if(ok){state.current=null;go('library',{force:true});}break;}
    case 'rmtag':{n.tags=n.tags.filter(t=>t!==b.dataset.tag);touch();renderNote();break;}
  }
});
$('#noteRoot').addEventListener('input',e=>{
  if(e.target.id==='noteTitle'&&state.current){state.current.note.title=e.target.textContent.trim()||'Apunte sin título';touch();}
});
$('#noteRoot').addEventListener('keydown',e=>{
  if(e.target.id==='noteTitle'&&e.key==='Enter'){e.preventDefault();e.target.blur();}
  if(e.target.id==='tagIn'&&e.key==='Enter'){
    e.preventDefault();const t=e.target.value.trim().replace(/^#/,'').toLowerCase();if(!t)return;
    const n=state.current.note;if(!n.tags.includes(t)&&n.tags.length<8){n.tags.push(t);touch();renderNote();$('#tagIn').focus();}
  }
});
$('#noteRoot').addEventListener('change',e=>{
  if(e.target.id==='subjSel'&&state.current){
    const n=state.current.note;n.subject=e.target.value;touch();
    $('#subjChip').style.setProperty('--sc',subj(n.subject).c);
    toast(`Materia cambiada a ${n.subject}`);
  }
});

/* ---------- Configuración ---------- */
function syncSettingsUI(){
  const s=state.settings;$('#rate').value=s.rate;$('#rateV').textContent=s.rate.toFixed(1)+'×';
  $('#optFast').checked=s.fast;$('#optErr').checked=s.simError;
  const r=$(`input[name=theme][value=${s.theme}]`);if(r)r.checked=true;
}
$$('input[name=theme]').forEach(r=>r.addEventListener('change',()=>{state.settings.theme=r.value;saveSettings();applyTheme();}));
$('#rate').addEventListener('input',e=>{state.settings.rate=+e.target.value;$('#rateV').textContent=state.settings.rate.toFixed(1)+'×';saveSettings();});
$('#rateTest').addEventListener('click',()=>{if(!('speechSynthesis' in window))return toast('Tu navegador no admite voz.');speechSynthesis.cancel();const u=new SpeechSynthesisUtterance('Hola, soy APUNTIA. Así sonará la lectura de tus apuntes.');u.lang='es-MX';u.rate=state.settings.rate;speechSynthesis.speak(u);});
$('#optFast').addEventListener('change',e=>{state.settings.fast=e.target.checked;saveSettings();});
$('#optErr').addEventListener('change',e=>{state.settings.simError=e.target.checked;saveSettings();});
$('#resetSeed').addEventListener('click',async()=>{
  if(!await confirmDlg({title:'¿Restablecer los ejemplos?',text:'Tu biblioteca se reemplazará por los 3 apuntes de muestra.',ok:'Restablecer'}))return;
  state.notes=seed();persist();updateBadges();toast('Apuntes de ejemplo restaurados');
});
$('#clearAll').addEventListener('click',async()=>{
  if(!await confirmDlg({title:'¿Borrar todos los apuntes?',text:'Se eliminarán todos tus apuntes de este navegador. No se puede deshacer.',ok:'Borrar todo',danger:true}))return;
  state.notes=[];persist();updateBadges();toast('Biblioteca vaciada');
});

/* ---------- Inicio de la app ---------- */
(async function init(){
  hydrate();loadSettings();applyTheme();syncSettingsUI();
  const fonts=Promise.all([document.fonts.load('700 40px Caveat'),document.fonts.load('700 40px "JetBrains Mono"')]).catch(()=>{});
  await Promise.race([fonts,sleep(1800)]);
  state.notes=loadNotes();
  if(localStorage.getItem(KEY)===null)persist();
  updateBadges();renderHome();
  if('speechSynthesis' in window)speechSynthesis.getVoices();
})();
