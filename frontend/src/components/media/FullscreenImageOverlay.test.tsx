import { AppRoot } from '@telegram-apps/telegram-ui'
import { cleanup, render, screen } from '@testing-library/react'
import { describe, expect, it, afterEach } from 'vitest'

import { FullscreenImageOverlay } from './FullscreenImageOverlay'

describe('FullscreenImageOverlay', () => {
  afterEach(() => {
    cleanup()
    document.body.style.overflow = ''
  })

  it('uses touch-manipulation on the backdrop image area so pinch-zoom is permitted', () => {
    render(
      <AppRoot appearance="dark">
        <FullscreenImageOverlay
          open={true}
          src="https://example.com/poster.webp"
          alt="poster"
          onClose={() => undefined}
        />
      </AppRoot>,
    )

    const backdropActivate = screen.getByRole('button', { name: /закрыть просмотр \(нажатие по фону\)/iu })
    expect(backdropActivate.className).toMatch(/touch-manipulation/)
    expect(backdropActivate.className).not.toMatch(/touch-pan-y/)
  })
})
