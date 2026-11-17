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
  apiAnalyzeImage,
  apiCheckDuplicate,
  apiGetAiMetrics,
  apiGetZonesSummary,
  apiGetZoneComplaints,
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

// Global State
let activeUser = null;
let currentReportLat = 13.3414;
let currentReportLng = 77.1022;
let selectedEvidenceFile = null;
let selectedAfterRepairFile = null;
let currentAiResult = null;
let cachedCitizenReports = [];
let cachedAdminReports = [];
let cachedZonesData = [];
let stippleOrbInstance = null;
let zoneLeafletMap = null;
let zonePolygonsLayer = null;
let zoneMarkersLayer = null;
let zoneRefreshInterval = null;
let zoneTimerCountdown = 20;

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

  // 4. Wire grievance lodging, AI analysis & GPS
  setupLodgeGrievance();

  // 5. Wire case tracking
  setupTracking();

  // 6. Wire officer console
  setupOfficerConsole();

  // 6.5 Wire live zone monitoring
  setupZoneMonitoring();

  // 7. Wire AI dashboard
  setupAiDashboard();

  // 8. Wire modals
  setupModals();

  // 9. Load initial Home radar & statistics
  loadHomeOverview();
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
  const navAiDashboard = document.getElementById('nav-ai-dashboard');
  const navZoneMonitoring = document.getElementById('nav-zone-monitoring');

  if (user) {
    badgeContainer.classList.remove('hidden');
    btnHeaderLogin.classList.add('hidden');
    userNameText.textContent = user.name || user.email;

    if (user.role === 'admin' || user.role === 'officer') {
      userRolePill.textContent = 'Municipal Officer';
      userRolePill.className = 'role-tag admin';
      navOfficer.classList.remove('hidden');
      if (navAiDashboard) navAiDashboard.classList.remove('hidden');
      if (navZoneMonitoring) navZoneMonitoring.classList.remove('hidden');
    } else {
      userRolePill.textContent = 'Registered Citizen';
      userRolePill.className = 'role-tag citizen';
      navOfficer.classList.add('hidden');
      if (navAiDashboard) navAiDashboard.classList.add('hidden');
      if (navZoneMonitoring) navZoneMonitoring.classList.add('hidden');
    }
  } else {
    badgeContainer.classList.add('hidden');
    btnHeaderLogin.classList.remove('hidden');
    navOfficer.classList.add('hidden');
    if (navAiDashboard) navAiDashboard.classList.add('hidden');
    if (navZoneMonitoring) navZoneMonitoring.classList.add('hidden');
  }
}

/**
 * Navigation Router
 */
function setupNavigation() {
  document.body.addEventListener('click', (e) => {
    const targetBtn = e.target.closest('[data-view-target]');
    if (targetBtn) {
      const viewId = targetBtn.getAttribute('data-view-target');
      navigate(viewId);
    }
  });

  document.getElementById('btn-global-logout').addEventListener('click', async () => {
    await apiLogout();
    activeUser = null;
    updateAuthUI(null);
    showToast("Logged out successfully.", "info");
    navigate('view-home');
  });
}

function navigate(viewId) {
  if (viewId === 'view-citizen-dashboard' || viewId === 'view-submit') {
    if (!activeUser) {
      showToast("Authentication Required: Please sign in or register to lodge/view dossiers.", "warning");
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

  if (viewId === 'view-ai-dashboard') {
    if (!activeUser || (activeUser.role !== 'admin' && activeUser.role !== 'officer')) {
      showToast("Access Restricted: Municipal Officer credentials required for AI metrics.", "error");
      return;
    }
    loadAiDashboard();
  }

  if (viewId === 'view-zone-monitoring') {
    if (!activeUser || (activeUser.role !== 'admin' && activeUser.role !== 'officer')) {
      showToast("Access Restricted: Municipal Officer credentials required for Zone Monitoring.", "error");
      return;
    }
    loadLiveZoneMonitoring();
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
        triggerDuplicateCheck();
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
    tabLogin.style.color = 'var(--teal-light)';
    tabRegister.style.borderBottom = 'none';
    tabRegister.style.color = 'var(--text-dim)';
    formLogin.classList.remove('hidden');
    formRegister.classList.add('hidden');
  });

  tabRegister.addEventListener('click', () => {
    tabRegister.style.borderBottom = '2px solid var(--teal-light)';
    tabRegister.style.color = 'var(--teal-light)';
    tabLogin.style.borderBottom = 'none';
    tabLogin.style.color = 'var(--text-dim)';
    formRegister.classList.remove('hidden');
    formLogin.classList.add('hidden');
  });

  document.getElementById('btn-toggle-login-pwd').addEventListener('click', () => {
    const pwdInput = document.getElementById('login-password');
    pwdInput.type = pwdInput.type === 'password' ? 'text' : 'password';
  });

  // Login Handler
  formLogin.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('login-email').value.trim();
    const password = document.getElementById('login-password').value;
    const btn = document.getElementById('btn-login-submit');

    try {
      btn.disabled = true;
      btn.textContent = 'Verifying Credentials...';
      const res = await apiLogin(email, password);
      activeUser = res.user;
      updateAuthUI(activeUser);
      showToast(`Welcome back, ${activeUser.name || activeUser.email}!`, "success");

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

  // Register Handler
  formRegister.addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('reg-name').value.trim();
    const email = document.getElementById('reg-email').value.trim();
    const phone = document.getElementById('reg-phone').value.trim();
    const password = document.getElementById('reg-password').value;
    const btn = document.getElementById('btn-reg-submit');

    try {
      btn.disabled = true;
      btn.textContent = 'Creating Citizen Account...';
      await apiRegister(name, email, password, phone);
      showToast("Account created successfully! Signing you in...", "success");

      const res = await apiLogin(email, password);
      activeUser = res.user;
      updateAuthUI(activeUser);
      navigate('view-citizen-dashboard');
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      btn.disabled = false;
      btn.textContent = 'Register Citizen Account';
    }
  });

  // Demo Credentials Autocomplete
  document.getElementById('btn-demo-citizen').addEventListener('click', () => {
    tabLogin.click();
    document.getElementById('login-email').value = 'rahul.citizen@gmail.com';
    document.getElementById('login-password').value = 'Citizen@2026';
    showToast("Filled demo Citizen credentials. Click 'Authenticate & Proceed'.", "info");
  });

  document.getElementById('btn-demo-admin').addEventListener('click', () => {
    tabLogin.click();
    document.getElementById('login-email').value = 'engineer@citizenshield.gov';
    document.getElementById('login-password').value = 'Engineer@2026';
    showToast("Filled Directorate Admin credentials. Click 'Authenticate & Proceed'.", "info");
  });
}

/**
 * Grievance Lodging, Real AI Vision Analysis & Geolocation
 */
function setupLodgeGrievance() {
  const btnDetectGps = document.getElementById('btn-detect-gps');
  const inputLoc = document.getElementById('lodge-location');
  const fileInput = document.getElementById('lodge-image');
  const previewBox = document.getElementById('lodge-img-preview-box');
  const previewImg = document.getElementById('lodge-img-preview');
  const aiProgress = document.getElementById('ai-scanning-progress');
  const aiResultCard = document.getElementById('ai-scan-result-card');

  // GPS Detection with Reverse Geocoding
  btnDetectGps.addEventListener('click', () => {
    if (!navigator.geolocation) {
      showToast("Geolocation is not supported by your browser.", "warning");
      return;
    }

    btnDetectGps.disabled = true;
    btnDetectGps.textContent = "Detecting...";

    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const { latitude, longitude } = pos.coords;
        currentReportLat = latitude;
        currentReportLng = longitude;

        document.getElementById('report-lat').value = latitude.toFixed(6);
        document.getElementById('report-lng').value = longitude.toFixed(6);
        document.getElementById('coords-readout').textContent = 
          `GPS Acquired: Lat ${latitude.toFixed(6)}, Lng ${longitude.toFixed(6)}`;

        setReportMapPin(latitude, longitude, 17);

        try {
          const res = await fetch(`https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${latitude}&lon=${longitude}`);
          if (res.ok) {
            const data = await res.json();
            if (data && data.display_name) {
              inputLoc.value = data.display_name;
            }
          }
        } catch (e) {
          console.debug("OSM geocode error:", e);
        }

        btnDetectGps.disabled = false;
        btnDetectGps.textContent = "📍 Detect GPS";
        showToast("GPS coordinates acquired with user consent.", "success");
        triggerDuplicateCheck();
      },
      (err) => {
        btnDetectGps.disabled = false;
        btnDetectGps.textContent = "📍 Detect GPS";
        showToast(`Location error: ${err.message}. Please enter address manually.`, "warning");
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  });

  // Image Upload + Real AI Vision Inference
  fileInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) {
      selectedEvidenceFile = null;
      currentAiResult = null;
      previewBox.classList.add('hidden');
      aiResultCard.classList.add('hidden');
      return;
    }

    if (file.size > 15 * 1024 * 1024) {
      showToast("Image exceeds 15 MB limit. Please select a smaller photo.", "error");
      fileInput.value = '';
      previewBox.classList.add('hidden');
      aiResultCard.classList.add('hidden');
      selectedEvidenceFile = null;
      return;
    }

    selectedEvidenceFile = file;

    // Show local preview
    const reader = new FileReader();
    reader.onload = (ev) => {
      previewImg.src = ev.target.result;
      previewBox.classList.remove('hidden');
    };
    reader.readAsDataURL(file);

    // Trigger Real Computer Vision Model Inference
    aiProgress.classList.remove('hidden');
    aiResultCard.classList.add('hidden');

    try {
      const aiData = await apiAnalyzeImage(file);
      currentAiResult = aiData;
      aiProgress.classList.add('hidden');

      if (aiData.detected) {
        aiResultCard.classList.remove('hidden');
        document.getElementById('ai-detected-title').textContent = `${aiData.detected_class} Detected`;
        document.getElementById('ai-confidence-badge').textContent = aiData.confidence_percent || `${Math.round(aiData.confidence_score * 100)}%`;
        document.getElementById('ai-model-name').textContent = aiData.model_name;
        document.getElementById('ai-suggested-cat').textContent = aiData.suggested_category;
        document.getElementById('ai-suggested-prio').textContent = aiData.suggested_priority;

        // Auto-select suggested category and priority in form
        const selectCat = document.getElementById('lodge-category');
        if (aiData.suggested_category) {
          for (let i = 0; i < selectCat.options.length; i++) {
            if (selectCat.options[i].value === aiData.suggested_category) {
              selectCat.selectedIndex = i;
              selectCat.dispatchEvent(new Event('change'));
              break;
            }
          }
        }

        const selectPrio = document.getElementById('lodge-priority');
        if (aiData.suggested_priority) {
          selectPrio.value = aiData.suggested_priority;
        }

        // Store hidden fields
        document.getElementById('ai-detected-class-input').value = aiData.detected_class;
        document.getElementById('ai-confidence-score-input').value = aiData.confidence_score;
        document.getElementById('ai-model-name-input').value = aiData.model_name;
        document.getElementById('ai-suggested-category-input').value = aiData.suggested_category;
        document.getElementById('ai-temp-filename-input').value = aiData.temp_image_filename || '';

        showToast(`AI Vision Analysis: ${aiData.detected_class} (${aiData.confidence_percent} confidence)`, "success");
        triggerDuplicateCheck();
      } else {
        aiResultCard.classList.add('hidden');
        showToast(aiData.message || "No supported civic problem detected. Please select category manually.", "info", 6000);
      }
    } catch (err) {
      aiProgress.classList.add('hidden');
      console.warn("AI analysis network issue:", err.message);
      showToast("AI vision service busy. You may continue with manual category selection.", "warning");
    }
  });

  // Citizen confirms AI Category Button
  document.getElementById('btn-ai-confirm-cat').addEventListener('click', () => {
    showToast("AI suggested category confirmed for submission.", "success");
  });

  // Department auto-sync on category change
  const catSelect = document.getElementById('lodge-category');
  const deptSelect = document.getElementById('lodge-dept');
  catSelect.addEventListener('change', () => {
    const val = catSelect.value;
    if (val === 'Roads and Transport') deptSelect.value = 'Roads & Civil Infrastructure';
    else if (val === 'Streetlights and Electricity') deptSelect.value = 'Electrical & Public Lighting';
    else if (val === 'Water and Drainage') deptSelect.value = 'Water Supply & Sewerage Board';
    else if (val === 'Garbage and Sanitation') deptSelect.value = 'Solid Waste Management Cell';
    triggerDuplicateCheck();
  });

  // Cancel Button in Lodge Form -> Clean reset and navigate to Home
  window.citizenShieldLodgeCancel = () => {
    document.getElementById('form-lodge-grievance').reset();
    const pBox = document.getElementById('lodge-img-preview-box');
    if (pBox) pBox.classList.add('hidden');
    const aiBox = document.getElementById('ai-scan-result-card');
    if (aiBox) aiBox.classList.add('hidden');
    const dupBox = document.getElementById('duplicate-warning-banner');
    if (dupBox) dupBox.classList.add('hidden');
    selectedEvidenceFile = null;
    currentAiResult = null;
    navigate('view-home');
    showToast("Grievance lodgment cancelled.", "info");
  };

  const btnLodgeCancel = document.getElementById('btn-lodge-cancel');
  if (btnLodgeCancel) {
    btnLodgeCancel.addEventListener('click', (e) => {
      e.preventDefault();
      window.citizenShieldLodgeCancel();
    });
  }

  // Review Modal Opener
  document.getElementById('btn-open-review').addEventListener('click', () => {
    const title = document.getElementById('lodge-title').value.trim();
    const dept = document.getElementById('lodge-dept').value;
    const cat = document.getElementById('lodge-category').value;
    const prio = document.getElementById('lodge-priority').value;
    const ward = document.getElementById('lodge-ward').value;
    const desc = document.getElementById('lodge-description').value.trim();
    const loc = inputLoc.value.trim();

    if (!title || !desc || !loc || !ward || !cat) {
      showToast("Please complete all mandatory fields (Title, Category, Ward, Address, Description) before reviewing.", "error");
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

  // Final Submission to Persistent SQLite Vault
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

    // Attach AI detection fields if available
    if (currentAiResult && currentAiResult.detected) {
      formData.append('ai_detected_class', currentAiResult.detected_class);
      formData.append('ai_confidence_score', currentAiResult.confidence_score);
      formData.append('ai_model_name', currentAiResult.model_name);
      formData.append('ai_suggested_category', currentAiResult.suggested_category);
      if (currentAiResult.temp_image_filename) {
        formData.append('temp_image_filename', currentAiResult.temp_image_filename);
      }
    }

    if (selectedEvidenceFile) {
      formData.append('image', selectedEvidenceFile);
    }

    try {
      btn.disabled = true;
      btn.textContent = 'Writing to SQLite Vault...';

      const res = await apiSubmitReport(formData);

      closeModal('modal-review');
      showToast(`Grievance permanently recorded! Tracking ID: ${res.report_id}`, "success", 7000);

      // Reset form
      document.getElementById('form-lodge-grievance').reset();
      previewBox.classList.add('hidden');
      aiResultCard.classList.add('hidden');
      document.getElementById('duplicate-warning-banner').classList.add('hidden');
      selectedEvidenceFile = null;
      currentAiResult = null;

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
 * Module 7: Duplicate Complaint Checking Logic
 */
async function triggerDuplicateCheck() {
  const cat = document.getElementById('lodge-category').value;
  const warningBanner = document.getElementById('duplicate-warning-banner');
  const warningText = document.getElementById('duplicate-warning-text');
  const nearbyList = document.getElementById('duplicate-nearby-list');

  if (!cat || !currentReportLat || !currentReportLng) {
    warningBanner.classList.add('hidden');
    return;
  }

  try {
    const res = await apiCheckDuplicate(cat, currentReportLat, currentReportLng);
    if (res.is_duplicate && res.nearby_reports.length > 0) {
      warningBanner.classList.remove('hidden');
      warningText.textContent = res.warning_message;
      nearbyList.innerHTML = res.nearby_reports.map(r => `
        <div style="margin-top: 4px;">• <strong>${escapeHtml(r.tracking_id)}</strong> (${escapeHtml(r.title)}) — ${escapeHtml(r.status)} [~${r.distance_meters}m away]</div>
      `).join('');
    } else {
      warningBanner.classList.add('hidden');
    }
  } catch (err) {
    console.debug("Duplicate check notice:", err);
  }
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
        <h3 style="font-size: 1.15rem; font-weight: 800; color: #ffffff; margin-bottom: 6px;">No Grievance Records Found</h3>
        <p style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 16px;">There are currently no active complaints matching your filter.</p>
        <button class="btn btn-lagoon btn-sm" data-view-target="view-submit">+ Lodge a Grievance Now</button>
      </div>
    `;
    return;
  }

  reports.forEach(r => {
    const card = document.createElement('div');
    card.className = 'lagoon-card';
    card.style.padding = '20px 24px';

    const aiBadge = r.detected_class ? `
      <span style="font-size: 0.76rem; background: rgba(56, 189, 248, 0.15); color: var(--teal-light); padding: 2px 8px; border-radius: var(--radius-full); border: 1px solid rgba(56, 189, 248, 0.3);">
        AI Detected: ${escapeHtml(r.detected_class)} (${Math.round((r.confidence_score || 0.85) * 100)}%)
      </span>
    ` : '';

    card.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; flex-wrap: wrap;">
        <div>
          <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px; flex-wrap: wrap;">
            <span class="report-token">${r.report_id || r.tracking_id}</span>
            <span class="dept-tag">${escapeHtml(r.department)}</span>
            ${getPriorityPill(r.priority)}
            ${aiBadge}
          </div>
          <h3 style="font-size: 1.15rem; font-weight: 700; color: #ffffff; margin-bottom: 4px;">${escapeHtml(r.title || r.complaint_title)}</h3>
          <p style="font-size: 0.88rem; color: var(--text-muted); line-height: 1.5; margin-bottom: 8px;">${escapeHtml(r.description)}</p>
          <div style="font-size: 0.82rem; color: var(--teal-light);">
            📍 ${escapeHtml(r.ward)} • ${escapeHtml(r.location)}
          </div>
        </div>
        <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 10px;">
          ${getStatusPill(r.status)}
          <button class="btn btn-glass btn-sm" onclick="window.inspectTrackReport('${r.report_id}')">
            Track Case Timeline →
          </button>
        </div>
      </div>
      ${r.admin_remarks ? `
        <div style="margin-top: 14px; padding: 10px 14px; background: rgba(8, 29, 36, 0.7); border-left: 3px solid var(--teal-light); border-radius: var(--radius-sm); font-size: 0.86rem; color: #e2e8f0;">
          <strong>Officer Remarks:</strong> ${escapeHtml(r.admin_remarks)}
        </div>
      ` : ''}
    `;
    container.appendChild(card);
  });
}

/**
 * Case Tracking Dossier View
 */
function setupTracking() {
  const btnTrack = document.getElementById('btn-execute-tracking');
  const inputTrack = document.getElementById('input-track-id');

  btnTrack.addEventListener('click', () => {
    const id = inputTrack.value.trim();
    if (!id) {
      showToast("Please enter a valid Report Reference ID.", "warning");
      return;
    }
    executeTrack(id);
  });

  inputTrack.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      btnTrack.click();
    }
  });

  window.inspectTrackReport = (reportId) => {
    navigate('view-tracking');
    document.getElementById('input-track-id').value = reportId;
    executeTrack(reportId);
  };
}

async function executeTrack(reportId) {
  const resultContainer = document.getElementById('tracking-result-dossier');
  const btn = document.getElementById('btn-execute-tracking');

  try {
    btn.disabled = true;
    btn.textContent = 'Verifying Record...';

    const r = await apiTrackReport(reportId);

    document.getElementById('dossier-ref-code').textContent = r.tracking_id || r.report_id;
    document.getElementById('dossier-lodged-date').textContent = r.created_at;
    document.getElementById('dossier-title').textContent = r.title || r.complaint_title;
    document.getElementById('dossier-dept').textContent = r.department;
    document.getElementById('dossier-category').textContent = r.category;
    document.getElementById('dossier-status-badge').innerHTML = getStatusPill(r.status);
    document.getElementById('dossier-priority-badge').innerHTML = getPriorityPill(r.priority);
    document.getElementById('dossier-ward').textContent = r.ward;
    document.getElementById('dossier-location').textContent = r.location;
    document.getElementById('dossier-sla').textContent = `${r.sla_hours || 48} Hours SLA`;
    document.getElementById('dossier-description').textContent = r.description;

    // AI Badge Box
    const aiBadgeBox = document.getElementById('dossier-ai-badge-box');
    if (r.detected_class && r.detected_class !== 'No supported civic problem detected') {
      aiBadgeBox.classList.remove('hidden');
      document.getElementById('dossier-ai-class').textContent = r.detected_class;
      document.getElementById('dossier-ai-conf').textContent = `${Math.round((r.confidence_score || 0.85) * 100)}%`;
      document.getElementById('dossier-ai-model').textContent = r.model_name || 'YOLOv8';
    } else {
      aiBadgeBox.classList.add('hidden');
    }

    // Evidence Photo
    const photoContainer = document.getElementById('dossier-photo-container');
    const photoImg = document.getElementById('dossier-photo');
    if (r.image_filename || r.image_path) {
      const imgFile = r.image_filename || r.image_path;
      photoImg.src = `/api/uploads/${imgFile}`;
      photoContainer.classList.remove('hidden');
    } else {
      photoContainer.classList.add('hidden');
    }

    // After Repair Photo (if resolved)
    const afterContainer = document.getElementById('dossier-after-photo-container');
    const afterImg = document.getElementById('dossier-after-photo');
    if (r.after_repair_image) {
      afterImg.src = `/api/uploads/${r.after_repair_image}`;
      afterContainer.classList.remove('hidden');
    } else {
      afterContainer.classList.add('hidden');
    }

    // Audit Timeline
    const timeline = document.getElementById('dossier-timeline');
    timeline.innerHTML = '';

    const history = r.status_history || [];
    history.forEach(step => {
      const node = document.createElement('div');
      node.className = 'audit-node';
      node.innerHTML = `
        <div class="audit-content">
          <div class="audit-heading">
            <span class="audit-title">${escapeHtml(step.new_status || step.status)} — ${escapeHtml(step.officer_name || step.updated_by || 'Municipal Authority')}</span>
            <span class="audit-time">${escapeHtml(step.created_at)}</span>
          </div>
          <div class="audit-remarks">${escapeHtml(step.officer_remarks || step.remarks)}</div>
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

  const searchInput = document.getElementById('adm-search-input');
  const filterStatus = document.getElementById('adm-filter-status');
  const filterPriority = document.getElementById('adm-filter-priority');
  const filterCat = document.getElementById('adm-filter-category');
  const filterWard = document.getElementById('adm-filter-ward');

  const onFilterChange = async () => {
    let searchVal = searchInput.value.trim();
    if (filterWard && filterWard.value !== 'ALL') {
      searchVal = searchVal ? `${searchVal} ${filterWard.value}` : filterWard.value;
    }
    const filters = {
      search: searchVal,
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
  if (filterWard) {
    filterWard.addEventListener('change', onFilterChange);
  }

  // Toggle mandatory after-repair photo field on status change
  const officerStatusSelect = document.getElementById('officer-select-status');
  const afterPhotoGroup = document.getElementById('officer-after-photo-group');
  officerStatusSelect.addEventListener('change', () => {
    if (officerStatusSelect.value === 'Resolved') {
      afterPhotoGroup.classList.remove('hidden');
    } else {
      afterPhotoGroup.classList.add('hidden');
    }
  });

  document.getElementById('officer-after-photo').addEventListener('change', (e) => {
    selectedAfterRepairFile = e.target.files && e.target.files[0] ? e.target.files[0] : null;
  });

  // Status Directive Update Modal Submission
  document.getElementById('btn-save-officer-directive').addEventListener('click', async () => {
    const reportId = (document.getElementById('officer-update-ref-id').value || '').trim();
    const newStatus = document.getElementById('officer-select-status').value;
    const newDept = document.getElementById('officer-select-dept').value;
    const newPriority = document.getElementById('officer-select-priority').value;
    const remarks = document.getElementById('officer-text-remarks').value.trim();
    const btn = document.getElementById('btn-save-officer-directive');

    // Retrieve file directly from input element or state variable
    const afterPhotoInput = document.getElementById('officer-after-photo');
    const repairPhotoFile = (afterPhotoInput && afterPhotoInput.files && afterPhotoInput.files[0]) ? afterPhotoInput.files[0] : selectedAfterRepairFile;

    if (!remarks) {
      showToast("Please provide an official justification and action remark.", "error");
      return;
    }

    if (newStatus === 'Resolved' && !repairPhotoFile) {
      // Check if complaint already has an after repair image in database
      const foundReport = cachedAdminReports.find(r => (r.report_id === reportId || r.tracking_id === reportId));
      if (!foundReport || !foundReport.after_repair_image) {
        showToast("Mandatory: Please attach an after-repair photo before marking as Resolved.", "error");
        return;
      }
    }

    try {
      btn.disabled = true;
      btn.textContent = 'Committing Directive...';

      await apiUpdateReportStatus(reportId, newStatus, remarks, newDept, repairPhotoFile, newPriority);

      showToast(`Grievance ${reportId} status updated to ${newStatus}.`, "success");
      closeModal('modal-officer-action');
      selectedAfterRepairFile = null;
      if (afterPhotoInput) afterPhotoInput.value = '';
      
      // Refresh Officer Console and Zone Monitoring data seamlessly
      await loadOfficerConsole();
      if (typeof loadLiveZoneData === 'function') {
        loadLiveZoneData();
      }
    } catch (err) {
      console.error("Directive publish failure:", err);
      showToast(err.message || "Failed to publish directive.", "error");
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

    const aiBadge = r.detected_class && r.detected_class !== 'No supported civic problem detected' ? `
      <div style="margin-top: 4px; font-size: 0.74rem; color: var(--teal-light);">
        🧠 <strong>${escapeHtml(r.detected_class)}</strong> (${Math.round((r.confidence_score || 0.85) * 100)}%)
      </div>
    ` : '';

    const imgFile = r.image_filename || r.image_path;
    const photoCell = imgFile ? `
      <div style="display: flex; align-items: center; gap: 8px;">
        <img src="/api/uploads/${encodeURIComponent(imgFile)}" alt="Evidence" style="width: 44px; height: 44px; object-fit: cover; border-radius: 4px; border: 1px solid var(--teal-light); cursor: pointer;" onclick="window.openImageLightbox('/api/uploads/${encodeURIComponent(imgFile)}', '${escapeAttr(r.tracking_id || r.report_id)}: ${escapeAttr(r.title || r.complaint_title)}')">
        <button type="button" class="btn btn-glass btn-sm" style="padding: 2px 6px; font-size: 0.72rem;" onclick="window.openImageLightbox('/api/uploads/${encodeURIComponent(imgFile)}', '${escapeAttr(r.tracking_id || r.report_id)}: ${escapeAttr(r.title || r.complaint_title)}')">View</button>
      </div>
    ` : `<span style="color: var(--text-muted); font-size: 0.78rem;">No Photo</span>`;

    tr.innerHTML = `
      <td><span class="report-token">${r.tracking_id || r.report_id}</span></td>
      <td><strong>${escapeHtml(r.citizen_name)}</strong><br><span style="font-size: 0.78rem; color: var(--text-muted);">${escapeHtml(r.citizen_phone || r.citizen_email)}</span></td>
      <td><span class="dept-tag">${escapeHtml(r.department)}</span></td>
      <td>${photoCell}</td>
      <td>${getPriorityPill(r.priority)}</td>
      <td style="max-width: 220px; font-weight: 600;">
        ${escapeHtml(r.title || r.complaint_title)}
        ${aiBadge}
      </td>
      <td style="max-width: 180px; font-size: 0.82rem;">${escapeHtml(r.ward)}<br><span style="color: var(--text-muted);">${escapeHtml(r.location)}</span></td>
      <td>${getStatusPill(r.status)}</td>
      <td>
        <button class="btn btn-lagoon btn-sm" onclick="window.openOfficerDirectiveModal('${r.report_id}', '${escapeAttr(r.title || r.complaint_title)}', '${r.status}', '${r.department}', '${r.priority}')">
          Directive ⚙️
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// Lightbox preview for full-resolution inspection
window.openImageLightbox = (imageUrl, caption = '') => {
  const lbModal = document.getElementById('modal-image-lightbox');
  const lbImg = document.getElementById('lightbox-img');
  const lbCaption = document.getElementById('lightbox-caption');
  const lbDownload = document.getElementById('lightbox-download-link');

  if (lbImg) lbImg.src = imageUrl;
  if (lbCaption) lbCaption.textContent = caption;
  if (lbDownload) lbDownload.href = imageUrl;

  openModal('modal-image-lightbox');
};

window.openOfficerDirectiveModal = (reportId, title, currentStatus, currentDept, currentPriority) => {
  document.getElementById('officer-update-ref-id').value = reportId;
  document.getElementById('officer-dialog-ref').textContent = reportId;
  document.getElementById('officer-dialog-title').textContent = title;
  document.getElementById('officer-select-status').value = currentStatus;
  document.getElementById('officer-select-dept').value = currentDept || '';
  document.getElementById('officer-select-priority').value = currentPriority || '';
  document.getElementById('officer-text-remarks').value = '';

  // Look up complaint to show image in directive modal
  const foundReport = cachedAdminReports.find(r => (r.report_id === reportId || r.tracking_id === reportId));
  const photoImg = document.getElementById('officer-dialog-photo');
  const photoPlaceholder = document.getElementById('officer-photo-placeholder');
  const expandBtn = document.getElementById('btn-officer-expand-photo');
  const aiTag = document.getElementById('officer-ai-detect-tag');

  const photoFile = foundReport ? (foundReport.image_filename || foundReport.image_path) : null;
  if (photoFile) {
    const photoUrl = `/api/uploads/${encodeURIComponent(photoFile)}`;
    photoImg.src = photoUrl;
    photoImg.classList.remove('hidden');
    photoPlaceholder.classList.add('hidden');
    expandBtn.classList.remove('hidden');
    photoImg.onclick = () => window.openImageLightbox(photoUrl, `${reportId}: ${title}`);
    expandBtn.onclick = () => window.openImageLightbox(photoUrl, `${reportId}: ${title}`);
  } else {
    photoImg.classList.add('hidden');
    photoPlaceholder.classList.remove('hidden');
    expandBtn.classList.add('hidden');
  }

  if (foundReport && foundReport.detected_class && foundReport.detected_class !== 'No supported civic problem detected') {
    aiTag.innerHTML = `🧠 <strong>Real AI Detection:</strong> ${escapeHtml(foundReport.detected_class)} (Confidence: ${Math.round((foundReport.confidence_score || 0.85)*100)}% via ${escapeHtml(foundReport.model_name || 'YOLOv8')})`;
  } else {
    aiTag.innerHTML = '';
  }

  const afterGroup = document.getElementById('officer-after-photo-group');
  if (currentStatus === 'Resolved') {
    afterGroup.classList.remove('hidden');
  } else {
    afterGroup.classList.add('hidden');
  }

  const afterPhotoInput = document.getElementById('officer-after-photo');
  if (afterPhotoInput) afterPhotoInput.value = '';
  selectedAfterRepairFile = null;
  openModal('modal-officer-action');
};

/**
 * Module 3: AI Detection Dashboard
 */
function setupAiDashboard() {
  const btnRefresh = document.getElementById('btn-refresh-ai-metrics');
  if (btnRefresh) {
    btnRefresh.addEventListener('click', () => {
      loadAiDashboard();
    });
  }
}

async function loadAiDashboard() {
  try {
    const data = await apiGetAiMetrics();

    document.getElementById('ai-metric-total-analyzed').textContent = data.total_analyzed;
    document.getElementById('ai-metric-supported-detected').textContent = data.total_supported_detections;
    document.getElementById('ai-metric-avg-conf').textContent = data.avg_confidence_percent;
    document.getElementById('ai-metric-failures').textContent = data.detection_failures;

    document.getElementById('ai-stat-potholes').textContent = data.potholes_detected;
    document.getElementById('ai-stat-garbage').textContent = data.garbage_detected;
    document.getElementById('ai-stat-road-damage').textContent = data.road_damage_detected;
    document.getElementById('ai-stat-drainage').textContent = data.drainage_detected;
    document.getElementById('ai-stat-water-leakage').textContent = data.water_leakage_detected;

    const tbody = document.getElementById('ai-detections-table-body');
    tbody.innerHTML = '';

    if (!data.recent_detections || data.recent_detections.length === 0) {
      tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 24px; color: var(--text-muted);">No AI detection records found.</td></tr>';
      return;
    }

    data.recent_detections.forEach(d => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><span style="font-family: var(--font-mono); color: var(--teal-light);">#${d.detection_id}</span></td>
        <td><span class="report-token">${d.report_id}</span></td>
        <td><strong>${escapeHtml(d.detected_class)}</strong></td>
        <td><span style="color: var(--mint-glow); font-weight: 700;">${Math.round(d.confidence_score * 100)}%</span></td>
        <td><span style="font-family: var(--font-mono); font-size: 0.8rem;">${escapeHtml(d.model_name)}</span></td>
        <td>${escapeHtml(d.suggested_category)}</td>
        <td>${d.detection_status === 'SUCCESS' ? '<span class="status-pill status-resolved">● Verified</span>' : '<span class="status-pill status-rejected">● Fallback</span>'}</td>
        <td style="font-size: 0.8rem; color: var(--text-muted);">${escapeHtml(d.detected_at)}</td>
      `;
      tbody.appendChild(tr);
    });

    showToast("AI Vision Analytics refreshed with live SQLite data.", "info");
  } catch (err) {
    showToast(`Error loading AI dashboard: ${err.message}`, "error");
  }
}

/**
 * Module: Live Colour-Coded Zone Monitoring & Spatial Density Map
 */
function setupZoneMonitoring() {
  const btnRefresh = document.getElementById('btn-manual-refresh-zones');
  if (btnRefresh) {
    btnRefresh.addEventListener('click', () => {
      fetchAndUpdateZoneData(true);
    });
  }
}

async function loadLiveZoneMonitoring() {
  initZoneLeafletMap();
  await fetchAndUpdateZoneData(false);

  // Clear existing timer if any
  if (zoneRefreshInterval) clearInterval(zoneRefreshInterval);
  zoneTimerCountdown = 20;

  // Set recurring auto-refresh every 20 seconds
  zoneRefreshInterval = setInterval(async () => {
    zoneTimerCountdown--;
    const timerEl = document.getElementById('zone-refresh-timer');
    if (timerEl) timerEl.textContent = `${zoneTimerCountdown}s`;

    if (zoneTimerCountdown <= 0) {
      zoneTimerCountdown = 20;
      // Only refresh if currently on view-zone-monitoring
      const viewZone = document.getElementById('view-zone-monitoring');
      if (viewZone && !viewZone.classList.contains('hidden')) {
        await fetchAndUpdateZoneData(false);
      }
    }
  }, 1000);
}

function initZoneLeafletMap() {
  if (zoneLeafletMap) {
    zoneLeafletMap.invalidateSize();
    return;
  }

  const mapContainer = document.getElementById('live-zone-leaflet-map');
  if (!mapContainer) return;

  // Centered on Tumakuru Municipal Corporation
  zoneLeafletMap = L.map('live-zone-leaflet-map', {
    center: [13.3385, 77.1120],
    zoom: 13,
    zoomControl: true
  });

  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; <a href="https://carto.com/">CARTO</a> | CitizenShield Spatial Engine',
    maxZoom: 19
  }).addTo(zoneLeafletMap);

  zonePolygonsLayer = L.layerGroup().addTo(zoneLeafletMap);
  zoneMarkersLayer = L.layerGroup().addTo(zoneLeafletMap);
}

async function fetchAndUpdateZoneData(isManual = false) {
  try {
    const data = await apiGetZonesSummary();
    cachedZonesData = data.zones || [];

    // Update KPI counters
    document.getElementById('kpi-total-zones').textContent = data.total_zones;
    document.getElementById('kpi-green-zones').textContent = data.green_zones;
    document.getElementById('kpi-orange-zones').textContent = data.orange_zones;
    document.getElementById('kpi-red-zones').textContent = data.red_zones;
    document.getElementById('kpi-active-complaints').textContent = data.total_active_complaints;
    document.getElementById('kpi-resolved-complaints').textContent = data.total_resolved_complaints;

    // Last updated timestamp
    const now = new Date();
    document.getElementById('zone-last-updated').textContent = now.toLocaleTimeString();

    // High volume emergency alert check (>10 complaints in any single zone)
    const criticalZone = cachedZonesData.find(z => z.warning);
    const alertBanner = document.getElementById('zone-high-volume-alert');
    const alertMsg = document.getElementById('zone-high-volume-msg');
    if (criticalZone) {
      alertBanner.classList.remove('hidden');
      alertMsg.textContent = `${criticalZone.name}: ${criticalZone.warning}`;
    } else {
      alertBanner.classList.add('hidden');
    }

    renderZoneOverlays(cachedZonesData);

    // If first load or no drawer open, select highest density zone
    if (cachedZonesData.length > 0) {
      // Sort to find zone with highest active complaints
      const sorted = [...cachedZonesData].sort((a, b) => b.active_complaints - a.active_complaints);
      renderZoneDrawer(sorted[0]);
    }

    if (isManual) {
      showToast("Zone monitoring map updated with live complaint counts.", "success");
    }
  } catch (err) {
    console.error("Zone fetch error:", err);
    if (isManual) {
      showToast(`Zone update failed: ${err.message}`, "error");
    }
  }
}

function renderZoneOverlays(zones) {
  if (!zoneLeafletMap || !zonePolygonsLayer || !zoneMarkersLayer) return;

  zonePolygonsLayer.clearLayers();
  zoneMarkersLayer.clearLayers();

  zones.forEach(z => {
    // Draw geographical boundary rectangle
    const rect = L.rectangle(z.bounds, {
      color: z.color,
      weight: 2.5,
      opacity: 0.9,
      fillColor: z.color,
      fillOpacity: 0.22,
      dashArray: z.tier === 'RED' ? '6, 6' : null
    });

    // Tooltip
    rect.bindTooltip(`
      <div style="font-family: sans-serif; font-size: 0.82rem; padding: 4px;">
        <strong style="color: ${z.color};">${z.name}</strong><br>
        <strong>${z.active_complaints} Active Complaints</strong> (${z.label})
      </div>
    `, { sticky: true, opacity: 0.95 });

    // Click handler -> Open Drawer
    rect.on('click', () => {
      renderZoneDrawer(z);
      zoneLeafletMap.panTo(z.center);
    });

    rect.addTo(zonePolygonsLayer);

    // Add Center Zone Label Badge Marker
    const badgeIcon = L.divIcon({
      className: 'zone-badge-label',
      html: `
        <div style="background: rgba(5, 19, 24, 0.9); border: 2px solid ${z.color}; color: #ffffff; padding: 4px 10px; border-radius: 20px; font-size: 0.76rem; font-weight: 800; white-space: nowrap; box-shadow: 0 4px 12px rgba(0,0,0,0.6); display: flex; align-items: center; gap: 6px; cursor: pointer;">
          <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: ${z.color};"></span>
          <span>${z.name.split(' - ')[0]}: <strong>${z.active_complaints}</strong></span>
        </div>
      `,
      iconSize: [120, 30],
      iconAnchor: [60, 15]
    });

    const centerMarker = L.marker(z.center, { icon: badgeIcon });
    centerMarker.on('click', () => {
      renderZoneDrawer(z);
    });
    centerMarker.addTo(zonePolygonsLayer);

    // Plot Individual Complaint Location Markers within this Zone
    (z.complaints || []).forEach(c => {
      if (c.latitude && c.longitude) {
        const markerColor = z.color;
        const cMarker = L.circleMarker([c.latitude, c.longitude], {
          radius: 7,
          fillColor: markerColor,
          color: '#ffffff',
          weight: 1.5,
          opacity: 1,
          fillOpacity: 0.85
        });

        cMarker.bindPopup(`
          <div style="font-family: sans-serif; font-size: 0.84rem; min-width: 220px;">
            <div style="font-size: 0.72rem; color: #94a3b8; font-weight: 700; text-transform: uppercase;">${escapeHtml(z.name)}</div>
            <strong style="color: #0284c7; font-size: 0.9rem;">${escapeHtml(c.tracking_id || c.report_id)}</strong>
            <div style="font-weight: 700; margin: 4px 0 2px 0;">${escapeHtml(c.title || c.complaint_title)}</div>
            <div style="font-size: 0.78rem; color: #64748b; margin-bottom: 6px;">📍 ${escapeHtml(c.location)}</div>
            <div style="display: flex; gap: 6px; margin-bottom: 8px;">
              <span style="font-size: 0.72rem; padding: 2px 6px; background: #e0f2fe; color: #0369a1; border-radius: 4px;">${escapeHtml(c.category)}</span>
              <span style="font-size: 0.72rem; padding: 2px 6px; background: #fef3c7; color: #92400e; border-radius: 4px;">${escapeHtml(c.priority)}</span>
            </div>
            ${c.image_filename ? `
              <div style="text-align: center; margin-bottom: 8px;">
                <img src="/api/uploads/${encodeURIComponent(c.image_filename)}" alt="Complaint Photo" style="max-height: 100px; max-width: 100%; border-radius: 4px; border: 1px solid #cbd5e1; cursor: pointer;" onclick="window.openImageLightbox('/api/uploads/${encodeURIComponent(c.image_filename)}', '${escapeAttr(c.tracking_id)}: ${escapeAttr(c.title)}')">
              </div>
            ` : ''}
            <button class="btn btn-lagoon btn-sm" style="width: 100%; font-size: 0.75rem; padding: 4px 8px;" onclick="window.openOfficerDirectiveModal('${c.report_id}', '${escapeAttr(c.title || c.complaint_title)}', '${c.status}', '${c.department}', '${c.priority}')">
              Directive &amp; Status ⚙️
            </button>
          </div>
        `);

        cMarker.addTo(zoneMarkersLayer);
      }
    });
  });
}

function renderZoneDrawer(zone) {
  const badge = document.getElementById('zone-drawer-badge');
  const title = document.getElementById('zone-drawer-title');
  const desc = document.getElementById('zone-drawer-desc');
  const dept = document.getElementById('zone-drawer-dept');
  const count = document.getElementById('zone-drawer-count');
  const list = document.getElementById('zone-drawer-complaints-list');

  if (!zone) return;

  badge.style.background = zone.color;
  badge.textContent = `${zone.tier} ZONE (${zone.active_complaints} ACTIVE)`;
  title.textContent = zone.name;
  desc.textContent = zone.description;
  dept.textContent = zone.assigned_department;
  count.textContent = `${zone.active_complaints} Active ${zone.active_complaints === 1 ? 'Complaint' : 'Complaints'}`;

  list.innerHTML = '';

  if (!zone.complaints || zone.complaints.length === 0) {
    list.innerHTML = `
      <div style="color: var(--mint-glow); font-size: 0.88rem; text-align: center; padding: 24px; background: rgba(16, 185, 129, 0.08); border-radius: var(--radius-sm); border: 1px solid rgba(16, 185, 129, 0.2);">
        ✓ No active grievances in this zone. Municipal standards compliant.
      </div>
    `;
    return;
  }

  zone.complaints.forEach(c => {
    const card = document.createElement('div');
    card.style.cssText = 'padding: 12px 14px; background: rgba(8, 29, 36, 0.75); border: 1px solid var(--lagoon-border); border-radius: var(--radius-sm); display: flex; flex-direction: column; gap: 8px;';

    const imgFile = c.image_filename || c.image_path;
    const photoThumb = imgFile ? `
      <div style="margin-top: 6px; display: flex; align-items: center; gap: 10px;">
        <img src="/api/uploads/${encodeURIComponent(imgFile)}" alt="Complaint Photo" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px; border: 1px solid var(--teal-light); cursor: pointer;" onclick="window.openImageLightbox('/api/uploads/${encodeURIComponent(imgFile)}', '${escapeAttr(c.tracking_id || c.report_id)}: ${escapeAttr(c.title)}')">
        <button type="button" class="btn btn-glass btn-sm" style="font-size: 0.72rem; padding: 3px 8px;" onclick="window.openImageLightbox('/api/uploads/${encodeURIComponent(imgFile)}', '${escapeAttr(c.tracking_id || c.report_id)}: ${escapeAttr(c.title)}')">
          🔍 View Photo
        </button>
      </div>
    ` : `<span style="font-size: 0.76rem; color: var(--text-muted); margin-top: 4px;">No image attached</span>`;

    card.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <span class="report-token" style="font-size: 0.78rem;">${escapeHtml(c.tracking_id || c.report_id)}</span>
        <span class="status-pill status-${(c.status || '').toLowerCase().replace(' ', '-')}">${escapeHtml(c.status)}</span>
      </div>
      <div style="font-weight: 700; color: #ffffff; font-size: 0.9rem;">${escapeHtml(c.title || c.complaint_title)}</div>
      <div style="font-size: 0.8rem; color: var(--text-muted); line-height: 1.4;">${escapeHtml(c.description)}</div>
      <div style="font-size: 0.78rem; color: var(--teal-light);">
        📍 ${escapeHtml(c.location)} (${c.latitude.toFixed(4)}, ${c.longitude.toFixed(4)})
      </div>
      <div style="font-size: 0.76rem; color: var(--text-muted);">
        Category: <strong>${escapeHtml(c.category)}</strong> • Priority: <strong>${escapeHtml(c.priority)}</strong>
      </div>
      ${photoThumb}
      <div style="margin-top: 6px; display: flex; justify-content: flex-end; gap: 8px;">
        <button class="btn btn-lagoon btn-sm" style="font-size: 0.75rem; padding: 4px 10px;" onclick="window.openOfficerDirectiveModal('${c.report_id}', '${escapeAttr(c.title || c.complaint_title)}', '${c.status}', '${c.department}', '${c.priority}')">
          Directive ⚙️
        </button>
      </div>
    `;

    list.appendChild(card);
  });
}

/**
 * Modals and Toast Infrastructure
 */
function setupModals() {
  // Global delegated click listener for modal close elements
  document.addEventListener('click', (e) => {
    const closeBtn = e.target.closest('[data-modal-close]');
    if (closeBtn) {
      e.preventDefault();
      const id = closeBtn.getAttribute('data-modal-close');
      closeModal(id);
      return;
    }

    // Backdrop click to dismiss
    if (e.target.classList.contains('modal-backdrop')) {
      closeModal(e.target.id);
    }
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

window.citizenShieldCloseModal = closeModal;

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
