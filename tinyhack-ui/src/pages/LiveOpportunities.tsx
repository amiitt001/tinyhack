import { useState } from 'react';
import { Download, ExternalLink, MapPin, Search } from 'lucide-react';
import { Card, Empty, Modal, PageHead } from '../components/ui';
import { fetchOpportunityPage, searchOpportunities, type TinyFishSearchResult } from '../lib/api';
import { useApp } from '../lib/store';

export default function LiveOpportunities() {
  const { state, toast } = useApp();
  const [query, setQuery] = useState(state.profile.role ? `${state.profile.role} internships` : '');
  const [location, setLocation] = useState(state.profile.location || '');
  const [results, setResults] = useState<TinyFishSearchResult[]>([]);
  const [total, setTotal] = useState(0);
  const [searching, setSearching] = useState(false);
  const [fetching, setFetching] = useState(false);
  const [page, setPage] = useState<TinyFishSearchResult | null>(null);

  async function search() {
    if (!query.trim() || searching) return;
    setSearching(true);
    try {
      const response = await searchOpportunities(query.trim(), location.trim() || undefined);
      setResults(response.results);
      setTotal(response.total_results);
      if (!response.results.length) toast('No opportunity URLs were found for that search.');
    } catch (error) {
      toast(error instanceof Error ? error.message : 'Opportunity search failed.');
    } finally {
      setSearching(false);
    }
  }

  async function fetchPage(result: TinyFishSearchResult) {
    setFetching(true);
    try {
      const content = await fetchOpportunityPage(result.url);
      setPage({ ...result, snippet: content.text });
    } catch (error) {
      toast(error instanceof Error ? error.message : 'The opportunity page could not be fetched.');
    } finally {
      setFetching(false);
    }
  }

  return (
    <>
      <PageHead eyebrow="FIND YOUR NEXT CHAPTER" title="Opportunities" description="Search official career pages for relevant internships and jobs." />
      <Card>
        <form className="filter-bar" onSubmit={(event) => { event.preventDefault(); void search(); }}>
          <div className="search-field"><Search size={18} /><input aria-label="Opportunity search" placeholder="Find Python developer internships…" value={query} onChange={(event) => setQuery(event.target.value)} /></div>
          <input aria-label="Opportunity location" placeholder="Location, e.g. India" value={location} onChange={(event) => setLocation(event.target.value)} />
          <button className="button" type="submit" disabled={searching || !query.trim()}>{searching ? 'Searching…' : 'Search'}</button>
        </form>
        <p className="muted">Search returns candidate URLs. Fetch a result to retrieve the known career page content.</p>
      </Card>
      {results.length ? <div className="results-heading"><span>{total} results found <span className="muted">· TinyFish Search</span></span></div> : null}
      {results.length ? <div className="opportunity-grid">{results.map((result) => <Card key={`${result.url}-${result.position}`}>
        <div className="job-top"><div><h3>{result.site_name}</h3><span className="muted">{result.publisher || 'Official career source'}</span></div><ExternalLink size={16} /></div>
        <h2>{result.title}</h2>
        <p className="location"><MapPin size={14} />{result.date || 'Date unavailable'}</p>
        <p className="job-description">{result.snippet}</p>
        <div className="job-card-bottom"><button className="button secondary" onClick={() => void fetchPage(result)} disabled={fetching}><Download size={15} />{fetching ? 'Fetching…' : 'Fetch page'}</button><a className="text-link" href={result.url} target="_blank" rel="noreferrer">Open source <ExternalLink size={14} /></a></div>
      </Card>)}</div> : <Card><Empty title="Search for a real opportunity">Try a role, skill, or internship query. Results are sourced from the connected web search provider.</Empty></Card>}
      {page && <Modal title={page.title} onClose={() => setPage(null)}><div className="fetched-page"><p className="muted">{page.url}</p><p>{page.snippet}</p></div></Modal>}
    </>
  );
}
