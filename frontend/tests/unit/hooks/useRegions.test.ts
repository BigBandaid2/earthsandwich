import { renderHook, waitFor, act } from '@testing-library/react';
import { useRegions } from '../../../src/hooks/useRegions';

const API_REGION = {
  iata_code: 'SYD',
  name: 'Sydney',
  airport_name: 'Sydney Kingsford Smith Airport',
  country: 'Australia',
  lat: -33.9399,
  lng: 151.1753,
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

describe('useRegions', () => {
  it('loading is true initially before fetch resolves', () => {
    vi.stubGlobal('fetch', vi.fn().mockReturnValue(new Promise(() => {})));
    const { result } = renderHook(() => useRegions());
    expect(result.current.loading).toBe(true);
    expect(result.current.regions).toEqual([]);
    expect(result.current.error).toBeNull();
  });

  it('successful fetch yields adapted Region array', async () => {
    mockFetchOk([API_REGION]);
    const { result } = renderHook(() => useRegions());
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.regions).toHaveLength(1);
    expect(result.current.regions[0].code).toBe('SYD');
    expect(result.current.regions[0].airportName).toBe('Sydney Kingsford Smith Airport');
    expect(result.current.error).toBeNull();
  });

  it('retries 3 times on failure then sets error string', async () => {
    vi.useFakeTimers();
    mockFetchFail('Network error');
    const { result } = renderHook(() => useRegions());

    await act(async () => {
      await vi.runAllTimersAsync();
    });

    expect(result.current.loading).toBe(false);
    expect(result.current.error).not.toBeNull();
    expect(result.current.regions).toEqual([]);
    expect(vi.mocked(fetch)).toHaveBeenCalledTimes(3);
  }, 10000);
});
