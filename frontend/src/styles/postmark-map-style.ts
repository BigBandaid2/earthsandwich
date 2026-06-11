// Google Maps style array — "Postmark" sepia theme.
// Pass to the <Map> component via the styles prop.
const postmarkMapStyle: google.maps.MapTypeStyle[] = [
  { elementType: 'geometry', stylers: [{ color: '#E7DCC4' }] },
  { elementType: 'labels.icon', stylers: [{ visibility: 'off' }] },
  { elementType: 'labels.text.fill', stylers: [{ color: '#6C6253' }] },
  { elementType: 'labels.text.stroke', stylers: [{ color: '#F4EDDF' }, { weight: 2 }] },

  { featureType: 'administrative', elementType: 'geometry.stroke', stylers: [{ color: '#D8CBAE' }] },
  { featureType: 'administrative.country', elementType: 'geometry.stroke', stylers: [{ color: '#C9B894' }, { weight: 1 }] },
  { featureType: 'administrative.land_parcel', stylers: [{ visibility: 'off' }] },
  { featureType: 'administrative.province', elementType: 'geometry.stroke', stylers: [{ color: '#DBCFB2' }] },
  { featureType: 'administrative.locality', elementType: 'labels.text.fill', stylers: [{ color: '#2B2620' }] },
  { featureType: 'administrative.neighborhood', stylers: [{ visibility: 'off' }] },

  { featureType: 'landscape.natural', elementType: 'geometry', stylers: [{ color: '#E7DCC4' }] },
  { featureType: 'landscape.man_made', elementType: 'geometry', stylers: [{ color: '#E2D6BC' }] },

  { featureType: 'poi', stylers: [{ visibility: 'off' }] },
  { featureType: 'poi.park', elementType: 'geometry', stylers: [{ color: '#DCD3B6' }] },
  { featureType: 'poi.park', elementType: 'labels.text.fill', stylers: [{ color: '#8A7A5C' }] },

  { featureType: 'road', elementType: 'geometry', stylers: [{ color: '#F0E7D5' }] },
  { featureType: 'road', elementType: 'labels', stylers: [{ visibility: 'off' }] },
  { featureType: 'road.arterial', elementType: 'geometry', stylers: [{ color: '#EDE3CF' }] },
  { featureType: 'road.highway', elementType: 'geometry', stylers: [{ color: '#E6D9BD' }] },
  { featureType: 'road.highway', elementType: 'geometry.stroke', stylers: [{ color: '#D8CBAE' }] },

  { featureType: 'transit', stylers: [{ visibility: 'off' }] },

  { featureType: 'water', elementType: 'geometry', stylers: [{ color: '#F4ECD9' }] },
  { featureType: 'water', elementType: 'labels.text.fill', stylers: [{ color: '#B6AC95' }] },
];

export default postmarkMapStyle;
