// hooks/useLimits.ts
import { useCallback, useEffect, useState } from "react";
import { getLimits, upgradeSession, ApiError } from "../lib/api";
import type { SessionLimitsResponse } from "../lib/api";

type UseLimitsOpts = { enabled?: boolean };

export function useLimits(opts?: UseLimitsOpts) {
  const [tier, setTier] = useState<string>("anonymous");
  const [limits, setLimits] = useState<SessionLimitsResponse["limits"] | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const [upgrading, setUpgrading] = useState(false);
  const [upgradeError, setUpgradeError] = useState<string | null>(null);

  const fetchLimits = useCallback(async () => {
    if (opts?.enabled === false) return;     // gated
    setLoading(true);
    setError(null);
    try {
      const r = await getLimits();           // header carries X-Session-Id
      setTier(r.tier || "anonymous");
      setLimits(r.limits || null);
    } catch (e: any) {
      const msg =
        e instanceof ApiError ? `${e.status} – ${e.bodyText || e.message}` : (e?.message || "Failed to fetch limits");
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [opts?.enabled]);

  useEffect(() => {
    if (opts?.enabled) fetchLimits();
  }, [opts?.enabled, fetchLimits]);

  const refresh = useCallback(() => { void fetchLimits(); }, [fetchLimits]);

  const upgrade = useCallback(async (accessKey: string): Promise<boolean> => {
    setUpgrading(true);
    setUpgradeError(null);
    try {
      const r= await upgradeSession(accessKey);  // server updates session/tier
      setTier(r.tier);
      await fetchLimits(); 
      if (r.limits) setLimits(r.limits);
      return true;
                  
    } catch (e: any) {
      setUpgradeError(e?.message || "Upgrade failed");
      return false;
    } finally {
      setUpgrading(false);
    }
  }, [fetchLimits]);

  return {
    tier,
    limits,
    loading,
    error,
    refresh,
    upgrade,
    upgrading,
    upgradeError,
    setUpgradeError,
  };
}
