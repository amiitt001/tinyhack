import { useState } from 'react';
import { ArrowUpRight, Pause, Play, Radar, Trash2 } from 'lucide-react';
import { Badge, Card, Empty, PageHead } from '../components/ui';
import { createDiscovery, fetchDiscovery, fetchDiscoveryResults, type DiscoveryRun } from '../lib/api';
import { useApp } from '../lib/store';

type Watch = { name: string; run: DiscoveryRun | null; paused: boolean };

export default function LiveMonitor() {
  const { state, toast } = useApp();
  const [name, setName] = useState('');
  const [watches, setWatches] = useState<Watch[]>([]);
  const [loading, setLoading] = useState(false);

  async function addWatch() {
    const query = name.trim();
    if (!query || loading) return;
    if (watches.some((watch) => watch.name.toLowerCase() === query.toLowerCase())) {
      toast('Already in your watchlist.');
      return;
    }
    setLoading(true);
    try {
      const run = await createDiscovery({
        query,
        location: state.profile.location || undefined,
        idempotency_key: `monitor-${query.toLowerCase()}-${Date.now()}`,
      });
      setWatches((items) => [...items, { name: query, run, paused: false }]);
      setName('');
      toast('Live monitor started. TinyFish is searching for matching opportunities.');
    } catch (error) {
      toast(error instanceof Error ? error.message : 'Live monitor could not be started.');
    } finally {
      setLoading(false);
    }
  }

  async function refreshWatch(index: number) {
    const watch = watches[index];
    if (!watch.run || watch.paused) return;
    try {
      const run = await fetchDiscovery(watch.run.id);
      setWatches((items) => items.map((item, itemIndex) => itemIndex === index ? { ...item, run } : item));
      if (run.status === 'completed') {
        await fetchDiscoveryResults(run.id);
        toast(`${watch.name}: ${run.accepted_results ?? 0} opportunities found.`);
      }
    } catch (error) {
      toast(error instanceof Error ? error.message : 'Monitor status could not be refreshed.');
    }
  }

  return (
    <>
      <PageHead eyebrow="STAY CLOSE TO WHAT MATTERS" title="Career Monitor" description="Keep target roles and companies in sight with live opportunity discovery." />
      <Card title="Create a watchlist" detail="Each watch starts a real backend discovery run using TinyFish.">
        <form className="inline-form" onSubmit={(event) => { event.preventDefault(); void addWatch(); }}>
          <input aria-label="Role or company to monitor" required value={name} onChange={(event) => setName(event.target.value)} placeholder="e.g. Frontend internships in Bengaluru" />
          <button className="button" disabled={loading}><Radar size={16} />{loading ? 'Starting…' : 'Start live monitor'}</button>
        </form>
      </Card>
      <div className="three-grid">
        {watches.map((watch, index) => <Card key={watch.name}>
          <span className="feature-icon"><Radar size={23} /></span>
          <h2>{watch.name}</h2>
          <Badge tone={watch.paused ? 'orange' : watch.run?.status === 'completed' ? 'green' : 'orange'}>{watch.paused ? 'Paused' : watch.run?.status || 'pending'}</Badge>
          <p className="muted">Results: {watch.run?.accepted_results ?? 'pending'}<br />Last checked: {watch.run?.updated_at ? new Date(watch.run.updated_at).toLocaleString() : 'just now'}</p>
          <div className="form-actions">
            <button className="button secondary" onClick={() => { const paused = !watch.paused; setWatches((items) => items.map((item, itemIndex) => itemIndex === index ? { ...item, paused } : item)); }}>{watch.paused ? <Play size={14} /> : <Pause size={14} />}{watch.paused ? 'Resume' : 'Pause'}</button>
            <button className="button secondary" onClick={() => void refreshWatch(index)} disabled={watch.paused}><Radar size={14} />Refresh</button>
            <button className="icon-button" aria-label={`Delete watchlist ${watch.name}`} onClick={() => setWatches((items) => items.filter((_, itemIndex) => itemIndex !== index))}><Trash2 size={16} /></button>
          </div>
        </Card>)}
      </div>
      {!watches.length && <Card><Empty title="Make room for the right signal.">Start a live watchlist to search the connected opportunity provider.</Empty></Card>}
      <p><a className="text-link" href="/settings">Manage notification preferences <ArrowUpRight size={15} /></a></p>
    </>
  );
}
