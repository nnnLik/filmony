/** Maps streak length to visual heat in [0, 1]; caps at 10 days. */
export function streakHeat(current: number): number {
  if (current <= 3) return 0
  return Math.min(1, Math.max(0, (current - 3) / 7))
}

/** CSS custom properties for flame color / glow intensity from heat. */
export function streakFlameStyleVars(heat: number): Record<string, string> {
  const h = Math.min(1, Math.max(0, heat))
  return {
    '--streak-flame-top': `color-mix(in srgb, #fff4d6 ${Math.round(18 + h * 72)}%, #ffb347)`,
    '--streak-flame-mid': `color-mix(in srgb, #ff8c00 ${Math.round(42 + h * 58)}%, #ff5500)`,
    '--streak-flame-base': `color-mix(in srgb, #e63600 ${Math.round(35 + h * 65)}%, #9a1f00)`,
    '--streak-glow-alpha': String(0.28 + h * 0.52),
    '--streak-glow-spread': `${(1.5 + h * 7).toFixed(2)}px`,
    '--streak-glow-blur': `${(2 + h * 10).toFixed(2)}px`,
    '--streak-flicker-speed': `${(1.35 - h * 0.45).toFixed(2)}s`,
  }
}
