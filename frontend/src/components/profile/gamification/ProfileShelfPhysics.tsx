import type { ReactNode } from 'react'

import type { ShelfPhysicsMode } from '../../../api/gamificationTypes'

import './profileShelfPhysics.css'

type ProfileShelfPhysicsProps = {
  mode: ShelfPhysicsMode
  children: ReactNode
}

export function ProfileShelfPhysics({ mode, children }: ProfileShelfPhysicsProps) {
  return (
    <div className={`profile-shelf-physics profile-shelf-physics--${mode}`}>
      <div className="profile-shelf-physics__rail" aria-hidden />
      <div className="profile-shelf-physics__grid">{children}</div>
    </div>
  )
}
