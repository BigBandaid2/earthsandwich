import { renderHook, waitFor, act } from '@testing-library/react';
import { useTrip } from '../../../src/hooks/useTrip';

const API_TRIP_DETAIL = {
  id: 'trip-1',
  title: 'Test Trip',
  description: 'A test trip',
  start_date: '2024-01-01',
  end_date: '2024-12-31',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  stops: [],
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

describe('useTrip', () => {
  it('does nothing when tripId is null', () => {
    const fetchSpy = vi.fn();
    vi.stubGlobal('fetch', fetchSpy);
    const { result } = renderHook(() => useTrip(null));
    expect(result.current.loading).toBe(false);
    expect(result.current.trip).toBeNull();
    expect(result.current.error).toBeNull();
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it('sets loading true when tripId changes from null to a value', async () => {
    vi.stubGlobal('fetch', vi.fn().mockReturnValue(new Promise(() => {})));
    const { result, rerender } = renderHook(({ id }) => useTrip(id), {
      initialProps: { id: null as string | null },
    });
    expect(result.current.loading).toBe(false);

    rerender({ id: 'trip-1' });
    expect(result.current.loading).toBe(true);
  });

  it('successful fetch populates trip', async () => {
    mockFetchOk(API_TRIP_DETAIL);
    const { result } = renderHook(() => useTrip('trip-1'));
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.trip).not.toBeNull();
    expect(result.current.trip?.id).toBe('trip-1');
    expect(result.current.error).toBeNull();
  });

  it('retries 3 times on failure then sets error and clears trip', async () => {
    vi.useFakeTimers();
    mockFetchFail('Network error');
    const { result } = renderHook(() => useTrip('trip-1'));

    await act(() => vi.runAllTimersAsync());

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.error).not.toBeNull();
    expect(result.current.trip).toBeNull();
    expect(vi.mocked(fetch)).toHaveBeenCalledTimes(3);
  });
});
