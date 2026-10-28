// CitizenShield - Reports Management & Submission
import { db, storage, isDemoMode } from './firebase-config.js';
import { getCurrentUser } from './auth.js';

// Seed sample reports for demo mode if not present
function initDemoReports() {
  if (!localStorage.getItem('cs_demo_reports')) {
    const sampleReports = [
      {
        id: 'rep_001',
        reportId: 'CS-2026-10482',
        userId: 'user_citizen_01',
        userDisplayName: 'Rahul Sharma',
        userEmail: 'citizen@test.com',
        title: 'Broken streetlights on 4th Main Road',
        category: 'Streetlights and Electricity',
        description: 'Two consecutive streetlights have not been functioning for over a week, causing dark spots and safety concerns for pedestrians at night.',
        location: '4th Main Road, Indiranagar, Bengaluru',
        latitude: 12.9784,
        longitude: 77.6408,
        imageUrl: null,
        status: 'In Progress',
        adminRemarks: 'Field inspection completed. Electrician team dispatched for bulb and cable replacement.',
        statusHistory: [
          { status: 'Submitted', remarks: 'Complaint registered by citizen.', updatedAt: new Date(Date.now() - 86400000 * 3).toISOString(), updatedBy: 'Citizen' },
          { status: 'Under Review', remarks: 'Assigned to Ward 112 Electrical Division.', updatedAt: new Date(Date.now() - 86400000 * 2).toISOString(), updatedBy: 'Municipal Admin Officer' },
          { status: 'In Progress', remarks: 'Field inspection completed. Electrician team dispatched for bulb and cable replacement.', updatedAt: new Date(Date.now() - 86400000).toISOString(), updatedBy: 'Municipal Admin Officer' }
        ],
        createdAt: new Date(Date.now() - 86400000 * 3).toISOString(),
        updatedAt: new Date(Date.now() - 86400000).toISOString()
      },
      {
        id: 'rep_002',
        reportId: 'CS-2026-28491',
        userId: 'user_citizen_01',
        userDisplayName: 'Rahul Sharma',
        userEmail: 'citizen@test.com',
        title: 'Deep pothole near school crossing',
        category: 'Roads and Transport',
        description: 'Large pothole forming right outside Government High School gate. Poses hazard to school buses and two-wheelers during rains.',
        location: 'Near Govt High School, MG Road cross',
        latitude: 12.9716,
        longitude: 77.5946,
        imageUrl: null,
        status: 'Under Review',
        adminRemarks: 'Work order queued under monthly road maintenance schedule.',
        statusHistory: [
          { status: 'Submitted', remarks: 'Complaint registered by citizen.', updatedAt: new Date(Date.now() - 86400000 * 5).toISOString(), updatedBy: 'Citizen' },
          { status: 'Under Review', remarks: 'Work order queued under monthly road maintenance schedule.', updatedAt: new Date(Date.now() - 86400000 * 2).toISOString(), updatedBy: 'Municipal Admin Officer' }
        ],
        createdAt: new Date(Date.now() - 86400000 * 5).toISOString(),
        updatedAt: new Date(Date.now() - 86400000 * 2).toISOString()
      },
      {
        id: 'rep_003',
        reportId: 'CS-2026-39182',
        userId: 'user_other',
        userDisplayName: 'Priya Patel',
        userEmail: 'priya@test.com',
        title: 'Overflowing garbage bin at commercial market',
        category: 'Garbage and Sanitation',
        description: 'Garbage has not been cleared for 3 days and is spilling onto the pedestrian footpath.',
        location: 'Commercial Street Market Gate 2',
        latitude: 12.9822,
        longitude: 77.6083,
        imageUrl: null,
        status: 'Resolved',
        adminRemarks: 'Waste clearing truck deployed. Secondary collection bin sanitized and emptied.',
        statusHistory: [
          { status: 'Submitted', remarks: 'Complaint registered by citizen.', updatedAt: new Date(Date.now() - 86400000 * 6).toISOString(), updatedBy: 'Citizen' },
          { status: 'Under Review', remarks: 'Notified Sanitation Supervisor.', updatedAt: new Date(Date.now() - 86400000 * 4).toISOString(), updatedBy: 'Municipal Admin Officer' },
          { status: 'In Progress', remarks: 'Sanitation vehicle en route.', updatedAt: new Date(Date.now() - 86400000 * 3).toISOString(), updatedBy: 'Municipal Admin Officer' },
          { status: 'Resolved', remarks: 'Waste clearing truck deployed. Secondary collection bin sanitized and emptied.', updatedAt: new Date(Date.now() - 86400000).toISOString(), updatedBy: 'Municipal Admin Officer' }
        ],
        createdAt: new Date(Date.now() - 86400000 * 6).toISOString(),
        updatedAt: new Date(Date.now() - 86400000).toISOString()
      }
    ];
    localStorage.setItem('cs_demo_reports', JSON.stringify(sampleReports));
  }
}

if (isDemoMode) {
  initDemoReports();
}

/**
 * Generate human-readable Report ID (e.g., CS-2026-48201)
 */
export function generateReportId() {
  const year = new Date().getFullYear();
  const randomSuffix = Math.floor(10000 + Math.random() * 90000);
  return `CS-${year}-${randomSuffix}`;
}

/**
 * Upload image to Firebase Storage or return base64 for demo
 */
async function uploadReportImage(file, userId) {
  if (!file) return null;

  if (file.size > 5 * 1024 * 1024) {
    throw new Error("Attached image exceeds the maximum permitted size of 5 MB.");
  }

  const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
  if (!validTypes.includes(file.type)) {
    throw new Error("Invalid image format. Allowed formats: JPG, PNG, WEBP.");
  }

  if (isDemoMode) {
    return new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = (e) => resolve(e.target.result);
      reader.onerror = () => resolve(null);
      reader.readAsDataURL(file);
    });
  }

  // Live Firebase Storage
  const { ref, uploadBytes, getDownloadURL } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-storage.js");
  const extension = file.name.split('.').pop() || 'jpg';
  const filename = `${Date.now()}_${Math.random().toString(36).substring(2, 9)}.${extension}`;
  const fileRef = ref(storage, `reports/${userId}/${filename}`);
  
  await uploadBytes(fileRef, file, { contentType: file.type });
  return await getDownloadURL(fileRef);
}

/**
 * Submit a new Civic Report
 */
export async function submitReport(reportData, imageFile = null) {
  const user = getCurrentUser();
  if (!user) {
    throw new Error("You must be logged in to submit a complaint.");
  }

  const { title, category, description, location, latitude, longitude } = reportData;

  if (!title || !title.trim()) throw new Error("Please enter a short title for the issue.");
  if (!category) throw new Error("Please select an issue category.");
  if (!description || !description.trim()) throw new Error("Please provide a detailed description.");
  if (!location || !location.trim()) throw new Error("Please specify the location or landmark.");

  const reportId = generateReportId();
  let imageUrl = null;

  if (imageFile) {
    imageUrl = await uploadReportImage(imageFile, user.uid);
  }

  const initialHistory = [
    {
      status: 'Submitted',
      remarks: 'Complaint successfully registered by citizen.',
      updatedAt: new Date().toISOString(),
      updatedBy: user.displayName || 'Citizen'
    }
  ];

  if (isDemoMode) {
    const reports = JSON.parse(localStorage.getItem('cs_demo_reports') || '[]');
    const newReport = {
      id: 'rep_' + Date.now(),
      reportId,
      userId: user.uid,
      userDisplayName: user.displayName || 'Anonymous Citizen',
      userEmail: user.email,
      title: title.trim(),
      category,
      description: description.trim(),
      location: location.trim(),
      latitude: latitude || null,
      longitude: longitude || null,
      imageUrl,
      status: 'Submitted',
      adminRemarks: '',
      statusHistory: initialHistory,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };

    reports.unshift(newReport);
    localStorage.setItem('cs_demo_reports', JSON.stringify(reports));
    return newReport;
  }

  // Live Firestore submission
  const { collection, addDoc, serverTimestamp } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js");
  const docRef = await addDoc(collection(db, "reports"), {
    reportId,
    userId: user.uid,
    userDisplayName: user.displayName || 'Citizen',
    userEmail: user.email,
    title: title.trim(),
    category,
    description: description.trim(),
    location: location.trim(),
    latitude: latitude || null,
    longitude: longitude || null,
    imageUrl: imageUrl || null,
    status: 'Submitted',
    adminRemarks: '',
    statusHistory: [
      {
        status: 'Submitted',
        remarks: 'Complaint registered by citizen.',
        updatedAt: new Date().toISOString(),
        updatedBy: user.displayName || 'Citizen'
      }
    ],
    createdAt: serverTimestamp(),
    updatedAt: serverTimestamp()
  });

  return { id: docRef.id, reportId };
}

/**
 * Fetch reports submitted by the logged-in citizen
 */
export async function getCitizenReports(userId) {
  if (!userId) return [];

  if (isDemoMode) {
    const reports = JSON.parse(localStorage.getItem('cs_demo_reports') || '[]');
    return reports
      .filter(r => r.userId === userId)
      .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
  }

  // Live Firestore
  const { collection, query, where, orderBy, getDocs } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js");
  const q = query(
    collection(db, "reports"),
    where("userId", "==", userId),
    orderBy("createdAt", "desc")
  );

  const snapshot = await getDocs(q);
  const list = [];
  snapshot.forEach(doc => {
    list.push({ id: doc.id, ...doc.data() });
  });
  return list;
}

/**
 * Track a report by its public Report ID (e.g. CS-2026-10482)
 */
export async function trackReportById(reportIdQuery) {
  const cleanId = (reportIdQuery || '').trim().toUpperCase();
  if (!cleanId) {
    throw new Error("Please enter a valid Report ID.");
  }

  if (isDemoMode) {
    const reports = JSON.parse(localStorage.getItem('cs_demo_reports') || '[]');
    const match = reports.find(r => r.reportId.toUpperCase() === cleanId);
    if (!match) {
      throw new Error(`No complaint found with Report ID: ${cleanId}`);
    }
    return match;
  }

  // Live Firestore
  const { collection, query, where, getDocs, limit } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js");
  const q = query(
    collection(db, "reports"),
    where("reportId", "==", cleanId),
    limit(1)
  );

  const snapshot = await getDocs(q);
  if (snapshot.empty) {
    throw new Error(`No complaint found with Report ID: ${cleanId}`);
  }

  const doc = snapshot.docs[0];
  return { id: doc.id, ...doc.data() };
}
