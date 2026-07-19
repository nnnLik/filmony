import { Button } from '@telegram-apps/telegram-ui'
import { useCallback, useRef, useState, type ChangeEvent } from 'react'

import { ApiError, formatApiDetail } from '../../api/client'
import { uploadUserCardCover } from '../../api/cardApi'
import { CREATE_CARD_TEXT_FIELD_CLASS } from '../../lib/createCardBinding'

type CardCoverBlockProps = {
  coverUrl: string | null
  onCoverUrlChange: (url: string | null) => void
  disabled?: boolean
}

export function CardCoverBlock({ coverUrl, onCoverUrlChange, disabled = false }: CardCoverBlockProps) {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [uploadBusy, setUploadBusy] = useState(false)
  const [linkOpen, setLinkOpen] = useState(false)
  const [linkDraft, setLinkDraft] = useState('')
  const [linkError, setLinkError] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)

  const uploadFile = useCallback(
    async (file: File) => {
      if (!file.type.startsWith('image/')) {
        setActionError('Выберите изображение')
        return
      }
      setUploadBusy(true)
      setActionError(null)
      try {
        const url = await uploadUserCardCover(file)
        onCoverUrlChange(url)
        setLinkOpen(false)
        setLinkDraft('')
        setLinkError(null)
      } catch (err) {
        setActionError(err instanceof ApiError ? formatApiDetail(err.detail) : 'Не удалось загрузить обложку')
      } finally {
        setUploadBusy(false)
      }
    },
    [onCoverUrlChange],
  )

  const onFileChange = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0]
      e.target.value = ''
      if (file == null) return
      void uploadFile(file)
    },
    [uploadFile],
  )

  const applyLink = useCallback(() => {
    const raw = linkDraft.trim()
    if (raw === '') {
      setLinkError('Вставьте ссылку на изображение')
      return
    }
    try {
      const parsed = new URL(raw.includes('://') ? raw : `https://${raw}`)
      if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
        setLinkError('Нужна ссылка http или https')
        return
      }
      onCoverUrlChange(parsed.href)
      setLinkError(null)
      setActionError(null)
    } catch {
      setLinkError('Некорректная ссылка')
    }
  }, [linkDraft, onCoverUrlChange])

  const pasteFromClipboard = useCallback(async () => {
    setActionError(null)
    try {
      if (typeof navigator === 'undefined' || navigator.clipboard?.read == null) {
        setActionError('Вставка из буфера недоступна в этом браузере')
        return
      }
      const items = await navigator.clipboard.read()
      for (const item of items) {
        const imageType = item.types.find((t) => t.startsWith('image/'))
        if (imageType == null) continue
        const blob = await item.getType(imageType)
        const ext = imageType.split('/')[1] ?? 'png'
        const file = new File([blob], `clipboard-cover.${ext}`, { type: imageType })
        await uploadFile(file)
        return
      }
      setActionError('В буфере нет изображения')
    } catch {
      setActionError('Не удалось вставить из буфера — попробуйте «Загрузить»')
    }
  }, [uploadFile])

  const busy = disabled || uploadBusy

  return (
    <div className="flex flex-col gap-3">
      <div className="mx-auto aspect-2/3 w-[8.5rem] overflow-hidden rounded-xl border border-(--tgui--divider_color) bg-(--tgui--secondary_bg_color)">
        {coverUrl ? (
          <img src={coverUrl} alt="Превью обложки" className="h-full w-full object-cover" />
        ) : (
          <div className="flex h-full w-full items-center justify-center px-2 text-center text-xs text-(--tgui--hint_color)">
            Нет обложки
          </div>
        )}
      </div>

      <div className="grid grid-cols-3 gap-2">
        <Button
          mode="gray"
          size="s"
          stretched
          type="button"
          disabled={busy}
          onClick={() => fileInputRef.current?.click()}
        >
          Загрузить
        </Button>
        <Button
          mode="gray"
          size="s"
          stretched
          type="button"
          disabled={busy}
          onClick={() => {
            setLinkOpen((v) => !v)
            setLinkError(null)
            setLinkDraft(coverUrl ?? '')
          }}
        >
          Ссылка
        </Button>
        <Button mode="gray" size="s" stretched type="button" disabled={busy} onClick={() => void pasteFromClipboard()}>
          Буфер
        </Button>
      </div>

      {linkOpen ? (
        <div className="rounded-xl border border-(--tgui--divider_color) bg-(--tgui--bg_color) p-3">
          <label htmlFor="create-card-cover-link" className="text-xs font-medium text-(--tgui--hint_color)">
            URL обложки
          </label>
          <input
            id="create-card-cover-link"
            type="url"
            inputMode="url"
            autoComplete="url"
            placeholder="https://…"
            value={linkDraft}
            onChange={(e) => {
              setLinkDraft(e.currentTarget.value)
              setLinkError(null)
            }}
            className={`mt-2 ${CREATE_CARD_TEXT_FIELD_CLASS}`}
          />
          {linkError != null ? (
            <p className="mt-1.5 text-xs text-(--tgui--destructive_text_color)">{linkError}</p>
          ) : null}
          <div className="mt-2">
            <Button mode="gray" size="s" stretched type="button" disabled={busy} onClick={applyLink}>
              Применить ссылку
            </Button>
          </div>
        </div>
      ) : null}

      {actionError != null ? (
        <p className="text-xs text-(--tgui--destructive_text_color)">{actionError}</p>
      ) : null}

      <input
        ref={fileInputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp,image/gif,.jpg,.jpeg,.png,.webp,.gif"
        className="hidden"
        onChange={onFileChange}
      />
    </div>
  )
}
