import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import TripFeed from '../../../src/components/Sidebar';
import { formatDateRange } from '../../../src/utils/regionUtils';
import type { RegionGroup } from '../../../src/utils/regionUtils';
import type { Trip, Region } from '../../../src/data/types';

// ── Fixtures ──────────────────────────────────────────────────────────────────

function makeGroup(
  code: string,
  overallStatus: RegionGroup['overallStatus'],
  overrides: Partial<RegionGroup> = {},
): RegionGroup {
  return {
    region: {
      code,
      name: `City ${code}`,
      airportName: `${code} Airport`,
      country: `Country ${code}`,
      coords: { lat: 0, lng: 0 },
    } satisfies Region,
    stops: [],
    startDate: '2024-01-01',
    endDate: '2024-01-31',
    overallStatus,
    ...overrides,
  };
}

const TRIP: Trip = { id: 'trip-1', title: 'Test Trip', description: '', stops: [] };

function renderFeed(groups: RegionGroup[]) {
  return render(
    <TripFeed
      regionGroups={groups}
      trip={TRIP}
      onExpandRegion={vi.fn()}
      onOpenStop={vi.fn()}
    />,
  );
}

// ── Section visibility and order ──────────────────────────────────────────────

describe('TripFeed sections', () => {
  it('renders Visited → Planned → Abandoned section headings in that order (FR-031)', () => {
    renderFeed([
      makeGroup('AAA', 'visited'),
      makeGroup('BBB', 'planned'),
      makeGroup('CCC', 'abandoned'),
    ]);
    const headings = screen.getAllByRole('heading', { level: 2 });
    expect(headings.map((h) => h.textContent)).toEqual(['Visited', 'Planned', 'Abandoned']);
  });

  it('hides Planned and Abandoned sections when they have no regions', () => {
    renderFeed([makeGroup('AAA', 'visited')]);
    expect(screen.getByRole('heading', { name: 'Visited' })).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Planned' })).not.toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Abandoned' })).not.toBeInTheDocument();
  });

  it('hides Visited and Abandoned sections when only planned regions exist', () => {
    renderFeed([makeGroup('AAA', 'planned')]);
    expect(screen.getByRole('heading', { name: 'Planned' })).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Visited' })).not.toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Abandoned' })).not.toBeInTheDocument();
  });

  it('places mixed-status regions in the Visited section (FR-031)', () => {
    renderFeed([makeGroup('AAA', 'mixed')]);
    const visitedSection = screen.getByRole('heading', { name: 'Visited' }).closest('section')!;
    expect(within(visitedSection).getByText('City AAA')).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Planned' })).not.toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Abandoned' })).not.toBeInTheDocument();
  });
});

// ── Region tile content ───────────────────────────────────────────────────────

describe('RegionTile content', () => {
  it('shows the region name', () => {
    renderFeed([makeGroup('SYD', 'visited')]);
    expect(screen.getByText('City SYD')).toBeInTheDocument();
  });

  it('shows the region country', () => {
    renderFeed([makeGroup('SYD', 'visited')]);
    expect(screen.getByText('Country SYD')).toBeInTheDocument();
  });

  it('shows a formatted date range', () => {
    const startDate = '2024-03-10';
    const endDate = '2024-04-25';
    renderFeed([makeGroup('SYD', 'visited', { startDate, endDate })]);
    expect(screen.getByText(formatDateRange(startDate, endDate))).toBeInTheDocument();
  });

  it('shows a single-date label when startDate equals endDate', () => {
    const date = '2024-06-01';
    renderFeed([makeGroup('SYD', 'visited', { startDate: date, endDate: date })]);
    expect(screen.getByText(formatDateRange(date, date))).toBeInTheDocument();
  });

  it('expand button fires onExpandRegion with the region code', async () => {
    const user = userEvent.setup();
    const onExpand = vi.fn();
    render(
      <TripFeed
        regionGroups={[makeGroup('AAA', 'visited')]}
        trip={TRIP}
        onExpandRegion={onExpand}
        onOpenStop={vi.fn()}
      />,
    );
    await user.click(screen.getByRole('button', { name: /expand/i }));
    expect(onExpand).toHaveBeenCalledWith('AAA');
  });
});

// ── Abandoned tile styling and connector line ─────────────────────────────────

describe('Abandoned region tile (US5 / FR-030)', () => {
  it('renders inside the Abandoned section', () => {
    renderFeed([makeGroup('AAA', 'abandoned')]);
    const abandonedSection = screen.getByRole('heading', { name: 'Abandoned' }).closest('section')!;
    expect(within(abandonedSection).getByText('City AAA')).toBeInTheDocument();
  });

  it('tile has the "abandoned" CSS class', () => {
    const { container } = renderFeed([makeGroup('AAA', 'abandoned')]);
    expect(container.querySelector('.region-tile')).toHaveClass('abandoned');
  });

  it('renders no connector line for a single abandoned tile (FR-030)', () => {
    const { container } = renderFeed([makeGroup('AAA', 'abandoned')]);
    expect(container.querySelector('.connector-line')).toBeNull();
  });

  it('renders no connector line even for non-last abandoned tiles (FR-030)', () => {
    // Two abandoned tiles: the first rendered (idx=0) is non-last but should still have no line
    const { container } = renderFeed([
      makeGroup('AAA', 'abandoned'),
      makeGroup('BBB', 'abandoned'),
    ]);
    expect(container.querySelectorAll('.connector-line')).toHaveLength(0);
  });

  it('non-abandoned non-last tiles DO render a connector line (control)', () => {
    // Ensures the abandoned suppression is specific to abandoned status, not an omission
    const { container } = renderFeed([
      makeGroup('AAA', 'visited'),
      makeGroup('BBB', 'visited'),
    ]);
    expect(container.querySelectorAll('.connector-line').length).toBeGreaterThan(0);
  });
});
