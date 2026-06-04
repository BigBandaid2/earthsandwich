import type { Stop, Trip, InstagramPost, SubstackPost, PlannedPost } from '../data/types';
import type { ApiTrip, ApiTripDetail, ApiStop, ApiInstagramPost, ApiSubstackPost } from './client';

function adaptPost(stop: ApiStop): Stop['post'] {
  if (stop.post_type === 'instagram' && stop.post !== null) {
    const p = stop.post as ApiInstagramPost;
    return {
      type: 'instagram',
      image: p.media_url,
      caption: p.caption,
      instagramId: p.instagram_id,
      shortcode: p.shortcode,
    } satisfies InstagramPost;
  }
  if (stop.post_type === 'substack' && stop.post !== null) {
    const p = stop.post as ApiSubstackPost;
    return {
      type: 'substack',
      title: p.title,
      subtitle: p.subtitle ?? undefined,
      body: p.body,
    } satisfies SubstackPost;
  }
  return {
    type: 'planned',
    caption: stop.caption ?? undefined,
  } satisfies PlannedPost;
}

export function adaptStop(apiStop: ApiStop): Stop {
  return {
    id: apiStop.id,
    date: apiStop.date,
    location: apiStop.location,
    coords: { lat: apiStop.lat, lng: apiStop.lng },
    status: apiStop.status,
    regionCode: apiStop.region_code,
    post: adaptPost(apiStop),
  };
}

export function adaptTrip(apiTrip: ApiTripDetail): Trip {
  return {
    id: apiTrip.id,
    title: apiTrip.title,
    description: apiTrip.description,
    stops: apiTrip.stops.map(adaptStop),
  };
}

export function adaptTripSummary(apiTrip: ApiTrip): Trip {
  return {
    id: apiTrip.id,
    title: apiTrip.title,
    description: apiTrip.description,
    stops: [],
  };
}
