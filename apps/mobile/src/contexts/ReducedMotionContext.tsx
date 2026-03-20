import { createContext, useContext } from "react";
import { useReducedMotion } from "../hooks/useReducedMotion";

const ReducedMotionContext = createContext(false);

export function ReducedMotionProvider({ children }: { children: React.ReactNode }) {
  const reduced = useReducedMotion();
  return (
    <ReducedMotionContext.Provider value={reduced}>
      {children}
    </ReducedMotionContext.Provider>
  );
}

export function useReducedMotionContext(): boolean {
  return useContext(ReducedMotionContext);
}
