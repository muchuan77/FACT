import { createPinia, defineStore } from "pinia";

export const pinia = createPinia();

export const useAppStore = defineStore("app", {
  state: () => ({
    backendBaseUrl: "",
  }),
});

