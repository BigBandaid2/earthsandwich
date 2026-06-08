const BASE_URL: string = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? 'http://localhost:8000';

interface ApiError {
  error: string;
  detail: string;
}

async function apiFetch<T>(path: string, params?: Record<string, string | undefined>): Promise<T> {
  let url = `${BASE_URL}${path}`;
  if (params) {
    const search = new URLSearchParams();
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined) search.set(k, v);
    }
    const qs = search.toString();
    if (qs) url += `?${qs}`;
  }
  const res = await fetch(url);
  if (!res.ok) {
    const body: ApiError = await res.json().catch(() => ({
      error: String(res.status),
      detail: res.statusText,
    }));
    throw new Error(body.detail || body.error);
  }
  return res.json() as Promise<T>;
}

// ── Response shapes ───────────────────────────────────────────────────────────

export interface ApiTrip {
  id: string;
  title: string;
  description: string;
  start_date: string;
  end_date: string;
  created_at: string;
  updated_at: string;
}

export interface ApiInstagramPost {
  id: string;
  stop_id: string;
  instagram_id: string;
  shortcode: string;
  media_url: string;
  caption: string;
  timestamp: string;
  created_at: string;
}

export interface ApiSubstackPost {
  id: string;
  stop_id: string | null;
  substack_id: string;
  title: string;
  subtitle: string | null;
  body: string;
  published_at: string;
  created_at: string;
}

export interface ApiStop {
  id: string;
  trip_id: string;
  date: string;
  location: string;
  lat: number;
  lng: number;
  status: 'visited' | 'planned';
  region_code: string;
  post_type: 'instagram' | 'substack' | 'planned';
  caption: string | null;
  post: ApiInstagramPost | ApiSubstackPost | null;
}

export interface ApiTripDetail extends ApiTrip {
  stops: ApiStop[];
}

export interface ApiRegion {
  iata_code: string;
  name: string;
  airport_name: string;
  country: string;
  lat: number;
  lng: number;
}

// ── Query param shapes ────────────────────────────────────────────────────────

export interface GetTripsParams {
  status?: 'active' | 'completed' | 'upcoming';
}

export interface GetStopsParams {
  trip_id?: string;
  status?: 'visited' | 'planned';
  region_code?: string;
  post_type?: 'instagram' | 'substack' | 'planned';
  after?: string;
  before?: string;
}

export interface GetPostsParams {
  stop_id?: string;
  after?: string;
  before?: string;
}

export interface GetRegionsParams {
  country?: string;
}

// ── Fetch functions ───────────────────────────────────────────────────────────

export function getTrips(params?: GetTripsParams): Promise<ApiTrip[]> {
  return apiFetch<ApiTrip[]>('/trips', params as Record<string, string | undefined>);
}

export function getTripDetail(id: string): Promise<ApiTripDetail> {
  return apiFetch<ApiTripDetail>(`/trips/${encodeURIComponent(id)}`);
}

export function getStops(params?: GetStopsParams): Promise<ApiStop[]> {
  return apiFetch<ApiStop[]>('/stops', params as Record<string, string | undefined>);
}

export function getInstagramPosts(params?: GetPostsParams): Promise<ApiInstagramPost[]> {
  return apiFetch<ApiInstagramPost[]>('/instagram-posts', params as Record<string, string | undefined>);
}

export function getSubstackPosts(params?: GetPostsParams): Promise<ApiSubstackPost[]> {
  return apiFetch<ApiSubstackPost[]>('/substack-posts', params as Record<string, string | undefined>);
}

export function getRegions(params?: GetRegionsParams): Promise<ApiRegion[]> {
  return apiFetch<ApiRegion[]>('/regions', params as Record<string, string | undefined>);
}
