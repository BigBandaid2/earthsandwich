import { renderHook, waitFor, act } from '@testing-library/react';
import { useTrips } from '../../../src/hooks/useTrips';

const API_TRIP = {
  id: 'trip-1',
  title: 'Test Trip',
  description: 'A test trip',
  start_date: '2024-01-01',
  end_date: '2024-12-31',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

function mockFetchOk(data: unknown) {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(data),
    }),
  );
}

function mockFetchFail(message = 'Network error') {
  vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error(message)));
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe('useTrips', () => {
  it('loading is true on mount before fetch resolves', () => {
    vi.stubGlobal('fetch', vi.fn().mockReturnValue(new Promise(() => {})));
    const { result } = renderHook(() => useTrips());
    expect(result.current.loading).toBe(true);
    expect(result.current.trips).toEqual([]);
    expect(result.current.error).toBeNull();
  });

  it('successful fetch sets trips array and clears loading', async () => {
    mockFetchOk([API_TRIP]);
    const { result } = renderHook(() => useTrips());
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.trips).toHaveLength(1);
    expect(result.current.trips[0].id).toBe('trip-1');
    expect(result.current.error).toBeNull();
  });

  it('empty list from API yields empty trips array', async () => {
    mockFetchOk([]);
    const { result } = renderHook(() => useTrips());
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.trips).toEqual([]);
    expect(result.current.error).toBeNull();
  });

  it('retries 3 times on failure then sets error and clears trips', async () => {
    vi.useFakeTimers();
    mockFetchFail('Network error');
    const { result } = renderHook(() => useTrips());

    await act(() => vi.runAllTimersAsync());

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.error).not.toBeNull();
    expect(result.current.trips).toEqual([]);
    expect(vi.mocked(fetch)).toHaveBeenCalledTimes(3);
  });
});
