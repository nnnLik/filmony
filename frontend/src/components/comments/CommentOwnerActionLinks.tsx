type CommentOwnerActionLinksProps = {
  onEdit: () => void
  onDelete: () => void
  deleteBusy?: boolean
  disabled?: boolean
}

export function CommentOwnerActionLinks({
  onEdit,
  onDelete,
  deleteBusy = false,
  disabled = false,
}: CommentOwnerActionLinksProps) {
  return (
    <>
      <button
        type="button"
        onClick={onEdit}
        disabled={disabled || deleteBusy}
        className="inline-flex bg-transparent px-0 py-0 text-xs leading-none text-(--tgui--link_color) disabled:opacity-50"
      >
        Изменить
      </button>
      <button
        type="button"
        onClick={onDelete}
        disabled={disabled || deleteBusy}
        className="inline-flex bg-transparent px-0 py-0 text-xs leading-none text-(--tgui--destructive_text_color) disabled:opacity-50"
      >
        {deleteBusy ? 'Удаление…' : 'Удалить'}
      </button>
    </>
  )
}
