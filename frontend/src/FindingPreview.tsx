import { ArrowDown, ShieldCheck } from 'lucide-react';

export function FindingPreview({outcome, text}: {outcome: string; text: string}) {
  return <section className="finding-preview" aria-label="Investigation outcome">
    <ShieldCheck size={21}/>
    <div><h2>{outcome === 'supported' ? 'Finding supported in the captured fixture' : 'Cause not established'}</h2>
      <p>{text}</p>
    </div>
    <button onClick={() => {
      const target = document.getElementById('final-finding');
      target?.scrollIntoView({behavior: 'smooth', block: 'center'});
      target?.focus({preventScroll: true});
    }}>Review finding<ArrowDown size={14}/></button>
  </section>;
}
