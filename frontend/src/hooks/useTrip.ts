import { useEffect, useState } from 'react';
import type { Trip } from '../data/types';
import { getTripDetail } from '../api/client';
import { adaptTrip } from '../api/adapters';
import { withRetry } from '../utils/retry';

interface UseTripResult {
  trip: Trip | null;
  loading: boolean;
  error: string | null;
}

export function useTrip(tripId: string | null): UseTripResult {
  const [trip, setTrip] = useState<Trip | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (tripId === null) return;
    let cancelled = false;
    setLoading(true);
    withRetry(() => getTripDetail(tripId))
      .then((data) => {
        if (!cancelled) {
          setTrip(adaptTrip(data));
          setError(null);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load trip.');
          setTrip(null);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [tripId]);

  return { trip, loading, error };
}
