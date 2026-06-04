import { useEffect, useState } from 'react';
import type { Trip } from '../data/types';
import { getTrips } from '../api/client';
import { adaptTripSummary } from '../api/adapters';

interface UseTripsResult {
  trips: Trip[];
  loading: boolean;
  error: string | null;
}

export function useTrips(): UseTripsResult {
  const [trips, setTrips] = useState<Trip[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    getTrips()
      .then((data) => {
        if (!cancelled) {
          setTrips(data.map(adaptTripSummary));
          setError(null);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load trips.');
          setTrips([]);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return { trips, loading, error };
}
