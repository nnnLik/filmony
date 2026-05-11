/** Читает тело ошибки FastAPI/Starlette из ответа (JSON `detail` или текст). */
export async function readHttpErrorDetail(res: Response): Promise<unknown> {
  const ct = res.headers.get('content-type') ?? ''
  if (ct.includes('application/json')) {
    try {
      const body = (await res.json()) as { detail?: unknown }
      return body.detail ?? body
    } catch {
      return null
    }
  }
  return await res.text()
}
