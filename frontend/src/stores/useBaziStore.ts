/**
 * Zustand store for Bazi calculation state.
 * Persists the latest reading and input to localStorage.
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { BaziInput, BaziReading } from "@/types/bazi";
import { calculateBazi } from "@/lib/api";

interface BaziState {
  /** The current input form data. */
  input: BaziInput;
  /** The latest calculated Bazi reading. */
  reading: BaziReading | null;
  /** Whether a calculation request is in flight. */
  isLoading: boolean;
  /** Error message from the last failed request. */
  error: string | null;
  /** History of past readings (for comparison). */
  history: BaziReading[];
}

interface BaziActions {
  /** Update the input form fields. */
  setInput: (input: Partial<BaziInput>) => void;
  /** Set the calculated reading. */
  setReading: (reading: BaziReading | null) => void;
  /** Set loading state. */
  setLoading: (loading: boolean) => void;
  /** Set error message. */
  setError: (error: string | null) => void;
  /** Add a reading to history. */
  addToHistory: (reading: BaziReading) => void;
  /**
   * Calculate Bazi from current input.
   * Returns the reading on success, null on failure.
   * Caller is responsible for navigation after success.
   */
  calculate: () => Promise<BaziReading | null>;
  /** Clear all state. */
  reset: () => void;
}

const DEFAULT_INPUT: BaziInput = {
  birth_date: "",
  birth_time: "",
  gender: "male",
  time_known: true,
  calendar_type: "solar",
};

export const useBaziStore = create<BaziState & BaziActions>()(
  persist(
    (set, get) => ({
      // State
      input: DEFAULT_INPUT,
      reading: null,
      isLoading: false,
      error: null,
      history: [],

      // Actions
      setInput: (partial) =>
        set((state) => ({
          input: { ...state.input, ...partial },
        })),

      setReading: (reading) => set({ reading, error: null }),

      setLoading: (isLoading) => set({ isLoading }),

      setError: (error) => set({ error, isLoading: false }),

      addToHistory: (reading) =>
        set((state) => ({
          history: [reading, ...state.history].slice(0, 20),
        })),

      calculate: async () => {
        const { input } = get();
        if (!input.birth_date || !input.birth_time) {
          set({ error: "请填写完整的出生日期和时间。" });
          return null;
        }
        set({ isLoading: true, error: null });
        try {
          const reading = await calculateBazi(input);
          set((state) => ({
            reading,
            isLoading: false,
            error: null,
            history: [reading, ...state.history].slice(0, 20),
          }));
          return reading;
        } catch (err: unknown) {
          const message =
            err instanceof Error ? err.message : "计算失败，请重试。";
          set({ error: message, isLoading: false });
          return null;
        }
      },

      reset: () =>
        set({
          input: DEFAULT_INPUT,
          reading: null,
          isLoading: false,
          error: null,
        }),
    }),
    {
      name: "bazi-storage",
      partialize: (state) => ({
        input: state.input,
        reading: state.reading,
        history: state.history,
      }),
    }
  )
);
