import type { Trip } from './types';
import { miscellaneousAdventures } from './miscellaneous-adventures';
import { earthSandwich2015 } from './earth-sandwich-2015';
import { earthClubSandwich2027 } from './earth-club-sandwich-2027';

export const trips: Trip[] = [
  earthClubSandwich2027,
  miscellaneousAdventures,
  earthSandwich2015,
];

// Most recent trip by start date — shown by default on page load (FR-010)
export const itinerary: Trip = earthClubSandwich2027;
