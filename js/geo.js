// CitizenShield - Geolocation Consent & Handling

let currentLocation = null;

/**
 * Request user's current GPS location with explicit consent
 * @returns {Promise<{latitude: number, longitude: number, accuracy: number, address?: string}>}
 */
export async function getGPSLocation() {
  if (!navigator.geolocation) {
    throw new Error("Geolocation is not supported by your browser. Please enter your address manually.");
  }

  return new Promise((resolve, reject) => {
    const options = {
      enableHighAccuracy: true,
      timeout: 12000,
      maximumAge: 60000
    };

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude, accuracy } = position.coords;
        let address = `Coordinates: ${latitude.toFixed(5)}, ${longitude.toFixed(5)}`;
        
        // Attempt lightweight reverse geocode using public OpenStreetMap Nominatim API
        try {
          const res = await fetch(
            `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${latitude}&lon=${longitude}`,
            { headers: { 'Accept': 'application/json' } }
          );
          if (res.ok) {
            const data = await res.json();
            if (data && data.display_name) {
              address = data.display_name;
            }
          }
        } catch (e) {
          // If network / CORS prevents reverse geocoding, fallback to coordinate string
          console.debug("Reverse geocoding not reachable, using raw coordinates", e);
        }

        currentLocation = {
          latitude,
          longitude,
          accuracy,
          address
        };

        resolve(currentLocation);
      },
      (error) => {
        let msg = "Failed to obtain location.";
        switch (error.code) {
          case error.PERMISSION_DENIED:
            msg = "Location access was denied. You can enter your address or landmark manually.";
            break;
          case error.POSITION_UNAVAILABLE:
            msg = "Location information is unavailable on your device. Please enter address manually.";
            break;
          case error.TIMEOUT:
            msg = "Location request timed out. Please check your GPS or enter address manually.";
            break;
        }
        reject(new Error(msg));
      },
      options
    );
  });
}

/**
 * Returns currently captured location
 */
export function getCurrentLocation() {
  return currentLocation;
}

/**
 * Clears cached location
 */
export function clearCurrentLocation() {
  currentLocation = null;
}
