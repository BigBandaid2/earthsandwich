import { useEffect, useState } from 'react';
import type { Stop } from '../data/types';

export function usePosts(): Stop[] {
  const [stops, setStops] = useState<Stop[]>([]);

  useEffect(() => {
    fetch('/posts.json')
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((data: Stop[]) => setStops(data))
      .catch(() => {});
  }, []);

  return stops;
}
