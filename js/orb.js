// CitizenShield - High-End 3D Dotted Earth Globe & Interactive Holographic GIS

// Accurate world continent boundary polygons (Longitude: -180 to 180, Latitude: -90 to 90)
const CONTINENT_POLYGONS = [
  // North America (Alaska, Canada, USA, Mexico)
  [
    [-168, 65], [-140, 70], [-120, 72], [-95, 75], [-80, 70], [-60, 60],
    [-65, 45], [-75, 35], [-80, 25], [-98, 26], [-82, 9], [-77, 8],
    [-90, 15], [-105, 20], [-120, 34], [-125, 49], [-140, 58], [-168, 65]
  ],
  // Greenland
  [
    [-55, 60], [-20, 70], [-25, 82], [-50, 83], [-60, 75], [-55, 60]
  ],
  // South America
  [
    [-77, 8], [-60, 10], [-50, 2], [-35, -5], [-35, -12], [-40, -22],
    [-50, -30], [-55, -35], [-65, -55], [-75, -50], [-75, -20], [-80, -2], [-77, 8]
  ],
  // Western & Central Europe
  [
    [-10, 36], [-9, 44], [2, 51], [10, 54], [25, 71], [40, 68],
    [35, 52], [30, 45], [25, 36], [-5, 36], [-10, 36]
  ],
  // British Isles
  [
    [-10, 50], [-5, 58], [2, 58], [1, 51], [-5, 50], [-10, 50]
  ],
  // Scandinavia
  [
    [5, 58], [15, 56], [28, 70], [18, 71], [5, 62], [5, 58]
  ],
  // Africa
  [
    [-17, 32], [10, 37], [32, 32], [43, 12], [51, 12], [42, -5],
    [35, -25], [20, -35], [15, -30], [10, 0], [-15, 12], [-17, 32]
  ],
  // Arabian Peninsula
  [
    [35, 30], [55, 25], [60, 22], [54, 16], [44, 12], [40, 20], [35, 30]
  ],
  // Madagascar
  [
    [44, -12], [50, -15], [48, -25], [44, -25], [44, -12]
  ],
  // Asia & Siberia
  [
    [50, 40], [60, 40], [45, 68], [60, 72], [100, 78], [170, 70],
    [180, 65], [160, 55], [142, 50], [130, 40], [120, 30], [105, 20],
    [105, 10], [80, 10], [70, 25], [60, 25], [50, 40]
  ],
  // India & Sri Lanka (Distinct triangular subcontinental wedge)
  [
    [68, 25], [78, 32], [88, 25], [88, 20], [82, 8], [75, 10], [70, 18], [68, 25]
  ],
  // Japan
  [
    [130, 32], [140, 36], [142, 44], [138, 38], [130, 32]
  ],
  // Southeast Asia & Indonesia
  [
    [98, 5], [105, -5], [115, -8], [125, -8], [110, 5], [98, 5]
  ],
  // Australia & Tasmania
  [
    [114, -22], [114, -35], [135, -38], [150, -38], [153, -28], [142, -11], [130, -13], [114, -22]
  ],
  // New Zealand
  [
    [166, -46], [174, -42], [178, -35], [174, -35], [168, -43], [166, -46]
  ],
  // Antarctica ice shelf
  [
    [-180, -68], [180, -68], [180, -90], [-180, -90], [-180, -68]
  ]
];

// Key Municipal City Beacons
const GLOBAL_BEACONS = [
  { name: "Bengaluru (Ward 112)", lat: 12.9716, lng: 77.5946, primary: true, code: "BLR" },
  { name: "New Delhi", lat: 28.6139, lng: 77.2090, primary: false, code: "DEL" },
  { name: "London", lat: 51.5074, lng: -0.1278, primary: false, code: "LDN" },
  { name: "New York", lat: 40.7128, lng: -74.0060, primary: false, code: "NYC" },
  { name: "Tokyo", lat: 35.6762, lng: 139.6503, primary: false, code: "TYO" },
  { name: "Dubai", lat: 25.2048, lng: 55.2708, primary: false, code: "DXB" },
  { name: "Sydney", lat: -33.8688, lng: 151.2093, primary: false, code: "SYD" }
];

function pointInPolygon(lon, lat, poly) {
  let inside = false;
  const n = poly.length;
  let p1x = poly[0][0];
  let p1y = poly[0][1];
  for (let i = 1; i <= n; i++) {
    const p2 = poly[i % n];
    const p2x = p2[0];
    const p2y = p2[1];
    if (lat > Math.min(p1y, p2y) && lat <= Math.max(p1y, p2y)) {
      if (lon <= Math.max(p1x, p2x)) {
        if (p1y !== p2y) {
          const xinters = (lat - p1y) * (p2x - p1x) / (p2y - p1y) + p1x;
          if (p1x === p2x || lon <= xinters) {
            inside = !inside;
          }
        }
      }
    }
    p1x = p2x;
    p1y = p2y;
  }
  return inside;
}

function isEarthLand(lon, lat) {
  for (let i = 0; i < CONTINENT_POLYGONS.length; i++) {
    if (pointInPolygon(lon, lat, CONTINENT_POLYGONS[i])) {
      return true;
    }
  }
  return false;
}

export class StippleOrb {
  constructor(canvasId, options = {}) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;

    this.ctx = this.canvas.getContext('2d');
    this.numPoints = options.numPoints || 4200; // High resolution point density
    this.rotationX = 0.22; // Natural 23.5 deg axial tilt
    this.rotationY = -1.35; // Centered on India / Indian Ocean
    this.targetRotationX = null;
    this.targetRotationY = null;
    this.velX = 0;
    this.velY = 0;
    this.isDragging = false;
    this.lastMouseX = 0;
    this.lastMouseY = 0;
    this.autoSpin = true;
    this.zoomScale = 1.0;

    this.points = [];
    this.beacons = [];
    this.arcs = [];
    this.telemetryTimer = 0;

    this.initPoints();
    this.initBeacons();
    this.initArcs();
    this.resize();

    window.addEventListener('resize', () => this.resize());
    this.bindEvents();
    this.wireHudButtons();
    this.animate();
  }

  resize() {
    if (!this.canvas) return;
    const rect = this.canvas.parentElement.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    this.width = rect.width;
    this.height = rect.height;
    this.canvas.width = this.width * dpr;
    this.canvas.height = this.height * dpr;
    this.ctx.scale(dpr, dpr);
    this.baseRadius = Math.min(this.width, this.height) * 0.42;
    this.radius = this.baseRadius * this.zoomScale;
  }

  initPoints() {
    this.points = [];
    const phi = Math.PI * (3 - Math.sqrt(5)); // Golden spiral angle

    // 1. Fibonacci Sphere Surface Points
    for (let i = 0; i < this.numPoints; i++) {
      const y = 1 - (i / (this.numPoints - 1)) * 2; // -1 to 1
      const radiusAtY = Math.sqrt(Math.max(0, 1 - y * y));
      const theta = phi * i;

      const x = Math.cos(theta) * radiusAtY;
      const z = Math.sin(theta) * radiusAtY;

      // Spherical coordinates -> Latitude / Longitude
      const lat = Math.asin(y) * (180 / Math.PI);
      const lon = Math.atan2(x, z) * (180 / Math.PI);

      const isLand = isEarthLand(lon, lat);

      this.points.push({
        x,
        y: -y, // Inverted Y for screen projection
        z,
        lon,
        lat,
        isLand,
        baseSize: isLand ? 1.8 + Math.random() * 0.7 : 0.85,
        pulseOffset: Math.random() * Math.PI * 2,
        pulseSpeed: 0.02 + Math.random() * 0.03
      });
    }

    // 2. Latitude Rings (Equator, Tropics, Arctic, Antarctic)
    const graticuleLats = [0, 23.5, -23.5, 66.5, -66.5];
    graticuleLats.forEach(ringLat => {
      const radLat = ringLat * (Math.PI / 180);
      const y = -Math.sin(radLat);
      const rRing = Math.cos(radLat);
      for (let lon = -180; lon < 180; lon += 6) {
        const radLon = lon * (Math.PI / 180);
        const x = Math.sin(radLon) * rRing;
        const z = Math.cos(radLon) * rRing;
        this.points.push({
          x,
          y,
          z,
          lon,
          lat: ringLat,
          isGraticule: true,
          baseSize: ringLat === 0 ? 0.9 : 0.65,
          pulseOffset: 0,
          pulseSpeed: 0.01
        });
      }
    });

    // 3. Longitude Meridians (Every 45 degrees)
    for (let lon = -180; lon < 180; lon += 45) {
      const radLon = lon * (Math.PI / 180);
      for (let lat = -80; lat <= 80; lat += 6) {
        const radLat = lat * (Math.PI / 180);
        const y = -Math.sin(radLat);
        const rRing = Math.cos(radLat);
        const x = Math.sin(radLon) * rRing;
        const z = Math.cos(radLon) * rRing;
        this.points.push({
          x,
          y,
          z,
          lon,
          lat,
          isGraticule: true,
          baseSize: 0.6,
          pulseOffset: 0,
          pulseSpeed: 0.01
        });
      }
    }
  }

  initBeacons() {
    this.beacons = GLOBAL_BEACONS.map(b => {
      const radLat = b.lat * (Math.PI / 180);
      const radLon = b.lng * (Math.PI / 180);
      const y = -Math.sin(radLat);
      const rRing = Math.cos(radLat);
      const x = Math.sin(radLon) * rRing;
      const z = Math.cos(radLon) * rRing;
      return {
        ...b,
        x,
        y,
        z,
        ping: Math.random()
      };
    });
  }

  initArcs() {
    // 3D Telemetry Links between Major Municipal Hubs
    this.arcs = [
      { from: "London", to: "Bengaluru (Ward 112)", progress: 0.15, speed: 0.007 },
      { from: "New York", to: "London", progress: 0.60, speed: 0.006 },
      { from: "Tokyo", to: "Bengaluru (Ward 112)", progress: 0.35, speed: 0.008 }
    ];
  }

  bindEvents() {
    const el = this.canvas;

    const onPointerDown = (e) => {
      this.isDragging = true;
      this.targetRotationX = null;
      this.targetRotationY = null;
      this.lastMouseX = e.clientX || (e.touches && e.touches[0].clientX) || 0;
      this.lastMouseY = e.clientY || (e.touches && e.touches[0].clientY) || 0;
      this.velX = 0;
      this.velY = 0;
    };

    const onPointerMove = (e) => {
      if (!this.isDragging) return;
      const clientX = e.clientX || (e.touches && e.touches[0].clientX) || 0;
      const clientY = e.clientY || (e.touches && e.touches[0].clientY) || 0;

      const deltaX = clientX - this.lastMouseX;
      const deltaY = clientY - this.lastMouseY;

      this.velY = deltaX * 0.004;
      this.velX = -deltaY * 0.004;

      this.rotationY += this.velY;
      this.rotationX += this.velX;

      this.lastMouseX = clientX;
      this.lastMouseY = clientY;
    };

    const onPointerUp = () => {
      this.isDragging = false;
    };

    el.addEventListener('mousedown', onPointerDown);
    window.addEventListener('mousemove', onPointerMove);
    window.addEventListener('mouseup', onPointerUp);

    el.addEventListener('touchstart', onPointerDown, { passive: true });
    window.addEventListener('touchmove', onPointerMove, { passive: true });
    window.addEventListener('touchend', onPointerUp, { passive: true });

    // Subtle Wheel Zoom
    el.addEventListener('wheel', (e) => {
      e.preventDefault();
      const delta = e.deltaY * -0.001;
      this.zoomScale = Math.min(1.35, Math.max(0.85, this.zoomScale + delta));
      this.radius = this.baseRadius * this.zoomScale;
    }, { passive: false });
  }

  wireHudButtons() {
    const btnFocus = document.getElementById('btn-focus-ward');
    if (btnFocus) {
      btnFocus.addEventListener('click', () => {
        this.focusWard();
      });
    }

    const btnSpin = document.getElementById('btn-toggle-spin');
    if (btnSpin) {
      btnSpin.addEventListener('click', () => {
        this.autoSpin = !this.autoSpin;
        btnSpin.textContent = this.autoSpin ? "Spin: On" : "Spin: Off";
        btnSpin.classList.toggle('active', !this.autoSpin);
      });
    }
  }

  focusWard(lat = 12.9716, lon = 77.5946) {
    // Smoothly interpolate rotation to face Bengaluru
    const radLon = lon * (Math.PI / 180);
    const radLat = lat * (Math.PI / 180);
    this.targetRotationY = -radLon;
    this.targetRotationX = radLat * 0.75;
    this.autoSpin = false;

    const btnSpin = document.getElementById('btn-toggle-spin');
    if (btnSpin) {
      btnSpin.textContent = "Spin: Off";
      btnSpin.classList.add('active');
    }
  }

  animate() {
    if (!this.ctx) return;

    this.ctx.clearRect(0, 0, this.width, this.height);

    // Target tracking interpolation
    if (this.targetRotationX !== null && this.targetRotationY !== null) {
      this.rotationX += (this.targetRotationX - this.rotationX) * 0.08;
      this.rotationY += (this.targetRotationY - this.rotationY) * 0.08;
      if (
        Math.abs(this.targetRotationX - this.rotationX) < 0.002 &&
        Math.abs(this.targetRotationY - this.rotationY) < 0.002
      ) {
        this.targetRotationX = null;
        this.targetRotationY = null;
      }
    } else if (!this.isDragging) {
      // Inertia & Continuous gentle spin
      this.velX *= 0.94;
      this.velY *= 0.94;
      this.rotationX += this.velX;
      this.rotationY += this.velY;

      if (this.autoSpin) {
        this.rotationY += 0.0024;
      }

      // Restrict latitude tilt to natural angles
      this.rotationX = Math.max(-0.65, Math.min(0.65, this.rotationX));
    }

    // Telemetry Coordinate Readout Update (Live sub-satellite lat/lon)
    this.telemetryTimer++;
    if (this.telemetryTimer % 6 === 0) {
      const coordEl = document.getElementById('pod-live-coords');
      if (coordEl) {
        let centerLon = ((-this.rotationY * (180 / Math.PI)) % 360);
        if (centerLon > 180) centerLon -= 360;
        if (centerLon < -180) centerLon += 360;
        const centerLat = (this.rotationX * (180 / Math.PI));

        const latStr = `${Math.abs(centerLat).toFixed(2)}° ${centerLat >= 0 ? 'N' : 'S'}`;
        const lonStr = `${Math.abs(centerLon).toFixed(2)}° ${centerLon >= 0 ? 'E' : 'W'}`;
        coordEl.textContent = `${latStr}, ${lonStr}`;
      }
    }

    const centerX = this.width / 2;
    const centerY = this.height / 2;
    const R = this.radius;
    const time = Date.now() * 0.0018;

    // 1. Atmospheric Lagoon Rim Glow
    const atmosGrad = this.ctx.createRadialGradient(
      centerX, centerY, R * 0.75,
      centerX, centerY, R * 1.30
    );
    atmosGrad.addColorStop(0, 'rgba(6, 182, 212, 0.03)');
    atmosGrad.addColorStop(0.7, 'rgba(16, 185, 129, 0.15)');
    atmosGrad.addColorStop(0.96, 'rgba(45, 212, 191, 0.28)');
    atmosGrad.addColorStop(1, 'rgba(3, 8, 12, 0)');

    this.ctx.fillStyle = atmosGrad;
    this.ctx.beginPath();
    this.ctx.arc(centerX, centerY, R * 1.30, 0, Math.PI * 2);
    this.ctx.fill();

    // 2. Translucent Planetary Body with Depth Gradient
    const sphereGrad = this.ctx.createRadialGradient(
      centerX - R * 0.25, centerY - R * 0.25, R * 0.1,
      centerX, centerY, R
    );
    sphereGrad.addColorStop(0, 'rgba(8, 34, 44, 0.92)');
    sphereGrad.addColorStop(0.7, 'rgba(4, 18, 24, 0.96)');
    sphereGrad.addColorStop(1, 'rgba(2, 10, 14, 1)');

    this.ctx.fillStyle = sphereGrad;
    this.ctx.beginPath();
    this.ctx.arc(centerX, centerY, R, 0, Math.PI * 2);
    this.ctx.fill();

    // Precision Specular Edge Ring
    this.ctx.strokeStyle = 'rgba(45, 212, 191, 0.35)';
    this.ctx.lineWidth = 1.2;
    this.ctx.stroke();

    // Rotation Matrices
    const cosX = Math.cos(this.rotationX);
    const sinX = Math.sin(this.rotationX);
    const cosY = Math.cos(this.rotationY);
    const sinY = Math.sin(this.rotationY);

    // 3. Project and Render 3D Dotted Surface
    const projected = [];

    for (let i = 0; i < this.points.length; i++) {
      const p = this.points[i];

      // Y-axis rotation
      const x1 = p.x * cosY - p.z * sinY;
      const z1 = p.z * cosY + p.x * sinY;

      // X-axis rotation
      const y2 = p.y * cosX - z1 * sinX;
      const z2 = z1 * cosX + p.y * sinX;

      // Render visible hemisphere + back edge gradient
      if (z2 > -0.25) {
        const fov = 650;
        const scale = fov / (fov + z2 * R);
        const projX = centerX + x1 * R * scale;
        const projY = centerY + y2 * R * scale;

        const pulse = Math.sin(time * 3 + p.pulseOffset) * 0.15 + 0.85;
        const depthAlpha = Math.max(0.08, Math.min(1, (z2 + 0.3) * 0.9));

        let color, size;

        if (p.isLand) {
          // Luminous emerald / lagoon cyan for continents
          color = `rgba(45, 212, 191, ${depthAlpha * pulse * 0.98})`;
          size = p.baseSize * scale * (z2 > 0 ? 1.3 : 0.85);
        } else if (p.isGraticule) {
          // Subtle graticule grid lines
          color = `rgba(6, 182, 212, ${depthAlpha * 0.35})`;
          size = p.baseSize * scale;
        } else {
          // Very faint deep ocean dots for contrast
          color = `rgba(14, 116, 144, ${depthAlpha * 0.22})`;
          size = p.baseSize * scale;
        }

        projected.push({
          x: projX,
          y: projY,
          z: z2,
          size,
          color,
          isLand: p.isLand
        });
      }
    }

    // Sort back-to-front for proper depth layering
    projected.sort((a, b) => a.z - b.z);

    // Draw Points
    for (let i = 0; i < projected.length; i++) {
      const pt = projected[i];
      this.ctx.fillStyle = pt.color;
      this.ctx.beginPath();
      this.ctx.arc(pt.x, pt.y, Math.max(0.5, pt.size), 0, Math.PI * 2);
      this.ctx.fill();
    }

    // 4. Render Telemetry Arcs
    this.renderArcs(centerX, centerY, R, cosX, sinX, cosY, sinY);

    // 5. Render City Radar Beacons
    this.renderBeacons(centerX, centerY, R, cosX, sinX, cosY, sinY);

    requestAnimationFrame(() => this.animate());
  }

  renderArcs(cx, cy, R, cosX, sinX, cosY, sinY) {
    this.arcs.forEach(arc => {
      const bFrom = this.beacons.find(b => b.name.includes(arc.from));
      const bTo = this.beacons.find(b => b.name.includes(arc.to));
      if (!bFrom || !bTo) return;

      const t1 = this.projectCoords(bFrom.x, bFrom.y, bFrom.z, cx, cy, R, cosX, sinX, cosY, sinY);
      const t2 = this.projectCoords(bTo.x, bTo.y, bTo.z, cx, cy, R, cosX, sinX, cosY, sinY);

      if (t1.z > -0.15 && t2.z > -0.15) {
        const midX = (t1.x + t2.x) / 2;
        const midY = (t1.y + t2.y) / 2 - R * 0.28;

        this.ctx.strokeStyle = 'rgba(45, 212, 191, 0.45)';
        this.ctx.lineWidth = 1.2;
        this.ctx.setLineDash([4, 4]);
        this.ctx.beginPath();
        this.ctx.moveTo(t1.x, t1.y);
        this.ctx.quadraticCurveTo(midX, midY, t2.x, t2.y);
        this.ctx.stroke();
        this.ctx.setLineDash([]);

        // Animated Tracer Particle
        arc.progress = (arc.progress + arc.speed) % 1;
        const t = arc.progress;
        const tracerX = (1 - t) * (1 - t) * t1.x + 2 * (1 - t) * t * midX + t * t * t2.x;
        const tracerY = (1 - t) * (1 - t) * t1.y + 2 * (1 - t) * t * midY + t * t * t2.y;

        this.ctx.fillStyle = '#ffffff';
        this.ctx.shadowColor = '#2dd4bf';
        this.ctx.shadowBlur = 10;
        this.ctx.beginPath();
        this.ctx.arc(tracerX, tracerY, 3, 0, Math.PI * 2);
        this.ctx.fill();
        this.ctx.shadowBlur = 0;
      }
    });
  }

  renderBeacons(cx, cy, R, cosX, sinX, cosY, sinY) {
    for (let i = 0; i < this.beacons.length; i++) {
      const b = this.beacons[i];
      const proj = this.projectCoords(b.x, b.y, b.z, cx, cy, R, cosX, sinX, cosY, sinY);

      if (proj.z > 0.05) {
        b.ping = (b.ping + 0.02) % 1;
        const ringRadius = 4 + b.ping * 16;
        const ringAlpha = (1 - b.ping) * 0.85;

        // Sonar Radar Ring
        this.ctx.strokeStyle = b.primary
          ? `rgba(16, 185, 129, ${ringAlpha})`
          : `rgba(6, 182, 212, ${ringAlpha})`;
        this.ctx.lineWidth = 1.3;
        this.ctx.beginPath();
        this.ctx.arc(proj.x, proj.y, ringRadius, 0, Math.PI * 2);
        this.ctx.stroke();

        // Core Pulse Dot
        this.ctx.fillStyle = b.primary ? '#ffffff' : '#5eead4';
        this.ctx.shadowColor = b.primary ? '#10b981' : '#06b6d4';
        this.ctx.shadowBlur = 8;
        this.ctx.beginPath();
        this.ctx.arc(proj.x, proj.y, b.primary ? 3.5 : 2.5, 0, Math.PI * 2);
        this.ctx.fill();
        this.ctx.shadowBlur = 0;

        // HUD City Code Label
        this.ctx.font = '700 10px "JetBrains Mono", monospace';
        this.ctx.fillStyle = b.primary ? '#ffffff' : 'rgba(94, 234, 212, 0.8)';
        this.ctx.fillText(b.code, proj.x + 8, proj.y - 4);

        if (b.primary) {
          this.ctx.font = '600 9px monospace';
          this.ctx.fillStyle = '#2dd4bf';
          this.ctx.fillText("● BENGALURU WARD 112", proj.x + 8, proj.y + 7);
        }
      }
    }
  }

  projectCoords(x, y, z, cx, cy, R, cosX, sinX, cosY, sinY) {
    const x1 = x * cosY - z * sinY;
    const z1 = z * cosY + x * sinY;
    const y2 = y * cosX - z1 * sinX;
    const z2 = z1 * cosX + y * sinX;

    const fov = 650;
    const scale = fov / (fov + z2 * R);
    return {
      x: cx + x1 * R * scale,
      y: cy + y2 * R * scale,
      z: z2
    };
  }
}
