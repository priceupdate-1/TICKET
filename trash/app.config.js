// KG Ticket Control — Runtime Configuration
// This file enables Firebase Firestore as the persistence backend.
// It is loaded at runtime via a <script> tag in index.html.
window.__APP_CONFIG__ = {
  appName: "KG Ticket Control",
  storageMode: "firebase",
  firebase: {
    enabled: true,
    config: {
      apiKey: "AIzaSyDtxIe7TOqoc-Ug9TegPtVc7GdNs0ki2QA",
      authDomain: "kg-ticket.firebaseapp.com",
      projectId: "kg-ticket",
      storageBucket: "kg-ticket.firebasestorage.app",
      messagingSenderId: "493482877327",
      appId: "1:493482877327:web:b751ad48bd405347f42bfa",
    },
    firestore: {
      collection: "ticket_system",
      documentId: "primary_state",
    },
  },
};
