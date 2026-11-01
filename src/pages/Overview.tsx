import { Link } from "react-router-dom";
import {
  ArrowUpRight,
  ArrowRight,
  Sparkles,
  Target,
  Bookmark,
  BriefcaseBusiness,
  Clock3,
  ChevronRight,
  Check,
  Flame,
  FileText,
  Route,
  CheckCircle2,
  Circle,
  Plus,
  Layers3,
} from "lucide-react";
import { useApp, opportunities, milestones } from "../lib/store";
import { Card, Badge } from "../components/ui";

export default function Overview() {
  const { state } = useApp();
  const { profile } = state;
  const complete = Object.values(profile).filter((value) =>
    value.trim(),
  ).length;
  const score = Math.round((complete / 8) * 100);
  const completed = milestones
    .flatMap((m) => m.tasks.map((_, index) => `${m.id}-${index}`))
    .filter((id) => state.completed.includes(id)).length;
  const nextMilestone = milestones.find((m) =>
    m.tasks.some((_, index) => !state.completed.includes(`${m.id}-${index}`)),
  );
  const nextTask = nextMilestone?.tasks.find(
    (_, index) => !state.completed.includes(`${nextMilestone.id}-${index}`),
  );
  const deadlineCount = state.applications.filter(
    (a) =>
      a.reminder &&
      a.status !== "Rejected" &&
      a.status !== "Offer" &&
      a.reminder >= new Date().toLocaleDateString("en-CA"),
  ).length;
  const stats = [
    {
      label: "Active applications",
      value: state.applications.filter(
        (a) => !["Offer", "Rejected"].includes(a.status),
      ).length,
      note: "Keep your next steps in sight",
      icon: BriefcaseBusiness,
      path: "/applications",
      tone: "orange",
    },
    {
      label: "Saved opportunities",
      value: state.saved.length,
      note: "Your personal shortlist",
      icon: Bookmark,
      path: "/opportunities",
      tone: "purple",
    },
    {
      label: "Learning tasks done",
      value: completed,
      note: `${12 - completed} steps left on your roadmap`,
      icon: CheckCircle2,
      path: "/roadmap",
      tone: "green",
    },
    {
      label: "Upcoming follow-ups",
      value: deadlineCount,
      note: "From your application tracker",
      icon: Clock3,
      path: "/applications",
      tone: "blue",
    },
  ];
  const progress = [
    {
      label: "Personal details",
      value:
        [profile.name, profile.location].filter((v) => v.trim()).length * 50,
    },
    {
      label: "Career direction",
      value:
        [profile.role, profile.interests].filter((v) => v.trim()).length * 50,
    },
    {
      label: "Skills & education",
      value:
        [profile.skills, profile.education].filter((v) => v.trim()).length * 50,
    },
    {
      label: "Experience & projects",
      value:
        [profile.experience, profile.projects].filter((v) => v.trim()).length *
        50,
    },
  ];

  return (
    <div className="command-center">
      <div className="dashboard-welcome">
        <div>
          <div className="eyebrow">
            <span className="eyebrow-line" /> YOUR PERSONAL CAREER OS
          </div>
          <h1>
            Your next chapter starts here
            {profile.name ? `, ${profile.name.split(" ")[0]}` : ""}
            <span className="heading-dot">.</span>
          </h1>
          <p>
            {profile.role
              ? `A little more progress toward ${profile.role}. You've got this.`
              : "Find your direction. Build your skills. Make your next move."}
          </p>
        </div>
        <Link className="button secondary" to="/profile">
          <Target size={16} />
          {profile.role || "Set your career goal"}
          <ArrowUpRight size={15} />
        </Link>
      </div>

      <div className="overview-tabs">
        <span className="selected">Career overview</span>
        <Link to="/activity">Recent activity</Link>
        <span className="updated">
          <span className="status-dot" />
          {state.demo
            ? "Demo opportunities enabled"
            : "Your workspace, your pace"}
        </span>
      </div>

      <div className="stat-grid dashboard-stats">
        {stats.map((s) => (
          <Link to={s.path} className="stat-card" key={s.label}>
            <div>
              <span className={`metric-icon ${s.tone}`}>
                <s.icon size={18} />
              </span>
              <ArrowUpRight size={15} />
            </div>
            <strong>{s.value.toString().padStart(2, "0")}</strong>
            <h2>{s.label}</h2>
            <p>{s.note}</p>
          </Link>
        ))}
      </div>

      <div className="dashboard-grid dashboard-primary">
        <Card
          className="readiness-card"
          title="A stronger foundation, one step at a time"
          detail="Your profile is the starting point for everything"
          action={<Badge>Profile progress</Badge>}
        >
          <div className="readiness-body">
            <div
              className="score-ring"
              role="img"
              aria-label={`Profile ${score}% complete`}
              style={{ "--score": `${score * 3.6}deg` } as React.CSSProperties}
            >
              <div>
                <strong>
                  {score}
                  <small>%</small>
                </strong>
                <span>PROFILE COMPLETE</span>
              </div>
            </div>
            <div className="readiness-bars">
              {progress.map((item) => (
                <div key={item.label}>
                  <div>
                    <span>{item.label}</span>
                    <strong>{item.value}%</strong>
                  </div>
                  <progress
                    aria-label={item.label}
                    max="100"
                    value={item.value}
                  />
                </div>
              ))}
            </div>
          </div>
          <div className="card-bottom">
            <span>
              <span className="mini-spark">✦</span>
              {score === 100
                ? "Your profile is ready for its next chapter."
                : `${8 - complete} profile sections left. Every detail adds clarity.`}
            </span>
            <Link to="/profile">
              {score === 100 ? "Review profile" : "Complete profile"}
              <ArrowRight size={14} />
            </Link>
          </div>
        </Card>
        <section className="next-move">
          <div className="next-top">
            <span>
              <Sparkles size={16} /> A LITTLE DIRECTION
            </span>
            <span className="next-tag">NEXT STEP</span>
          </div>
          <h2>
            Big ambitions.
            <br />
            Small, steady steps.
          </h2>
          <p>
            {!profile.role
              ? "Start with where you want to go. We’ll help you organize the steps to get there."
              : nextTask
                ? `Make room for your next step: ${nextTask.toLowerCase()}.`
                : "You’ve finished the starter roadmap. Take a moment to review what you’ve built."}
          </p>
          <Link
            to={profile.role ? "/roadmap" : "/onboarding"}
            className="button"
          >
            {profile.role
              ? "Continue your roadmap"
              : "Build your career profile"}
            <ArrowRight size={16} />
          </Link>
          <div className="direction-art" aria-hidden="true">
            <div className="direction-orbit orbit-one" />
            <div className="direction-orbit orbit-two" />
            <span className="direction-star">✦</span>
            <span className="orbit-point" />
          </div>
          <div className="next-foot">
            <span className="status-dot" /> Progress at your own pace.
          </div>
        </section>
      </div>

      <div className="dashboard-grid lower">
        <Card
          className="opportunity-panel"
          title="Your next opportunity"
          detail={
            state.demo
              ? "Fictional sample roles · explore the experience"
              : "Good things start with the right fit"
          }
          action={
            <Link className="text-link" to="/opportunities">
              Explore all
              <ArrowUpRight size={14} />
            </Link>
          }
        >
          {state.demo ? (
            opportunities.slice(0, 2).map((o) => (
              <Link
                to={`/opportunities/${o.id}`}
                className="compact-job"
                key={o.id}
              >
                <span className={`company-logo ${o.color}`}>{o.initial}</span>
                <div>
                  <h3>{o.role}</h3>
                  <p>
                    {o.company}
                    <span>·</span>
                    {o.location}
                  </p>
                  <div className="job-tags">
                    <Badge>{o.type}</Badge>
                    <Badge>{o.mode}</Badge>
                  </div>
                </div>
                <div className="compact-job-end">
                  <Badge tone="orange">Demo</Badge>
                  <ArrowUpRight size={17} />
                </div>
              </Link>
            ))
          ) : (
            <div className="discovery-empty">
              <div className="empty-visual" aria-hidden="true">
                <span className="empty-tile tile-back">
                  <Layers3 size={22} />
                </span>
                <span className="empty-tile tile-front">
                  <BriefcaseBusiness size={25} />
                  <span>
                    <i />
                    <i />
                  </span>
                </span>
                <span className="empty-spark">✦</span>
              </div>
              <h3>A world of possibility. A place to start.</h3>
              <p>
                Add your career direction, explore sample roles, and start
                shaping your shortlist.
              </p>
              <Link to="/opportunities" className="button secondary">
                Explore opportunities
                <ArrowRight size={15} />
              </Link>
            </div>
          )}
          <div className="card-bottom">
            <span>
              <Circle size={11} />
              {state.demo
                ? "Sample listings are for exploration only."
                : "Live opportunity sources are not connected yet."}
            </span>
          </div>
        </Card>
        <Card
          className="compass-panel"
          title="Your skill compass"
          detail="A little focus goes a long way"
          action={
            <span className="panel-icon">
              <Target size={18} />
            </span>
          }
        >
          <div className="skill-compass-label">
            <span>YOUR BUILDING BLOCKS</span>
            <Check size={13} />
          </div>
          <div className="skill-chips">
            {(profile.skills
              ? profile.skills
                  .split(",")
                  .map((s) => s.trim())
                  .filter(Boolean)
              : []
            ).map((s) => (
              <Badge key={s} tone="strength">
                {s}
              </Badge>
            ))}
            {!profile.skills.trim() && (
              <Link className="add-skills" to="/profile">
                <Plus size={13} />
                Add your skills
              </Link>
            )}
          </div>
          <div className="skill-divider" />
          <div className="skill-compass-label">
            <span>GIVE YOURSELF A DIRECTION</span>
            <Flame size={14} className="orange-text" />
          </div>
          {[
            {
              name: profile.role
                ? "Explore your skill gaps"
                : "Choose your target role",
              detail: profile.role || "Start with what interests you",
              path: profile.role ? "/skills" : "/explorer",
            },
            {
              name: "Put your strengths into practice",
              detail: "A roadmap you can work through",
              path: "/roadmap",
            },
          ].map((item, index) => (
            <Link to={item.path} className="skill-focus" key={item.name}>
              <span className="skill-number">0{index + 1}</span>
              <div>
                <strong>{item.name}</strong>
                <small>{item.detail}</small>
              </div>
              <ChevronRight size={15} />
            </Link>
          ))}
        </Card>
      </div>

      <div className="dashboard-grid bottom">
        <Card
          className="journey-panel"
          title="Your path forward"
          detail="A practical starter roadmap for frontend development"
          action={
            <Link className="text-link" to="/roadmap">
              View roadmap
              <ArrowUpRight size={14} />
            </Link>
          }
        >
          <div className="journey-track">
            {milestones.map((milestone, index) => {
              const done = milestone.tasks.every((_, index) =>
                state.completed.includes(`${milestone.id}-${index}`),
              );
              const active = nextMilestone?.id === milestone.id;
              return (
                <Link
                  to="/roadmap"
                  className={`journey-step ${done ? "is-done" : ""} ${active ? "is-current" : ""}`}
                  key={milestone.id}
                >
                  <span className="journey-node">
                    {done ? <Check size={16} /> : index + 1}
                  </span>
                  <strong>
                    {
                      [
                        "The foundation",
                        "Build your skills",
                        "Make it real",
                        "Your next role",
                      ][index]
                    }
                  </strong>
                  <small>
                    {done
                      ? "COMPLETED"
                      : active
                        ? "YOU ARE HERE"
                        : milestone.time}
                  </small>
                </Link>
              );
            })}
          </div>
          <div className="journey-progress">
            <span>{completed} of 12 tasks complete</span>
            <progress
              aria-label="Roadmap completion"
              max={12}
              value={completed}
            />
            <span>{Math.round((completed / 12) * 100)}%</span>
          </div>
        </Card>
        <Card
          className="recent-panel"
          title="Little wins add up"
          detail="Your latest workspace activity"
          action={
            <Link to="/activity" aria-label="View activity">
              <ArrowUpRight size={17} />
            </Link>
          }
        >
          {state.activity.length ? (
            state.activity.slice(0, 3).map((activity, index) => (
              <div className="activity-line" key={`${index}-${activity}`}>
                <span className="activity-icon">
                  <Check size={14} />
                </span>
                <p>{activity}</p>
              </div>
            ))
          ) : (
            <div className="fresh-activity">
              <span className="activity-icon">
                <FileText size={18} />
              </span>
              <div>
                <h3>This is your starting line.</h3>
                <p>
                  Profile updates, learning milestones, and application progress
                  will appear here.
                </p>
                <Link to="/profile" className="text-link">
                  Make your first move
                  <ArrowRight size={13} />
                </Link>
              </div>
            </div>
          )}
        </Card>
      </div>
      <Link to="/coach" className="coach-banner">
        <span className="coach-symbol">
          <Sparkles size={23} />
        </span>
        <div>
          <h3>A space to think about what’s next.</h3>
          <p>Organize your career questions in the coach workspace.</p>
        </div>
        <span className="coach-availability">AI service not connected</span>
        <span className="button secondary">
          Open coach
          <ArrowUpRight size={15} />
        </span>
      </Link>
      <div className="dashboard-endnote">
        <Route size={13} />
        <span>
          Your career is a journey. You don’t have to map it all today.
        </span>
      </div>
    </div>
  );
}
