import type { Stop, Region, Trip } from '../data/types';
import { REGIONS } from '../data/regions';

export interface RegionGroup {
  region: Region;
  stops: Stop[];
  startDate: string;
  endDate: string;
  overallStatus: 'visited' | 'planned' | 'mixed';
}

export function equirectangularProject(coords: { lat: number; lng: number }) {
  const x = ((coords.lng + 180) / 360) * 100;
  const y = ((90 - coords.lat) / 180) * 100;
  return { x, y };
}

export function groupStopsByRegion(trip: Trip): RegionGroup[] {
  const groupMap = new Map<string, Stop[]>();

  for (const stop of trip.stops) {
    if (!groupMap.has(stop.regionCode)) {
      groupMap.set(stop.regionCode, []);
    }
    groupMap.get(stop.regionCode)!.push(stop);
  }

  const groups: RegionGroup[] = [];

  for (const [code, stops] of groupMap) {
    const region = REGIONS.find((r) => r.code === code);
    if (!region) continue;

    const sorted = [...stops].sort((a, b) => a.date.localeCompare(b.date));
    const hasVisited = sorted.some((s) => s.status === 'visited');
    const hasPlanned = sorted.some((s) => s.status === 'planned');
    const overallStatus = hasVisited && hasPlanned ? 'mixed' : hasVisited ? 'visited' : 'planned';

    groups.push({
      region,
      stops: sorted,
      startDate: sorted[0].date,
      endDate: sorted[sorted.length - 1].date,
      overallStatus,
    });
  }

  // Sort groups by first stop date
  groups.sort((a, b) => a.startDate.localeCompare(b.startDate));

  // Apply FR-014: end date is the later of last stop date or day before next region's start
  for (let i = 0; i < groups.length - 1; i++) {
    const nextStart = new Date(groups[i + 1].startDate);
    nextStart.setDate(nextStart.getDate() - 1);
    const dayBeforeNext = nextStart.toISOString().split('T')[0];
    if (dayBeforeNext > groups[i].endDate) {
      groups[i] = { ...groups[i], endDate: dayBeforeNext };
    }
  }

  return groups;
}

// FR-011: Last region in sequence with at least one visited stop.
// Returns null if all regions share the same status (all visited or all planned).
export function getActiveRegion(groups: RegionGroup[]): RegionGroup | null {
  const hasAnyVisited = groups.some((g) => g.overallStatus !== 'planned');
  const hasAnyPlanned = groups.some((g) => g.overallStatus !== 'visited');

  if (!hasAnyVisited || !hasAnyPlanned) return null;

  let active: RegionGroup | null = null;
  for (const group of groups) {
    if (group.stops.some((s) => s.status === 'visited')) {
      active = group;
    }
  }
  return active;
}

// FR-012: Segment is solid if either adjacent region has at least one visited stop.
export function isSegmentSolid(from: RegionGroup, to: RegionGroup): boolean {
  return (
    from.stops.some((s) => s.status === 'visited') ||
    to.stops.some((s) => s.status === 'visited')
  );
}

export function formatDateRange(startDate: string, endDate: string): string {
  const fmt = (d: string) => {
    const date = new Date(d + 'T00:00:00');
    return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
  };
  const start = fmt(startDate);
  const end = fmt(endDate);
  return start === end ? start : `${start} – ${end}`;
}

export function formatDate(date: string): string {
  return new Date(date + 'T00:00:00').toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

export { REGIONS };
