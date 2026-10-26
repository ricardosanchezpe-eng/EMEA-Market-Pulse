import fs from 'node:fs';
const s=fs.readFileSync('src/trends-main.jsx','utf8');
for(const x of ['Activity indicators included in the {pc(vblock.avgYoY)} average','INCLUDED','Supporting evidence · not included in the average','LEADING SURVEY','COST PRESSURE','filter(i=>i.includedInVerticalAverage)','filter(i=>!i.includedInVerticalAverage)','evidenceWindow(vblock.indicators)']) if(!s.includes(x)) throw new Error('missing '+x);
console.log('V2.36.2 TRANSPARENCY UI CONTRACT OK');
