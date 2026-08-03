import { describe, expect, it } from 'vitest'

import { directorChipStyles, getDirectorColor } from '../directorColor'

describe('directorColor', () => {
  it('returns stable color for the same director id', () => {
    expect(getDirectorColor(66539)).toBe(getDirectorColor(66539))
  })

  it('returns different colors for different ids in most cases', () => {
    const a = getDirectorColor(66539)
    const b = getDirectorColor(525)
    expect(a).not.toBe(b)
  })

  it('builds chip style classes from color', () => {
    const styles = directorChipStyles(42)
    expect(styles.color).toMatch(/^#/)
    expect(styles.borderClass).toContain('border-[color-mix')
    expect(styles.backgroundClass).toContain('bg-[color-mix')
  })
})
