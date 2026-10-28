// CitizenShield - Authentication Service (Firebase & Demo Fallback)
import { auth, db, isDemoMode } from './firebase-config.js';

let currentUser = null;
let userRole = 'citizen'; // 'citizen' | 'admin'
const authListeners = [];

// Seed default demo users in localStorage if needed
function initDemoAuth() {
  if (!localStorage.getItem('cs_demo_users')) {
    const defaultUsers = [
      {
        uid: 'user_citizen_01',
        displayName: 'Rahul Sharma',
        email: 'citizen@test.com',
        password: 'password123',
        role: 'citizen',
        createdAt: new Date().toISOString()
      },
      {
        uid: 'user_admin_01',
        displayName: 'Municipal Admin Officer',
        email: 'admin@citizenshield.gov',
        password: 'admin123',
        role: 'admin',
        createdAt: new Date().toISOString()
      }
    ];
    localStorage.setItem('cs_demo_users', JSON.stringify(defaultUsers));
  }

  // Restore session if demo user was logged in
  const savedSession = localStorage.getItem('cs_demo_session');
  if (savedSession) {
    try {
      const user = JSON.parse(savedSession);
      currentUser = user;
      userRole = user.role || 'citizen';
    } catch (e) {
      localStorage.removeItem('cs_demo_session');
    }
  }
}

if (isDemoMode) {
  initDemoAuth();
}

/**
 * Register a new citizen
 */
export async function registerUser(displayName, email, password) {
  if (!displayName || !email || !password) {
    throw new Error("All fields are required for registration.");
  }
  if (password.length < 6) {
    throw new Error("Password must be at least 6 characters.");
  }

  if (isDemoMode) {
    const users = JSON.parse(localStorage.getItem('cs_demo_users') || '[]');
    if (users.some(u => u.email.toLowerCase() === email.toLowerCase())) {
      throw new Error("An account with this email already exists.");
    }

    const newUser = {
      uid: 'user_' + Date.now(),
      displayName: displayName.trim(),
      email: email.trim().toLowerCase(),
      password,
      role: email.toLowerCase().includes('admin') ? 'admin' : 'citizen',
      createdAt: new Date().toISOString()
    };
    users.push(newUser);
    localStorage.setItem('cs_demo_users', JSON.stringify(users));

    // Log the user in
    currentUser = {
      uid: newUser.uid,
      displayName: newUser.displayName,
      email: newUser.email,
      role: newUser.role
    };
    userRole = newUser.role;
    localStorage.setItem('cs_demo_session', JSON.stringify(currentUser));
    notifyAuthListeners();
    return currentUser;
  }

  // Live Firebase Authentication
  const { createUserWithEmailAndPassword, updateProfile } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js");
  const { doc, setDoc, serverTimestamp } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js");

  const credential = await createUserWithEmailAndPassword(auth, email, password);
  await updateProfile(credential.user, { displayName: displayName.trim() });

  const role = email.toLowerCase().endsWith('@admin.citizenshield.gov') ? 'admin' : 'citizen';

  // Save profile to Firestore users collection
  await setDoc(doc(db, "users", credential.user.uid), {
    uid: credential.user.uid,
    displayName: displayName.trim(),
    email: email.trim().toLowerCase(),
    role: role,
    createdAt: serverTimestamp()
  });

  return credential.user;
}

/**
 * Log in with email & password
 */
export async function loginUser(email, password) {
  if (!email || !password) {
    throw new Error("Please enter both email and password.");
  }

  if (isDemoMode) {
    const users = JSON.parse(localStorage.getItem('cs_demo_users') || '[]');
    const user = users.find(u => u.email.toLowerCase() === email.trim().toLowerCase() && u.password === password);
    if (!user) {
      throw new Error("Invalid email or password. Please try again.");
    }

    currentUser = {
      uid: user.uid,
      displayName: user.displayName,
      email: user.email,
      role: user.role
    };
    userRole = user.role;
    localStorage.setItem('cs_demo_session', JSON.stringify(currentUser));
    notifyAuthListeners();
    return currentUser;
  }

  // Live Firebase
  const { signInWithEmailAndPassword } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js");
  const credential = await signInWithEmailAndPassword(auth, email, password);
  return credential.user;
}

/**
 * Log out current user
 */
export async function logoutUser() {
  if (isDemoMode) {
    currentUser = null;
    userRole = 'citizen';
    localStorage.removeItem('cs_demo_session');
    notifyAuthListeners();
    return;
  }

  const { signOut } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js");
  await signOut(auth);
}

/**
 * Subscribe to authentication state changes
 */
export function subscribeAuthChanges(callback) {
  authListeners.push(callback);

  if (isDemoMode) {
    callback(currentUser, userRole);
    return () => {
      const idx = authListeners.indexOf(callback);
      if (idx > -1) authListeners.splice(idx, 1);
    };
  }

  import("https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js").then(({ onAuthStateChanged }) => {
    import("https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js").then(({ doc, getDoc }) => {
      onAuthStateChanged(auth, async (user) => {
        if (user) {
          currentUser = user;
          try {
            const userDoc = await getDoc(doc(db, "users", user.uid));
            if (userDoc.exists() && userDoc.data().role === 'admin') {
              userRole = 'admin';
            } else if (user.email && user.email.toLowerCase().endsWith('@admin.citizenshield.gov')) {
              userRole = 'admin';
            } else {
              userRole = 'citizen';
            }
          } catch (e) {
            userRole = (user.email && user.email.toLowerCase().endsWith('@admin.citizenshield.gov')) ? 'admin' : 'citizen';
          }
        } else {
          currentUser = null;
          userRole = 'citizen';
        }
        notifyAuthListeners();
      });
    });
  });

  return () => {
    const idx = authListeners.indexOf(callback);
    if (idx > -1) authListeners.splice(idx, 1);
  };
}

function notifyAuthListeners() {
  authListeners.forEach(listener => listener(currentUser, userRole));
}

export function getCurrentUser() {
  return currentUser;
}

export function getUserRole() {
  return userRole;
}

export function isAdminUser() {
  return userRole === 'admin';
}
