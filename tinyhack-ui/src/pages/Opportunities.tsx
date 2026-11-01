import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type FormEvent,
  type MouseEvent,
} from "react";
import {
  Link,
  useLocation,
  useParams,
  useSearchParams,
} from "react-router-dom";
import {
  ArrowLeft,
  ArrowRight,
  ArrowUpRight,
  Bookmark,
  Check,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Compass,
  GitCompareArrows,
  LoaderCircle,
  MapPin,
  RotateCcw,
  Search,
  ShieldCheck,
  SlidersHorizontal,
  X,
} from "lucide-react";
import { useApp, opportunities as samples } from "../lib/store";
import { ApiError } from "../lib/api";
import {
  activeRun,
  fetchOpportunity,
  fetchSaved,
  setOpportunitySaved,
  sourceName,
  validId,
  type DiscoveryInput,
  type DiscoveryRun,
  type Opportunity,
} from "../lib/opportunities";
import {
  useOpportunityDiscovery,
  errorMessage,
} from "../hooks/useOpportunityDiscovery";
import { Badge, Modal, PageHead } from "../components/ui";
import {
  ComparisonDialog,
  DiscoveryEmpty,
  LoadingCards,
  Notice,
  OpportunityCard,
  OpportunityContent,
  RunProgress,
  SourceDialog,
} from "../components/opportunities/OpportunityUI";
import { OpportunityDetail as DemoOpportunityDetail } from "./Discovery";

function sampleJobs(): Opportunity[] {
  return samples.map((sample) => ({
    id: sample.id,
    title: sample.role,
    company_name: sample.company,
    description: sample.description,
    location: sample.location,
    work_mode: sample.mode,
    employment_type: sample.type,
    experience_requirement: null,
    required_skills: sample.skills,
    preferred_skills: null,
    salary_min: null,
    salary_max: null,
    salary_currency: null,
    salary_unit: null,
    stipend: null,
    application_url: null,
    canonical_url: null,
    source_url: "",
    source_id: null,
    source_external_id: null,
    deadline: null,
    discovered_at: "",
    last_verified_at: null,
    last_attempted_at: null,
    expires_at: null,
    status: "demo",
    extraction_status: null,
    content_hash: null,
    sources: [],
  }));
}
const demoJobs = sampleJobs();

function DetailPanel({
  id,
  cached,
  onClose,
  saved,
  busy,
  onSave,
  onTrack,
}: {
  id: string;
  cached?: Opportunity;
  onClose: () => void;
  saved: boolean;
  busy: boolean;
  onSave: () => void;
  onTrack: (job: Opportunity) => void;
}) {
  const [job, setJob] = useState<Opportunity | null>(cached || null);
  const [error, setError] = useState("");
  const [version, setVersion] = useState(0);
  useEffect(() => {
    if (cached) {
      setJob(cached);
      return;
    }
    const controller = new AbortController();
    setError("");
    if (!validId(id)) {
      setError("This opportunity link is invalid.");
      return;
    }
    fetchOpportunity(id, controller.signal)
      .then(setJob)
      .catch((failure) => {
        if (!controller.signal.aborted) setError(errorMessage(failure));
      });
    return () => controller.abort();
  }, [id, cached, version]);
  return (
    <Modal
      title={job?.title || "Opportunity details"}
      onClose={onClose}
      className="opportunity-drawer"
    >
      {error ? (
        <Notice
          title="Opportunity details aren’t available"
          error
          action={
            <button
              className="button secondary"
              onClick={() => setVersion((value) => value + 1)}
            >
              Try again
            </button>
          }
        >
          {error}
        </Notice>
      ) : job ? (
        <OpportunityContent
          job={job}
          saved={saved}
          busy={busy}
          onSave={onSave}
          onTrack={() => onTrack(job)}
        />
      ) : (
        <div className="detail-loading" role="status">
          <LoaderCircle className="spin" size={22} />
          Loading opportunity details…
        </div>
      )}
    </Modal>
  );
}

export function Opportunities() {
  const { state, update, toast, log } = useApp();
  const [params, setParams] = useSearchParams();
  const runId = params.get("run") || "";
  const savedView = params.get("view") === "saved";
  const offset = Math.min(
    9996,
    Math.max(0, Math.floor((Number(params.get("page")) || 1) - 1) * 6),
  );
  const detailId = params.get("detail") || "";
  const [query, setQuery] = useState(
    params.get("q") || state.profile.role || "",
  );
  const [location, setLocation] = useState(
    params.get("location") || state.profile.location || "",
  );
  const [employment, setEmployment] =
    useState<DiscoveryInput["employment_type"]>(null);
  const [experience, setExperience] = useState("");
  const [skills, setSkills] = useState("");
  const [selectedSource, setSelectedSource] = useState("");
  const [sourceDialog, setSourceDialog] = useState(false);
  const [formError, setFormError] = useState("");
  const [comparison, setComparison] = useState<Opportunity[]>([]);
  const [showComparison, setShowComparison] = useState(false);
  const [filtersOpen, setFiltersOpen] = useState(!runId && !savedView);
  const onCreated = useCallback(
    (run: DiscoveryRun) => {
      setFiltersOpen(false);
      setParams((current) => {
        const next = new URLSearchParams(current);
        next.set("run", run.id);
        next.set("q", run.query);
        if (run.location) next.set("location", run.location);
        else next.delete("location");
        next.delete("view");
        next.delete("page");
        next.delete("detail");
        return next;
      });
    },
    [setParams],
  );
  const workspace = useOpportunityDiscovery({
    demo: state.demo,
    runId,
    savedView,
    offset,
    onCreated,
  });
  const available = workspace.sources.filter(
    (source) => source.supported && source.status === "enabled",
  );
  const source =
    available.find((item) => item.name === selectedSource) || available[0];
  const searching = activeRun(workspace.run);
  useEffect(() => {
    if (
      workspace.run?.status === "failed" ||
      workspace.run?.status === "cancelled"
    )
      setFiltersOpen(true);
  }, [workspace.run?.status]);
  const liveDisabled =
    workspace.sourcesLoading || !source || workspace.submitting || searching;
  const demoResults = demoJobs.filter(
    (job) =>
      `${job.title} ${job.company_name} ${job.required_skills?.join(" ")}`
        .toLowerCase()
        .includes(query.toLowerCase()) &&
      (!employment ||
        job.employment_type?.toLowerCase().replaceAll("-", "_") ===
          employment) &&
      (!savedView || state.saved.includes(job.id)),
  );
  const jobs = state.demo ? demoResults : workspace.page.items;
  const total = state.demo ? demoResults.length : workspace.page.total;
  const savedCount = state.demo ? state.saved.length : workspace.savedTotal;

  function setView(saved: boolean) {
    setParams((current) => {
      const next = new URLSearchParams(current);
      if (saved) next.set("view", "saved");
      else next.delete("view");
      next.delete("page");
      next.delete("detail");
      return next;
    });
  }
  function setOffset(nextOffset: number) {
    setParams((current) => {
      const next = new URLSearchParams(current);
      next.set("page", String(Math.floor(nextOffset / 6) + 1));
      next.delete("detail");
      return next;
    });
  }
  function showDetail(event: MouseEvent<HTMLAnchorElement>, job: Opportunity) {
    if (
      state.demo ||
      event.metaKey ||
      event.ctrlKey ||
      event.shiftKey ||
      event.altKey ||
      event.button !== 0
    )
      return;
    event.preventDefault();
    setParams((current) => {
      const next = new URLSearchParams(current);
      next.set("detail", job.id);
      return next;
    });
  }
  function closeDetail() {
    setParams(
      (current) => {
        const next = new URLSearchParams(current);
        next.delete("detail");
        return next;
      },
      { replace: true },
    );
  }
  async function submit(event: FormEvent) {
    event.preventDefault();
    setFormError("");
    if (state.demo) return;
    if (query.trim().length < 2) {
      setFormError("Enter a role or at least two search characters.");
      return;
    }
    const skillList = [
      ...new Set(
        skills
          .split(",")
          .map((value) => value.trim())
          .filter(Boolean),
      ),
    ];
    if (
      skillList.length > 30 ||
      skillList.some((value) => value.length > 128)
    ) {
      setFormError(
        "Use up to 30 comma-separated skills, each under 129 characters.",
      );
      return;
    }
    if (liveDisabled) return;
    await workspace.submit({
      query: query.trim(),
      location: location.trim() || null,
      employment_type: employment,
      experience_level: experience || null,
      skills: skillList,
      sources: [source.name],
    });
  }
  async function toggleSaved(job: Opportunity) {
    if (state.demo) {
      const exists = state.saved.includes(job.id);
      update({
        saved: exists
          ? state.saved.filter((id) => id !== job.id)
          : [...state.saved, job.id],
      });
      log(
        exists
          ? "Demo opportunity removed from shortlist"
          : "Demo opportunity saved",
      );
      toast(
        exists
          ? "Removed from demo shortlist."
          : "Saved to your demo shortlist on this device.",
      );
      return;
    }
    try {
      await workspace.toggleSaved(job.id);
      toast(
        workspace.savedIds.has(job.id)
          ? "Removed from your shortlist."
          : "Saved to your shortlist.",
      );
    } catch (error) {
      toast(errorMessage(error));
    }
  }
  function toggleCompare(job: Opportunity) {
    if (comparison.some((item) => item.id === job.id)) {
      setComparison((current) => current.filter((item) => item.id !== job.id));
    } else if (comparison.length >= 3) {
      toast("Compare up to three opportunities at a time.");
    } else {
      setComparison((current) => [...current, job]);
    }
  }
  function track(job: Opportunity) {
    if (
      state.applications.some(
        (item) => item.company === job.company_name && item.role === job.title,
      )
    ) {
      toast("This opportunity is already in your local tracker.");
      return;
    }
    update({
      applications: [
        ...state.applications,
        {
          id: crypto.randomUUID(),
          company: job.company_name || "Company not listed",
          role: job.title,
          status: "Interested",
          date: new Date().toISOString().slice(0, 10),
          notes: `Source: ${job.source_url}. Tracked locally; no application submitted.`,
          reminder: "",
        },
      ],
    });
    log(`Opportunity added to local tracker: ${job.title}`);
    toast("Added to your local tracker. No application was submitted.");
  }
  useEffect(() => {
    if (
      !state.demo &&
      savedView &&
      !workspace.pageLoading &&
      !workspace.pageError &&
      offset > 0 &&
      workspace.page.total <= offset
    )
      setOffset(Math.max(0, offset - 6));
  }, [
    state.demo,
    savedView,
    workspace.pageLoading,
    workspace.pageError,
    workspace.page.total,
    offset,
  ]);
  useEffect(() => {
    setComparison([]);
    setShowComparison(false);
  }, [state.demo]);

  return (
    <div className="opportunity-workspace">
      <div className="discovery-heading">
        <div>
          <div className="eyebrow">
            <span className="eyebrow-line" /> YOUR NEXT CHAPTER
          </div>
          <h1>
            Good work. A better fit<span className="heading-dot">.</span>
          </h1>
          <p>A thoughtful search today. A little more possibility tomorrow.</p>
        </div>
        <div className="discovery-heading-actions">
          <span
            className={`connection-pill ${state.demo ? "is-demo" : available.length ? "is-ready" : ""}`}
          >
            <span />
            {state.demo
              ? "Demo workspace"
              : workspace.sourcesLoading
                ? "Checking sources"
                : available.length
                  ? "Discovery available"
                  : "Discovery not ready"}
          </span>
          {!state.demo && (
            <button
              className="button secondary"
              onClick={() => setSourceDialog(true)}
            >
              <ShieldCheck size={15} />
              Source availability
            </button>
          )}
        </div>
      </div>
      <div className="discovery-view-bar">
        <div
          role="tablist"
          aria-label="Opportunity views"
          onKeyDown={(event) => {
            if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
              event.preventDefault();
              const other =
                event.currentTarget.querySelector<HTMLButtonElement>(
                  '[aria-selected="false"]',
                );
              other?.click();
              other?.focus();
            }
          }}
        >
          <button
            id="discover-tab"
            role="tab"
            aria-selected={!savedView}
            aria-controls="opportunity-results"
            tabIndex={savedView ? -1 : 0}
            onClick={() => setView(false)}
          >
            <Compass size={16} />
            Discover
          </button>
          <button
            id="saved-tab"
            role="tab"
            aria-selected={savedView}
            aria-controls="opportunity-results"
            tabIndex={savedView ? 0 : -1}
            onClick={() => setView(true)}
          >
            <Bookmark size={16} />
            Saved<span>{savedCount === null ? "—" : savedCount}</span>
          </button>
        </div>
        <span className="discovery-view-note">
          <ShieldCheck size={13} />
          {state.demo
            ? "Sample data · saved on this device"
            : "Source evidence comes with every result"}
        </span>
      </div>
      {state.demo && (
        <Notice
          title="You’re exploring demo opportunities"
          action={
            <button
              className="text-link"
              onClick={() => update({ demo: false })}
            >
              Back to discovery
              <ArrowRight size={14} />
            </button>
          }
        >
          These fictional companies and roles help you try search, saving, and
          comparison. They are not real openings.
        </Notice>
      )}
      <div className="discovery-layout">
        <aside
          className={`discovery-search-panel ${filtersOpen ? "filters-open" : ""}`}
        >
          <button
            className="mobile-filter-toggle"
            aria-expanded={filtersOpen}
            aria-controls="discovery-search-content"
            onClick={() => setFiltersOpen((value) => !value)}
          >
            <SlidersHorizontal size={18} />
            <span>
              {filtersOpen ? "Your search preferences" : "Refine your search"}
            </span>
            <ChevronDown size={17} />
          </button>
          <div
            className="discovery-search-content"
            id="discovery-search-content"
          >
            <div className="search-panel-heading">
              <span>
                <SlidersHorizontal size={17} />
              </span>
              <div>
                <h2>Your direction</h2>
                <p>Make the search your own.</p>
              </div>
            </div>
            <form onSubmit={submit} noValidate>
              <label htmlFor="discovery-query">Role or keywords</label>
              <div className="input-with-icon">
                <Search size={16} />
                <input
                  id="discovery-query"
                  aria-label="Search opportunities"
                  placeholder="e.g. Python Developer Intern"
                  maxLength={255}
                  value={query}
                  onChange={(event) => {
                    setQuery(event.target.value);
                    setFormError("");
                  }}
                  aria-invalid={!!formError}
                  aria-describedby={
                    formError ? "discovery-form-error" : undefined
                  }
                />
              </div>
              <label htmlFor="discovery-location">
                Location <span>optional</span>
              </label>
              <div className="input-with-icon">
                <MapPin size={16} />
                <input
                  id="discovery-location"
                  placeholder="City, region, or country"
                  value={location}
                  onChange={(event) => setLocation(event.target.value)}
                  maxLength={255}
                  disabled={state.demo}
                />
              </div>
              {state.demo && (
                <small className="field-hint">
                  Demo filtering uses role, skills, and employment type.
                </small>
              )}
              <label htmlFor="discovery-employment">Employment type</label>
              <select
                id="discovery-employment"
                value={employment || ""}
                onChange={(event) =>
                  setEmployment(
                    (event.target.value ||
                      null) as DiscoveryInput["employment_type"],
                  )
                }
              >
                <option value="">Any employment type</option>
                <option value="internship">Internship</option>
                <option value="full_time">Full-time</option>
                <option value="part_time">Part-time</option>
                <option value="contract">Contract</option>
                <option value="temporary">Temporary</option>
                <option value="volunteer">Volunteer</option>
                <option value="other">Other</option>
              </select>
              {!state.demo && (
                <>
                  <details className="discovery-more-filters">
                    <summary>
                      Refine your direction
                      <ChevronDown size={14} />
                    </summary>
                    <label htmlFor="discovery-experience">
                      Experience level
                    </label>
                    <select
                      id="discovery-experience"
                      value={experience}
                      onChange={(event) => setExperience(event.target.value)}
                    >
                      <option value="">Any experience level</option>
                      <option value="fresher">Fresher</option>
                      <option value="early career">Early career</option>
                      <option value="mid level">Mid-level</option>
                      <option value="senior">Senior</option>
                    </select>
                    <label htmlFor="discovery-skills">
                      Skills <span>optional</span>
                    </label>
                    <input
                      id="discovery-skills"
                      placeholder="Python, SQL, FastAPI"
                      value={skills}
                      onChange={(event) => setSkills(event.target.value)}
                      maxLength={3870}
                    />
                    <small className="field-hint">
                      Separate skills with commas.
                    </small>
                  </details>
                  <div className="discovery-source-picker">
                    <label htmlFor="discovery-source">Search source</label>
                    {available.length ? (
                      <select
                        id="discovery-source"
                        value={source?.name || ""}
                        onChange={(event) =>
                          setSelectedSource(event.target.value)
                        }
                      >
                        {available.map((item) => (
                          <option key={item.name} value={item.name}>
                            {sourceName(item.name)}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <div className="source-unavailable">
                        <span className="status-dot" />
                        {workspace.sourcesLoading
                          ? "Checking availability…"
                          : workspace.sourceError
                            ? "Connection unavailable"
                            : "No available sources"}
                      </div>
                    )}
                    {source && (
                      <small className="field-hint">
                        Coverage: {source.allowed_domains.join(", ")}.
                      </small>
                    )}
                  </div>
                </>
              )}
              {formError && (
                <p
                  className="inline-field-error"
                  id="discovery-form-error"
                  role="alert"
                >
                  {formError}
                </p>
              )}
              {workspace.submitError && !state.demo && (
                <p className="inline-field-error" role="alert">
                  {workspace.submitError}
                </p>
              )}
              <button
                className="button discovery-submit"
                disabled={!state.demo && liveDisabled}
              >
                {workspace.submitting || searching ? (
                  <LoaderCircle className="spin" size={16} />
                ) : (
                  <Search size={16} />
                )}{" "}
                {state.demo
                  ? "Filter demo roles"
                  : workspace.submitting
                    ? "Starting your search…"
                    : searching
                      ? "Search in progress"
                      : "Discover opportunities"}
                {!searching && !workspace.submitting && (
                  <ArrowRight size={15} />
                )}
              </button>
              <button
                className="search-reset"
                type="button"
                onClick={() => {
                  setQuery("");
                  setLocation("");
                  setEmployment(null);
                  setExperience("");
                  setSkills("");
                  setFormError("");
                }}
              >
                <RotateCcw size={12} />
                Reset preferences
              </button>
            </form>
            <div className="search-panel-footer">
              <ShieldCheck size={16} />
              <p>
                {state.demo
                  ? "Demo saves stay separate from your real shortlist."
                  : "Only available sources are searched. Missing details stay unlisted."}
              </p>
            </div>
            <Link className="search-profile-link" to="/profile">
              <span>
                Start with your strengths
                <small>Review your career profile</small>
              </span>
              <ArrowUpRight size={16} />
            </Link>
          </div>
        </aside>
        <section
          className="discovery-results-panel"
          id="opportunity-results"
          role="tabpanel"
          aria-labelledby={savedView ? "saved-tab" : "discover-tab"}
        >
          {!state.demo && workspace.sourceError && (
            <Notice
              title="We couldn’t connect to discovery"
              error
              action={
                <button
                  className="button secondary"
                  onClick={workspace.retrySources}
                >
                  Try again
                </button>
              }
            >
              {workspace.sourceError}
            </Notice>
          )}
          {!state.demo &&
            !workspace.sourcesLoading &&
            !workspace.sourceError &&
            !available.length && (
              <Notice
                title="Discovery sources aren’t ready yet"
                action={
                  <button
                    className="text-link"
                    onClick={() => setSourceDialog(true)}
                  >
                    View sources
                    <ArrowUpRight size={13} />
                  </button>
                }
              >
                Your workspace needs an available source before a new search can
                start. You can still browse saved opportunities or explore the
                demo.
              </Notice>
            )}
          {!state.demo && !savedView && runId && (
            <RunProgress
              run={workspace.run}
              loading={workspace.runLoading}
              error={workspace.runError}
              retry={workspace.retryRun}
            />
          )}
          <div className="discovery-results-heading">
            <div>
              <h2>
                {savedView
                  ? "A shortlist worth coming back to"
                  : state.demo
                    ? "Explore the possibilities"
                    : runId
                      ? "Your discovery results"
                      : "A little direction goes a long way"}
              </h2>
              <p>
                {total
                  ? `${total} ${state.demo ? "sample " : ""}opportunit${total === 1 ? "y" : "ies"}${savedView ? " saved" : " to explore"}`
                  : savedView
                    ? "Your next steps, kept in one place."
                    : runId
                      ? "Accepted listings will appear here."
                      : "Start with a role you’re curious about."}
              </p>
            </div>
            {jobs.length > 0 && (
              <span className="results-layout-label">
                {state.demo ? (
                  <Badge tone="orange">Demo</Badge>
                ) : (
                  <>
                    <Check size={13} />
                    Source-backed details
                  </>
                )}
              </span>
            )}
          </div>
          {!state.demo && workspace.pageError && (
            <Notice
              title={
                savedView
                  ? "Your shortlist couldn’t be loaded"
                  : "Results couldn’t be loaded"
              }
              error
              action={
                <button
                  className="button secondary"
                  onClick={workspace.retryPage}
                >
                  Retry results
                </button>
              }
            >
              {workspace.pageError}
            </Notice>
          )}
          {!state.demo && workspace.pageLoading && !jobs.length ? (
            <LoadingCards />
          ) : jobs.length ? (
            <div className="discovery-card-grid">
              {jobs.map((job) => (
                <OpportunityCard
                  key={job.id}
                  job={job}
                  demo={state.demo}
                  saved={
                    state.demo
                      ? state.saved.includes(job.id)
                      : workspace.savedIds.has(job.id)
                  }
                  busy={workspace.savingIds.has(job.id)}
                  onSave={() => void toggleSaved(job)}
                  onOpen={(event) => showDetail(event, job)}
                  compare={comparison.some((item) => item.id === job.id)}
                  onCompare={() => toggleCompare(job)}
                />
              ))}
            </div>
          ) : !workspace.pageError || state.demo ? (
            <DiscoveryEmpty
              saved={savedView}
              searching={!state.demo && searching}
              completed={!!runId || state.demo}
              onDemo={state.demo ? undefined : () => update({ demo: true })}
              onSearch={() => {
                setView(false);
                if (state.demo) setQuery("");
              }}
            />
          ) : null}
          {!state.demo && total > 0 && (
            <div className="discovery-pagination">
              <span>
                Showing {Math.min(offset + 1, total)}–
                {Math.min(offset + workspace.page.limit, total)} of {total}
              </span>
              <div>
                <button
                  className="button secondary"
                  aria-label="Previous opportunities page"
                  disabled={offset === 0 || workspace.pageLoading}
                  onClick={() => setOffset(Math.max(0, offset - 6))}
                >
                  <ChevronLeft size={15} />
                  Previous
                </button>
                <button
                  className="button secondary"
                  aria-label="Next opportunities page"
                  disabled={
                    !workspace.page.has_more ||
                    workspace.pageLoading ||
                    offset + 6 > 9996
                  }
                  onClick={() => setOffset(offset + 6)}
                >
                  Next
                  <ChevronRight size={15} />
                </button>
              </div>
            </div>
          )}
        </section>
      </div>
      <div className="discovery-bottom-note">
        <ShieldCheck size={13} />
        <span>
          A source check is a starting point. Always review the original listing
          before applying.
        </span>
      </div>
      {comparison.length > 0 && (
        <div className="opportunity-compare-tray">
          <span>
            <GitCompareArrows size={17} />
            <strong>{comparison.length}</strong> selected
          </span>
          <button
            className="button"
            disabled={comparison.length < 2}
            onClick={() => setShowComparison(true)}
          >
            Compare opportunities
            <ArrowRight size={14} />
          </button>
          <button
            className="icon-button"
            aria-label="Clear comparison"
            onClick={() => setComparison([])}
          >
            <X size={16} />
          </button>
        </div>
      )}
      {sourceDialog && (
        <SourceDialog
          sources={workspace.sources}
          error={workspace.sourceError}
          retry={workspace.retrySources}
          onClose={() => setSourceDialog(false)}
        />
      )}
      {showComparison && (
        <ComparisonDialog
          jobs={comparison}
          onClose={() => setShowComparison(false)}
          onRemove={(id) =>
            setComparison((current) => current.filter((job) => job.id !== id))
          }
        />
      )}
      {detailId && !state.demo && (
        <DetailPanel
          key={detailId}
          id={detailId}
          cached={jobs.find((job) => job.id === detailId)}
          onClose={closeDetail}
          saved={workspace.savedIds.has(detailId)}
          busy={workspace.savingIds.has(detailId)}
          onSave={() => {
            const job = jobs.find((item) => item.id === detailId);
            if (job) void toggleSaved(job);
            else
              void workspace
                .toggleSaved(detailId)
                .catch((error) => toast(errorMessage(error)));
          }}
          onTrack={track}
        />
      )}
    </div>
  );
}

function LiveOpportunityDetail({ id }: { id: string }) {
  const location = useLocation();
  const { state, update, log, toast } = useApp();
  const [job, setJob] = useState<Opportunity | null>(null);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);
  const [busy, setBusy] = useState(false);
  const [version, setVersion] = useState(0);
  const savedEpoch = useRef(0);
  useEffect(() => {
    const controller = new AbortController();
    const epoch = ++savedEpoch.current;
    setError("");
    setJob(null);
    setSaved(false);
    fetchOpportunity(id, controller.signal)
      .then(setJob)
      .catch((failure) => {
        if (!controller.signal.aborted)
          setError(
            failure instanceof ApiError && failure.status === 404
              ? "This opportunity is no longer available."
              : errorMessage(failure),
          );
      });
    fetchSaved(0, 100, controller.signal)
      .then((page) => {
        if (!controller.signal.aborted && epoch === savedEpoch.current)
          setSaved(page.items.some((item) => item.id === id));
      })
      .catch(() => {});
    return () => controller.abort();
  }, [id, version]);
  async function save() {
    if (busy) return;
    setBusy(true);
    const epoch = ++savedEpoch.current;
    try {
      const result = await setOpportunitySaved(id, !saved);
      if (epoch !== savedEpoch.current) return;
      setSaved(result.saved);
      toast(
        result.saved
          ? "Saved to your shortlist."
          : "Removed from your shortlist.",
      );
    } catch (failure) {
      toast(errorMessage(failure));
    } finally {
      setBusy(false);
    }
  }
  const previous = (location.state as { from?: string } | null)?.from;
  const back = previous?.startsWith("/opportunities")
    ? previous
    : "/opportunities";
  return (
    <>
      <Link className="back-link" to={back}>
        <ArrowLeft size={15} />
        Back to opportunities
      </Link>
      <PageHead
        eyebrow="A CLOSER LOOK"
        title={job?.title || "Opportunity details"}
        description={
          job?.company_name || "Make your next step an informed one."
        }
      />
      {error ? (
        <Notice
          title="Opportunity unavailable"
          error
          action={
            <button
              className="button secondary"
              onClick={() => setVersion((value) => value + 1)}
            >
              Try again
            </button>
          }
        >
          {error}
        </Notice>
      ) : job ? (
        <section className="card standalone-opportunity">
          <OpportunityContent
            job={job}
            saved={saved}
            busy={busy}
            onSave={() => void save()}
            onTrack={() => {
              if (
                state.applications.some(
                  (item) =>
                    item.company === job.company_name &&
                    item.role === job.title,
                )
              ) {
                toast("Already in your local tracker.");
                return;
              }
              update({
                applications: [
                  ...state.applications,
                  {
                    id: crypto.randomUUID(),
                    company: job.company_name || "Company not listed",
                    role: job.title,
                    status: "Interested",
                    date: new Date().toISOString().slice(0, 10),
                    notes: `Source: ${job.source_url}. Tracked locally; no application submitted.`,
                    reminder: "",
                  },
                ],
              });
              log("Opportunity added to local application tracker");
              toast(
                "Added to your local tracker. No application was submitted.",
              );
            }}
          />
        </section>
      ) : (
        <LoadingCards />
      )}
    </>
  );
}

export function OpportunityDetail() {
  const { id = "" } = useParams();
  if (samples.some((sample) => sample.id === id))
    return <DemoOpportunityDetail />;
  if (!validId(id))
    return (
      <>
        <PageHead
          title="Opportunity unavailable"
          description="This opportunity link is invalid or no longer available."
        />
        <Link className="button secondary" to="/opportunities">
          Back to opportunities
          <ArrowLeft size={15} />
        </Link>
      </>
    );
  return <LiveOpportunityDetail key={id} id={id} />;
}
