import { useState } from 'react';
import { ArrowUpRight, Building2, Search } from 'lucide-react';
import { Badge, Card, PageHead } from '../components/ui';
import { compareCareers, type CareerComparison } from '../lib/api';
import { useApp } from '../lib/store';

const careers = [
  { name: 'Frontend Engineer', skills: 'React, TypeScript, CSS, Accessibility', why: 'For people who enjoy building interfaces and making complex things feel simple.', next: 'Senior Engineer → Staff Engineer → Engineering Lead' },
  { name: 'Data Analyst', skills: 'SQL, Python, Statistics, Visualization', why: 'For people who enjoy asking questions, finding patterns, and explaining evidence.', next: 'Senior Analyst → Analytics Lead → Head of Analytics' },
  { name: 'AI / ML Engineer', skills: 'Python, Mathematics, Machine Learning, Evaluation', why: 'For people who enjoy experimentation, modeling, and building reliable intelligent systems.', next: 'ML Engineer → Senior ML Engineer → Applied Research Lead' },
];

export default function CareerExplorer() {
  const { state, update, toast } = useApp();
  const [query, setQuery] = useState('');
  const [selected, setSelected] = useState<string[]>([]);
  const [comparison, setComparison] = useState<CareerComparison | null>(null);
  const [loading, setLoading] = useState(false);
  const profileSummary = [state.profile.role, state.profile.location, state.profile.skills, state.profile.experience, state.profile.projects, state.profile.interests].filter(Boolean).join('\n');

  async function compare() {
    if (selected.length !== 2 || loading) return;
    setLoading(true);
    try {
      setComparison(await compareCareers(selected[0], selected[1], profileSummary));
    } catch (error) {
      toast(error instanceof Error ? error.message : 'Career comparison failed.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <PageHead eyebrow="POSSIBILITY STARTS WITH CURIOSITY" title="Career Explorer" description="Select exactly two paths to compare them with Gemini against your profile." />
      <div className="search-field wide-search"><Search size={18} /><input aria-label="Search careers" placeholder="Explore a role or skill…" value={query} onChange={(event) => setQuery(event.target.value)} /></div>
      <p className="muted">Curated role guides · Gemini comparison is grounded in your profile.</p>
      <div className="three-grid">
        {careers.filter((career) => `${career.name} ${career.skills}`.toLowerCase().includes(query.toLowerCase())).map((career) => (
          <Card key={career.name}>
            <span className="feature-icon"><Building2 size={22} /></span>
            <h2>{career.name}</h2><p>{career.why}</p>
            <h3>Skills to build</h3><div className="skill-chips">{career.skills.split(', ').map((skill) => <Badge key={skill}>{skill}</Badge>)}</div>
            <h3>Typical progression</h3><p className="muted">{career.next}</p>
            <h3>Evidence in your profile</h3><p className="muted">{career.skills.split(', ').filter((skill) => state.profile.skills.toLowerCase().includes(skill.toLowerCase())).join(', ') || 'No matching skill evidence added yet.'}</p>
            <div className="form-actions"><label className="inline-check"><input type="checkbox" checked={selected.includes(career.name)} onChange={(event) => { setComparison(null); setSelected(event.target.checked ? [...selected, career.name].slice(-2) : selected.filter((item) => item !== career.name)); }} />Compare</label><button className="text-link" onClick={() => { update({ profile: { ...state.profile, role: career.name } }); toast('Career target updated.'); }}>Set target <ArrowUpRight size={15} /></button></div>
          </Card>
        ))}
      </div>
      {selected.length === 2 && <Card title="Your Gemini career comparison" action={<button className="button" onClick={() => void compare()} disabled={loading}>{loading ? 'Comparing…' : 'Compare with Gemini'}</button>}>
        {!comparison ? <p className="muted">Compare the selected paths using your profile, skills, experience, and interests.</p> : <div className="comparison-grid"><div><h3>{comparison.first_career}</h3><p>{comparison.career_a_fit}</p></div><div><h3>{comparison.second_career}</h3><p>{comparison.career_b_fit}</p></div><div><h3>Summary</h3><p>{comparison.summary}</p><h3>Shared skills</h3><p>{comparison.shared_skills.join(', ') || 'None identified'}</p><h3>Trade-offs</h3><ul className="prose-list">{comparison.tradeoffs.map((item) => <li key={item}>{item}</li>)}</ul><h3>Recommended next step</h3><p>{comparison.recommended_next_step}</p></div></div>}
      </Card>}
    </>
  );
}
