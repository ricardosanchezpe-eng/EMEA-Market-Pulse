import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { ComposableMap, Geographies, Geography, Marker } from 'react-simple-maps';
import world from 'world-atlas/countries-110m.json';
import { feature } from 'topojson-client';
import './styles.css';

const GEO = feature(world, world.objects.countries);
const FIELD = {
  Overall: 'overall', Transportation: 'transport', 'Site Development': 'site',
  'Waste & Water': 'water', 'Oil & Gas': 'oil', Mining: 'mining',
  Renewables: 'renewables', Agriculture: 'agriculture'
};
const VERTICALS = Object.keys(FIELD);
const SOLMAX = { navy:'#063b52', teal:'#007f86', green:'#55b96d', lime:'#a7cb58', sand:'#eee8d8', orange:'#eea33a', red:'#c94e49' };
const colorFor = v => v == null ? '#dce4e7' : v >= 70 ? '#178353' : v >= 55 ? '#78bd6d' : v >= 40 ? '#dbc98c' : v >= 20 ? '#eea33a' : '#c94e49';
const band = v => v == null ? { label:'Insufficient evidence', arrow:'—', tone:'none' } : v >= 70 ? { label:'Strong positive', arrow:'↗', tone:'strong' } : v >= 55 ? { label:'Positive', arrow:'↗', tone:'positive' } : v >= 40 ? { label:'Mixed / stable', arrow:'→', tone:'mixed' } : v >= 20 ? { label:'Weakening', arrow:'↘', tone:'weak' } : { label:'Strong weakening', arrow:'↓', tone:'negative' };
const fmt = value => value == null ? '—' : Number(value).toLocaleString(undefined,{maximumFractionDigits:2});
const prettyDate = value => {
  if (!value) return '—';
  if (/^\d{4}-\d{2}$/.test(value)) {
    const [y,m]=value.split('-'); return new Intl.DateTimeFormat('en',{month:'short',year:'2-digit'}).format(new Date(Number(y),Number(m)-1,1));
  }
  if (/^\d{4}-Q[1-4]$/.test(value)) return value.replace('-', ' ');
  return String(value);
};
const fresh = value => {
  if(!value) return {label:'NO DATA', cls:'missing'};
  const year=Number(String(value).slice(0,4)); const age=2026-year;
  if(age<=0) return {label:'CURRENT',cls:'current'};
  if(age===1) return {label:'RECENT',cls:'recent'};
  if(age<=3) return {label:'STRUCTURAL',cls:'structural'};
  return {label:'STALE',cls:'stale'};
};
const movement = z => {
  if(z?.growthPct==null) return {text:'—',dir:0};
  const n=Number(z.growthPct); const comp=(z.comparison||'vs previous').toUpperCase();
  return {text:`${n>0?'↗ ':n<0?'↘ ':'→ '}${n>0?'+':''}${n.toFixed(1)}% ${comp}`,dir:n>0?1:n<0?-1:0};
};
const roleLabel = role => ({Now:'ACTIVITY',Forward:'FORWARD',Need:'STRUCTURAL NEED',Context:'CONTEXT'}[role]||String(role||'EVIDENCE').toUpperCase());
const flag = geo => `https://flagcdn.com/w40/${String(geo||'').toLowerCase()}.png`;
const newest = rows => rows.map(r=>r.z?.date).filter(Boolean).sort().at(-1)||'—';

function weightedRegional(list, field){
  const usable=list.filter(c=>c[field]!=null && (c.coverage?.[field]||0)>0);
  if(!usable.length) return {score:null,coverage:0,positive:0,weakening:0,unavailable:100,count:0,latest:'—'};
  // Transparent proxy: fixed GDP order with coverage adjustment. Higher-ranked economies receive greater weight.
  const n=list.length; const parts=usable.map(c=>({c,w:Math.max(1,n-(c.gdpRank||n)+1)*(c.coverage?.[field]||0)/100}));
  const total=parts.reduce((s,x)=>s+x.w,0); const score=parts.reduce((s,x)=>s+x.c[field]*x.w,0)/total;
  const positive=parts.filter(x=>x.c[field]>=55).reduce((s,x)=>s+x.w,0)/total*100;
  const weakening=parts.filter(x=>x.c[field]<40).reduce((s,x)=>s+x.w,0)/total*100;
  const possible=list.reduce((s,c)=>s+Math.max(1,n-(c.gdpRank||n)+1),0);
  const coverage=Math.round(total/possible*100);
  const dates=usable.flatMap(c=>Object.values(c.indicators||{}).map(z=>z?.date).filter(Boolean));
  return {score:Math.round(score),coverage,positive:Math.round(positive),weakening:Math.round(weakening),unavailable:Math.max(0,100-Math.round(positive)-Math.round(weakening)),count:usable.length,latest:dates.sort().at(-1)||'—'};
}

function App(){
  const [data,setData]=useState(null),[method,setMethod]=useState({}),[universe,setUniverse]=useState('europe'),[vertical,setVertical]=useState('Overall'),[selected,setSelected]=useState(null),[detail,setDetail]=useState(null),[allCountries,setAllCountries]=useState(false),[methodOpen,setMethodOpen]=useState(false),[sourcesOpen,setSourcesOpen]=useState(false);
  useEffect(()=>{Promise.all([fetch('./data/market-pulse.json').then(r=>r.json()),fetch('./data/indicator-methodology.json').then(r=>r.json())]).then(([d,m])=>{setData(d);setMethod(m);setSelected(d.europe?.[0]?.country||null)});},[]);
  const list=useMemo(()=>data?(universe==='europe'?data.europe:data.emea):[],[data,universe]);
  useEffect(()=>{if(list.length&&!list.some(c=>c.country===selected))setSelected(list[0].country)},[list,selected]);
  if(!data) return <div className="loading">Loading EMEA Market Pulse…</div>;
  const field=FIELD[vertical], country=list.find(c=>c.country===selected)||list[0];
  const methodology=method[vertical]||[];
  const audit=methodology.map(m=>({m,z:country?.indicators?.[m.key],status:country?.sourceStatus?.[m.key]}));
  const withValues=audit.filter(x=>x.z?.raw!=null);
  const up=withValues.filter(x=>movement(x.z).dir>0).length, down=withValues.filter(x=>movement(x.z).dir<0).length, flat=withValues.filter(x=>movement(x.z).dir===0).length, unavailable=audit.length-withValues.length;
  const score=country?.[field], direction=band(score), coverage=country?.coverage?.[field]??0, confidence=country?.confidence?.[field]||'Insufficient';
  const regional=weightedRegional(list,field), regionalBand=band(regional.score);
  const sortedMoves=[...withValues].filter(x=>x.z?.growthPct!=null).sort((a,b)=>Number(b.z.growthPct)-Number(a.z.growthPct));
  const positives=sortedMoves.slice(0,2), negative=[...sortedMoves].reverse()[0];
  const countryRows=[...list].sort((a,b)=>(a.gdpRank||999)-(b.gdpRank||999));
  const shown=allCountries?countryRows:countryRows.slice(0,10);
  const latestEvidence=newest(withValues);
  const applicable=audit.filter(x=>x.m.weight>0).length;
  const currentCount=withValues.filter(x=>['current','recent'].includes(fresh(x.z?.date).cls)).length;
  const structuralCount=withValues.filter(x=>fresh(x.z?.date).cls==='structural').length;
  const staleCount=withValues.filter(x=>fresh(x.z?.date).cls==='stale').length;

  function chooseUniverse(u){setUniverse(u);setSelected((u==='europe'?data.europe:data.emea)?.[0]?.country||null)}
  return <main>
    <header className="hero">
      <div className="heroInner">
        <div><span className="eyebrow">SOLMAX MARKET INTELLIGENCE</span><h1>EMEA Market Pulse</h1><p>Real values. Real movement. Clear dates. Official public sources.</p></div>
        <div className="refresh"><span>LAST SUCCESSFUL REFRESH</span><b>{prettyDate(data.generatedAt||data.lastRefresh)}</b></div>
      </div>
      <div className="globalControls">
        <div className="segmented" aria-label="Universe selector"><button className={universe==='europe'?'active':''} onClick={()=>chooseUniverse('europe')}>Harmonised Europe</button><button className={universe==='emea'?'active':''} onClick={()=>chooseUniverse('emea')}>Broader EMEA</button></div>
        <nav className="verticals">{VERTICALS.map(v=><button key={v} className={v===vertical?'active':''} onClick={()=>setVertical(v)}>{v}</button>)}</nav>
      </div>
    </header>

    <section className="regionalPulse panel">
      <div className="sectionKicker">REGIONAL PULSE</div>
      <div className="regionalGrid">
        <div className={`pulseMark ${regionalBand.tone}`}><span>{regionalBand.arrow}</span><div><small>{universe==='europe'?'HARMONISED EUROPE':'BROADER EMEA'} · {vertical.toUpperCase()}</small><h2>{regionalBand.label}</h2><p>{universe==='europe'?'GDP-order and coverage-adjusted synthesis':'Coverage-adjusted synthesis'} of qualifying country evidence</p></div></div>
        <div className="evidenceBars">
          <div><span>Positive evidence</span><b>{regional.positive}%</b><i><em style={{width:`${regional.positive}%`}}/></i></div>
          <div className="weak"><span>Weakening evidence</span><b>{regional.weakening}%</b><i><em style={{width:`${regional.weakening}%`}}/></i></div>
          <div className="neutral"><span>Mixed / unavailable</span><b>{regional.unavailable}%</b><i><em style={{width:`${regional.unavailable}%`}}/></i></div>
        </div>
        <div className="regionalStats"><div><small>Markets included</small><b>{regional.count}/{list.length}</b></div><div><small>Weighted coverage</small><b>{regional.coverage}%</b></div><div><small>Latest evidence</small><b>{prettyDate(regional.latest)}</b></div></div>
      </div>
    </section>

    <section className="stickyMarket">
      <div className="marketIdentity"><img src={flag(country?.geo)} alt=""/><div><span>YOU ARE VIEWING</span><h2>{country?.country}</h2><p>{vertical} · {universe==='europe'?'Harmonised Europe':'Broader EMEA'}</p></div></div>
      <div className={`marketDirection ${direction.tone}`}><strong>{direction.arrow} {direction.label}</strong><span>{up} ↑ &nbsp; {down} ↓ &nbsp; {flat} → &nbsp; {unavailable} unavailable</span></div>
      <div className="marketMeta"><div><small>Latest evidence</small><b>{prettyDate(latestEvidence)}</b></div><div><small>Coverage</small><b>{coverage}%</b></div><div><small>Confidence</small><b>{confidence}</b></div></div>
      <label className="countrySelect"><span>Change country</span><select value={country?.country||''} onChange={e=>setSelected(e.target.value)}>{countryRows.map(c=><option key={c.country}>{c.country}</option>)}</select></label>
    </section>

    <section className="panel keyMovements">
      <div className="sectionHeading"><div><span className="sectionKicker">EXECUTIVE SNAPSHOT</span><h2>Key movements</h2></div><p>Largest available changes for {country?.country} · {vertical}</p></div>
      <div className="movementGrid">
        {positives.map(({m,z})=><article key={m.key} className="moveCard up"><small>INCREASE</small><h3>{m.name}</h3><b>{movement(z).text}</b><span>{fmt(z.previous)} · {prettyDate(z.previousDate)} → {fmt(z.raw)} · {prettyDate(z.date)}</span></article>)}
        {negative&&<article className="moveCard down"><small>MAIN WEAKENING SIGNAL</small><h3>{negative.m.name}</h3><b>{movement(negative.z).text}</b><span>{fmt(negative.z.previous)} · {prettyDate(negative.z.previousDate)} → {fmt(negative.z.raw)} · {prettyDate(negative.z.date)}</span></article>}
        {!sortedMoves.length&&<article className="moveCard neutral"><h3>No comparable movements available</h3><p>The table below explains each source status.</p></article>}
      </div>
    </section>

    <section className="panel intelligence">
      <div className="sectionHeading"><div><span className="sectionKicker">PRIMARY EVIDENCE</span><h2>Indicator Intelligence</h2><p>Complete public evidence for {country?.country} · {vertical}</p></div><div className="balance"><span className="up">{up} ↑ increasing</span><span className="down">{down} ↓ decreasing</span><span>{unavailable} unavailable</span></div></div>
      <div className="tableWrap"><table><thead><tr><th>Indicator</th><th>Previous observation</th><th>Latest observation</th><th>Movement</th><th>Freshness</th><th>Official source</th></tr></thead><tbody>{audit.map(({m,z,status})=>{
        const fr=fresh(z?.date), mv=movement(z); const src=m.displaySourceUrl||m.url||z?.source||z?.url; const reason=status?.retrieval==='error'?'Retrieval temporarily unavailable':status?.retrieval==='no_usable_series'?'No comparable series reported':m.pipelineStatus==='pending'?'Connector pending':'Not reported by source';
        return <tr key={m.key} className={!z?.raw?'empty':''} onClick={()=>setDetail({m,z,status,fr,reason})}>
          <td><strong>{m.name}</strong><small className="role">{roleLabel(m.role)}</small></td>
          <td>{z?.previous!=null?<><b>{fmt(z.previous)}</b><small>{prettyDate(z.previousDate)}</small></>:<span className="emptyText">—</span>}</td>
          <td>{z?.raw!=null?<><b>{fmt(z.raw)}</b><small>{prettyDate(z.date)}</small></>:<><span className="emptyText">{reason}</span><small>{(status?.datasetsTried||[]).join(', ')}</small></>}</td>
          <td><strong className={mv.dir>0?'deltaUp':mv.dir<0?'deltaDown':'deltaFlat'}>{mv.text}</strong></td>
          <td><span className={`fresh ${fr.cls}`}>● {fr.label}</span></td>
          <td>{src?<a href={src} target="_blank" rel="noreferrer" onClick={e=>e.stopPropagation()}>{m.source||z?.provider||'Official source'} · Official ↗</a>:<span>—</span>}</td>
        </tr>})}</tbody></table></div>
      <p className="tableHint">Select any row for full evidence details and the comparison basis.</p>
    </section>

    <section className="comparisonHead"><div><span className="sectionKicker">MARKET COMPARISON</span><h2>Compare with other markets</h2><p>Map and matrix use the same weighted direction for {vertical}. Select a country to update the evidence above.</p></div></section>
    <section className="compareGrid">
      <article className="panel mapPanel"><div className="miniHead"><div><h3>{universe==='europe'?'European':'Broader EMEA'} market map</h3><p>{vertical} · Evidence direction</p></div><div className="legend"><span><i style={{background:'#178353'}}/>Positive</span><span><i style={{background:'#dbc98c'}}/>Mixed</span><span><i style={{background:'#c94e49'}}/>Weakening</span></div></div>
        <div className={`map ${universe}`}><ComposableMap projection={universe==='europe'?'geoAzimuthalEqualArea':'geoMercator'} projectionConfig={universe==='europe'?{rotate:[-12,-52,0],scale:690}:{center:[28,19],scale:360}} width={800} height={520}><Geographies geography={GEO}>{({geographies})=>geographies.map(g=>{const c=list.find(x=>String(x.id)===String(g.id));if(!c)return <Geography key={g.rsmKey} geography={g} fill="#edf1f2" stroke="#fff" strokeWidth={0.45}/>;const is=c.country===country?.country;return <Geography key={g.rsmKey} geography={g} fill={colorFor(c[field])} stroke={is?SOLMAX.navy:'#fff'} strokeWidth={is?2.5:0.65} onClick={()=>setSelected(c.country)} className="geo"/>})}</Geographies></ComposableMap></div>
      </article>
      <article className="panel matrixPanel"><div className="miniHead"><div><h3>Country × vertical matrix</h3><p>Fixed GDP order · Direction and evidence balance</p></div></div><div className="matrixScroll"><table className="matrix"><thead><tr><th>Country</th>{VERTICALS.map(v=><th key={v}>{v}</th>)}</tr></thead><tbody>{shown.map(c=><tr key={c.country} className={c.country===country?.country?'selected':''} onClick={()=>setSelected(c.country)}><td><img src={flag(c.geo)} alt=""/><b>{c.country}</b></td>{VERTICALS.map(v=>{const f=FIELD[v],b=band(c[f]);const items=(method[v]||[]).map(m=>c.indicators?.[m.key]).filter(Boolean);const u=items.filter(z=>movement(z).dir>0).length,dn=items.filter(z=>movement(z).dir<0).length;return <td key={v}><span className={`cell ${b.tone}`}>{b.arrow} {b.label}</span><small>{u}↑ {dn}↓</small></td>})}</tr>)}</tbody></table></div><button className="showAll" onClick={()=>setAllCountries(!allCountries)}>{allCountries?'Fold to top 10':'Show all countries'}</button></article>
    </section>

    <section className="marketRead panel"><div className="sectionHeading"><div><span className="sectionKicker">INTERPRETATION</span><h2>Market read</h2></div></div><div className="readGrid">{['Now','Forward','Need','Context'].map(role=>{const rows=audit.filter(x=>x.m.role===role&&x.z?.raw!=null),u=rows.filter(x=>movement(x.z).dir>0).length,d=rows.filter(x=>movement(x.z).dir<0).length;const text=!rows.length?'Limited evidence':u>d?'Positive evidence':d>u?'Weakening evidence':'Mixed evidence';return <article key={role}><small>{roleLabel(role)}</small><h3>{u>d?'↗':d>u?'↘':'→'} {text}</h3><p>{rows.length?`${u} increasing · ${d} decreasing · ${rows.length} available`:'No comparable observations currently available'}</p></article>})}</div></section>

    <section className="panel quality"><div className="sectionHeading"><div><span className="sectionKicker">TRUST & TRANSPARENCY</span><h2>Data quality</h2></div></div><div className="qualityGrid"><div><small>Applicable coverage</small><b>{coverage}%</b><progress max="100" value={coverage}/></div><div><small>Current / recent</small><b>{currentCount}</b></div><div><small>Structural</small><b>{structuralCount}</b></div><div><small>Stale</small><b>{staleCount}</b></div><div><small>Unavailable</small><b>{unavailable}</b></div><div><small>Confidence</small><b>{confidence}</b></div></div></section>

    <section className="accordions"><div className="panel accordion"><button onClick={()=>setMethodOpen(!methodOpen)}>ⓘ How is overall direction calculated? <span>{methodOpen?'−':'+'}</span></button>{methodOpen&&<div><p>Real observations and their appropriate comparisons are the primary evidence. Changes are normalized internally because indicators use different units. Applicable indicator weights, coverage and freshness produce the country direction bands used by the map and matrix. Missing data never becomes zero.</p><p>The regional pulse synthesizes qualifying country signals. Harmonised Europe uses the configured fixed GDP order and coverage adjustment; Broader EMEA uses coverage-adjusted evidence.</p></div>}</div><div className="panel accordion"><button onClick={()=>setSourcesOpen(!sourcesOpen)}>ⓘ Sources, freshness & data quality <span>{sourcesOpen?'−':'+'}</span></button>{sourcesOpen&&<div><p>Each evidence row retains its latest and previous observations, dates, comparison basis and a link to the human-facing official source where configured. Current, Recent, Structural and Stale describe publication age relative to the role of the indicator.</p></div>}</div></section>

    {detail&&<div className="shade" onClick={()=>setDetail(null)}><aside className="drawer" onClick={e=>e.stopPropagation()}><button className="close" onClick={()=>setDetail(null)}>×</button><span className="sectionKicker">EVIDENCE DETAIL</span><h2>{detail.m.name}</h2><span className="role">{roleLabel(detail.m.role)}</span><dl><dt>Previous comparable observation</dt><dd>{fmt(detail.z?.previous)} · {prettyDate(detail.z?.previousDate)}</dd><dt>Latest observation</dt><dd>{fmt(detail.z?.raw)} · {prettyDate(detail.z?.date)}</dd><dt>Movement</dt><dd className={movement(detail.z).dir>0?'deltaUp':movement(detail.z).dir<0?'deltaDown':''}>{movement(detail.z).text}</dd><dt>Frequency</dt><dd>{detail.m.frequency||'Source-defined'}</dd><dt>Freshness</dt><dd><span className={`fresh ${detail.fr.cls}`}>● {detail.fr.label}</span></dd><dt>Availability status</dt><dd>{detail.z?.raw!=null?'Live observation':detail.reason}</dd></dl>{(detail.m.displaySourceUrl||detail.m.url||detail.z?.source)&&<a className="sourceButton" href={detail.m.displaySourceUrl||detail.m.url||detail.z?.source} target="_blank" rel="noreferrer">View original public source ↗</a>}</aside></div>}
  </main>
}
createRoot(document.getElementById('root')).render(<App/>);
