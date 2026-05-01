import type { EffectiveStopStatus, Stop, Region, Trip } from '../data/types';
import { REGIONS } from '../data/regions';

export interface RegionGroup {
  region: Region;
  stops: Stop[];
  startDate: string;
  endDate: string;
  overallStatus: 'visited' | 'planned' | 'mixed' | 'abandoned';
}

// FR-028: today as YYYY-MM-DD in UTC, so abandoned classification is
// identical for every visitor regardless of their local timezone. Cached per
// module load — stale-by-a-day at worst, which is acceptable for a static
// travelogue.
const TODAY_ISO = new Date().toISOString().slice(0, 10);

// FR-028: derive the effective status of a single stop. Stops authored as
// "visited" are never reclassified; planned stops whose date has passed
// become "abandoned".
export function getEffectiveStopStatus(stop: Stop): EffectiveStopStatus {
  if (stop.status === 'planned' && stop.date < TODAY_ISO) return 'abandoned';
  return stop.status;
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
    // FR-029: classify each stop by its effective status, then roll up to the
    // region. A region is "abandoned" only if every stop is abandoned;
    // otherwise abandoned stops are ignored when choosing visited/planned/mixed.
    const effective = sorted.map(getEffectiveStopStatus);
    const allAbandoned = effective.every((s) => s === 'abandoned');
    let overallStatus: RegionGroup['overallStatus'];
    if (allAbandoned) {
      overallStatus = 'abandoned';
    } else {
      const hasVisited = effective.some((s) => s === 'visited');
      const hasPlanned = effective.some((s) => s === 'planned');
      overallStatus = hasVisited && hasPlanned ? 'mixed' : hasVisited ? 'visited' : 'planned';
    }

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

  // Apply FR-014: end date is the later of last stop date or day before next
  // *non-abandoned* region's start. Abandoned regions are skipped for the
  // "next region" anchor (consistent with FR-030) and themselves get no
  // end-date extension.
  for (let i = 0; i < groups.length; i++) {
    if (groups[i].overallStatus === 'abandoned') continue;
    let nextNonAbandoned: RegionGroup | undefined;
    for (let j = i + 1; j < groups.length; j++) {
      if (groups[j].overallStatus !== 'abandoned') {
        nextNonAbandoned = groups[j];
        break;
      }
    }
    if (!nextNonAbandoned) continue;
    const nextStart = new Date(nextNonAbandoned.startDate);
    nextStart.setDate(nextStart.getDate() - 1);
    const dayBeforeNext = nextStart.toISOString().split('T')[0];
    if (dayBeforeNext > groups[i].endDate) {
      groups[i] = { ...groups[i], endDate: dayBeforeNext };
    }
  }

  return groups;
}

// FR-011: Last region in sequence with at least one visited stop.
// Returns null if no region is mixed (i.e. no transition between visited and
// planned/abandoned exists for the visitor to anchor on).
export function getActiveRegion(groups: RegionGroup[]): RegionGroup | null {
  const hasAnyVisited = groups.some((g) => g.overallStatus === 'visited' || g.overallStatus === 'mixed');
  const hasAnyNonVisited = groups.some((g) => g.overallStatus !== 'visited');

  if (!hasAnyVisited || !hasAnyNonVisited) return null;

  let active: RegionGroup | null = null;
  for (const group of groups) {
    if (group.stops.some((s) => s.status === 'visited')) {
      active = group;
    }
  }
  return active;
}

// FR-030: only non-abandoned regions participate in the route polyline.
export function getRoutedGroups(groups: RegionGroup[]): RegionGroup[] {
  return groups.filter((g) => g.overallStatus !== 'abandoned');
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
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
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
