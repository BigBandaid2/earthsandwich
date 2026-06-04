import {
  groupStopsByRegion,
  getEffectiveStopStatus,
  getActiveRegion,
  getRoutedGroups,
  isSegmentSolid,
} from '../../../src/utils/regionUtils';
import type { Stop, Region, Trip } from '../../../src/data/types';
import type { RegionGroup } from '../../../src/utils/regionUtils';

// ── Fixtures ──────────────────────────────────────────────────────────────────

const R_A: Region = { code: 'AAA', name: 'Alpha', airportName: 'Alpha Intl', country: 'AX', coords: { lat: 1, lng: 1 } };
const R_B: Region = { code: 'BBB', name: 'Beta', airportName: 'Beta Intl', country: 'BX', coords: { lat: 2, lng: 2 } };
const R_C: Region = { code: 'CCC', name: 'Gamma', airportName: 'Gamma Intl', country: 'CX', coords: { lat: 3, lng: 3 } };

function makeStop(id: string, overrides: Partial<Stop> = {}): Stop {
  return {
    id,
    date: '2024-06-01',
    location: 'Test Location',
    coords: { lat: 0, lng: 0 },
    status: 'visited',
    regionCode: 'AAA',
    post: { type: 'planned' },
    ...overrides,
  };
}

function makeTrip(stops: Stop[]): Trip {
  return { id: 'trip-1', title: 'Test Trip', description: '', stops };
}

function makeGroup(
  region: Region,
  stops: Stop[],
  overallStatus: RegionGroup['overallStatus'],
  startDate: string,
  endDate: string,
): RegionGroup {
  return { region, stops, overallStatus, startDate, endDate };
}

// ── getEffectiveStopStatus ────────────────────────────────────────────────────

describe('getEffectiveStopStatus', () => {
  it('visited stop is never reclassified', () => {
    const stop = makeStop('s1', { status: 'visited', date: '2020-01-01' });
    expect(getEffectiveStopStatus(stop)).toBe('visited');
  });

  it('planned stop with future date stays planned', () => {
    const stop = makeStop('s1', { status: 'planned', date: '2040-01-01' });
    expect(getEffectiveStopStatus(stop)).toBe('planned');
  });

  it('planned stop with past date becomes abandoned (FR-028)', () => {
    const stop = makeStop('s1', { status: 'planned', date: '2020-01-01' });
    expect(getEffectiveStopStatus(stop)).toBe('abandoned');
  });
});

// ── groupStopsByRegion ────────────────────────────────────────────────────────

describe('groupStopsByRegion', () => {
  it('groups stops by region_code', () => {
    const stops = [
      makeStop('s1', { regionCode: 'AAA', date: '2024-01-01' }),
      makeStop('s2', { regionCode: 'BBB', date: '2024-02-01' }),
      makeStop('s3', { regionCode: 'AAA', date: '2024-01-15' }),
    ];
    const groups = groupStopsByRegion(makeTrip(stops), [R_A, R_B]);
    expect(groups).toHaveLength(2);
    const groupA = groups.find((g) => g.region.code === 'AAA')!;
    expect(groupA.stops).toHaveLength(2);
    expect(groupA.stops.map((s) => s.id)).toContain('s1');
    expect(groupA.stops.map((s) => s.id)).toContain('s3');
  });

  it('skips stops whose region_code has no matching region', () => {
    const stops = [
      makeStop('s1', { regionCode: 'AAA' }),
      makeStop('s2', { regionCode: 'ZZZ' }),
    ];
    const groups = groupStopsByRegion(makeTrip(stops), [R_A]);
    expect(groups).toHaveLength(1);
    expect(groups[0].region.code).toBe('AAA');
  });

  it('derives startDate and endDate from stop dates sorted ascending', () => {
    const stops = [
      makeStop('s1', { regionCode: 'AAA', date: '2024-06-10' }),
      makeStop('s2', { regionCode: 'AAA', date: '2024-06-01' }),
      makeStop('s3', { regionCode: 'AAA', date: '2024-06-20' }),
    ];
    const [group] = groupStopsByRegion(makeTrip(stops), [R_A]);
    expect(group.startDate).toBe('2024-06-01');
    expect(group.endDate).toBe('2024-06-20');
  });

  it('sorts groups chronologically by startDate', () => {
    const stops = [
      makeStop('s1', { regionCode: 'BBB', date: '2024-03-01' }),
      makeStop('s2', { regionCode: 'AAA', date: '2024-01-01' }),
    ];
    const groups = groupStopsByRegion(makeTrip(stops), [R_A, R_B]);
    expect(groups[0].region.code).toBe('AAA');
    expect(groups[1].region.code).toBe('BBB');
  });

  // ── overallStatus rollup (FR-029) ──────────────────────────────────────────

  it('overallStatus is visited when all stops are visited', () => {
    const stops = [makeStop('s1', { status: 'visited', date: '2024-06-01' })];
    const [group] = groupStopsByRegion(makeTrip(stops), [R_A]);
    expect(group.overallStatus).toBe('visited');
  });

  it('overallStatus is planned when all non-abandoned stops are planned', () => {
    const stops = [makeStop('s1', { status: 'planned', date: '2040-01-01' })];
    const [group] = groupStopsByRegion(makeTrip(stops), [R_A]);
    expect(group.overallStatus).toBe('planned');
  });

  it('overallStatus is mixed when visited and planned stops coexist', () => {
    const stops = [
      makeStop('s1', { status: 'visited', date: '2024-06-01' }),
      makeStop('s2', { status: 'planned', date: '2040-01-01' }),
    ];
    const [group] = groupStopsByRegion(makeTrip(stops), [R_A]);
    expect(group.overallStatus).toBe('mixed');
  });

  it('overallStatus is abandoned when all planned stops have past dates (FR-028)', () => {
    const stops = [
      makeStop('s1', { status: 'planned', date: '2020-01-01' }),
      makeStop('s2', { status: 'planned', date: '2020-06-01' }),
    ];
    const [group] = groupStopsByRegion(makeTrip(stops), [R_A]);
    expect(group.overallStatus).toBe('abandoned');
  });

  it('visited stops in a mixed-abandoned region are not demoted (FR-029)', () => {
    const stops = [
      makeStop('s1', { status: 'visited', date: '2024-01-01' }),
      makeStop('s2', { status: 'planned', date: '2020-01-01' }),
    ];
    const [group] = groupStopsByRegion(makeTrip(stops), [R_A]);
    expect(group.overallStatus).toBe('visited');
  });

  // ── FR-033: Substack date exclusion ───────────────────────────────────────

  it('FR-033: excludes Substack stop dates when non-Substack stops exist', () => {
    const stops = [
      makeStop('s1', { regionCode: 'AAA', date: '2024-06-01', post: { type: 'planned' } }),
      makeStop('s2', {
        regionCode: 'AAA',
        date: '2024-12-31',
        post: { type: 'substack', title: 'Post', body: 'Body' },
      }),
    ];
    const [group] = groupStopsByRegion(makeTrip(stops), [R_A]);
    expect(group.startDate).toBe('2024-06-01');
    expect(group.endDate).toBe('2024-06-01');
  });

  it('FR-033: uses all stop dates when region is Substack-only', () => {
    const stops = [
      makeStop('s1', {
        regionCode: 'AAA',
        date: '2024-01-01',
        post: { type: 'substack', title: 'A', body: 'B' },
      }),
      makeStop('s2', {
        regionCode: 'AAA',
        date: '2024-06-30',
        post: { type: 'substack', title: 'C', body: 'D' },
      }),
    ];
    const [group] = groupStopsByRegion(makeTrip(stops), [R_A]);
    expect(group.startDate).toBe('2024-01-01');
    expect(group.endDate).toBe('2024-06-30');
  });

  // ── FR-014: endDate extension ──────────────────────────────────────────────

  it('FR-014: extends endDate to day before next non-abandoned region starts', () => {
    const stops = [
      makeStop('s1', { regionCode: 'AAA', date: '2024-06-01', status: 'visited' }),
      makeStop('s2', { regionCode: 'BBB', date: '2024-06-15', status: 'visited' }),
    ];
    const groups = groupStopsByRegion(makeTrip(stops), [R_A, R_B]);
    const groupA = groups.find((g) => g.region.code === 'AAA')!;
    // Day before BBB starts (2024-06-15) → 2024-06-14
    expect(groupA.endDate).toBe('2024-06-14');
  });

  it('FR-014: does not extend endDate when last stop date already meets the day-before-next boundary', () => {
    // AAA ends on 2024-06-14; BBB starts 2024-06-15 (day before = 2024-06-14)
    // dayBeforeNext (2024-06-14) is NOT strictly greater than endDate (2024-06-14) → no extension
    const stops = [
      makeStop('s1', { regionCode: 'AAA', date: '2024-06-01', status: 'visited' }),
      makeStop('s2', { regionCode: 'AAA', date: '2024-06-14', status: 'visited' }),
      makeStop('s3', { regionCode: 'BBB', date: '2024-06-15', status: 'visited' }),
    ];
    const groups = groupStopsByRegion(makeTrip(stops), [R_A, R_B]);
    const groupA = groups.find((g) => g.region.code === 'AAA')!;
    expect(groupA.endDate).toBe('2024-06-14');
  });

  it('FR-014: abandoned regions are skipped as the next-region anchor', () => {
    const stops = [
      makeStop('s1', { regionCode: 'AAA', date: '2024-06-01', status: 'visited' }),
      makeStop('s2', { regionCode: 'BBB', date: '2020-01-01', status: 'planned' }),
      makeStop('s3', { regionCode: 'CCC', date: '2024-07-01', status: 'visited' }),
    ];
    const groups = groupStopsByRegion(makeTrip(stops), [R_A, R_B, R_C]);
    const groupA = groups.find((g) => g.region.code === 'AAA')!;
    // BBB is abandoned (planned + past date); next non-abandoned is CCC (2024-07-01)
    // Day before CCC starts → 2024-06-30
    expect(groupA.endDate).toBe('2024-06-30');
  });

  it('FR-014: abandoned region itself gets no endDate extension', () => {
    const stops = [
      makeStop('s1', { regionCode: 'AAA', date: '2020-01-01', status: 'planned' }),
      makeStop('s2', { regionCode: 'BBB', date: '2024-06-01', status: 'visited' }),
    ];
    const groups = groupStopsByRegion(makeTrip(stops), [R_A, R_B]);
    const groupA = groups.find((g) => g.region.code === 'AAA')!;
    expect(groupA.overallStatus).toBe('abandoned');
    expect(groupA.endDate).toBe('2020-01-01');
  });
});

// ── getActiveRegion ───────────────────────────────────────────────────────────

describe('getActiveRegion', () => {
  it('returns the last group that has a visited stop when a boundary exists', () => {
    const visitedStop = makeStop('s1', { status: 'visited' });
    const plannedStop = makeStop('s2', { status: 'planned' });
    const groups = [
      makeGroup(R_A, [visitedStop], 'visited', '2024-01-01', '2024-02-28'),
      makeGroup(R_B, [plannedStop], 'planned', '2024-03-01', '2024-03-31'),
    ];
    expect(getActiveRegion(groups)?.region.code).toBe('AAA');
  });

  it('returns the LAST visited group when multiple have visited stops', () => {
    const visitedA = makeStop('s1', { status: 'visited' });
    const visitedB = makeStop('s2', { status: 'visited' });
    const planned = makeStop('s3', { status: 'planned' });
    const groups = [
      makeGroup(R_A, [visitedA], 'visited', '2024-01-01', '2024-01-31'),
      makeGroup(R_B, [visitedB], 'visited', '2024-02-01', '2024-02-28'),
      makeGroup(R_C, [planned], 'planned', '2024-03-01', '2024-03-31'),
    ];
    expect(getActiveRegion(groups)?.region.code).toBe('BBB');
  });

  it('returns null when all regions are visited (no boundary)', () => {
    const groups = [
      makeGroup(R_A, [makeStop('s1', { status: 'visited' })], 'visited', '2024-01-01', '2024-01-31'),
      makeGroup(R_B, [makeStop('s2', { status: 'visited' })], 'visited', '2024-02-01', '2024-02-28'),
    ];
    expect(getActiveRegion(groups)).toBeNull();
  });

  it('returns null when no regions have visited stops', () => {
    const groups = [
      makeGroup(R_A, [makeStop('s1', { status: 'planned' })], 'planned', '2024-01-01', '2024-01-31'),
    ];
    expect(getActiveRegion(groups)).toBeNull();
  });
});

// ── getRoutedGroups ───────────────────────────────────────────────────────────

describe('getRoutedGroups', () => {
  it('excludes abandoned regions from the route (FR-030)', () => {
    const groups = [
      makeGroup(R_A, [], 'visited', '2024-01-01', '2024-01-31'),
      makeGroup(R_B, [], 'abandoned', '2024-02-01', '2024-02-28'),
      makeGroup(R_C, [], 'planned', '2024-03-01', '2024-03-31'),
    ];
    const routed = getRoutedGroups(groups);
    expect(routed).toHaveLength(2);
    expect(routed.map((g) => g.region.code)).toEqual(['AAA', 'CCC']);
  });

  it('returns all groups when none are abandoned', () => {
    const groups = [
      makeGroup(R_A, [], 'visited', '2024-01-01', '2024-01-31'),
      makeGroup(R_B, [], 'mixed', '2024-02-01', '2024-02-28'),
    ];
    expect(getRoutedGroups(groups)).toHaveLength(2);
  });
});

// ── isSegmentSolid ────────────────────────────────────────────────────────────

describe('isSegmentSolid', () => {
  it('is solid when the from region has a visited stop (FR-012)', () => {
    const from = makeGroup(R_A, [makeStop('s1', { status: 'visited' })], 'visited', '2024-01-01', '2024-01-31');
    const to = makeGroup(R_B, [makeStop('s2', { status: 'planned' })], 'planned', '2024-02-01', '2024-02-28');
    expect(isSegmentSolid(from, to)).toBe(true);
  });

  it('is solid when the to region has a visited stop (FR-012)', () => {
    const from = makeGroup(R_A, [makeStop('s1', { status: 'planned' })], 'planned', '2024-01-01', '2024-01-31');
    const to = makeGroup(R_B, [makeStop('s2', { status: 'visited' })], 'visited', '2024-02-01', '2024-02-28');
    expect(isSegmentSolid(from, to)).toBe(true);
  });

  it('is not solid when neither region has a visited stop', () => {
    const from = makeGroup(R_A, [makeStop('s1', { status: 'planned' })], 'planned', '2024-01-01', '2024-01-31');
    const to = makeGroup(R_B, [makeStop('s2', { status: 'planned' })], 'planned', '2024-02-01', '2024-02-28');
    expect(isSegmentSolid(from, to)).toBe(false);
  });
});
