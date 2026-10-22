import fs from'fs';const j=fs.readFileSync('src/trends-main.jsx','utf8'),c=fs.readFileSync('src/trends-styles.css','utf8');let e=[];
for(const x of ["center([13,54])","scale(560)","clipExtent([[0,0],[600,420]])",'viewBox="0 0 600 420"','preserveAspectRatio="xMidYMid meet"'])if(!j.includes(x))e.push('map '+x);
for(const x of ['min-height:430px','height:430px','min-height:500px','min-height:520px','min-height:330px'])if(!c.includes(x))e.push('css '+x);
for(const x of ['#B4C1D1','2F6B8A','D39100','All map values are percentages'])if(!(j+c).includes(x))e.push('rule '+x);
if(e.length){console.error(e);process.exit(1)}console.log('V2.34.1 MAP VISIBILITY CONTRACT OK');
