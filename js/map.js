// CitizenShield - Municipal GIS & Leaflet Geo-Explorer

let reportMapInstance = null;
let reportMarker = null;
let cityMapInstance = null;
let cityMarkerGroup = null;

// Default city center (Bengaluru Central Municipal Ward)
const DEFAULT_CENTER = [12.9716, 77.5946];
const DEFAULT_ZOOM = 13;

/**
 * Initializes the pin-dropping map in the Report Issue form
 */
export function initReportMap(containerId, onLocationPicked) {
  if (typeof L === 'undefined') {
    console.warn("Leaflet library not loaded yet.");
    return null;
  }

  const container = document.getElementById(containerId);
  if (!container) return null;

  if (reportMapInstance) {
    reportMapInstance.remove();
    reportMapInstance = null;
  }

  try {
    reportMapInstance = L.map(containerId).setView(DEFAULT_CENTER, DEFAULT_ZOOM);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '© OpenStreetMap contributors | CitizenShield GIS'
    }).addTo(reportMapInstance);

    // Map Click Listener
    reportMapInstance.on('click', async (e) => {
      const { lat, lng } = e.latlng;
      setReportMapPin(lat, lng);
      if (typeof onLocationPicked === 'function') {
        onLocationPicked(lat, lng);
      }
    });

    // Invalidate size after modal/container becomes visible
    setTimeout(() => {
      reportMapInstance.invalidateSize();
    }, 200);

    return reportMapInstance;
  } catch (err) {
    console.error("Failed to initialize Report Map:", err);
    return null;
  }
}

/**
 * Updates marker position on the report map
 */
export function setReportMapPin(lat, lng, zoom = 16) {
  if (!reportMapInstance || typeof L === 'undefined') return;

  if (reportMarker) {
    reportMarker.setLatLng([lat, lng]);
  } else {
    reportMarker = L.marker([lat, lng], { draggable: true }).addTo(reportMapInstance);
    reportMarker.on('dragend', () => {
      const pos = reportMarker.getLatLng();
      const inputLat = document.getElementById('report-lat');
      const inputLng = document.getElementById('report-lng');
      if (inputLat) inputLat.value = pos.lat.toFixed(6);
      if (inputLng) inputLng.value = pos.lng.toFixed(6);
    });
  }

  reportMapInstance.setView([lat, lng], zoom, { animate: true });
}

/**
 * Initializes the city-wide live grievance heatmap & pin cluster map
 */
export function initCityMap(containerId, pins = []) {
  if (typeof L === 'undefined') return null;

  const container = document.getElementById(containerId);
  if (!container) return null;

  if (cityMapInstance) {
    cityMapInstance.remove();
    cityMapInstance = null;
  }

  try {
    cityMapInstance = L.map(containerId).setView(DEFAULT_CENTER, 12);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '© OpenStreetMap | Municipal Dispatch GIS'
    }).addTo(cityMapInstance);

    cityMarkerGroup = L.layerGroup().addTo(cityMapInstance);
    updateCityMapPins(pins);

    setTimeout(() => {
      cityMapInstance.invalidateSize();
    }, 250);

    return cityMapInstance;
  } catch (err) {
    console.error("Failed to initialize City GIS Map:", err);
    return null;
  }
}

/**
 * Populates pins across the municipal city map
 */
export function updateCityMapPins(pins = []) {
  if (!cityMarkerGroup || typeof L === 'undefined') return;

  cityMarkerGroup.clearLayers();

  const colorMap = {
    'Urgent': '#dc2626',
    'High': '#ea580c',
    'Normal': '#2563eb',
    'Low': '#64748b'
  };

  const statusBg = {
    'Submitted': '#f1f5f9',
    'Under Review': '#e0f2fe',
    'In Progress': '#fef3c7',
    'Resolved': '#dcfce7',
    'Rejected': '#fee2e2'
  };

  pins.forEach(pin => {
    if (!pin.latitude || !pin.longitude) return;

    const dotColor = colorMap[pin.priority] || '#2563eb';

    // Custom tactical marker icon
    const icon = L.divIcon({
      className: 'custom-gis-pin',
      html: `<div style="
        background-color: ${dotColor};
        width: 22px;
        height: 22px;
        border-radius: 50%;
        border: 2px solid #ffffff;
        box-shadow: 0 2px 6px rgba(0,0,0,0.35);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 10px;
        font-weight: bold;
      ">●</div>`,
      iconSize: [24, 24],
      iconAnchor: [12, 12]
    });

    const marker = L.marker([pin.latitude, pin.longitude], { icon });

    const popupHtml = `
      <div style="font-family: system-ui, sans-serif; font-size: 12px; line-height: 1.4; min-width: 200px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
          <span style="font-family: monospace; font-weight: bold; color: #1d4ed8;">${pin.report_id}</span>
          <span style="background: ${statusBg[pin.status] || '#f1f5f9'}; padding: 2px 6px; border-radius: 4px; font-weight: 700; font-size: 10px; text-transform: uppercase;">${pin.status}</span>
        </div>
        <div style="font-weight: 700; font-size: 13px; color: #0f172a; margin-bottom: 4px;">${escapeHtml(pin.title)}</div>
        <div style="color: #64748b; margin-bottom: 2px;">🏢 ${escapeHtml(pin.department || pin.category)}</div>
        <div style="color: #475569; margin-bottom: 8px;">📍 ${escapeHtml(pin.location || pin.ward || '')}</div>
        <button 
          onclick="window.trackReportFromMap('${pin.report_id}')"
          style="
            background: #1d4ed8;
            color: #ffffff;
            border: none;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            cursor: pointer;
            width: 100%;
          ">Inspect Grievance Dossier →</button>
      </div>
    `;

    marker.bindPopup(popupHtml);
    cityMarkerGroup.addLayer(marker);
  });
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
