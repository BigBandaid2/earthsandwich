import type { Region } from './types';

export const REGIONS: Region[] = [
  // ── Miscellaneous Adventures ──────────────────────────────
  { code: 'MDE', name: 'Medellín', airportName: 'José María Córdova International Airport', country: 'Colombia', coords: { lat: 6.1645, lng: -75.4231 } },
  { code: 'JFK', name: 'New York', airportName: 'John F. Kennedy International Airport', country: 'USA', coords: { lat: 40.6413, lng: -73.7781 } },
  { code: 'ARN', name: 'Stockholm', airportName: 'Stockholm Arlanda Airport', country: 'Sweden', coords: { lat: 59.6519, lng: 17.9186 } },
  { code: 'MEX', name: 'Mexico City', airportName: 'Benito Juárez International Airport', country: 'Mexico', coords: { lat: 19.4363, lng: -99.0721 } },
  { code: 'OAX', name: 'Oaxaca', airportName: 'Xoxocotlán International Airport', country: 'Mexico', coords: { lat: 17.0517, lng: -96.7264 } },

  // ── Western Europe ────────────────────────────────────────
  { code: 'DUB', name: 'Dublin', airportName: 'Dublin Airport', country: 'Ireland', coords: { lat: 53.4213, lng: -6.2701 } },
  { code: 'LIS', name: 'Lisbon', airportName: 'Humberto Delgado Airport', country: 'Portugal', coords: { lat: 38.7756, lng: -9.1354 } },
  { code: 'FAO', name: 'Faro (Algarve)', airportName: 'Faro Airport', country: 'Portugal', coords: { lat: 37.0144, lng: -7.9659 } },
  { code: 'SVQ', name: 'Seville', airportName: 'Seville Airport', country: 'Spain', coords: { lat: 37.4180, lng: -5.8931 } },
  { code: 'GRX', name: 'Granada', airportName: 'Federico García Lorca Granada-Jaén Airport', country: 'Spain', coords: { lat: 37.1887, lng: -3.7774 } },
  { code: 'AGP', name: 'Málaga (Costa del Sol)', airportName: 'Málaga-Costa del Sol Airport', country: 'Spain', coords: { lat: 36.6749, lng: -4.4991 } },
  { code: 'AMS', name: 'Amsterdam', airportName: 'Amsterdam Airport Schiphol', country: 'Netherlands', coords: { lat: 52.3086, lng: 4.7639 } },
  { code: 'BRU', name: 'Brussels', airportName: 'Brussels Airport', country: 'Belgium', coords: { lat: 50.9010, lng: 4.4844 } },
  { code: 'LUX', name: 'Luxembourg', airportName: 'Luxembourg Findel Airport', country: 'Luxembourg', coords: { lat: 49.6233, lng: 6.2044 } },
  { code: 'FRA', name: 'Frankfurt (Rhine-Neckar)', airportName: 'Frankfurt Airport', country: 'Germany', coords: { lat: 50.0379, lng: 8.5622 } },
  { code: 'MUC', name: 'Munich', airportName: 'Munich Airport', country: 'Germany', coords: { lat: 48.3537, lng: 11.7750 } },
  { code: 'DRS', name: 'Dresden', airportName: 'Dresden Airport', country: 'Germany', coords: { lat: 51.1328, lng: 13.7672 } },
  { code: 'BER', name: 'Berlin', airportName: 'Berlin Brandenburg Airport', country: 'Germany', coords: { lat: 52.3667, lng: 13.5033 } },
  { code: 'SZG', name: 'Salzburg', airportName: 'Salzburg Airport', country: 'Austria', coords: { lat: 47.7933, lng: 13.0043 } },
  { code: 'VIE', name: 'Vienna', airportName: 'Vienna International Airport', country: 'Austria', coords: { lat: 48.1103, lng: 16.5697 } },
  { code: 'VCE', name: 'Venice', airportName: 'Venice Marco Polo Airport', country: 'Italy', coords: { lat: 45.5053, lng: 12.3519 } },
  { code: 'BLQ', name: 'Bologna', airportName: 'Bologna Guglielmo Marconi Airport', country: 'Italy', coords: { lat: 44.5354, lng: 11.2887 } },
  { code: 'FLR', name: 'Florence', airportName: 'Florence Peretola Airport', country: 'Italy', coords: { lat: 43.8100, lng: 11.2051 } },
  { code: 'FCO', name: 'Rome', airportName: 'Leonardo da Vinci–Fiumicino Airport', country: 'Italy', coords: { lat: 41.8003, lng: 12.2389 } },
  { code: 'PRG', name: 'Prague', airportName: 'Václav Havel Airport Prague', country: 'Czech Republic', coords: { lat: 50.1008, lng: 14.2600 } },
  { code: 'BUD', name: 'Budapest', airportName: 'Budapest Ferenc Liszt International Airport', country: 'Hungary', coords: { lat: 47.4298, lng: 19.2611 } },
  { code: 'WAW', name: 'Warsaw', airportName: 'Warsaw Chopin Airport', country: 'Poland', coords: { lat: 52.1657, lng: 20.9671 } },
  { code: 'KRK', name: 'Kraków', airportName: 'John Paul II International Airport Kraków-Balice', country: 'Poland', coords: { lat: 50.0777, lng: 19.7848 } },
  { code: 'RIX', name: 'Riga', airportName: 'Riga International Airport', country: 'Latvia', coords: { lat: 56.9236, lng: 23.9711 } },

  // ── North Africa & Morocco ────────────────────────────────
  { code: 'TNG', name: 'Tangier (Northern Morocco)', airportName: 'Tangier Ibn Battouta Airport', country: 'Morocco', coords: { lat: 35.7269, lng: -5.9169 } },
  { code: 'FEZ', name: 'Fez', airportName: 'Fès–Saïss Airport', country: 'Morocco', coords: { lat: 33.9273, lng: -4.9779 } },
  { code: 'RAK', name: 'Marrakech', airportName: 'Marrakech Menara Airport', country: 'Morocco', coords: { lat: 31.6069, lng: -8.0363 } },
  { code: 'CAI', name: 'Cairo', airportName: 'Cairo International Airport', country: 'Egypt', coords: { lat: 30.1219, lng: 31.4056 } },
  { code: 'ASW', name: 'Aswan', airportName: 'Aswan International Airport', country: 'Egypt', coords: { lat: 23.9644, lng: 32.8199 } },
  { code: 'LXR', name: 'Luxor', airportName: 'Luxor International Airport', country: 'Egypt', coords: { lat: 25.6710, lng: 32.7066 } },

  // ── Middle East ───────────────────────────────────────────
  { code: 'BEY', name: 'Beirut', airportName: 'Beirut Rafic Hariri International Airport', country: 'Lebanon', coords: { lat: 33.8209, lng: 35.4884 } },
  { code: 'AMM', name: 'Amman', airportName: 'Queen Alia International Airport', country: 'Jordan', coords: { lat: 31.7226, lng: 35.9932 } },
  { code: 'TLV', name: 'Tel Aviv (Israel)', airportName: 'Ben Gurion Airport', country: 'Israel', coords: { lat: 32.0055, lng: 34.8706 } },
  { code: 'DXB', name: 'Dubai', airportName: 'Dubai International Airport', country: 'UAE', coords: { lat: 25.2532, lng: 55.3657 } },
  { code: 'DOH', name: 'Doha', airportName: 'Hamad International Airport', country: 'Qatar', coords: { lat: 25.2609, lng: 51.6138 } },
  { code: 'BAH', name: 'Bahrain', airportName: 'Bahrain International Airport', country: 'Bahrain', coords: { lat: 26.2708, lng: 50.6336 } },
  { code: 'RUH', name: 'Riyadh', airportName: 'King Khalid International Airport', country: 'Saudi Arabia', coords: { lat: 24.9576, lng: 46.6988 } },

  // ── Turkey & Greece ───────────────────────────────────────
  { code: 'IST', name: 'Istanbul', airportName: 'Istanbul Airport', country: 'Turkey', coords: { lat: 41.2753, lng: 28.7519 } },
  { code: 'ADB', name: 'Izmir (Aegean Coast)', airportName: 'Adnan Menderes Airport', country: 'Turkey', coords: { lat: 38.2924, lng: 27.1570 } },
  { code: 'DNZ', name: 'Pamukkale (Denizli)', airportName: 'Çardak Airport', country: 'Turkey', coords: { lat: 37.7856, lng: 29.7013 } },
  { code: 'AYT', name: 'Antalya (Mediterranean Coast)', airportName: 'Antalya Airport', country: 'Turkey', coords: { lat: 36.8987, lng: 30.8005 } },
  { code: 'ASR', name: 'Cappadocia (Kayseri)', airportName: 'Kayseri Erkilet International Airport', country: 'Turkey', coords: { lat: 38.7704, lng: 35.4954 } },
  { code: 'JTR', name: 'Santorini (Greek Islands)', airportName: 'Santorini (Thira) National Airport', country: 'Greece', coords: { lat: 36.3992, lng: 25.4793 } },
  { code: 'ATH', name: 'Athens', airportName: 'Athens International Airport Eleftherios Venizelos', country: 'Greece', coords: { lat: 37.9364, lng: 23.9445 } },

  // ── Balkans & Eastern Europe ──────────────────────────────
  { code: 'SOF', name: 'Sofia', airportName: 'Sofia Airport', country: 'Bulgaria', coords: { lat: 42.6952, lng: 23.4114 } },
  { code: 'VAR', name: 'Varna', airportName: 'Varna Airport', country: 'Bulgaria', coords: { lat: 43.2321, lng: 27.8251 } },
  { code: 'OTP', name: 'Bucharest', airportName: 'Henri Coandă International Airport', country: 'Romania', coords: { lat: 44.5722, lng: 26.1022 } },
  { code: 'BEG', name: 'Belgrade', airportName: 'Belgrade Nikola Tesla Airport', country: 'Serbia', coords: { lat: 44.8184, lng: 20.3091 } },
  { code: 'SJJ', name: 'Sarajevo', airportName: 'Sarajevo International Airport', country: 'Bosnia and Herzegovina', coords: { lat: 43.8246, lng: 18.3315 } },
  { code: 'DBV', name: 'Dubrovnik', airportName: 'Dubrovnik Airport', country: 'Croatia', coords: { lat: 42.5614, lng: 18.2682 } },
  { code: 'SPU', name: 'Split', airportName: 'Split Airport', country: 'Croatia', coords: { lat: 43.5389, lng: 16.2998 } },
  { code: 'ZAG', name: 'Zagreb', airportName: 'Zagreb Airport', country: 'Croatia', coords: { lat: 45.7429, lng: 16.0688 } },

  // ── Caucasus & Central Asia ───────────────────────────────
  { code: 'EVN', name: 'Yerevan', airportName: 'Zvartnots International Airport', country: 'Armenia', coords: { lat: 40.1473, lng: 44.3959 } },
  { code: 'TAS', name: 'Tashkent', airportName: 'Tashkent International Airport', country: 'Uzbekistan', coords: { lat: 41.2579, lng: 69.2811 } },
  { code: 'ALA', name: 'Almaty', airportName: 'Almaty International Airport', country: 'Kazakhstan', coords: { lat: 43.3521, lng: 77.0405 } },
  { code: 'FRU', name: 'Bishkek', airportName: 'Manas International Airport', country: 'Kyrgyzstan', coords: { lat: 43.0613, lng: 74.4777 } },

  // ── East Asia & Southeast Asia ────────────────────────────
  { code: 'PVG', name: 'Shanghai', airportName: 'Shanghai Pudong International Airport', country: 'China', coords: { lat: 31.1443, lng: 121.8083 } },
  { code: 'PEK', name: 'Beijing', airportName: 'Beijing Capital International Airport', country: 'China', coords: { lat: 40.0799, lng: 116.6031 } },
  { code: 'KWL', name: 'Guilin (Yangshuo)', airportName: 'Guilin Liangjiang International Airport', country: 'China', coords: { lat: 25.2181, lng: 110.0390 } },
  { code: 'URC', name: 'Ürümqi', airportName: 'Ürümqi Diwopu International Airport', country: 'China', coords: { lat: 43.9071, lng: 87.4742 } },
  { code: 'TPE', name: 'Taipei', airportName: 'Taiwan Taoyuan International Airport', country: 'Taiwan', coords: { lat: 25.0777, lng: 121.2328 } },
  { code: 'NRT', name: 'Tokyo', airportName: 'Narita International Airport', country: 'Japan', coords: { lat: 35.7647, lng: 140.3864 } },
  { code: 'KTM', name: 'Kathmandu', airportName: 'Tribhuvan International Airport', country: 'Nepal', coords: { lat: 27.6966, lng: 85.3591 } },
  { code: 'PBH', name: 'Paro (Bhutan)', airportName: 'Paro International Airport', country: 'Bhutan', coords: { lat: 27.4033, lng: 89.4246 } },
  { code: 'SIN', name: 'Singapore', airportName: 'Singapore Changi Airport', country: 'Singapore', coords: { lat: 1.3644, lng: 103.9915 } },
  { code: 'DPS', name: 'Bali', airportName: 'Ngurah Rai International Airport', country: 'Indonesia', coords: { lat: -8.7482, lng: 115.1670 } },
  { code: 'MNL', name: 'Manila', airportName: 'Ninoy Aquino International Airport', country: 'Philippines', coords: { lat: 14.5086, lng: 121.0197 } },

  // ── Pacific ───────────────────────────────────────────────
  { code: 'GUM', name: 'Guam', airportName: 'Antonio B. Won Pat International Airport', country: 'USA', coords: { lat: 13.4834, lng: 144.7959 } },
  { code: 'PNI', name: 'Pohnpei (Micronesia)', airportName: 'Pohnpei International Airport', country: 'Micronesia', coords: { lat: 6.9851, lng: 158.2090 } },
  { code: 'HNL', name: 'Honolulu (Hawaii)', airportName: 'Daniel K. Inouye International Airport', country: 'USA', coords: { lat: 21.3187, lng: -157.9224 } },

  // ── North America ─────────────────────────────────────────
  { code: 'IAH', name: 'Houston', airportName: 'George Bush Intercontinental Airport', country: 'USA', coords: { lat: 29.9902, lng: -95.3368 } },
  { code: 'MSY', name: 'New Orleans', airportName: 'Louis Armstrong New Orleans International Airport', country: 'USA', coords: { lat: 29.9934, lng: -90.2580 } },
  { code: 'HAV', name: 'Havana', airportName: 'José Martí International Airport', country: 'Cuba', coords: { lat: 22.9892, lng: -82.4091 } },

  // ── South America ─────────────────────────────────────────
  { code: 'BOG', name: 'Bogotá', airportName: 'El Dorado International Airport', country: 'Colombia', coords: { lat: 4.7016, lng: -74.1469 } },
  { code: 'PEI', name: 'Pereira', airportName: 'Matecaña International Airport', country: 'Colombia', coords: { lat: 4.8127, lng: -75.7395 } },
  { code: 'CTG', name: 'Cartagena', airportName: 'Rafael Núñez International Airport', country: 'Colombia', coords: { lat: 10.4424, lng: -75.5130 } },
  { code: 'SMR', name: 'Santa Marta', airportName: 'Simón Bolívar International Airport', country: 'Colombia', coords: { lat: 11.1196, lng: -74.2306 } },
  { code: 'LET', name: 'Leticia', airportName: 'Alfredo Vásquez Cobo International Airport', country: 'Colombia', coords: { lat: -4.1933, lng: -69.9432 } },
  { code: 'MAO', name: 'Manaus', airportName: 'Eduardo Gomes International Airport', country: 'Brazil', coords: { lat: -3.0386, lng: -60.0497 } },
  { code: 'GIG', name: 'Rio de Janeiro', airportName: 'Rio de Janeiro Galeão International Airport', country: 'Brazil', coords: { lat: -22.8099, lng: -43.2505 } },
  { code: 'GRU', name: 'São Paulo', airportName: 'São Paulo/Guarulhos International Airport', country: 'Brazil', coords: { lat: -23.4356, lng: -46.4731 } },
  { code: 'SRE', name: 'Sucre (Southern Bolivia)', airportName: 'Alcantarí International Airport', country: 'Bolivia', coords: { lat: -19.2470, lng: -65.1549 } },
  { code: 'LPB', name: 'La Paz', airportName: 'El Alto International Airport', country: 'Bolivia', coords: { lat: -16.5133, lng: -68.1922 } },
  { code: 'IQQ', name: 'Iquique', airportName: 'Diego Aracena International Airport', country: 'Chile', coords: { lat: -20.5353, lng: -70.1812 } },
  { code: 'PMC', name: 'Puerto Montt', airportName: 'El Tepual International Airport', country: 'Chile', coords: { lat: -41.4389, lng: -73.0940 } },
  { code: 'SCL', name: 'Santiago', airportName: 'Arturo Merino Benítez International Airport', country: 'Chile', coords: { lat: -33.3930, lng: -70.7858 } },
  { code: 'MDZ', name: 'Mendoza', airportName: 'Governor Francisco Gabrielli International Airport', country: 'Argentina', coords: { lat: -32.8317, lng: -68.7929 } },
  { code: 'EZE', name: 'Buenos Aires', airportName: 'Ministro Pistarini International Airport', country: 'Argentina', coords: { lat: -34.8222, lng: -58.5358 } },
  { code: 'GPS', name: 'Galápagos Islands', airportName: 'Seymour Airport', country: 'Ecuador', coords: { lat: -0.4538, lng: -90.2659 } },
  { code: 'FTE', name: 'El Calafate (Patagonia)', airportName: 'Comandante Armando Tola International Airport', country: 'Argentina', coords: { lat: -50.2803, lng: -72.0531 } },

  // ── Oceania ───────────────────────────────────────────────
  { code: 'AKL', name: 'Auckland', airportName: 'Auckland Airport', country: 'New Zealand', coords: { lat: -37.0082, lng: 174.7850 } },
  { code: 'TRG', name: 'Tauranga', airportName: 'Tauranga Airport', country: 'New Zealand', coords: { lat: -37.6719, lng: 176.1961 } },
  { code: 'WLG', name: 'Wellington', airportName: 'Wellington International Airport', country: 'New Zealand', coords: { lat: -41.3272, lng: 174.8050 } },
  { code: 'CHC', name: 'Christchurch', airportName: 'Christchurch Airport', country: 'New Zealand', coords: { lat: -43.4894, lng: 172.5322 } },
  { code: 'NSN', name: 'Nelson', airportName: 'Nelson Airport', country: 'New Zealand', coords: { lat: -41.2983, lng: 173.2211 } },
  { code: 'ZQN', name: 'Queenstown', airportName: 'Queenstown Airport', country: 'New Zealand', coords: { lat: -45.0211, lng: 168.7392 } },
  { code: 'SYD', name: 'Sydney', airportName: 'Sydney Kingsford Smith Airport', country: 'Australia', coords: { lat: -33.9399, lng: 151.1753 } },
  { code: 'CNS', name: 'Cairns', airportName: 'Cairns Airport', country: 'Australia', coords: { lat: -16.8858, lng: 145.7552 } },

  // ── Sub-Saharan Africa ────────────────────────────────────
  { code: 'CPT', name: 'Cape Town', airportName: 'Cape Town International Airport', country: 'South Africa', coords: { lat: -33.9715, lng: 18.6021 } },
  { code: 'GBE', name: 'Gaborone', airportName: 'Sir Seretse Khama International Airport', country: 'Botswana', coords: { lat: -24.5552, lng: 25.9182 } },
  { code: 'KGL', name: 'Kigali', airportName: 'Kigali International Airport', country: 'Rwanda', coords: { lat: -1.9686, lng: 30.1395 } },
  { code: 'WDH', name: 'Windhoek', airportName: 'Hosea Kutako International Airport', country: 'Namibia', coords: { lat: -22.4799, lng: 17.4709 } },
];
