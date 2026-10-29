// CitizenShield - Full-Stack Application Controller
import { 
  apiLogin, 
  apiRegister, 
  apiGetProfile, 
  apiLogout, 
  apiSubmitReport, 
  apiGetMyReports, 
  apiTrackReport, 
  apiGetAllReports, 
  apiGetMapPins, 
  apiUpdateReportStatus, 
  apiGetAdminMetrics, 
  getCurrentUser, 
  getToken 
} from './js/api.js';

import { 
  initReportMap, 
  setReportMapPin, 
  initCityMap, 
  updateCityMapPins 
} from './js/map.js';

import { StippleOrb } from './js/orb.js';
import { BENGALURU_BBMP_WARDS } from './js/bengaluru-wards.js';

// Global State
let activeUser = null;
let currentReportLat = 12.9716;
let currentReportLng = 77.5946;
let selectedEvidenceFile = null;
let cachedCitizenReports = [];
let cachedAdminReports = [];
let stippleOrbInstance = null;

document.addEventListener('DOMContentLoaded', () => {
  initApp();
});

async function initApp() {
  // 0. Initialize 3D Stipple Orb Canvas
  stippleOrbInstance = new StippleOrb('orb-canvas');

  // 1. Check existing session
  await restoreSession();

  // 2. Wire navigation & views
  setupNavigation();

  // 3. Wire authentication
  setupAuth();

  // 4. Wire grievance lodging & GPS
  setupLodgeGrievance();

  // 5. Wire case tracking
  setupTracking();

  // 6. Wire officer console
  setupOfficerConsole();

  // 7. Wire modals
  setupModals();

  // 8. Load initial Home radar & statistics
  loadHomeOverview();

  // 9. Register Progressive Web App (PWA) & Install Prompt
  setupPwaApp();
}

/**
 * PWA Service Worker Registration & One-Click App Install Prompt
 */
function setupPwaApp() {
  // Register Service Worker
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/sw.js')
        .then((reg) => console.log('[PWA] Service Worker registered:', reg.scope))
        .catch((err) => console.debug('[PWA] Service Worker registration skipped:', err));
    });
  }

  // Handle native "Install App" prompt on Chrome, Edge, Android, iOS
  let deferredPrompt = null;
  const btnInstall = document.getElementById('btn-pwa-install');

  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    if (btnInstall) {
      btnInstall.classList.remove('hidden');
    }
  });

  if (btnInstall) {
    btnInstall.addEventListener('click', async () => {
      if (!deferredPrompt) {
        showToast("To install as an app on your phone: Tap browser menu (⋮ or Share) ➔ 'Add to Home Screen' / 'Install App'", "info", 8000);
        return;
      }
      deferredPrompt.prompt();
      const { outcome } = await deferredPrompt.userChoice;
      if (outcome === 'accepted') {
        showToast("CitizenShield installed successfully on your device!", "success");
      }
      deferredPrompt = null;
      btnInstall.classList.add('hidden');
    });
  }
}

/**
 * Restore persistent user session from localStorage and backend
 */
async function restoreSession() {
  const token = getToken();
  if (token) {
    try {
      activeUser = await apiGetProfile();
      updateAuthUI(activeUser);
    } catch (err) {
      console.warn("Session restore expired or failed:", err.message);
      activeUser = null;
      updateAuthUI(null);
    }
  } else {
    updateAuthUI(null);
  }
}

function updateAuthUI(user) {
  const badgeContainer = document.getElementById('user-profile-badge');
  const btnHeaderLogin = document.getElementById('btn-header-login');
  const userNameText = document.getElementById('header-user-name');
  const userRolePill = document.getElementById('header-user-role');
  const navOfficer = document.getElementById('nav-officer-console');

  if (user) {
    badgeContainer.classList.remove('hidden');
    btnHeaderLogin.classList.add('hidden');
    userNameText.textContent = user.name || user.email;

    if (user.role === 'admin' || user.role === 'officer') {
      userRolePill.textContent = 'Officer';
      userRolePill.classList.add('admin');
      navOfficer.classList.remove('hidden');
    } else {
      userRolePill.textContent = 'Citizen';
      userRolePill.classList.remove('admin');
      navOfficer.classList.add('hidden');
    }
  } else {
    badgeContainer.classList.add('hidden');
    btnHeaderLogin.classList.remove('hidden');
    navOfficer.classList.add('hidden');
  }
}

/**
 * Navigation & View Router
 */
function setupNavigation() {
  // Mobile Navigation Hamburger Toggle
  const btnMobileMenu = document.getElementById('btn-mobile-menu');
  const mainNav = document.getElementById('main-navigation');
  if (btnMobileMenu && mainNav) {
    btnMobileMenu.addEventListener('click', () => {
      mainNav.classList.toggle('mobile-open');
    });
  }

  document.querySelectorAll('[data-view-target]').forEach(el => {
    el.addEventListener('click', (e) => {
      e.preventDefault();
      const target = el.getAttribute('data-view-target');
      navigate(target);
      // Close mobile menu upon selection
      if (mainNav) mainNav.classList.remove('mobile-open');
    });
  });

  // Global Logout Button
  document.getElementById('btn-global-logout').addEventListener('click', async () => {
    await apiLogout();
    activeUser = null;
    updateAuthUI(null);
    showToast("You have been signed out of CitizenShield.", "info");
    navigate('view-home');
  });

  // Expose global track function for Leaflet Popups
  window.trackReportFromMap = (reportId) => {
    navigate('view-tracking');
    document.getElementById('track-search-input').value = reportId;
    performTrackSearch(reportId);
  };
}

function navigate(viewId) {
  // Route Guards
  if (viewId === 'view-submit' || viewId === 'view-citizen-dashboard') {
    if (!activeUser) {
      showToast("Authentication required. Please sign in or register as a citizen.", "warning");
      showView('view-auth');
      return;
    }
  }

  if (viewId === 'view-admin-dashboard') {
    if (!activeUser || (activeUser.role !== 'admin' && activeUser.role !== 'officer')) {
      showToast("Access Restricted: Municipal Officer credentials required.", "error");
      return;
    }
    loadOfficerConsole();
  }

  if (viewId === 'view-home') {
    loadHomeOverview();
  }

  if (viewId === 'view-citizen-dashboard') {
    loadCitizenDossiers();
  }

  if (viewId === 'view-gis-map') {
    loadFullCityMap();
  }

  if (viewId === 'view-submit') {
    setTimeout(() => {
      initReportMap('report-gis-map', (lat, lng) => {
        currentReportLat = lat;
        currentReportLng = lng;
        document.getElementById('report-lat').value = lat.toFixed(6);
        document.getElementById('report-lng').value = lng.toFixed(6);
        document.getElementById('coords-readout').textContent = 
          `Selected Coordinates: Lat ${lat.toFixed(6)}, Lng ${lng.toFixed(6)}`;
      });
    }, 150);
  }

  showView(viewId);
}

function showView(viewId) {
  document.querySelectorAll('.app-view').forEach(v => {
    if (v.id === viewId) {
      v.classList.remove('hidden');
    } else {
      v.classList.add('hidden');
    }
  });

  // Update navbar active classes
  document.querySelectorAll('.nav-menu-btn, .gov-nav-link').forEach(link => {
    if (link.getAttribute('data-view-target') === viewId) {
      link.classList.add('active');
    } else {
      link.classList.remove('active');
    }
  });

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

/**
 * Home Overview & Live Radar
 */
async function loadHomeOverview() {
  try {
    const pins = await apiGetMapPins();
    
    // Update Stats if elements exist
    const elTotal = document.getElementById('home-stat-total');
    if (elTotal) elTotal.textContent = pins.length;
    const elInsp = document.getElementById('home-stat-inspection');
    if (elInsp) elInsp.textContent = 
      pins.filter(p => p.status === 'Under Review' || p.status === 'In Progress').length;
    const elUrg = document.getElementById('home-stat-urgent');
    if (elUrg) elUrg.textContent = 
      pins.filter(p => p.priority === 'Urgent').length;
    const elRes = document.getElementById('home-stat-resolved');
    if (elRes) elRes.textContent = 
      pins.filter(p => p.status === 'Resolved').length;

    // Initialize Home mini radar map
    setTimeout(() => {
      initCityMap('home-gis-map', pins);
    }, 150);
  } catch (err) {
    console.debug("Home overview load note:", err.message);
  }
}

/**
 * Authentication Module
 */
function setupAuth() {
  const tabLogin = document.getElementById('auth-tab-login');
  const tabRegister = document.getElementById('auth-tab-register');
  const formLogin = document.getElementById('form-auth-login');
  const formRegister = document.getElementById('form-auth-register');

  tabLogin.addEventListener('click', () => {
    tabLogin.style.borderBottom = '2px solid var(--teal-light)';
    tabLogin.style.fontWeight = '700';
    tabLogin.style.color = 'var(--teal-light)';
    tabRegister.style.borderBottom = 'none';
    tabRegister.style.fontWeight = '600';
    tabRegister.style.color = 'var(--text-dim)';
    formLogin.classList.remove('hidden');
    formRegister.classList.add('hidden');
  });

  tabRegister.addEventListener('click', () => {
    tabRegister.style.borderBottom = '2px solid var(--teal-light)';
    tabRegister.style.fontWeight = '700';
    tabRegister.style.color = 'var(--teal-light)';
    tabLogin.style.borderBottom = 'none';
    tabLogin.style.fontWeight = '600';
    tabLogin.style.color = 'var(--text-dim)';
    formRegister.classList.remove('hidden');
    formLogin.classList.add('hidden');
  });

  // Password toggle
  const pwdBtn = document.getElementById('btn-toggle-login-pwd');
  const pwdInput = document.getElementById('login-password');
  pwdBtn.addEventListener('click', () => {
    if (pwdInput.type === 'password') {
      pwdInput.type = 'text';
      pwdBtn.textContent = '🔒';
    } else {
      pwdInput.type = 'password';
      pwdBtn.textContent = '👁️';
    }
  });

  // Login Submit
  formLogin.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('login-email').value.trim();
    const pass = document.getElementById('login-password').value;
    const btn = document.getElementById('btn-login-submit');

    try {
      btn.disabled = true;
      btn.textContent = 'Authenticating with Backend...';
      const data = await apiLogin(email, pass);
      activeUser = data.user;
      updateAuthUI(activeUser);
      showToast(`Welcome back, ${activeUser.name}!`, "success");
      formLogin.reset();

      if (activeUser.role === 'admin' || activeUser.role === 'officer') {
        navigate('view-admin-dashboard');
      } else {
        navigate('view-citizen-dashboard');
      }
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      btn.disabled = false;
      btn.textContent = 'Authenticate & Proceed';
    }
  });

  // Register Submit
  formRegister.addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('reg-name').value.trim();
    const email = document.getElementById('reg-email').value.trim();
    const phone = document.getElementById('reg-phone').value.trim();
    const pass = document.getElementById('reg-password').value;
    const btn = document.getElementById('btn-reg-submit');

    try {
      btn.disabled = true;
      btn.textContent = 'Registering in Municipal Vault...';
      const data = await apiRegister(name, email, pass, phone);
      activeUser = data.user;
      updateAuthUI(activeUser);
      showToast("Account successfully registered! Welcome to CitizenShield.", "success");
      formRegister.reset();
      navigate('view-citizen-dashboard');
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      btn.disabled = false;
      btn.textContent = 'Register Citizen Account';
    }
  });

  // Viva demo credential fillers
  document.getElementById('btn-demo-citizen').addEventListener('click', () => {
    document.getElementById('login-email').value = 'rahul.citizen@gmail.com';
    document.getElementById('login-password').value = 'Citizen@2026';
    showToast("Filled demo Citizen credentials. Click 'Authenticate & Proceed'.", "info");
  });

  document.getElementById('btn-demo-admin').addEventListener('click', () => {
    document.getElementById('login-email').value = 'admin@citizenshield.gov';
    document.getElementById('login-password').value = 'Admin@2026';
    showToast("Filled Directorate Admin credentials. Click 'Authenticate & Proceed'.", "info");
  });
}

/**
 * Grievance Lodging & Geolocation
 */
function setupLodgeGrievance() {
  const btnDetectGps = document.getElementById('btn-detect-gps');
  const inputLoc = document.getElementById('lodge-location');
  const fileInput = document.getElementById('lodge-image');
  const previewBox = document.getElementById('lodge-img-preview-box');
  const previewImg = document.getElementById('lodge-img-preview');
  const wardSelect = document.getElementById('lodge-ward');

  // Live Camera Controls
  const btnOpenCam = document.getElementById('btn-open-live-cam');
  const btnCloseCam = document.getElementById('btn-close-live-cam');
  const btnSnap = document.getElementById('btn-snap-photo');
  const camContainer = document.getElementById('live-cam-container');
  const videoElem = document.getElementById('live-cam-video');
  const canvasElem = document.getElementById('live-cam-canvas');
  const btnRemovePhoto = document.getElementById('btn-remove-photo');
  let mediaStream = null;

  // 1. Populate all 198 Bengaluru BBMP Wards exclusively
  if (wardSelect) {
    wardSelect.innerHTML = '<option value="">-- Select Bengaluru BBMP Ward (1 to 198) --</option>';
    BENGALURU_BBMP_WARDS.forEach(wardName => {
      const opt = document.createElement('option');
      opt.value = wardName;
      opt.textContent = wardName;
      wardSelect.appendChild(opt);
    });

    // Default select Ward 112 (Domlur / Indiranagar Central)
    wardSelect.value = "Ward 112 - Domlur / Indiranagar (Central Division)";
  }

  // 2. Live Camera Access (with Automatic Fallback for Mobile Camera Hardware)
  if (btnOpenCam) {
    btnOpenCam.addEventListener('click', async () => {
      // If WebRTC getUserMedia is blocked on plain HTTP on mobile, trigger native camera shutter directly
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        showToast("Opening native mobile camera shutter...", "info");
        fileInput.click();
        return;
      }
      try {
        camContainer.classList.remove('hidden');
        
        // Try back / environmental camera with video constraints
        const constraints = [
          { video: { facingMode: { ideal: 'environment' }, width: { ideal: 1280 } }, audio: false },
          { video: { facingMode: 'user' }, audio: false },
          { video: true, audio: false }
        ];

        let streamObtained = null;
        for (const c of constraints) {
          try {
            streamObtained = await navigator.mediaDevices.getUserMedia(c);
            if (streamObtained) break;
          } catch (e) {
            console.debug("Constraint trial fallback:", e);
          }
        }

        if (!streamObtained) {
          throw new Error("Unable to access camera sensor on this connection");
        }

        mediaStream = streamObtained;
        videoElem.srcObject = mediaStream;
        await videoElem.play();
        showToast("Live Camera Active! Frame the defect and tap Capture Snapshot.", "info");
      } catch (err) {
        console.warn("Direct video viewfinder unavailable, switching to mobile native shutter:", err);
        camContainer.classList.add('hidden');
        showToast("Opening device camera app...", "info");
        fileInput.click();
      }
    });
  }

  const stopCamera = () => {
    if (mediaStream) {
      mediaStream.getTracks().forEach(track => track.stop());
      mediaStream = null;
    }
    if (videoElem) {
      videoElem.srcObject = null;
    }
    if (camContainer) {
      camContainer.classList.add('hidden');
    }
  };

  if (btnCloseCam) {
    btnCloseCam.addEventListener('click', () => {
      stopCamera();
    });
  }

  if (btnSnap) {
    btnSnap.addEventListener('click', () => {
      if (!videoElem || !videoElem.videoWidth) {
        showToast("Waiting for live camera frame...", "warning");
        return;
      }
      const width = videoElem.videoWidth;
      const height = videoElem.videoHeight;
      canvasElem.width = width;
      canvasElem.height = height;
      const ctx = canvasElem.getContext('2d');
      ctx.drawImage(videoElem, 0, 0, width, height);

      // Convert snapshot to Blob file
      canvasElem.toBlob((blob) => {
        if (!blob) {
          showToast("Failed to capture image snapshot.", "error");
          return;
        }
        const fileName = `live_cam_${Date.now()}.jpg`;
        selectedEvidenceFile = new File([blob], fileName, { type: 'image/jpeg' });

        // Update preview
        previewImg.src = canvasElem.toDataURL('image/jpeg');
        document.getElementById('preview-file-name').textContent = `Live Camera Photo (${fileName})`;
        previewBox.classList.remove('hidden');

        stopCamera();
        showToast("Live snapshot captured and attached to grievance!", "success");
      }, 'image/jpeg', 0.92);
    });
  }

  if (btnRemovePhoto) {
    btnRemovePhoto.addEventListener('click', () => {
      selectedEvidenceFile = null;
      fileInput.value = '';
      previewBox.classList.add('hidden');
      showToast("Evidence photo removed.", "info");
    });
  }

  // GPS Detection with Multi-Tier Fallback for Mobile Phones
  btnDetectGps.addEventListener('click', () => {
    btnDetectGps.disabled = true;
    btnDetectGps.textContent = "Detecting GPS...";

    const handleSuccess = async (latitude, longitude, sourceLabel = "GPS Sensor") => {
      currentReportLat = latitude;
      currentReportLng = longitude;

      document.getElementById('report-lat').value = latitude.toFixed(6);
      document.getElementById('report-lng').value = longitude.toFixed(6);
      document.getElementById('coords-readout').textContent = 
        `${sourceLabel} Acquired: Lat ${latitude.toFixed(6)}, Lng ${longitude.toFixed(6)}`;

      setReportMapPin(latitude, longitude, 17);

      // Reverse geocoding via local server proxy (never blocked by mobile browser CORS)
      try {
        const res = await fetch(`/api/reverse-geocode?lat=${latitude}&lon=${longitude}`);
        if (res.ok) {
          const data = await res.json();
          if (data && data.display_name) {
            inputLoc.value = data.display_name;
          }
        }
      } catch (e) {
        console.debug("Geocode proxy error:", e);
      }

      btnDetectGps.disabled = false;
      btnDetectGps.textContent = "📍 Detect GPS";
      showToast(`${sourceLabel} acquired successfully! Pin dropped on map.`, "success");
    };

    // Fallback: If device GPS fails or permission denied, fetch IP location
    const fallbackToIp = async (reason) => {
      try {
        btnDetectGps.textContent = "Finding Area...";
        const res = await fetch('/api/ip-location');
        if (res.ok) {
          const data = await res.json();
          handleSuccess(data.latitude, data.longitude, "Network Location");
          showToast(`Device GPS prompt unavailable (${reason}). Located via city network. Tap map to fine-tune exact street.`, "info", 6000);
          return;
        }
      } catch (e) {
        console.warn("IP location fallback failed:", e);
      }
      btnDetectGps.disabled = false;
      btnDetectGps.textContent = "📍 Detect GPS";
      showToast("Unable to detect automatic location. Tap directly on the map to place your pin.", "warning", 6000);
    };

    if (!navigator.geolocation) {
      fallbackToIp("Browser unsupported");
      return;
    }

    // Attempt 1: High Accuracy with reasonable timeout
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        handleSuccess(pos.coords.latitude, pos.coords.longitude, "Satellite GPS");
      },
      (err1) => {
        console.warn("High accuracy GPS failed, trying standard cellular/wifi position:", err1.message);
        // Attempt 2: Standard Accuracy (works instantly on mobile cellular & wifi)
        navigator.geolocation.getCurrentPosition(
          (pos) => {
            handleSuccess(pos.coords.latitude, pos.coords.longitude, "Cellular/Wi-Fi GPS");
          },
          (err2) => {
            console.warn("Standard geolocation failed:", err2.message);
            fallbackToIp(err2.message);
          },
          { enableHighAccuracy: false, timeout: 12000, maximumAge: 60000 }
        );
      },
      { enableHighAccuracy: true, timeout: 7000, maximumAge: 30000 }
    );
  });

  // Image Preview
  fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.size > 10 * 1024 * 1024) {
        showToast("Image exceeds 10 MB limit. Please select a smaller photo.", "error");
        fileInput.value = '';
        previewBox.classList.add('hidden');
        selectedEvidenceFile = null;
        return;
      }
      selectedEvidenceFile = file;
      const reader = new FileReader();
      reader.onload = (ev) => {
        previewImg.src = ev.target.result;
        previewBox.classList.remove('hidden');
      };
      reader.readAsDataURL(file);
    } else {
      selectedEvidenceFile = null;
      previewBox.classList.add('hidden');
    }
  });

  // Review Modal Opener
  document.getElementById('btn-open-review').addEventListener('click', () => {
    const title = document.getElementById('lodge-title').value.trim();
    const dept = document.getElementById('lodge-dept').value;
    const cat = document.getElementById('lodge-category').value;
    const prio = document.getElementById('lodge-priority').value;
    const ward = document.getElementById('lodge-ward').value;
    const desc = document.getElementById('lodge-description').value.trim();
    const loc = inputLoc.value.trim();

    if (!title || !desc || !loc) {
      showToast("Please complete all mandatory fields before reviewing.", "error");
      return;
    }

    document.getElementById('rev-title').textContent = title;
    document.getElementById('rev-dept').textContent = dept;
    document.getElementById('rev-category').textContent = cat;
    document.getElementById('rev-priority').textContent = prio;
    document.getElementById('rev-ward').textContent = ward;
    document.getElementById('rev-location').textContent = loc;
    document.getElementById('rev-coords').textContent = `Lat ${currentReportLat.toFixed(6)}, Lng ${currentReportLng.toFixed(6)}`;

    openModal('modal-review');
  });

  // Final Submission to Persistent Database
  document.getElementById('btn-final-lodge-submit').addEventListener('click', async () => {
    const btn = document.getElementById('btn-final-lodge-submit');
    
    const formData = new FormData();
    formData.append('title', document.getElementById('lodge-title').value.trim());
    formData.append('department', document.getElementById('lodge-dept').value);
    formData.append('category', document.getElementById('lodge-category').value);
    formData.append('priority', document.getElementById('lodge-priority').value);
    formData.append('ward', document.getElementById('lodge-ward').value);
    formData.append('description', document.getElementById('lodge-description').value.trim());
    formData.append('location', inputLoc.value.trim());
    formData.append('latitude', currentReportLat);
    formData.append('longitude', currentReportLng);

    if (selectedEvidenceFile) {
      formData.append('image', selectedEvidenceFile);
    }

    try {
      btn.disabled = true;
      btn.textContent = 'Writing to SQLite Vault...';

      const res = await apiSubmitReport(formData);

      closeModal('modal-review');
      showToast(`Grievance permanently recorded! Official Reference: ${res.report_id}`, "success", 7000);

      // Reset form
      document.getElementById('form-lodge-grievance').reset();
      previewBox.classList.add('hidden');
      selectedEvidenceFile = null;

      // Navigate to Citizen Dossier
      navigate('view-citizen-dashboard');
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      btn.disabled = false;
      btn.textContent = 'Confirm & Lodge into Database';
    }
  });
}

/**
 * Citizen Dossier View
 */
async function loadCitizenDossiers() {
  const container = document.getElementById('citizen-grievances-list');
  container.innerHTML = '<div style="text-align: center; padding: 32px; color: var(--text-tertiary);">Loading your grievance records from SQLite vault...</div>';

  try {
    const reports = await apiGetMyReports();
    cachedCitizenReports = reports;

    // Metrics
    document.getElementById('cit-metric-total').textContent = reports.length;
    document.getElementById('cit-metric-submitted').textContent = 
      reports.filter(r => r.status === 'Submitted').length;
    document.getElementById('cit-metric-progress').textContent = 
      reports.filter(r => r.status === 'In Progress' || r.status === 'Dispatched' || r.status === 'Under Review').length;
    document.getElementById('cit-metric-resolved').textContent = 
      reports.filter(r => r.status === 'Resolved').length;

    renderCitizenList(reports);
  } catch (err) {
    container.innerHTML = `<div style="text-align: center; padding: 32px; color: var(--status-urgent);">Failed to retrieve records: ${err.message}</div>`;
  }

  // Filter handlers
  const filterStatus = document.getElementById('cit-filter-status');
  const filterDept = document.getElementById('cit-filter-dept');

  const applyFilters = () => {
    let list = [...cachedCitizenReports];
    if (filterStatus.value !== 'ALL') {
      list = list.filter(r => r.status === filterStatus.value);
    }
    if (filterDept.value !== 'ALL') {
      list = list.filter(r => r.department === filterDept.value);
    }
    renderCitizenList(list);
  };

  filterStatus.onchange = applyFilters;
  filterDept.onchange = applyFilters;
}

function renderCitizenList(reports) {
  const container = document.getElementById('citizen-grievances-list');
  container.innerHTML = '';

  if (reports.length === 0) {
    container.innerHTML = `
      <div class="gov-card" style="text-align: center; padding: 48px;">
        <div style="font-size: 2.2rem; margin-bottom: 8px;">📂</div>
        <h3 style="font-size: 1.15rem; font-weight: 800; color: var(--gov-navy); margin-bottom: 6px;">No Grievance Records Found</h3>
        <p style="color: var(--text-tertiary); font-size: 0.9rem; margin-bottom: 16px;">There are currently no active complaints matching your filter.</p>
        <button class="btn btn-amber" onclick="navigate('view-submit')">+ Lodge a Grievance</button>
      </div>
    `;
    return;
  }

  reports.forEach(r => {
    const card = document.createElement('div');
    card.className = 'gov-card';
    card.style.padding = '20px';
    card.style.marginBottom = '16px';

    const statusPillHtml = getStatusPill(r.status);
    const priorityPillHtml = getPriorityPill(r.priority);

    let remarkSnippet = '';
    if (r.admin_remarks) {
      remarkSnippet = `
        <div style="margin-top: 12px; background: var(--surface-muted); padding: 10px 14px; border-left: 3px solid var(--gov-blue); font-size: 0.88rem;">
          <strong style="color: var(--gov-navy);">Latest Official Directive:</strong> ${escapeHtml(r.admin_remarks)}
        </div>
      `;
    }

    card.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 10px; margin-bottom: 10px;">
        <div>
          <span class="report-token">${r.report_id}</span>
          <span class="dept-tag" style="margin-left: 6px;">🏢 ${escapeHtml(r.department)}</span>
          ${priorityPillHtml}
          <h3 style="font-size: 1.15rem; font-weight: 800; color: var(--gov-navy); margin-top: 6px;">${escapeHtml(r.title)}</h3>
        </div>
        <div>${statusPillHtml}</div>
      </div>
      <p style="font-size: 0.92rem; color: var(--text-secondary); line-height: 1.5;">${escapeHtml(r.description)}</p>
      ${remarkSnippet}
      <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; margin-top: 14px; padding-top: 12px; border-top: 1px solid var(--border-light); font-size: 0.82rem; color: var(--text-tertiary);">
        <div>📍 ${escapeHtml(r.location)} • 📅 Lodged: ${escapeHtml(r.created_at)}</div>
        <button class="btn btn-secondary btn-sm" onclick="window.trackReportFromMap('${r.report_id}')">Inspect Case Dossier & Audit Log →</button>
      </div>
    `;

    container.appendChild(card);
  });
}

/**
 * Case Tracker & Certificate Dossier
 */
function setupTracking() {
  const form = document.getElementById('form-tracking-search');
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const id = document.getElementById('track-search-input').value.trim();
    performTrackSearch(id);
  });
}

async function performTrackSearch(reportId) {
  const resultContainer = document.getElementById('tracking-dossier-result');
  const btn = document.getElementById('btn-search-track');

  try {
    btn.disabled = true;
    btn.textContent = 'Querying Vault...';

    const r = await apiTrackReport(reportId);

    // Populate Dossier Certificate
    document.getElementById('dossier-title').textContent = r.title;
    document.getElementById('dossier-ref-id').textContent = r.report_id;
    document.getElementById('dossier-status-pill').innerHTML = getStatusPill(r.status);
    document.getElementById('dossier-priority-pill').innerHTML = getPriorityPill(r.priority);
    document.getElementById('dossier-dept').textContent = r.department;
    document.getElementById('dossier-ward').textContent = r.ward || 'Central Division';
    document.getElementById('dossier-created').textContent = r.created_at;
    document.getElementById('dossier-sla').textContent = `${r.sla_hours || 48} Hours Standard`;
    document.getElementById('dossier-location').textContent = r.location;
    document.getElementById('dossier-description').textContent = r.description;

    // Photo
    const photoBox = document.getElementById('dossier-photo-container');
    const photoImg = document.getElementById('dossier-photo');
    if (r.image_filename) {
      photoImg.src = `/api/uploads/${r.image_filename}`;
      photoBox.classList.remove('hidden');
    } else {
      photoBox.classList.add('hidden');
    }

    // Audit History Timeline
    const timeline = document.getElementById('dossier-timeline');
    timeline.innerHTML = '';

    const history = r.status_history || [];
    history.forEach(step => {
      const node = document.createElement('div');
      node.className = 'audit-node';
      node.innerHTML = `
        <div class="audit-content">
          <div class="audit-heading">
            <span class="audit-title">${escapeHtml(step.status)} — ${escapeHtml(step.officer_name || 'System')}</span>
            <span class="audit-time">${escapeHtml(step.created_at)}</span>
          </div>
          <div class="audit-remarks">${escapeHtml(step.remarks)}</div>
        </div>
      `;
      timeline.appendChild(node);
    });

    resultContainer.classList.remove('hidden');
    showToast(`Dossier loaded for ${r.report_id}`, "success");
  } catch (err) {
    resultContainer.classList.add('hidden');
    showToast(err.message, "error");
  } finally {
    btn.disabled = false;
    btn.textContent = 'Inspect Case Dossier';
  }
}

/**
 * Fullscreen City GIS Map
 */
async function loadFullCityMap() {
  try {
    const pins = await apiGetMapPins();
    setTimeout(() => {
      initCityMap('full-city-gis-map', pins);
    }, 150);
  } catch (err) {
    showToast(`Failed to load GIS pins: ${err.message}`, "error");
  }

  document.getElementById('btn-refresh-gis').onclick = async () => {
    const pins = await apiGetMapPins();
    updateCityMapPins(pins);
    showToast("GIS Incident Map updated with live backend data.", "info");
  };
}

/**
 * Officer Administration Console
 */
function setupOfficerConsole() {
  document.getElementById('btn-adm-refresh').addEventListener('click', () => {
    loadOfficerConsole();
  });

  // Filter listeners
  const searchInput = document.getElementById('adm-search-input');
  const filterStatus = document.getElementById('adm-filter-status');
  const filterPriority = document.getElementById('adm-filter-priority');
  const filterCat = document.getElementById('adm-filter-category');

  const onFilterChange = async () => {
    const filters = {
      search: searchInput.value.trim(),
      status: filterStatus.value,
      priority: filterPriority.value,
      category: filterCat.value
    };
    try {
      const reports = await apiGetAllReports(filters);
      renderAdminTable(reports);
    } catch (err) {
      showToast(err.message, "error");
    }
  };

  searchInput.addEventListener('input', debounce(onFilterChange, 300));
  filterStatus.addEventListener('change', onFilterChange);
  filterPriority.addEventListener('change', onFilterChange);
  filterCat.addEventListener('change', onFilterChange);

  // Status Directive Update Modal Submission
  document.getElementById('btn-save-officer-directive').addEventListener('click', async () => {
    const reportId = document.getElementById('officer-update-ref-id').value;
    const newStatus = document.getElementById('officer-select-status').value;
    const newDept = document.getElementById('officer-select-dept').value;
    const remarks = document.getElementById('officer-text-remarks').value.trim();
    const btn = document.getElementById('btn-save-officer-directive');

    if (!remarks) {
      showToast("Please provide an official justification and action remark.", "error");
      return;
    }

    try {
      btn.disabled = true;
      btn.textContent = 'Committing Directive...';

      await apiUpdateReportStatus(reportId, newStatus, remarks, newDept);

      showToast(`Grievance ${reportId} status updated to ${newStatus}.`, "success");
      closeModal('modal-officer-action');
      loadOfficerConsole();
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      btn.disabled = false;
      btn.textContent = 'Publish Official Directive';
    }
  });
}

async function loadOfficerConsole() {
  const tableBody = document.getElementById('adm-table-body');
  tableBody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 24px; color: var(--text-tertiary);">Loading municipal registry records from SQLite...</td></tr>';

  try {
    const [reports, metrics] = await Promise.all([
      apiGetAllReports(),
      apiGetAdminMetrics()
    ]);

    cachedAdminReports = reports;

    // Display Officer Metrics
    document.getElementById('adm-metric-total').textContent = metrics.total;
    document.getElementById('adm-metric-submitted').textContent = metrics.submitted;
    document.getElementById('adm-metric-review').textContent = metrics.underReview;
    document.getElementById('adm-metric-progress').textContent = metrics.inProgress;
    document.getElementById('adm-metric-resolved').textContent = metrics.resolved;

    renderAdminTable(reports);
  } catch (err) {
    tableBody.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: 24px; color: var(--status-urgent);">Error loading records: ${err.message}</td></tr>`;
  }
}

function renderAdminTable(reports) {
  const tbody = document.getElementById('adm-table-body');
  tbody.innerHTML = '';

  if (reports.length === 0) {
    tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 32px; color: var(--text-tertiary);">No grievances match the search filter.</td></tr>';
    return;
  }

  reports.forEach(r => {
    const tr = document.createElement('tr');

    tr.innerHTML = `
      <td><span class="report-token">${r.report_id}</span></td>
      <td><strong>${escapeHtml(r.citizen_name)}</strong><br><span style="font-size: 0.78rem; color: var(--text-tertiary);">${escapeHtml(r.citizen_phone || r.citizen_email)}</span></td>
      <td><span class="dept-tag">${escapeHtml(r.department)}</span></td>
      <td>${getPriorityPill(r.priority)}</td>
      <td style="max-width: 220px; font-weight: 600;">${escapeHtml(r.title)}</td>
      <td style="max-width: 180px; font-size: 0.82rem;">${escapeHtml(r.ward)}<br><span style="color: var(--text-tertiary);">${escapeHtml(r.location)}</span></td>
      <td>${getStatusPill(r.status)}</td>
      <td>
        <button class="btn btn-primary btn-sm" onclick="window.openOfficerDirectiveModal('${r.report_id}', '${escapeAttr(r.title)}', '${r.status}', '${r.department}')">
          Directive ⚙️
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// Global modal opener for officer directive
window.openOfficerDirectiveModal = (reportId, title, currentStatus, currentDept) => {
  document.getElementById('officer-update-ref-id').value = reportId;
  document.getElementById('officer-dialog-ref').textContent = reportId;
  document.getElementById('officer-dialog-title').textContent = title;
  document.getElementById('officer-select-status').value = currentStatus;
  document.getElementById('officer-select-dept').value = currentDept || '';
  document.getElementById('officer-text-remarks').value = '';

  openModal('modal-officer-action');
};

/**
 * Modals and Toast Infrastructure
 */
function setupModals() {
  document.querySelectorAll('[data-modal-close]').forEach(btn => {
    btn.addEventListener('click', () => {
      const id = btn.getAttribute('data-modal-close');
      closeModal(id);
    });
  });

  document.querySelectorAll('.modal-backdrop').forEach(modal => {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) closeModal(modal.id);
    });
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      document.querySelectorAll('.modal-backdrop:not(.hidden)').forEach(m => closeModal(m.id));
    }
  });
}

function openModal(id) {
  const m = document.getElementById(id);
  if (m) m.classList.remove('hidden');
}

function closeModal(id) {
  const m = document.getElementById(id);
  if (m) m.classList.add('hidden');
}

export function showToast(message, type = 'info', duration = 5000) {
  const shelf = document.getElementById('toast-shelf');
  if (!shelf) return;

  const toast = document.createElement('div');
  toast.className = `gov-toast ${type}`;

  const iconMap = {
    success: '✓',
    error: '✕',
    warning: '⚠',
    info: 'ℹ'
  };

  toast.innerHTML = `
    <span style="font-weight: 800; font-size: 1.1rem;">${iconMap[type] || 'ℹ'}</span>
    <span style="flex: 1; line-height: 1.4;">${escapeHtml(message)}</span>
    <button style="background: none; border: none; font-size: 1.2rem; cursor: pointer; color: var(--text-tertiary);" onclick="this.parentElement.remove()">&times;</button>
  `;

  shelf.appendChild(toast);

  setTimeout(() => {
    if (toast.parentElement) toast.remove();
  }, duration);
}

// Helpers
function getStatusPill(status) {
  const map = {
    'Submitted': 'status-submitted',
    'Under Review': 'status-review',
    'In Progress': 'status-progress',
    'Dispatched': 'status-progress',
    'Resolved': 'status-resolved',
    'Rejected': 'status-rejected'
  };
  const cls = map[status] || 'status-submitted';
  return `<span class="status-pill ${cls}">● ${escapeHtml(status || 'Submitted')}</span>`;
}

function getPriorityPill(priority) {
  const map = {
    'Urgent': 'priority-urgent',
    'High': 'priority-high',
    'Normal': 'priority-normal',
    'Low': 'priority-low'
  };
  const cls = map[priority] || 'priority-normal';
  return `<span class="priority-tag ${cls}">${escapeHtml(priority || 'Normal')}</span>`;
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function escapeAttr(str) {
  if (!str) return '';
  return String(str).replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

function debounce(func, wait) {
  let timeout;
  return function (...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}
