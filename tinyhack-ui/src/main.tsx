import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import { Provider } from "./lib/store";
import Layout from "./components/Layout";
import Overview from "./pages/Overview";
import Profile, { Onboarding } from "./pages/Profile";
import {
  OpportunityDetail,
  Companies,
} from "./pages/Discovery";
import { Skills, Roadmap, Resume, Interview } from "./pages/Development";
import { Applications } from "./pages/Execution";
import LiveCoach from "./pages/Coach";
import CareerExplorer from "./pages/CareerExplorer";
import LiveOpportunities from "./pages/LiveOpportunities";
import LiveMonitor from "./pages/LiveMonitor";
import {
  Notifications,
  ActivityPage,
  Settings,
  Help,
  Auth,
} from "./pages/System";
import "./styles.css";
import "./refinements.css";
ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <Provider>
      <BrowserRouter>
        <Routes>
          <Route path="/auth/:mode" element={<Auth />} />
          <Route element={<Layout />}>
            <Route index element={<Overview />} />
            <Route path="profile" element={<Profile />} />
            <Route path="onboarding" element={<Onboarding />} />
            <Route path="explorer" element={<CareerExplorer />} />
            <Route path="opportunities" element={<LiveOpportunities />} />
            <Route path="opportunities/:id" element={<OpportunityDetail />} />
            <Route path="companies" element={<Companies />} />
            <Route path="skills" element={<Skills />} />
            <Route path="roadmap" element={<Roadmap />} />
            <Route path="resume" element={<Resume />} />
            <Route path="interview" element={<Interview />} />
            <Route path="applications" element={<Applications />} />
            <Route path="monitor" element={<LiveMonitor />} />
            <Route path="coach" element={<LiveCoach />} />
            <Route path="notifications" element={<Notifications />} />
            <Route path="activity" element={<ActivityPage />} />
            <Route path="settings" element={<Settings />} />
            <Route path="help" element={<Help />} />
            <Route
              path="*"
              element={
                <div className="empty">
                  <h1>This page took a different path.</h1>
                  <Link className="button" to="/">
                    Back to overview
                  </Link>
                </div>
              }
            />
          </Route>
        </Routes>
      </BrowserRouter>
    </Provider>
  </React.StrictMode>,
);
