// Stored status authored on each stop. The view layer derives a third
// effective status, "abandoned", for planned stops whose date is in the past
// (see FR-028). The stored value is never reclassified.
export type StopStatus = 'visited' | 'planned';
export type EffectiveStopStatus = 'visited' | 'planned' | 'abandoned';

export interface Coordinates {
  lat: number;
  lng: number;
}

export interface InstagramPost {
  type: 'instagram';
  image: string;
  caption: string;
  instagramId?: string;
  shortcode?: string;
}

export interface SubstackPost {
  type: 'substack';
  title: string;
  subtitle?: string;
  body: string;
}

export interface PlannedPost {
  type: 'planned';
  caption?: string;
}

export type StopPost = InstagramPost | SubstackPost | PlannedPost;

export interface Stop {
  id: string;
  date: string;
  location: string;
  coords: Coordinates;
  status: StopStatus;
  regionCode: string;
  post: StopPost;
}

export interface Region {
  code: string;
  name: string;
  airportName: string;
  country: string;
  coords: Coordinates;
}

export interface Trip {
  id: string;
  title: string;
  description: string;
  stops: Stop[];
}
