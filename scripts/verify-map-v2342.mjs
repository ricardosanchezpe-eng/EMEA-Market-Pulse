import fs from'fs';const j=fs.readFileSync('src/trends-main.jsx','utf8'),c=fs.readFileSync('src/trends-styles.css','utf8');let e=[];
for(const x of ["center([11,54])","scale(430)","translate([300,210])","clipExtent([[0,0],[600,420]])",'viewBox="0 0 600 420"'])if(!j.includes(x))e.push(x);
for(const x of ['min-height:400px','height:400px','min-height:440px','min-height:320px'])if(!c.includes(x))e.push(x);
for(const x of ['All map values are percentages','#B4C1D1','2F6B8A','D39100'])if(!(j+c).includes(x))e.push(x);
if(e.length){console.error(e);process.exit(1)}console.log('V2.34.2 BALANCED MAP CONTRACT OK');
