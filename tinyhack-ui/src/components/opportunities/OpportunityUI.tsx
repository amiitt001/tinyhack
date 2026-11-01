import {
  ArrowRight,
  ArrowUpRight,
  Bookmark,
  Building2,
  Check,
  ChevronRight,
  Clock3,
  ExternalLink,
  Info,
  LoaderCircle,
  MapPin,
  Search,
  ShieldCheck,
  TriangleAlert,
  X,
} from "lucide-react";
import { Link } from "react-router-dom";
import type { MouseEvent, ReactNode } from "react";
import { Badge, Modal } from "../ui";
import {
  activeRun,
  compensation,
  formatDate,
  safeExternalUrl,
  sourceHost,
  sourceLabel,
  sourceName,
  type DiscoveryRun,
  type Opportunity,
  type Source,
} from "../../lib/opportunities";

export function Notice({
  title,
  children,
  action,
  error = false,
}: {
  title: string;
  children?: ReactNode;
  action?: ReactNode;
  error?: boolean;
}) {
  return (
    <div
      className={`discovery-notice ${error ? "notice-error" : ""}`}
      role={error ? "alert" : undefined}
    >
      <span className="notice-icon">
        {error ? <TriangleAlert size={18} /> : <Info size={18} />}
      </span>
      <div>
        <strong>{title}</strong>
        {children && <p>{children}</p>}
      </div>
      {action}
    </div>
  );
}

export function SourceDialog({
  sources,
  error,
  onClose,
  retry,
}: {
  sources: Source[];
  error: string;
  onClose: () => void;
  retry: () => void;
}) {
  return (
    <Modal title="Discovery sources" onClose={onClose} className="source-modal">
      <p className="dialog-lead">
        Good opportunities start with clear sources. Availability reflects your
        workspace’s current connections.
      </p>
      {error && (
        <Notice
          title="Sources could not be loaded"
          error
          action={
            <button className="button secondary" onClick={retry}>
              Try again
            </button>
          }
        >
          {error}
        </Notice>
      )}
      <div className="source-list">
        {sources.map((source) => (
          <div key={source.name}>
            <span className="source-emblem">
              <Building2 size={18} />
            </span>
            <div>
              <h3>{sourceName(source.name)}</h3>
              <p>{source.allowed_domains.join(", ")}</p>
              <small>
                {source.status === "enabled"
                  ? "Available for this workspace"
                  : source.status === "restricted"
                    ? "Access restrictions · not available for discovery"
                    : source.status === "configured"
                      ? "Connection setup and source review are pending"
                      : "Not available for discovery"}
              </small>
            </div>
            <Badge tone={source.status === "enabled" ? "green" : "neutral"}>
              {sourceLabel(source)}
            </Badge>
          </div>
        ))}
      </div>
      <p className="dialog-note">
        <ShieldCheck size={15} />
        Only available sources can be selected. Search coverage is limited to
        the domains shown here.
      </p>
    </Modal>
  );
}

export function RunProgress({
  run,
  loading,
  error,
  retry,
}: {
  run: DiscoveryRun | null;
  loading: boolean;
  error: string;
  retry: () => void;
}) {
  const inProgress = activeRun(run);
  const labels = {
    pending: "Your search is queued",
    running: "Looking for your next opportunity",
    completed: "Your search is complete",
    partially_completed: "Some opportunities are ready",
    failed: "This search couldn’t be completed",
    cancelled: "This search was cancelled",
  };
  return (
    <div
      className={`run-progress ${run?.status === "failed" ? "run-failed" : ""}`}
    >
      <div className="run-progress-top">
        <span className="run-symbol">
          {inProgress || loading ? (
            <LoaderCircle size={19} className="spin" />
          ) : !run || run.status === "failed" || run.status === "cancelled" ? (
            <TriangleAlert size={19} />
          ) : (
            <Check size={19} />
          )}
        </span>
        <div aria-live="polite">
          <h2>
            {run
              ? labels[run.status]
              : loading
                ? "Checking your discovery…"
                : "Search status unavailable"}
          </h2>
          <p>
            {run
              ? `“${run.query}”${run.location ? ` · ${run.location}` : ""}`
              : "Check the search status to continue."}
          </p>
        </div>
        <span className="run-status-tag">
          {run?.status.replaceAll("_", " ") ||
            (loading ? "Checking" : "Unavailable")}
        </span>
      </div>
      {run && run.status !== "failed" && run.status !== "cancelled" && (
        <div className="run-steps" aria-label="Discovery stages">
          {["Queued", "Discovering", "Review results"].map((label, index) => {
            const stage =
              run?.status === "pending" ? 0 : run?.status === "running" ? 1 : 2;
            return (
              <span key={label} className={index <= stage ? "reached" : ""}>
                <i>{index < stage ? <Check size={10} /> : index + 1}</i>
                {label}
                {index < 2 && <ChevronRight size={12} />}
              </span>
            );
          })}
        </div>
      )}
      {run && (
        <div className="run-counts">
          <span>
            <strong>{run.accepted_results}</strong> accepted
          </span>
          <span>
            <strong>{run.rejected_results}</strong> rejected
          </span>
          <span>
            <strong>{run.total_results}</strong> candidates reviewed
          </span>
        </div>
      )}
      {run?.status === "partially_completed" && (
        <p className="run-explanation">
          Available results are shown below. Some candidates or sources could
          not be validated.
        </p>
      )}
      {run?.status === "failed" && (
        <p className="run-explanation">
          {run.error_code === "no_validated_results"
            ? "No candidates could be validated. Try a different role or a broader location."
            : "Try a new discovery when the source is available. Any previously accepted results are retained."}
        </p>
      )}
      {error && (
        <Notice
          title="We couldn’t update this search"
          error
          action={
            <button className="button secondary" onClick={retry}>
              Check status again
            </button>
          }
        >
          {error}
        </Notice>
      )}
    </div>
  );
}

export function LoadingCards() {
  return (
    <div
      className="discovery-card-grid"
      role="status"
      aria-label="Loading opportunities"
    >
      <span className="visually-hidden">Loading opportunities</span>
      {[0, 1, 2, 3].map((index) => (
        <div key={index} className="opportunity-skeleton" aria-hidden="true">
          <i />
          <b />
          <b />
          <span />
          <span />
          <div />
        </div>
      ))}
    </div>
  );
}

export function DiscoveryEmpty({
  saved = false,
  searching = false,
  completed = false,
  onDemo,
  onSearch,
}: {
  saved?: boolean;
  searching?: boolean;
  completed?: boolean;
  onDemo?: () => void;
  onSearch?: () => void;
}) {
  return (
    <div className="discovery-welcome">
      <div className="search-illustration" aria-hidden="true">
        <span className="illustration-ring" />
        <span className="illustration-sheet">
          <i />
          <i />
          <i />
          <b>
            <Search size={22} />
          </b>
        </span>
        <span className="illustration-star">✦</span>
        <span className="illustration-dot" />
      </div>
      <span className="eyebrow">
        {saved
          ? "MAKE ROOM FOR POSSIBILITY"
          : searching
            ? "A LITTLE PATIENCE. A LITTLE POSSIBILITY."
            : "YOUR NEXT CHAPTER"}
      </span>
      <h2>
        {saved
          ? "Your shortlist starts here."
          : searching
            ? "Looking for something worth your next step."
            : completed
              ? "A fresh search could open a new door."
              : "Find work that fits who you’re becoming."}
      </h2>
      <p>
        {saved
          ? "Save an opportunity to keep its details and source close at hand."
          : searching
            ? "We’ll show accepted opportunities as they become available. There’s no need to submit again."
            : completed
              ? "No accepted opportunities are available on this page. Try another role, location, or employment type."
              : "Choose a role, add your preferences, and discover opportunities from available sources."}
      </p>
      {saved ? (
        <button className="button secondary" onClick={onSearch}>
          Discover opportunities
          <ArrowRight size={15} />
        </button>
      ) : (
        !searching && (
          <div className="discovery-starter-actions">
            <Link className="button secondary" to="/profile">
              Review your career profile
              <ArrowUpRight size={15} />
            </Link>
            {onDemo && (
              <button className="text-link" onClick={onDemo}>
                Explore the demo
                <ArrowRight size={14} />
              </button>
            )}
          </div>
        )
      )}
      <div className="discovery-principles">
        <span>
          <ShieldCheck size={14} />
          Clear source attribution
        </span>
        <span>
          <Bookmark size={14} />
          Your own shortlist
        </span>
        <span>
          <Check size={14} />
          Details you can verify
        </span>
      </div>
    </div>
  );
}

export function OpportunityCard({
  job,
  saved,
  busy,
  onSave,
  onOpen,
  demo = false,
  compare,
  onCompare,
}: {
  job: Opportunity;
  saved: boolean;
  busy: boolean;
  onSave: () => void;
  onOpen?: (event: MouseEvent<HTMLAnchorElement>) => void;
  demo?: boolean;
  compare?: boolean;
  onCompare?: () => void;
}) {
  return (
    <article className="opportunity-card">
      <div className="opportunity-card-header">
        <span className="company-monogram">
          {(job.company_name || "?").slice(0, 2).toUpperCase()}
        </span>
        <div>
          <strong>{job.company_name || "Company not provided"}</strong>
          <span>
            {demo ? "Fictional demo company" : sourceHost(job.source_url)}
          </span>
        </div>
        <button
          className={`icon-button bookmark-button ${saved ? "is-saved" : ""}`}
          onClick={onSave}
          disabled={busy}
          aria-label={`${saved ? "Unsave" : "Save"} ${job.title}`}
          aria-pressed={saved}
        >
          {busy ? (
            <LoaderCircle size={18} className="spin" />
          ) : (
            <Bookmark size={18} fill={saved ? "currentColor" : "none"} />
          )}
        </button>
      </div>
      <h3>
        <Link to={`/opportunities/${job.id}`} onClick={onOpen}>
          {job.title}
        </Link>
      </h3>
      <div className="opportunity-meta">
        <span>
          <MapPin size={13} />
          {job.location || "Location not listed"}
        </span>
        {job.work_mode && <span>{job.work_mode.replaceAll("_", " ")}</span>}
      </div>
      <div className="opportunity-card-tags">
        {job.employment_type && (
          <Badge>{job.employment_type.replaceAll("_", " ")}</Badge>
        )}
        {(job.required_skills || []).slice(0, 3).map((skill) => (
          <Badge key={skill}>{skill}</Badge>
        ))}
      </div>
      <p className="opportunity-excerpt">
        {job.description ||
          "A description hasn’t been provided by this source."}
      </p>
      <div className="opportunity-compensation">
        {demo ? "Illustrative opportunity" : compensation(job)}
      </div>
      <div className="opportunity-evidence">
        <ShieldCheck size={13} />
        <span>
          {demo
            ? "Demo · not a real opening"
            : job.last_verified_at
              ? `Checked ${formatDate(job.last_verified_at)}`
              : "Verification date unavailable"}
        </span>
        {job.deadline && (
          <span className="job-deadline">
            <Clock3 size={12} />
            {formatDate(job.deadline)}
          </span>
        )}
      </div>
      <footer>
        {onCompare && (
          <label className="inline-check">
            <input type="checkbox" checked={compare} onChange={onCompare} />
            Compare
          </label>
        )}
        <Link
          className="text-link"
          to={`/opportunities/${job.id}`}
          onClick={onOpen}
        >
          View details
          <ArrowUpRight size={14} />
        </Link>
      </footer>
    </article>
  );
}

export function OpportunityContent({
  job,
  saved,
  busy,
  onSave,
  onTrack,
}: {
  job: Opportunity;
  saved: boolean;
  busy: boolean;
  onSave: () => void;
  onTrack?: () => void;
}) {
  const application = safeExternalUrl(job.application_url);
  const deadlinePassed =
    !!job.deadline && Date.parse(job.deadline) < Date.now();
  const expired = [job.expires_at, job.deadline].some(
    (value) => value && Date.parse(value) < Date.now(),
  );
  const sources = job.sources.filter((source) =>
    safeExternalUrl(source.original_url || source.canonical_url),
  );
  return (
    <div className="opportunity-content">
      <div className="detail-company">
        <span className="company-monogram">
          {(job.company_name || "?").slice(0, 2).toUpperCase()}
        </span>
        <div>
          <strong>{job.company_name || "Company not provided"}</strong>
          <span>
            <MapPin size={13} />
            {job.location || "Location not listed"}
          </span>
        </div>
        <Badge tone="green">Source evidence</Badge>
      </div>
      <div className="detail-facts">
        <div>
          <span>Employment</span>
          <strong>
            {job.employment_type?.replaceAll("_", " ") || "Not listed"}
          </strong>
        </div>
        <div>
          <span>Work mode</span>
          <strong>{job.work_mode?.replaceAll("_", " ") || "Not listed"}</strong>
        </div>
        <div>
          <span>Compensation</span>
          <strong>{compensation(job)}</strong>
        </div>
        <div>
          <span>Apply by</span>
          <strong>{formatDate(job.deadline)}</strong>
        </div>
      </div>
      <div className="detail-section">
        <h3>About the opportunity</h3>
        <p className="detail-description">
          {job.description || "The source did not provide a description."}
        </p>
      </div>
      <div className="detail-section">
        <h3>Required skills</h3>
        {job.required_skills?.length ? (
          <div className="skill-chips">
            {job.required_skills.map((skill) => (
              <Badge key={skill}>{skill}</Badge>
            ))}
          </div>
        ) : (
          <p className="muted">Required skills were not listed.</p>
        )}
      </div>
      {job.preferred_skills?.length ? (
        <div className="detail-section">
          <h3>Preferred skills</h3>
          <div className="skill-chips">
            {job.preferred_skills.map((skill) => (
              <Badge key={skill}>{skill}</Badge>
            ))}
          </div>
        </div>
      ) : null}
      {job.experience_requirement && (
        <div className="detail-section">
          <h3>Experience</h3>
          <p>{job.experience_requirement}</p>
        </div>
      )}
      <div className="detail-source-block">
        <h3>
          <ShieldCheck size={16} />
          Know where it came from
        </h3>
        <p>
          Last checked:{" "}
          {formatDate(job.last_verified_at, "Verification date unavailable")}.
          Review the original listing before applying.
        </p>
        {sources.length ? (
          sources.map((source, index) => (
            <a
              href={safeExternalUrl(
                source.original_url || source.canonical_url,
              )!}
              target="_blank"
              rel="noopener noreferrer"
              key={`${source.source_id}-${index}`}
            >
              <span>
                {sourceHost(source.original_url || source.canonical_url)}
              </span>
              <span>
                {formatDate(source.observed_at)}
                <ExternalLink size={13} />
              </span>
            </a>
          ))
        ) : safeExternalUrl(job.source_url) ? (
          <a
            href={safeExternalUrl(job.source_url)!}
            target="_blank"
            rel="noopener noreferrer"
          >
            View original source
            <ExternalLink size={13} />
          </a>
        ) : (
          <p>No source link is available.</p>
        )}
      </div>
      <div className="detail-actions">
        <button
          className={`button ${saved ? "secondary" : ""}`}
          disabled={busy}
          onClick={onSave}
        >
          {busy ? (
            <LoaderCircle size={16} className="spin" />
          ) : (
            <Bookmark size={16} fill={saved ? "currentColor" : "none"} />
          )}{" "}
          {saved ? "Saved · remove" : "Save opportunity"}
        </button>
        {application && !expired ? (
          <a
            className="button secondary"
            href={application}
            target="_blank"
            rel="noopener noreferrer"
          >
            View application page
            <ArrowUpRight size={15} />
          </a>
        ) : (
          <span className="muted">
            {expired
              ? deadlinePassed
                ? "The listed deadline has passed."
                : "This listing may be out of date. Review the original source."
              : "An application link is not available."}
          </span>
        )}
      </div>
      {onTrack && (
        <div className="local-track">
          <button className="text-link" onClick={onTrack}>
            Track this opportunity on this device
            <ArrowRight size={14} />
          </button>
          <p>Tracking does not submit an application.</p>
        </div>
      )}
    </div>
  );
}

export function ComparisonDialog({
  jobs,
  onClose,
  onRemove,
}: {
  jobs: Opportunity[];
  onClose: () => void;
  onRemove: (id: string) => void;
}) {
  return (
    <Modal
      title="Compare opportunities"
      onClose={onClose}
      className="comparison-modal"
    >
      <p className="dialog-lead">
        Compare the evidence side by side. Missing information remains unlisted.
      </p>
      <div className="opportunity-comparison">
        {jobs.map((job) => (
          <div key={job.id}>
            <div className="comparison-top">
              <h3>{job.title}</h3>
              <button
                className="icon-button"
                aria-label={`Remove ${job.title} from comparison`}
                onClick={() => onRemove(job.id)}
              >
                <X size={16} />
              </button>
            </div>
            <p>{job.company_name || "Company not listed"}</p>
            <dl>
              <div>
                <dt>Location</dt>
                <dd>{job.location || "Not listed"}</dd>
              </div>
              <div>
                <dt>Employment</dt>
                <dd>
                  {job.employment_type?.replaceAll("_", " ") || "Not listed"}
                </dd>
              </div>
              <div>
                <dt>Compensation</dt>
                <dd>{compensation(job)}</dd>
              </div>
              <div>
                <dt>Required skills</dt>
                <dd>{job.required_skills?.join(", ") || "Not listed"}</dd>
              </div>
              <div>
                <dt>Deadline</dt>
                <dd>{formatDate(job.deadline)}</dd>
              </div>
            </dl>
          </div>
        ))}
      </div>
    </Modal>
  );
}
