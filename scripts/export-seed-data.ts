/**
 * Exports hardcoded TypeScript trip/stop/post data to JSON files for the Python seed pipeline.
 *
 * Run from the project root:
 *   cd frontend && npx tsx ../scripts/export-seed-data.ts
 *
 * Outputs to scripts/seed-data/{trips,stops,instagram_posts,substack_posts}.json
 */

import { writeFileSync, mkdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

import { miscellaneousAdventures } from '../frontend/src/data/miscellaneous-adventures';
import { earthSandwich2015 } from '../frontend/src/data/earth-sandwich-2015';
import { earthClubSandwich2027 } from '../frontend/src/data/earth-club-sandwich-2027';
import type { Trip, Stop, InstagramPost, SubstackPost } from '../frontend/src/data/types';

// ── Output directory ──────────────────────────────────────────────────────────

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const OUT_DIR = join(__dirname, 'seed-data');

mkdirSync(OUT_DIR, { recursive: true });

// ── Seed records ──────────────────────────────────────────────────────────────

interface TripRecord {
  id: string;
  title: string;
  description: string;
  start_date: string;
  end_date: string;
}

interface StopRecord {
  id: string;
  trip_id: string;
  date: string;
  location: string;
  lat: number | null;
  lng: number | null;
  status: string;
  region_code: string | null;
  post_type: string;
  sequence_order: number;
  caption: string | null;
}

interface InstagramPostRecord {
  stop_id: string;
  instagram_id: string;
  shortcode: string;
  media_url: string;
  caption: string;
  timestamp: string;
}

interface SubstackPostRecord {
  stop_id: string;
  substack_id: string;
  title: string;
  subtitle: string | null;
  body: string;
  published_at: string;
}

// ── Transform logic ───────────────────────────────────────────────────────────

const trips: TripRecord[] = [];
const stops: StopRecord[] = [];
const instagramPosts: InstagramPostRecord[] = [];
const substackPosts: SubstackPostRecord[] = [];

function processTrip(trip: Trip): void {
  const dates = trip.stops.map((s) => s.date).sort();
  const startDate = dates[0] ?? '';
  const endDate = dates[dates.length - 1] ?? '';

  trips.push({
    id: trip.id,
    title: trip.title,
    description: trip.description,
    start_date: startDate,
    end_date: endDate,
  });

  trip.stops.forEach((stop: Stop, index: number) => {
    const post = stop.post;

    let caption: string | null = null;
    if (post.type === 'planned' && 'caption' in post && post.caption) {
      caption = post.caption;
    }

    stops.push({
      id: stop.id,
      trip_id: trip.id,
      date: stop.date,
      location: stop.location,
      lat: stop.coords?.lat ?? null,
      lng: stop.coords?.lng ?? null,
      status: stop.status,
      region_code: stop.regionCode ?? null,
      post_type: post.type,
      sequence_order: index,
      caption,
    });

    if (post.type === 'instagram') {
      const ig = post as InstagramPost;
      instagramPosts.push({
        stop_id: stop.id,
        instagram_id: ig.instagramId ?? '',
        shortcode: ig.shortcode ?? '',
        media_url: ig.image,
        caption: ig.caption,
        // Use date at midnight UTC — exact time not available in seeded data
        timestamp: `${stop.date}T00:00:00Z`,
      });
    } else if (post.type === 'substack') {
      const ss = post as SubstackPost;
      substackPosts.push({
        stop_id: stop.id,
        // Stable seed identifier — these posts have no RSS guid in the source data
        substack_id: `seed:${stop.id}`,
        title: ss.title,
        subtitle: ss.subtitle ?? null,
        body: ss.body,
        published_at: `${stop.date}T00:00:00Z`,
      });
    }
  });
}

[miscellaneousAdventures, earthSandwich2015, earthClubSandwich2027].forEach(processTrip);

// ── Write output ──────────────────────────────────────────────────────────────

function write(filename: string, data: unknown[]): void {
  const path = join(OUT_DIR, filename);
  writeFileSync(path, JSON.stringify(data, null, 2), 'utf-8');
  console.log(`Wrote ${data.length} records → ${path}`);
}

write('trips.json', trips);
write('stops.json', stops);
write('instagram_posts.json', instagramPosts);
write('substack_posts.json', substackPosts);

console.log('Export complete.');
