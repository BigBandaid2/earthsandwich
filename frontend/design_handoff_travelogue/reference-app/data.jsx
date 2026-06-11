// Travelogue App — sample content. Real captions & voice from the trip data.
// Regions are in travel order (drives the route line). x/y are % on the map.
window.TGDATA = {
  trips: [
    { id: 'misc', name: 'Miscellaneous Adventures', meta: '23 stops · 5 countries', active: true },
    { id: 'es2015', name: 'Earth Sandwich 2015', meta: 'Dublin → New York · round-the-world' },
    { id: 'ecs2027', name: 'Earth Club Sandwich 2027', meta: 'planned · the next slice' },
  ],
  trip: {
    name: 'Miscellaneous Adventures',
    blurb: 'across three continents,',
    stops: 23, visited: 21, planned: 2, countries: 5,
  },
  regions: [
    {
      code: 'MDE', name: 'Medellín', country: 'Colombia', iso: 'co',
      dates: 'May 2019', status: 'visited', x: 20, y: 66, stopCount: 5,
      photos: [
        { hue: 14, location: 'La Piedra del Peñol', caption: '700 steps up a vertical monolith. They thoughtfully built a second set of stairs so that the descending traffic wouldn’t demotivate the upward climbers.' },
        { hue: 168, location: 'Plaza Botero, Medellín', caption: 'Mom being casually fabulous.' },
        { hue: 38, location: 'Medellín, Antioquia', caption: 'That is some admirably succinct visual symbology.' },
        { hue: 320, location: 'Aeropuerto José María Córdova', caption: 'Botched translation or profound truth, I genuinely cannot say.' },
      ],
      note: 'Only got to overlap a couple days with my bro. Parents baton is yours now — good luck!',
    },
    {
      code: 'JFK', name: 'New York', country: 'USA', iso: 'us',
      dates: 'Sep 2019', status: 'visited', x: 29, y: 40, stopCount: 2,
      photos: [
        { hue: 210, location: "Hell's Kitchen, New York", caption: 'Thanks for the memories 540. Onward and upward!' },
        { hue: 26, location: "Hell's Kitchen, New York", caption: 'Courtesy of the most passionate volunteer iPhone photographer ever.' },
      ],
      note: null,
    },
    {
      code: 'ARN', name: 'Stockholm', country: 'Sweden', iso: 'se',
      dates: 'Oct 2019', status: 'visited', x: 60, y: 26, stopCount: 1,
      photos: [
        { hue: 48, location: 'IKEA, Stockholm', caption: 'Soft serve and plywood. Our pilgrimage to the OG temple of Swedish culture is truly complete.' },
      ],
      note: null,
    },
    {
      code: 'MEX', name: 'Mexico City', country: 'Mexico', iso: 'mx',
      dates: 'Nov 2019', status: 'visited', x: 15, y: 52, stopCount: 8, open: true,
      photos: [
        { hue: 350, location: 'Ciudad de México', caption: 'Feliz Día de los Muertos!', count: 3 },
        { hue: 30, location: 'El 123, Mexico City', caption: 'Enjoy your coffee, Cthulhu watches over you.' },
        { hue: 198, location: 'Biblioteca José Vasconcelos', caption: 'The magical floating stacks blur a library visit with a trip through the Matrix.', count: 2 },
        { hue: 12, location: 'El Dragón, Mexico City', caption: 'In Mexico, Beijing duck roasts with all the fiery drama of a ritual fit for Montezuma.' },
      ],
      extra: 4,
      dispatch: {
        kind: 'substack', no: 6, location: 'Ciudad de México', readMins: 7, hue: 26,
        title: 'Mexico City belongs in the same breath as London',
        dek: 'A week of ivories, floating libraries, and duck roasted like a ritual — and the slow realization that this is a world capital nobody warned us about.',
        body: [
          'On top of everything else, an exhibit of Asian ivories more spectacular than anything I’ve seen in China or Taiwan. We kept turning to each other with the same look: how is this not the only thing people talk about?',
          'The Biblioteca Vasconcelos alone would justify the trip — stacks floating in the air like someone paused a library mid-explosion. You walk in expecting books and leave feeling like you wandered onto a film set for the future.',
          { sub: 'A city that keeps under-selling itself' },
          'You come for the tacos and the murals, and you leave convinced you’ve undersold every postcard you’ll ever send home. Day of the Dead turns whole neighborhoods into something between a parade and a prayer.',
          { quote: 'This city should be said in the same breath as London or LA.' },
          'And then there’s the food — a Beijing duck roasted with all the fiery drama of a ritual fit for Montezuma, carved tableside like the main event of an opera. We have already started plotting the trip back.',
        ],
      },
      note: 'On top of everything else, an exhibit of Asian ivories more spectacular than anything I’ve seen in China or Taiwan. This city should be said in the same breath as London or LA.',
    },
    {
      code: 'OAX', name: 'Oaxaca', country: 'Mexico', iso: 'mx',
      dates: 'Feb 2024', status: 'visited', x: 18, y: 61, stopCount: 6,
      photos: [
        { hue: 96, location: 'Centro Cultural San Pablo', caption: 'Where even a cooking school is beautiful.' },
        { hue: 142, location: 'El Árbol del Tule', caption: 'Cthulhu in tree form. Reaching through the millennia.' },
        { hue: 188, location: 'Hierve el Agua', caption: '“For your safety, do not approach the abyss.”', count: 4 },
        { hue: 36, location: 'Oaxaca Centro', caption: 'Never a wrong time or place for hot chocolate.' },
      ],
      extra: 2,
      dispatch: {
        kind: 'substack', no: 7, location: 'Hierve el Agua', readMins: 5, hue: 188,
        title: 'On the abyss at Hierve el Agua',
        dek: 'A petrified waterfall, a hand-painted warning sign, and a long argument with myself about whether the most honest travel advice is just “do not approach.”',
        body: [
          'The sign at the top is hand-painted and entirely sincere. Naturally, everyone is at the abyss — leaning over it, photographing it, daring each other a half-step closer.',
          { quote: '“For your safety, do not approach the abyss.”' },
          'The water here has turned the cliff to stone mid-fall, frozen the way a story freezes the moment you start telling it to other people. From the right angle it pours forever and never moves an inch.',
          { sub: 'The joy in everything' },
          'Some places can find the joy in anything — even a thousand-foot drop gets a cheerful coat of paint and an orderly queue for photos. We left sunburned, slightly terrified, and completely charmed.',
        ],
      },
      note: 'Some places can find the joy in anything.',
    },
    {
      code: 'PAT', name: 'Patagonia', country: 'Argentina', iso: 'ar',
      dates: 'Mar 2027', status: 'planned', x: 29, y: 88, stopCount: 0,
      photos: [],
      note: 'Up next — the long way south. Part of Earth Club Sandwich 2027.',
    },
  ],
};
