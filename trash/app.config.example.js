window.__APP_CONFIG__ = {
  appName: "Trybe + Lattice Ticket Control",
  storageMode: "firebase",
  firebase: {
    enabled: false,
    config: {
      apiKey: "your-api-key",
      authDomain: "your-project.firebaseapp.com",
      projectId: "your-project-id",
      storageBucket: "your-project.appspot.com",
      messagingSenderId: "your-messaging-sender-id",
      appId: "your-app-id",
    },
    firestore: {
      collection: "ticket_system",
      documentId: "primary_state",
    },
  },
};
