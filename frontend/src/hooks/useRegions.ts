import { useEffect, useState } from 'react';
import type { Region } from '../data/types';
import { getRegions } from '../api/client';
import { adaptRegion } from '../api/adapters';
import { withRetry } from '../utils/retry';

interface UseRegionsResult {
  regions: Region[];
  loading: boolean;
  error: string | null;
}

export function useRegions(): UseRegionsResult {
  const [regions, setRegions] = useState<Region[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    withRetry(() => getRegions())
      .then((data) => {
        if (!cancelled) {
          setRegions(data.map(adaptRegion));
          setError(null);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load regions.');
          setRegions([]);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return { regions, loading, error };
}
