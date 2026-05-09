const STORAGE_KEY = "trybe-lattice-ticket-control";

export function createLocalAdapter() {
  return {
    mode: "local",
    warning: "",
    async load(seedState) {
      const saved = window.localStorage.getItem(STORAGE_KEY);
      if (!saved) {
        window.localStorage.setItem(STORAGE_KEY, JSON.stringify(seedState));
        return seedState;
      }

      try {
        return JSON.parse(saved);
      } catch (error) {
        console.warn("Saved state invalid, resetting with seed data.", error);
        window.localStorage.setItem(STORAGE_KEY, JSON.stringify(seedState));
        return seedState;
      }
    },
    async save(state) {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    },
  };
}
