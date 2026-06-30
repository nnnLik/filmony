import { describe, expect, it, vi } from 'vitest';

import { ScrollRestoreService } from '../service';

describe('ScrollRestoreService', () => {
  it('clamps to max scroll height', async () => {
    const container = document.createElement('div');
    Object.defineProperty(container, 'scrollHeight', { value: 400, configurable: true });
    Object.defineProperty(container, 'clientHeight', { value: 200, configurable: true });
    container.scrollTop = 0;

    const service = new ScrollRestoreService();
    await service.restore({
      container,
      position: 350,
    });

    expect(container.scrollTop).toBe(200);
  });

  it('retries until content is ready', async () => {
    const container = document.createElement('div');
    Object.defineProperty(container, 'scrollHeight', { value: 0, configurable: true });
    Object.defineProperty(container, 'clientHeight', { value: 0, configurable: true });
    const service = new ScrollRestoreService({ maxFrames: 3 });

    const raf = vi.spyOn(window, 'requestAnimationFrame').mockImplementation((cb) => {
      Object.defineProperty(container, 'scrollHeight', { value: 100, configurable: true });
      Object.defineProperty(container, 'clientHeight', { value: 50, configurable: true });
      cb(0);
      return 0;
    });

    await service.restore({ container, position: 40 });
    expect(container.scrollTop).toBe(40);
    raf.mockRestore();
  });
});
