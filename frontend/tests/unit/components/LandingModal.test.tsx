import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useState } from 'react';
import LandingModal from '../../../src/components/LandingModal';

const DISMISSED_KEY = 'travelogue:landing-dismissed';

// Mirrors App.tsx's showLandingModal pattern (T134) so the localStorage-driven
// visibility and dismiss contract (SC-013) can be verified before App.tsx is wired up.
function LandingModalFeature() {
  const [show, setShow] = useState(!localStorage.getItem(DISMISSED_KEY));
  if (!show) return null;
  return (
    <LandingModal
      onDismiss={() => {
        localStorage.setItem(DISMISSED_KEY, '1');
        setShow(false);
      }}
    />
  );
}

// ── (a): renders when key is absent ──────────────────────────────────────────

describe('LandingModal – key absent', () => {
  beforeEach(() => {
    vi.stubGlobal('localStorage', { getItem: vi.fn(() => null), setItem: vi.fn() });
  });
  afterEach(() => vi.unstubAllGlobals());

  it('renders the modal when travelogue:landing-dismissed is not set', () => {
    render(<LandingModalFeature />);
    expect(screen.getByRole('button', { name: /start exploring/i })).toBeInTheDocument();
  });
});

// ── (b): does not render when key is set ─────────────────────────────────────

describe('LandingModal – key present', () => {
  beforeEach(() => {
    vi.stubGlobal('localStorage', { getItem: vi.fn(() => '1'), setItem: vi.fn() });
  });
  afterEach(() => vi.unstubAllGlobals());

  it('does not render the modal when travelogue:landing-dismissed is set', () => {
    render(<LandingModalFeature />);
    expect(screen.queryByRole('button', { name: /start exploring/i })).not.toBeInTheDocument();
  });
});

// ── dismiss: writes key and removes modal ─────────────────────────────────────

describe('LandingModal – dismiss writes key and hides modal', () => {
  const setItem = vi.fn();

  beforeEach(() => {
    vi.stubGlobal('localStorage', { getItem: vi.fn(() => null), setItem });
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    setItem.mockClear();
  });

  it('writes the dismissed key and removes the modal on dismiss', async () => {
    const user = userEvent.setup();
    render(<LandingModalFeature />);
    await user.click(screen.getByRole('button', { name: /start exploring/i }));
    expect(setItem).toHaveBeenCalledWith(DISMISSED_KEY, '1');
    expect(screen.queryByRole('button', { name: /start exploring/i })).not.toBeInTheDocument();
  });
});

// ── (c): dismiss button calls onDismiss prop ──────────────────────────────────

describe('LandingModal – onDismiss prop', () => {
  it('clicking the dismiss button calls onDismiss', async () => {
    const user = userEvent.setup();
    const onDismiss = vi.fn();
    render(<LandingModal onDismiss={onDismiss} />);
    await user.click(screen.getByRole('button', { name: /start exploring/i }));
    expect(onDismiss).toHaveBeenCalled();
  });
});
