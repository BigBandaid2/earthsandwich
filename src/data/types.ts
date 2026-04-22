export type StopType = 'trip' | 'city' | 'site';
export type StopStatus = 'visited' | 'planned';

export interface Coordinates {
  lat: number;
  lng: number;
}

export interface Stop {
  id: string;
  type: StopType;
  title: string;
  caption: string;
  date: string;
  coords: Coordinates;
  status: StopStatus;
  image?: string;
  blog?: string;
  details?: string;
  children?: Stop[];
}

export interface Itinerary {
  title: string;
  description: string;
  stops: Stop[];
}
