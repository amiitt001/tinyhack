import { useEffect, useRef, useState } from "react";
import {
  NavLink,
  Outlet,
  Link,
  useNavigate,
  useLocation,
} from "react-router-dom";
import {
  LayoutDashboard,
  UserRound,
  Compass,
  BriefcaseBusiness,
  Building2,
  ChartNoAxesCombined,
  Route,
  FileText,
  Mic,
  Columns3,
  Radar,
  Sparkles,
  Bell,
  Settings,
  CircleHelp,
  Search,
  PanelLeftClose,
  Menu,
  X,
  ChevronDown,
  ArrowUpRight,
  Command,
  Plus,
  LogOut,
  MoreHorizontal,
} from "lucide-react";
import { useApp } from "../lib/store";
import { Modal } from "./ui";
export const groups = [
  {
    name: "WORKSPACE",
    items: [
      ["Overview", "/", LayoutDashboard],
      ["My Career Profile", "/profile", UserRound],
      ["Career Explorer", "/explorer", Compass],
      ["Opportunities", "/opportunities", BriefcaseBusiness],
      ["Company Intelligence", "/companies", Building2],
    ],
  },
  {
    name: "DEVELOP",
    items: [
      ["Skill Gap Analysis", "/skills", ChartNoAxesCombined],
      ["Learning Roadmap", "/roadmap", Route],
      ["Resume Studio", "/resume", FileText],
      ["Interview Lab", "/interview", Mic],
    ],
  },
  {
    name: "EXECUTE",
    items: [
      ["Applications", "/applications", Columns3],
      ["Career Monitor", "/monitor", Radar],
      ["AI Career Coach", "/coach", Sparkles],
    ],
  },
] as const;
export function Logo() {
  return (
    <Link to="/" className="logo">
      <span className="logo-mark">
        <svg
          className="logo-symbol"
          viewBox="0 0 32 32"
          fill="none"
          aria-hidden="true"
        >
          <path
            d="M25 13a10 10 0 1 0-6 12M21 7l4-4M7 25l-3 3"
            stroke="currentColor"
            strokeWidth="3"
            strokeLinecap="round"
          />
          <path
            d="m16 9 3 7-3 7-3-7 3-7Z"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
          />
        </svg>
      </span>
      <span>
        SkillSphere<span className="version">V3</span>
      </span>
    </Link>
  );
}
export default function Layout() {
  const { state, update } = useApp();
  const [mobile, setMobile] = useState(false),
    [collapsed, setCollapsed] = useState(false),
    [search, setSearch] = useState(false),
    [query, setQuery] = useState(""),
    [user, setUser] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const mobileTrigger = useRef<HTMLButtonElement | null>(null);
  const sidebarRef = useRef<HTMLElement>(null);
  const workspaceRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const media = window.matchMedia("(max-width: 760px)");
    const sync = () => {
      if (sidebarRef.current)
        sidebarRef.current.inert = media.matches && !mobile;
      if (workspaceRef.current)
        workspaceRef.current.inert = media.matches && mobile;
    };
    sync();
    media.addEventListener("change", sync);
    return () => media.removeEventListener("change", sync);
  }, [mobile]);
  useEffect(() => {
    if (!mobile) return;
    const previous =
      mobileTrigger.current ||
      document.querySelector<HTMLElement>(
        'button[aria-label="Open navigation"]',
      );
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    sidebarRef.current
      ?.querySelector<HTMLElement>('button[aria-label="Close navigation"]')
      ?.focus();
    const trap = (event: KeyboardEvent) => {
      if (event.key !== "Tab") return;
      const items = Array.from(
        sidebarRef.current?.querySelectorAll<HTMLElement>("a[href],button") ||
          [],
      ).filter((item) => item.getClientRects().length);
      const first = items[0],
        last = items.at(-1);
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last?.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first?.focus();
      }
    };
    document.addEventListener("keydown", trap);
    return () => {
      document.body.style.overflow = overflow;
      document.removeEventListener("keydown", trap);
      if (workspaceRef.current) workspaceRef.current.inert = false;
      previous?.focus();
    };
  }, [mobile]);
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setSearch((v) => !v);
      }
      if (e.key === "Escape") {
        setMobile(false);
        setUser(false);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);
  const links = [
    ...groups.flatMap((g) => g.items.map(([name, path]) => ({ name, path }))),
    { name: "Settings", path: "/settings" },
    { name: "Notifications", path: "/notifications" },
    { name: "Activity & Automation", path: "/activity" },
    { name: "Help & Support", path: "/help" },
  ];
  return (
    <div className={`app ${collapsed ? "collapsed" : ""}`}>
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      {mobile && (
        <div className="drawer-shade" onClick={() => setMobile(false)} />
      )}
      <aside
        id="workspace-navigation"
        ref={sidebarRef}
        className={`sidebar ${mobile ? "mobile-open" : ""}`}
      >
        <div className="sidebar-brand">
          <Logo />
          <button
            className="icon-button mobile-only"
            onClick={() => setMobile(false)}
            aria-label="Close navigation"
          >
            <X size={20} />
          </button>
        </div>
        <button
          className="workspace-picker"
          onClick={() => navigate("/profile")}
        >
          <span className="workspace-avatar">
            {state.profile.name?.[0] || "Y"}
          </span>
          <span>
            Personal workspace<small>Your next chapter starts here</small>
          </span>
          <ChevronDown size={14} />
        </button>
        <nav aria-label="Main navigation">
          {groups.map((g) => (
            <div className="nav-group" key={g.name}>
              <div className="nav-label">{g.name}</div>
              {g.items.map(([name, path, Icon]) => (
                <NavLink
                  end={path === "/"}
                  title={name}
                  key={path}
                  to={path}
                  onClick={() => setMobile(false)}
                >
                  <Icon size={18} />
                  <span>{name}</span>
                  {name === "Opportunities" && state.demo && (
                    <small className="nav-count">3</small>
                  )}
                  {name === "AI Career Coach" && (
                    <span className="tiny-new">AI</span>
                  )}
                </NavLink>
              ))}
            </div>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="sidebar-promo">
            <span className="promo-icon">
              <Sparkles size={18} />
            </span>
            <strong>Your next move, clearer.</strong>
            <p>Build a career that feels like you.</p>
            <Link to="/roadmap">
              Explore your roadmap <ArrowUpRight size={14} />
            </Link>
          </div>
          <NavLink to="/settings">
            <Settings size={18} />
            <span>Settings</span>
          </NavLink>
          <NavLink to="/help">
            <CircleHelp size={18} />
            <span>Help & Support</span>
            <ArrowUpRight size={14} />
          </NavLink>
          <button
            className="collapse-button"
            onClick={() => setCollapsed(!collapsed)}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            <PanelLeftClose size={17} />
            <span>Collapse sidebar</span>
          </button>
        </div>
      </aside>
      <div className="workspace-main" ref={workspaceRef}>
        <header className="topbar">
          <div className="breadcrumb">
            <button
              className="icon-button mobile-only"
              onClick={(event) => {
                mobileTrigger.current = event.currentTarget;
                setMobile(true);
              }}
              aria-label="Open navigation"
              aria-expanded={mobile}
              aria-controls="workspace-navigation"
            >
              <Menu size={20} />
            </button>
            <span>Workspace</span>
            <span>/</span>
            <strong>
              {links.find((l) => l.path === location.pathname)?.name ||
                "Career workspace"}
            </strong>
          </div>
          <div className="top-actions">
            <button
              className="search-trigger"
              aria-label="Search anything"
              onClick={() => setSearch(true)}
            >
              <Search size={16} />
              <span>Search anything...</span>
              <kbd>⌘ K</kbd>
            </button>
            <button
              className="icon-button notification-dot"
              onClick={() => navigate("/notifications")}
              aria-label="Notifications"
            >
              <Bell size={19} />
              {state.notices.some((n) => !n.read) && <i />}
            </button>
            <div className="user-menu">
              <button
                className="avatar"
                aria-label="User menu"
                aria-expanded={user}
                onClick={() => setUser(!user)}
              >
                {state.profile.name?.slice(0, 2).toUpperCase() || "YO"}
              </button>
              {user && (
                <div className="dropdown">
                  <Link to="/profile" onClick={() => setUser(false)}>
                    My profile
                  </Link>
                  <Link to="/settings" onClick={() => setUser(false)}>
                    Account settings
                  </Link>
                  <Link to="/auth/sign-in" onClick={() => setUser(false)}>
                    <LogOut size={15} />
                    Sign in
                  </Link>
                </div>
              )}
            </div>
          </div>
        </header>
        <div className="demo-strip">
          <span>
            <span
              className={`status-dot ${state.backendError ? "is-offline" : ""}`}
            />{" "}
            {state.backendLoading
              ? "Connecting to workspace"
              : state.backendError
                ? "Local workspace"
                : "Workspace connected"}{" "}
            <span className="strip-extra">
              ·{" "}
              {state.backendError
                ? "Backend unavailable"
                : "Profile and resume API"}
            </span>
          </span>
          <button onClick={() => update({ demo: !state.demo })}>
            {state.demo ? "Hide demo content" : "Explore demo content"}{" "}
            <ArrowUpRight size={13} />
          </button>
        </div>
        <main id="main" tabIndex={-1}>
          <Outlet />
        </main>
        <footer className="app-footer">
          <span>
            SkillSphere V3 <span>·</span> A little direction. A lot of
            possibility.
          </span>
          <Link to="/help">
            Help & feedback <ArrowUpRight size={12} />
          </Link>
        </footer>
        <nav className="mobile-bottom-nav" aria-label="Quick navigation">
          <NavLink end to="/">
            <LayoutDashboard size={19} />
            <span>Overview</span>
          </NavLink>
          <NavLink to="/opportunities">
            <Compass size={19} />
            <span>Discover</span>
          </NavLink>
          <NavLink to="/roadmap">
            <Route size={19} />
            <span>Roadmap</span>
          </NavLink>
          <NavLink to="/applications">
            <Columns3 size={19} />
            <span>Applications</span>
          </NavLink>
          <button
            onClick={(event) => {
              mobileTrigger.current = event.currentTarget;
              setMobile(true);
            }}
            aria-expanded={mobile}
            aria-controls="workspace-navigation"
            aria-label="More navigation"
          >
            <MoreHorizontal size={20} />
            <span>More</span>
          </button>
        </nav>
      </div>
      {search && (
        <Modal title="Jump to your next move" onClose={() => setSearch(false)}>
          <div className="search-field">
            <Search size={18} />
            <input
              autoFocus
              placeholder="Search pages and tools…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            <Command size={16} />
          </div>
          {!query && (
            <div className="command-quick-actions">
              <span className="eyebrow">QUICK ACTIONS</span>
              <button
                onClick={() => {
                  navigate("/applications?add=1");
                  setSearch(false);
                }}
              >
                <Plus size={16} />
                Add an application<span>Local tracker</span>
              </button>
              <button
                onClick={() => {
                  navigate("/resume");
                  setSearch(false);
                }}
              >
                <FileText size={16} />
                Continue your resume<span>Resume Studio</span>
              </button>
            </div>
          )}
          <div className="search-results">
            {links
              .filter((l) => l.name.toLowerCase().includes(query.toLowerCase()))
              .map((l) => (
                <button
                  key={l.path}
                  onClick={() => {
                    navigate(l.path);
                    setSearch(false);
                    setQuery("");
                  }}
                >
                  {l.name}
                  <ArrowUpRight size={15} />
                </button>
              ))}
            {links.filter((l) =>
              l.name.toLowerCase().includes(query.toLowerCase()),
            ).length === 0 && (
              <p>No pages found. Try “resume” or “opportunities”.</p>
            )}
          </div>
        </Modal>
      )}
    </div>
  );
}
export function QuickAction() {
  return (
    <Link className="button" to="/applications?add=1">
      <Plus size={16} />
      Add application
    </Link>
  );
}
