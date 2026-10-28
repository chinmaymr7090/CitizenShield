// CitizenShield - Firebase Configuration & Initialization
// Replace the placeholder values below with your credentials from the Firebase Console:
// Firebase Console -> Project Settings -> General -> Your apps -> Web app -> SDK setup and configuration

export const firebaseConfig = {
  apiKey: "YOUR_API_KEY_HERE",
  authDomain: "citizenshield-demo.firebaseapp.com",
  projectId: "citizenshield-demo",
  storageBucket: "citizenshield-demo.appspot.com",
  messagingSenderId: "123456789012",
  appId: "1:123456789012:web:abcdef1234567890"
};

// Check if actual configuration has been supplied
export const isConfigured = 
  firebaseConfig.apiKey && 
  firebaseConfig.apiKey !== "YOUR_API_KEY_HERE" &&
  !firebaseConfig.apiKey.includes("YOUR_");

let app = null;
let auth = null;
let db = null;
let storage = null;
let isDemoMode = !isConfigured;

if (isConfigured) {
  try {
    const { initializeApp } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js");
    const { getAuth } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js");
    const { getFirestore } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js");
    const { getStorage } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-storage.js");

    app = initializeApp(firebaseConfig);
    auth = getAuth(app);
    db = getFirestore(app);
    storage = getStorage(app);
    isDemoMode = false;
    console.info("CitizenShield: Connected to live Firebase backend.");
  } catch (err) {
    console.warn("CitizenShield: Failed to connect to Firebase. Falling back to Demo/Local mode.", err);
    isDemoMode = true;
  }
} else {
  console.info("CitizenShield: Running in Local Demo Mode. Update js/firebase-config.js with your Firebase Console credentials to use Cloud Firestore.");
}

export { app, auth, db, storage, isDemoMode };
