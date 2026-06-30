type RestoreTarget = {
  container: HTMLElement | null;
  position: number;
};

type ServiceOptions = {
  maxFrames?: number;
};

export class ScrollRestoreService {
  private readonly maxFrames: number;

  constructor({ maxFrames = 5 }: ServiceOptions = {}) {
    this.maxFrames = maxFrames;
  }

  async restore({ container, position }: RestoreTarget): Promise<void> {
    const target = container ?? document.documentElement;
    await this.waitForReady(target, position);
    const maxScroll = Math.max(target.scrollHeight - target.clientHeight, 0);
    target.scrollTop = Math.min(position, maxScroll);
  }

  private waitForReady(target: HTMLElement, position: number): Promise<void> {
    let frame = 0;
    return new Promise((resolve) => {
      const tick = () => {
        frame += 1;
        const maxScroll = Math.max(target.scrollHeight - target.clientHeight, 0);
        if (maxScroll >= position || frame >= this.maxFrames) {
          resolve();
          return;
        }
        requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    });
  }
}
