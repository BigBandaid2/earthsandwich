import type { Region } from './types';

export const REGIONS: Region[] = [
  {
    code: 'MDE',
    name: 'Medellín',
    airportName: 'José María Córdova International Airport',
    country: 'Colombia',
    coords: { lat: 6.1645, lng: -75.4231 },
  },
  {
    code: 'JFK',
    name: 'New York',
    airportName: 'John F. Kennedy International Airport',
    country: 'USA',
    coords: { lat: 40.6413, lng: -73.7781 },
  },
  {
    code: 'ARN',
    name: 'Stockholm',
    airportName: 'Stockholm Arlanda Airport',
    country: 'Sweden',
    coords: { lat: 59.6519, lng: 17.9186 },
  },
  {
    code: 'MEX',
    name: 'Mexico City',
    airportName: 'Benito Juárez International Airport',
    country: 'Mexico',
    coords: { lat: 19.4363, lng: -99.0721 },
  },
  {
    code: 'OAX',
    name: 'Oaxaca',
    airportName: 'Xoxocotlán International Airport',
    country: 'Mexico',
    coords: { lat: 17.0517, lng: -96.7264 },
  },
];
