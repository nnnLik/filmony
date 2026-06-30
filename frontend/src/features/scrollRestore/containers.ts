type ContainerEntry = { id: string; element: HTMLElement };
const registry = new Map<string, ContainerEntry>();

export function registerScrollContainer(id: string, element: HTMLElement): () => void {
  registry.set(id, { id, element });
  return () => registry.delete(id);
}

export function getScrollContainer(id: string): HTMLElement | null {
  return registry.get(id)?.element ?? null;
}
