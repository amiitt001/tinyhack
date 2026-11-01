import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError } from "../lib/api";
import {
  activeRun,
  createDiscovery,
  fetchDiscovery,
  fetchResults,
  fetchSaved,
  fetchSources,
  setOpportunitySaved,
  validId,
  type DiscoveryInput,
  type DiscoveryRun,
  type OpportunityPage,
  type Source,
} from "../lib/opportunities";

export const errorMessage = (error: unknown) =>
  error instanceof ApiError && error.status === 401
    ? "Your session has expired. Sign in to continue."
    : error instanceof Error
      ? error.message
      : "Something went wrong. Please try again.";
const emptyPage: OpportunityPage = {
  items: [],
  total: 0,
  limit: 6,
  offset: 0,
  has_more: false,
};

export function useOpportunityDiscovery({
  demo,
  runId,
  savedView,
  offset,
  onCreated,
}: {
  demo: boolean;
  runId: string;
  savedView: boolean;
  offset: number;
  onCreated: (run: DiscoveryRun) => void;
}) {
  const [sources, setSources] = useState<Source[]>([]);
  const [sourcesLoading, setSourcesLoading] = useState(true);
  const [sourceError, setSourceError] = useState("");
  const [sourceVersion, setSourceVersion] = useState(0);
  const [run, setRun] = useState<DiscoveryRun | null>(null);
  const [runLoading, setRunLoading] = useState(false);
  const [runError, setRunError] = useState("");
  const [runVersion, setRunVersion] = useState(0);
  const [page, setPage] = useState<OpportunityPage>(emptyPage);
  const [pageLoading, setPageLoading] = useState(false);
  const [pageError, setPageError] = useState("");
  const [pageVersion, setPageVersion] = useState(0);
  const [savedIds, setSavedIds] = useState<Set<string>>(new Set());
  const [savedTotal, setSavedTotal] = useState<number | null>(null);
  const [savingIds, setSavingIds] = useState<Set<string>>(new Set());
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");
  const keyRef = useRef<{ signature: string; key: string } | null>(null);
  const submittingRef = useRef(false);
  const mounted = useRef(true);
  const submitController = useRef<AbortController | null>(null);
  const dataKey = useRef("");
  const mutationEpoch = useRef(0);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      submitController.current?.abort();
    };
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    if (demo) {
      setSourcesLoading(false);
      return () => controller.abort();
    }
    setSourcesLoading(true);
    setSourceError("");
    fetchSources(controller.signal)
      .then(setSources)
      .catch((error) => {
        if (!controller.signal.aborted) {
          setSourceError(errorMessage(error));
          setSources([]);
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setSourcesLoading(false);
      });
    return () => controller.abort();
  }, [demo, sourceVersion]);

  useEffect(() => {
    const controller = new AbortController();
    if (demo) return () => controller.abort();
    const requestedEpoch = mutationEpoch.current;
    fetchSaved(0, 100, controller.signal)
      .then((result) => {
        if (
          controller.signal.aborted ||
          requestedEpoch !== mutationEpoch.current
        )
          return;
        setSavedIds(new Set(result.items.map((job) => job.id)));
        setSavedTotal(result.total);
      })
      .catch(() => {
        if (
          !controller.signal.aborted &&
          requestedEpoch === mutationEpoch.current
        )
          setSavedTotal(null);
      });
    return () => controller.abort();
  }, [demo]);

  useEffect(() => {
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout> | undefined;
    const started = Date.now();
    if (demo || !runId) {
      setRun(null);
      setRunError("");
      setRunLoading(false);
      return () => controller.abort();
    }
    if (!validId(runId)) {
      setRun(null);
      setRunLoading(false);
      setRunError("This discovery link is invalid. Start a new search.");
      return () => controller.abort();
    }
    setRun((current) => (current?.id === runId ? current : null));
    setRunLoading(true);
    setRunError("");
    async function poll() {
      if (controller.signal.aborted) return;
      if (document.hidden) {
        timer = setTimeout(poll, 1500);
        return;
      }
      try {
        const next = await fetchDiscovery(runId, controller.signal);
        if (controller.signal.aborted) return;
        setRun(next);
        setRunLoading(false);
        if (activeRun(next)) {
          if (Date.now() - started > 300_000)
            setRunError(
              "This search is taking longer than expected. Check its status again; your search will not be submitted twice.",
            );
          else timer = setTimeout(poll, 1500);
        }
      } catch (error) {
        if (!controller.signal.aborted) {
          setRunError(errorMessage(error));
          setRunLoading(false);
        }
      }
    }
    void poll();
    return () => {
      controller.abort();
      if (timer) clearTimeout(timer);
    };
  }, [demo, runId, runVersion]);

  const accepted = run?.accepted_results || 0;
  const terminal = !!run && !activeRun(run);
  useEffect(() => {
    const controller = new AbortController();
    if (demo) {
      setPageLoading(false);
      return () => controller.abort();
    }
    const nextKey = `${savedView ? "saved" : runId}:${offset}`;
    if (dataKey.current !== nextKey) {
      setPage(emptyPage);
      dataKey.current = nextKey;
    }
    if (!savedView && (!runId || !validId(runId))) {
      setPage(emptyPage);
      setPageLoading(false);
      setPageError("");
      return () => controller.abort();
    }
    setPageLoading(true);
    setPageError("");
    const operation = savedView
      ? fetchSaved(offset, 6, controller.signal)
      : fetchResults(runId, offset, controller.signal);
    const requestedEpoch = mutationEpoch.current;
    operation
      .then((result) => {
        if (controller.signal.aborted) return;
        if (savedView && requestedEpoch !== mutationEpoch.current) return;
        setPage(result);
        if (savedView) {
          setSavedTotal(result.total);
          setSavedIds(
            (current) =>
              new Set([...current, ...result.items.map((job) => job.id)]),
          );
        }
      })
      .catch((error) => {
        if (!controller.signal.aborted) setPageError(errorMessage(error));
      })
      .finally(() => {
        if (!controller.signal.aborted) setPageLoading(false);
      });
    return () => controller.abort();
  }, [demo, savedView, runId, offset, accepted, terminal, pageVersion]);

  async function submit(input: DiscoveryInput) {
    if (submittingRef.current) return;
    submittingRef.current = true;
    setSubmitting(true);
    setSubmitError("");
    const signature = JSON.stringify(input);
    if (keyRef.current?.signature !== signature)
      keyRef.current = { signature, key: crypto.randomUUID() };
    const controller = new AbortController();
    submitController.current = controller;
    try {
      const result = await createDiscovery(
        input,
        keyRef.current.key,
        controller.signal,
      );
      if (!mounted.current) return;
      keyRef.current = null;
      setRun(result);
      onCreated(result);
    } catch (error) {
      if (mounted.current && !controller.signal.aborted)
        setSubmitError(errorMessage(error));
    } finally {
      submittingRef.current = false;
      if (mounted.current) setSubmitting(false);
    }
  }

  async function toggleSaved(id: string) {
    if (savingIds.has(id)) return;
    const next = !savedIds.has(id);
    setSavingIds((current) => new Set(current).add(id));
    try {
      await setOpportunitySaved(id, next);
      if (!mounted.current) return;
      setSavedIds((current) => {
        const copy = new Set(current);
        if (next) copy.add(id);
        else copy.delete(id);
        return copy;
      });
      const epoch = ++mutationEpoch.current;
      // Refresh authoritative totals; a POST may be an idempotent save that already existed.
      try {
        const summary = await fetchSaved(0, 1);
        if (mounted.current && epoch === mutationEpoch.current)
          setSavedTotal(summary.total);
      } catch {
        if (mounted.current && epoch === mutationEpoch.current)
          setSavedTotal(null);
      }
      if (mounted.current && savedView) setPageVersion((value) => value + 1);
    } finally {
      if (mounted.current)
        setSavingIds((current) => {
          const copy = new Set(current);
          copy.delete(id);
          return copy;
        });
    }
  }
  const retrySources = useCallback(
    () => setSourceVersion((value) => value + 1),
    [],
  );
  const retryRun = useCallback(() => setRunVersion((value) => value + 1), []);
  const retryPage = useCallback(() => setPageVersion((value) => value + 1), []);
  return {
    sources,
    sourcesLoading,
    sourceError,
    retrySources,
    run,
    runLoading,
    runError,
    retryRun,
    page,
    pageLoading,
    pageError,
    retryPage,
    savedIds,
    savedTotal,
    savingIds,
    toggleSaved,
    submit,
    submitting,
    submitError,
  };
}
