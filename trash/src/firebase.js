function hasFirebaseConfig(config) {
  const firebaseConfig = config.firebase?.config || {};
  return (
    config.firebase?.enabled &&
    firebaseConfig.apiKey &&
    firebaseConfig.projectId &&
    firebaseConfig.appId
  );
}

async function loadFirebaseModules() {
  const [{ initializeApp }, { getFirestore, doc, getDoc, setDoc }] = await Promise.all([
    import("https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js"),
    import("https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js"),
  ]);

  return { initializeApp, getFirestore, doc, getDoc, setDoc };
}

export async function createFirebaseAdapter(config, localAdapter) {
  if (!hasFirebaseConfig(config)) {
    return {
      ...localAdapter,
      mode: "local",
      warning: "Firebase config missing, running on local browser storage.",
    };
  }

  try {
    const { initializeApp, getFirestore, doc, getDoc, setDoc } = await loadFirebaseModules();
    const app = initializeApp(config.firebase.config);
    const db = getFirestore(app);
    const ref = doc(
      db,
      config.firebase.firestore.collection,
      config.firebase.firestore.documentId,
    );

    return {
      mode: "firebase",
      warning: "",
      async load(seedState) {
        const snapshot = await getDoc(ref);
        if (!snapshot.exists()) {
          await setDoc(ref, seedState);
          return seedState;
        }

        return snapshot.data();
      },
      async save(state) {
        await setDoc(ref, state);
      },
    };
  } catch (error) {
    console.warn("Firebase adapter failed, falling back to local storage.", error);
    return {
      ...localAdapter,
      mode: "local",
      warning: "Firebase adapter failed, fallback persisted in local browser storage.",
    };
  }
}
