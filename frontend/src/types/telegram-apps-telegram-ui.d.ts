declare module '@telegram-apps/telegram-ui' {
  import type { ButtonHTMLAttributes, ChangeEvent, FC, ReactNode } from 'react'

  export interface AppRootProps {
    children?: ReactNode
    appearance?: 'light' | 'dark'
  }
  export const AppRoot: FC<AppRootProps>

  export interface AvatarProps {
    src?: string
    acronym?: string
    size?: number
  }
  export const Avatar: FC<AvatarProps>

  export interface TitleProps {
    level?: '1' | '2' | '3'
    weight?: '1' | '2' | '3'
    className?: string
    children?: ReactNode
  }
  export const Title: FC<TitleProps>

  export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
    stretched?: boolean
    size?: 's' | 'm' | 'l'
    mode?: 'filled' | 'bezeled' | 'plain' | 'gray' | 'outline' | 'white'
  }
  export const Button: FC<ButtonProps>

  export interface InputProps {
    header?: ReactNode
    placeholder?: string
    value?: string
    onChange?: (event: ChangeEvent<HTMLInputElement>) => void
  }
  export const Input: FC<InputProps>

  export interface SectionProps {
    header?: ReactNode
    className?: string
    children?: ReactNode
  }
  export const Section: FC<SectionProps>

  export interface ListProps {
    children?: ReactNode
  }
  export const List: FC<ListProps>

  export interface CellProps {
    subtitle?: ReactNode
    children?: ReactNode
  }
  export const Cell: FC<CellProps>
}
