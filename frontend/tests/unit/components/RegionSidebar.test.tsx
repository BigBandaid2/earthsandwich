import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import RegionSidebar from '../../../src/components/RegionSidebar';
import type { RegionGroup } from '../../../src/utils/regionUtils';
import type { Stop, Region } from '../../../src/data/types';

// ── Fixtures ──────────────────────────────────────────────────────────────────

function makeRegion(code: string): Region {
  return {
    code,
    name: `City ${code}`,
    airportName: `${code} Airport`,
    country: `Country ${code}`,
    coords: { lat: 0, lng: 0 },
  };
}

function makeStop(id: string, overrides: Partial<Stop> = {}): Stop {
  return {
    id,
    date: '2024-06-01',
    location: `${id} Location, District`,
    coords: { lat: 0, lng: 0 },
    status: 'visited',
    regionCode: 'AAA',
    post: { type: 'planned' },
    ...overrides,
  };
}

const IG_STOP = makeStop('ig-1', {
  post: {
    type: 'instagram',
    image: 'https://example.com/photo.jpg',
    caption: 'Sunset over the harbour',
    instagramId: 'ig123',
    shortcode: 'abc123',
  },
});

const SS_STOP = makeStop('ss-1', {
  post: {
    type: 'substack',
    title: 'Pacific Adventures',
    subtitle: 'A week in the islands',
    body: 'Long article body text goes here with many more words...',
  },
});

const PL_STOP = makeStop('pl-1', {
  status: 'planned',
  post: { type: 'planned', caption: 'Hoping to visit here' },
});

function makeGroup(code: string, stops: Stop[], overrides: Partial<RegionGroup> = {}): RegionGroup {
  return {
    region: makeRegion(code),
    stops,
    startDate: '2024-06-01',
    endDate: '2024-06-30',
    overallStatus: 'visited',
    ...overrides,
  };
}

function renderSidebar(
  groups: RegionGroup[],
  activeCode: string | null,
  handlers: { onSelectRegion?: ReturnType<typeof vi.fn>; onOpenStop?: ReturnType<typeof vi.fn> } = {},
) {
  return render(
    <RegionSidebar
      regionGroups={groups}
      activeRegionCode={activeCode}
      onSelectRegion={handlers.onSelectRegion ?? vi.fn()}
      onOpenStop={handlers.onOpenStop ?? vi.fn()}
    />,
  );
}

// ── Active / collapsed accordion state ───────────────────────────────────────

describe('RegionSidebar accordion state', () => {
  it('active region header has aria-expanded=true', () => {
    renderSidebar([makeGroup('AAA', [IG_STOP])], 'AAA');
    expect(screen.getByRole('button', { name: /City AAA/ })).toHaveAttribute(
      'aria-expanded',
      'true',
    );
  });

  it('active region shows its stop tiles below the header', () => {
    renderSidebar([makeGroup('AAA', [IG_STOP])], 'AAA');
    expect(screen.getByText('Sunset over the harbour')).toBeInTheDocument();
  });

  it('inactive regions have aria-expanded=false and hide their stop tiles', () => {
    renderSidebar(
      [makeGroup('AAA', [IG_STOP]), makeGroup('BBB', [SS_STOP])],
      'AAA',
    );
    const bbbHeader = screen.getByRole('button', { name: /City BBB/ });
    expect(bbbHeader).toHaveAttribute('aria-expanded', 'false');
    expect(screen.queryByText('Pacific Adventures')).not.toBeInTheDocument();
  });

  it('clicking a collapsed region header calls onSelectRegion with its code', async () => {
    const user = userEvent.setup();
    const onSelectRegion = vi.fn();
    renderSidebar(
      [makeGroup('AAA', [IG_STOP]), makeGroup('BBB', [SS_STOP])],
      'AAA',
      { onSelectRegion },
    );
    await user.click(screen.getByRole('button', { name: /City BBB/ }));
    expect(onSelectRegion).toHaveBeenCalledWith('BBB');
  });

  it('clicking the active region header also calls onSelectRegion with its code', async () => {
    const user = userEvent.setup();
    const onSelectRegion = vi.fn();
    renderSidebar([makeGroup('AAA', [IG_STOP])], 'AAA', { onSelectRegion });
    await user.click(screen.getByRole('button', { name: /City AAA/ }));
    expect(onSelectRegion).toHaveBeenCalledWith('AAA');
  });
});

// ── FR-018: planned stop suppression ─────────────────────────────────────────

describe('RegionSidebar planned stop suppression (FR-018)', () => {
  it('suppresses planned stop tiles when an Instagram stop exists in the region', () => {
    const group = makeGroup('AAA', [IG_STOP, PL_STOP]);
    renderSidebar([group], 'AAA');
    expect(screen.getByText('Sunset over the harbour')).toBeInTheDocument();
    expect(screen.queryByText('Hoping to visit here')).not.toBeInTheDocument();
  });

  it('suppresses planned stop tiles when a Substack stop exists in the region', () => {
    const group = makeGroup('AAA', [SS_STOP, PL_STOP]);
    renderSidebar([group], 'AAA');
    expect(screen.getByText('Pacific Adventures')).toBeInTheDocument();
    expect(screen.queryByText('Hoping to visit here')).not.toBeInTheDocument();
  });

  it('shows planned stop tiles when the region has no Instagram or Substack stops', () => {
    const group = makeGroup('AAA', [PL_STOP]);
    renderSidebar([group], 'AAA');
    expect(screen.getByText('Hoping to visit here')).toBeInTheDocument();
  });
});

// ── FR-019: planned stop tile click is a no-op ────────────────────────────────

describe('RegionSidebar planned stop tile click (FR-019)', () => {
  it('clicking a visible planned stop tile does NOT call onOpenStop', async () => {
    const user = userEvent.setup();
    const onOpenStop = vi.fn();
    // No rich stops → planned stop is visible
    const group = makeGroup('AAA', [PL_STOP]);
    renderSidebar([group], 'AAA', { onOpenStop });
    const plannedBtn = screen.getByText('Hoping to visit here').closest('button')!;
    await user.click(plannedBtn);
    expect(onOpenStop).not.toHaveBeenCalled();
  });

  it('clicking an Instagram stop tile DOES call onOpenStop', async () => {
    const user = userEvent.setup();
    const onOpenStop = vi.fn();
    const group = makeGroup('AAA', [IG_STOP]);
    renderSidebar([group], 'AAA', { onOpenStop });
    await user.click(screen.getByText('Sunset over the harbour').closest('button')!);
    expect(onOpenStop).toHaveBeenCalledWith('ig-1', ['ig-1']);
  });
});

// ── Instagram stop tile content (f) ──────────────────────────────────────────

describe('Instagram stop tile content', () => {
  it('shows the caption text', () => {
    renderSidebar([makeGroup('AAA', [IG_STOP])], 'AAA');
    expect(screen.getByText('Sunset over the harbour')).toBeInTheDocument();
  });

  it('shows a photo image element', () => {
    renderSidebar([makeGroup('AAA', [IG_STOP])], 'AAA');
    const img = screen.getByRole('img');
    expect(img).toHaveAttribute('src', 'https://example.com/photo.jpg');
  });
});

// ── Substack stop tile content (g) ───────────────────────────────────────────

describe('Substack stop tile content', () => {
  it('shows the article title', () => {
    renderSidebar([makeGroup('AAA', [SS_STOP])], 'AAA');
    expect(screen.getByText('Pacific Adventures')).toBeInTheDocument();
  });

  it('shows the subtitle as a preview', () => {
    renderSidebar([makeGroup('AAA', [SS_STOP])], 'AAA');
    expect(screen.getByText('A week in the islands')).toBeInTheDocument();
  });

  it('omits subtitle when absent', () => {
    const noSubtitle = makeStop('ss-2', {
      post: { type: 'substack', title: 'Solo Article', body: 'Body text.' },
    });
    renderSidebar([makeGroup('AAA', [noSubtitle])], 'AAA');
    expect(screen.getByText('Solo Article')).toBeInTheDocument();
    // No subtitle element — only title and body should appear
    expect(screen.queryByText('A week in the islands')).not.toBeInTheDocument();
  });
});
