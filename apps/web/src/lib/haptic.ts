/**
 * Haptic feedback utility.
 * Uses navigator.vibrate() on Android and falls back to a no-op on iOS/desktop.
 */

type HapticIntensity = "light" | "medium" | "heavy";

const PATTERNS: Record<HapticIntensity, number | number[]> = {
  light: 10,
  medium: 25,
  heavy: [30, 10, 30],
};

export function haptic(intensity: HapticIntensity = "light"): void {
  if (typeof navigator === "undefined") return;
  if (!("vibrate" in navigator)) return;

  try {
    navigator.vibrate(PATTERNS[intensity]);
  } catch {
    // Silently fail — vibration not supported or permission denied
  }
}

/**
 * Wrap a click/tap handler with haptic feedback.
 */
export function withHaptic<T extends (...args: unknown[]) => unknown>(
  fn: T,
  intensity: HapticIntensity = "light"
): T {
  return ((...args: unknown[]) => {
    haptic(intensity);
    return fn(...args);
  }) as T;
}
