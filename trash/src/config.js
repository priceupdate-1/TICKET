const DEFAULT_CONFIG = {
  appName: "Trybe + Lattice Ticket Control",
  storageMode: "local",
  firebase: {
    enabled: false,
    config: {
      apiKey: "",
      authDomain: "",
      projectId: "",
      storageBucket: "",
      messagingSenderId: "",
      appId: "",
    },
    firestore: {
      collection: "ticket_system",
      documentId: "primary_state",
    },
  },
};

function mergeConfig(base, patch) {
  const merged = { ...base, ...patch };

  if (base.firebase || patch.firebase) {
    merged.firebase = {
      ...base.firebase,
      ...(patch.firebase || {}),
      config: {
        ...(base.firebase?.config || {}),
        ...(patch.firebase?.config || {}),
      },
      firestore: {
        ...(base.firebase?.firestore || {}),
        ...(patch.firebase?.firestore || {}),
      },
    };
  }

  return merged;
}

export async function loadOptionalRuntimeConfig() {
  await new Promise((resolve) => {
    const script = document.createElement("script");
    script.src = "./app.config.js";
    script.async = true;
    script.onload = () => resolve();
    script.onerror = () => resolve();
    document.head.append(script);
  });
}

export function getAppConfig() {
  return mergeConfig(DEFAULT_CONFIG, window.__APP_CONFIG__ || {});
}
