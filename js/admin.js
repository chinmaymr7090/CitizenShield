// CitizenShield - Administrator Dashboard & Operations
import { db, isDemoMode } from './firebase-config.js';
import { getCurrentUser, isAdminUser } from './auth.js';

/**
 * Fetch all civic complaints across the municipality (Admin restricted)
 */
export async function getAllReports() {
  if (!isAdminUser()) {
    throw new Error("Access restricted: Administrator credentials required.");
  }

  if (isDemoMode) {
    const reports = JSON.parse(localStorage.getItem('cs_demo_reports') || '[]');
    return reports.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
  }

  // Live Firestore
  const { collection, getDocs, orderBy, query } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js");
  const q = query(collection(db, "reports"), orderBy("createdAt", "desc"));
  const snapshot = await getDocs(q);
  
  const list = [];
  snapshot.forEach(doc => {
    list.push({ id: doc.id, ...doc.data() });
  });
  return list;
}

/**
 * Calculate aggregate portal statistics
 */
export function computeMetrics(reports) {
  const metrics = {
    total: reports.length,
    submitted: 0,
    underReview: 0,
    inProgress: 0,
    resolved: 0,
    rejected: 0,
    byCategory: {}
  };

  reports.forEach(r => {
    // Status counts
    switch (r.status) {
      case 'Submitted': metrics.submitted++; break;
      case 'Under Review': metrics.underReview++; break;
      case 'In Progress': metrics.inProgress++; break;
      case 'Resolved': metrics.resolved++; break;
      case 'Rejected': metrics.rejected++; break;
    }

    // Category counts
    const cat = r.category || 'Other';
    metrics.byCategory[cat] = (metrics.byCategory[cat] || 0) + 1;
  });

  return metrics;
}

/**
 * Update report status and append an official administrative remark
 */
export async function updateReportStatus(reportId, newStatus, remarks) {
  const admin = getCurrentUser();
  if (!isAdminUser() || !admin) {
    throw new Error("Access denied: You must be signed in as an administrator to perform this action.");
  }

  if (!newStatus) {
    throw new Error("Please select a valid new status.");
  }

  const validStatuses = ['Submitted', 'Under Review', 'In Progress', 'Resolved', 'Rejected'];
  if (!validStatuses.includes(newStatus)) {
    throw new Error("Invalid status selection.");
  }

  const historyEntry = {
    status: newStatus,
    remarks: (remarks || '').trim() || `Status updated to ${newStatus}.`,
    updatedAt: new Date().toISOString(),
    updatedBy: admin.displayName || 'Municipal Admin Officer'
  };

  if (isDemoMode) {
    const reports = JSON.parse(localStorage.getItem('cs_demo_reports') || '[]');
    const target = reports.find(r => r.id === reportId || r.reportId === reportId);
    if (!target) {
      throw new Error("Report not found.");
    }

    target.status = newStatus;
    if (remarks && remarks.trim()) {
      target.adminRemarks = remarks.trim();
    }
    target.statusHistory = target.statusHistory || [];
    target.statusHistory.push(historyEntry);
    target.updatedAt = new Date().toISOString();

    localStorage.setItem('cs_demo_reports', JSON.stringify(reports));
    return target;
  }

  // Live Firestore
  const { doc, updateDoc, arrayUnion, serverTimestamp } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js");
  const reportRef = doc(db, "reports", reportId);

  const updateData = {
    status: newStatus,
    statusHistory: arrayUnion(historyEntry),
    updatedAt: serverTimestamp()
  };

  if (remarks && remarks.trim()) {
    updateData.adminRemarks = remarks.trim();
  }

  await updateDoc(reportRef, updateData);
  return { id: reportId, status: newStatus };
}
