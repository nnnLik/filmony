import type { ReactNode } from 'react'

import { StickyBackHeader } from './StickyBackHeader'

type CatalogPageShellProps = {
  headerTitle: string
  children: ReactNode
  mainClassName?: string
}

export function CatalogPageShell({ headerTitle, children, mainClassName }: CatalogPageShellProps) {
  return (
    <div className="min-h-dvh bg-(--tgui--bg_color) pb-8 text-(--tgui--text_color)">
      <StickyBackHeader title={headerTitle} />
      <main className={mainClassName ?? 'mx-auto max-w-md px-4 pt-4'}>{children}</main>
    </div>
  )
}
