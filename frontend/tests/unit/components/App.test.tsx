import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from '../../../src/App';
import { useTrips } from '../../../src/hooks/useTrips';
import { useTrip } from '../../../src/hooks/useTrip';
import { useRegions } from '../../../src/hooks/useRegions';

vi.mock('../../../src/hooks/useTrips');
vi.mock('../../../src/hooks/useTrip');
vi.mock('../../../src/hooks/useRegions');

vi.mock('@vis.gl/react-google-maps', () => ({
  APIProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));
vi.mock('../../../src/components/MapView', () => ({
  default: () => <div data-testid="world-map" />,
}));
vi.mock('../../../src/components/Sidebar', () => ({
  default: () => <div data-testid="trip-feed" />,
}));
vi.mock('../../../src/components/RegionSidebar', () => ({
  default: () => <div data-testid="region-sidebar" />,
}));
vi.mock('../../../src/components/StopDetail', () => ({
  default: () => <div data-testid="stop-modal" />,
}));
vi.mock('../../../src/utils/regionUtils', () => ({
  groupStopsByRegion: vi.fn().mockReturnValue([]),
}));

const MOCK_TRIP_SUMMARY = { id: 'trip-1', title: 'Test Trip', description: '', stops: [] };
const MOCK_TRIP_DETAIL = { id: 'trip-1', title: 'Test Trip', description: '', stops: [] };
const MOCK_TRIP_SUMMARY_2 = { id: 'trip-2', title: 'Second Trip', description: '', stops: [] };

function setupHooks({
  tripsLoading = false,
  tripsError = null as string | null,
  trips = [MOCK_TRIP_SUMMARY],
  tripLoading = false,
  tripError = null as string | null,
  regionsLoading = false,
  regionsError = null as string | null,
  regions = [] as unknown[],
} = {}) {
  vi.mocked(useTrips).mockReturnValue({ trips, loading: tripsLoading, error: tripsError });
  vi.mocked(useTrip).mockImplementation((id) => ({
    trip: id ? MOCK_TRIP_DETAIL : null,
    loading: tripLoading,
    error: tripError,
  }));
  vi.mocked(useRegions).mockReturnValue({
    regions: regions as ReturnType<typeof useRegions>['regions'],
    loading: regionsLoading,
    error: regionsError,
  });
}

afterEach(() => {
  vi.clearAllMocks();
  window.location.hash = '';
});

describe('App', () => {
  it('shows loading indicator while useTrips is loading', () => {
    setupHooks({ tripsLoading: true, trips: [] });
    render(<App />);
    expect(screen.getByText('Loading…')).toBeInTheDocument();
  });

  it('shows error panel when useTrips yields an error', async () => {
    setupHooks({ tripsError: 'Failed to load trips.', trips: [], tripsLoading: false });
    render(<App />);
    await waitFor(() => {
      expect(screen.getByText(/Failed to load trips\./i)).toBeInTheDocument();
    });
  });

  it('shows empty-state message when trips list is empty and not loading', async () => {
    setupHooks({ trips: [], tripsLoading: false });
    render(<App />);
    await waitFor(() => {
      expect(screen.getByText('No trips are currently available.')).toBeInTheDocument();
    });
  });

  it('selecting a trip calls useTrip with the new trip id', async () => {
    const user = userEvent.setup();
    setupHooks({ trips: [MOCK_TRIP_SUMMARY, MOCK_TRIP_SUMMARY_2] });
    render(<App />);

    await waitFor(() => expect(screen.queryByText('Loading…')).not.toBeInTheDocument());

    const hamburger = screen.getByLabelText('Open trip selector');
    await user.click(hamburger);

    const secondTripButton = screen.getByText('Second Trip');
    await user.click(secondTripButton);

    expect(vi.mocked(useTrip)).toHaveBeenCalledWith('trip-2');
  });
});
