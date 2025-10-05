// utils/timezone.ts
import type { Location } from '../types/app';

/**
 * Detecting timezone from coordinates using a free API with fallback to manual mapping
 */
export const getTimezoneFromLocation = async (location: Location): Promise<string> => {
  try {
    const response = await fetch(
      `https://api.timezonedb.com/v2.1/get-time-zone?key=demo&format=json&by=position&lat=${location.latitude}&lng=${location.longitude}`
    );
    
    if (response.ok) {
      const data = await response.json();
      if (data.zoneName) {
        return data.zoneName;
      }
    }
  } catch (error) {
    console.warn('Error fetching timezone from API:', error);
  }

  return getTimezoneByCountryAndCoordinates(location);
};


const getTimezoneByCountryAndCoordinates = (location: Location): string => {
  const { country, latitude, longitude } = location;

  if (country === 'BR' || country === 'Brazil') {
    if (longitude < -67) {
      return 'America/Rio_Branco';
    }
    else if (longitude < -57 || (latitude > -10 && longitude < -60)) {
      return 'America/Manaus';
    }
    else if (latitude < -3 && longitude > -33) {
      return 'America/Noronha';
    }
    else {
      return 'America/Sao_Paulo';
    }
  }

  if (country === 'US' || country === 'United States') {
    if (longitude > -87) return 'America/New_York';        
    if (longitude > -102) return 'America/Chicago';        
    if (longitude > -115) return 'America/Denver';         
    return 'America/Los_Angeles';                          
  }

  // Argentina
  if (country === 'AR' || country === 'Argentina') {
    return 'America/Argentina/Buenos_Aires';
  }

  // Chile
  if (country === 'CL' || country === 'Chile') {
    return 'America/Santiago';
  }

  // Colombia
  if (country === 'CO' || country === 'Colombia') {
    return 'America/Bogota';
  }

  // Venezuela
  if (country === 'VE' || country === 'Venezuela') {
    return 'America/Caracas';
  }

  // Peru
  if (country === 'PE' || country === 'Peru') {
    return 'America/Lima';
  }

  // Mexico
  if (country === 'MX' || country === 'Mexico') {
    return 'America/Mexico_City';
  }

  // UK
  if (country === 'GB' || country === 'UK' || country === 'United Kingdom') {
    return 'Europe/London';
  }

  // France
  if (country === 'FR' || country === 'France') {
    return 'Europe/Paris';
  }

  // Germany
  if (country === 'DE' || country === 'Germany') {
    return 'Europe/Berlin';
  }

  // Spain
  if (country === 'ES' || country === 'Spain') {
    return 'Europe/Madrid';
  }

  // Portugal
  if (country === 'PT' || country === 'Portugal') {
    return 'Europe/Lisbon';
  }

  // Italy
  if (country === 'IT' || country === 'Italy') {
    return 'Europe/Rome';
  }

  // Japan
  if (country === 'JP' || country === 'Japan') {
    return 'Asia/Tokyo';
  }

  // China
  if (country === 'CN' || country === 'China') {
    return 'Asia/Shanghai';
  }

  // India
  if (country === 'IN' || country === 'India') {
    return 'Asia/Kolkata';
  }

  // Australia 
  if (country === 'AU' || country === 'Australia') {
    if (longitude < 130) return 'Australia/Perth';      // Western
    if (longitude < 140) return 'Australia/Adelaide';   // Central
    return 'Australia/Sydney';                          // Eastern
  }

  return getTimezoneByCoordinates(latitude, longitude);
};


const getTimezoneByCoordinates = (_latitude: number, longitude: number): string => {
  const timezoneOffset = Math.round(longitude / 15);
  
  const timezoneMap: { [key: string]: string } = {
    '-12': 'Pacific/Auckland',      // UTC-12
    '-11': 'Pacific/Samoa',         // UTC-11
    '-10': 'Pacific/Honolulu',      // UTC-10
    '-9': 'America/Anchorage',      // UTC-9
    '-8': 'America/Los_Angeles',    // UTC-8
    '-7': 'America/Denver',         // UTC-7
    '-6': 'America/Chicago',        // UTC-6
    '-5': 'America/New_York',       // UTC-5
    '-4': 'America/Caracas',        // UTC-4
    '-3': 'America/Sao_Paulo',      // UTC-3
    '-2': 'America/Noronha',        // UTC-2
    '-1': 'Atlantic/Azores',        // UTC-1
    '0': 'Europe/London',           // UTC+0
    '1': 'Europe/Paris',            // UTC+1
    '2': 'Europe/Berlin',           // UTC+2
    '3': 'Europe/Moscow',           // UTC+3
    '4': 'Asia/Dubai',              // UTC+4
    '5': 'Asia/Karachi',            // UTC+5
    '6': 'Asia/Dhaka',              // UTC+6
    '7': 'Asia/Bangkok',            // UTC+7
    '8': 'Asia/Shanghai',           // UTC+8
    '9': 'Asia/Tokyo',              // UTC+9
    '10': 'Australia/Sydney',       // UTC+10
    '11': 'Pacific/Norfolk',        // UTC+11
    '12': 'Pacific/Auckland'        // UTC+12
  };

  return timezoneMap[timezoneOffset.toString()] || 'UTC';
};


export const getTimezoneFromLocationSync = (location: Location): string => {
  return getTimezoneByCountryAndCoordinates(location);
};
