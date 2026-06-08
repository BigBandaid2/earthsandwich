import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import StopModal from '../../../src/components/StopDetail';
import type { Stop } from '../../../src/data/types';
import type { RegionGroup } from '../../../src/utils/regionUtils';

// ── Fixtures ──────────────────────────────────────────────────────────────────

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
    shortcode: 'abc123',
  },
});

const SS_STOP = makeStop('ss-1', {
  post: {
    type: 'substack',
    title: 'Pacific Adventures',
    subtitle: 'A week in the islands',
    body: 'Long article body text goes here.',
  },
});

const EMPTY_GROUPS: RegionGroup[] = [];

function renderModal(
  stop: Stop,
  stopList: string[],
  handlers: { onClose?: ReturnType<typeof vi.fn>; onNav?: ReturnType<typeof vi.fn> } = {},
) {
  return render(
    <StopModal
      stop={stop}
      stopList={stopList}
      allStops={[stop]}
      regionGroups={EMPTY_GROUPS}
      onClose={handlers.onClose ?? vi.fn()}
      onNav={handlers.onNav ?? vi.fn()}
    />,
  );
}

// ── Instagram layout (a) ──────────────────────────────────────────────────────

describe('StopModal Instagram layout', () => {
  it('renders the stop location as the heading', () => {
    renderModal(IG_STOP, ['ig-1']);
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('ig-1 Location, District');
  });

  it('renders the caption text', () => {
    renderModal(IG_STOP, ['ig-1']);
    expect(screen.getByText('Sunset over the harbour')).toBeInTheDocument();
  });

  it('renders an image with the post image URL as src', () => {
    renderModal(IG_STOP, ['ig-1']);
    expect(screen.getByRole('img')).toHaveAttribute('src', 'https://example.com/photo.jpg');
  });
});

// ── Substack layout (b) ───────────────────────────────────────────────────────

describe('StopModal Substack layout', () => {
  it('renders the article title as the heading', () => {
    renderModal(SS_STOP, ['ss-1']);
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Pacific Adventures');
  });

  it('renders the subtitle', () => {
    renderModal(SS_STOP, ['ss-1']);
    expect(screen.getByText('A week in the islands')).toBeInTheDocument();
  });

  it('renders the body text', () => {
    renderModal(SS_STOP, ['ss-1']);
    expect(screen.getByText('Long article body text goes here.')).toBeInTheDocument();
  });
});

// ── Missing optional fields (c) ───────────────────────────────────────────────

describe('StopModal missing optional fields', () => {
  it('omits subtitle when Substack post has no subtitle', () => {
    const noSubtitle = makeStop('ss-2', {
      post: { type: 'substack', title: 'Solo Article', body: 'Just the body.' },
    });
    renderModal(noSubtitle, ['ss-2']);
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Solo Article');
    expect(screen.queryByText('A week in the islands')).not.toBeInTheDocument();
  });
});

// ── Navigation (d, e) ─────────────────────────────────────────────────────────

describe('StopModal navigation', () => {
  it('prev arrow calls onNav("prev")', async () => {
    const user = userEvent.setup();
    const onNav = vi.fn();
    // Stop in the middle so prev is enabled
    renderModal(IG_STOP, ['other-1', 'ig-1', 'other-2'], { onNav });
    await user.click(screen.getByRole('button', { name: /previous stop/i }));
    expect(onNav).toHaveBeenCalledWith('prev');
  });

  it('next arrow calls onNav("next")', async () => {
    const user = userEvent.setup();
    const onNav = vi.fn();
    renderModal(IG_STOP, ['other-1', 'ig-1', 'other-2'], { onNav });
    await user.click(screen.getByRole('button', { name: /next stop/i }));
    expect(onNav).toHaveBeenCalledWith('next');
  });
});

// ── Close (f) ─────────────────────────────────────────────────────────────────

describe('StopModal close', () => {
  it('close button calls onClose', async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    renderModal(IG_STOP, ['ig-1'], { onClose });
    await user.click(screen.getByRole('button', { name: /close/i }));
    expect(onClose).toHaveBeenCalled();
  });
});
