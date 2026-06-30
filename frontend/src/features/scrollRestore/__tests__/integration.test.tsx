import { act, render, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';

import { ScrollRestoreProvider } from '../ScrollRestoreProvider';
import { buildRouteKey } from '../routeKey';
import { ScrollRestoreService } from '../service';

let navigationType = 'PUSH';

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');

  return {
    ...actual,
    useLocation: () => ({
      pathname: '/feed',
      search: '',
      hash: '',
      state: null,
      key: 'scroll-restore-key',
    }),
    useNavigationType: () => navigationType,
  };
});

const setScrollRestoreFlag = (enabled: boolean) => {
  (window as typeof window & { __flags__?: { scrollRestore?: boolean } }).__flags__ = {
    scrollRestore: enabled,
  };
};

const clearScrollRestoreFlag = () => {
  (window as typeof window & { __flags__?: { scrollRestore?: boolean } }).__flags__ = undefined;
};

afterEach(() => {
  vi.restoreAllMocks();
  sessionStorage.clear();
  navigationType = 'PUSH';
  clearScrollRestoreFlag();
});

describe('ScrollRestoreProvider', () => {
  it('restores scroll on POP navigation only', async () => {
    setScrollRestoreFlag(true);
    navigationType = 'POP';

    const routeKey = buildRouteKey({ pathname: '/feed', search: '' });
    sessionStorage.setItem(
      'scrollRestore:v1',
      JSON.stringify({
        [routeKey]: { position: 120, containerId: null, updatedAt: Date.now() },
      }),
    );

    const restoreSpy = vi
      .spyOn(ScrollRestoreService.prototype, 'restore')
      .mockImplementation(() => undefined);

    const { unmount } = render(
      <MemoryRouter initialEntries={['/feed']}>
        <ScrollRestoreProvider>
          <div>Child</div>
        </ScrollRestoreProvider>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(restoreSpy).toHaveBeenCalledTimes(1);
    });

    restoreSpy.mockClear();
    navigationType = 'PUSH';
    unmount();

    render(
      <MemoryRouter initialEntries={['/feed']}>
        <ScrollRestoreProvider>
          <div>Child</div>
        </ScrollRestoreProvider>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(restoreSpy).not.toHaveBeenCalled();
    });
  });

  it('restores scroll after POP navigation asynchronously', async () => {
    setScrollRestoreFlag(true);
    navigationType = 'PUSH';

    const routeKey = buildRouteKey({ pathname: '/feed', search: '' });
    sessionStorage.setItem(
      'scrollRestore:v1',
      JSON.stringify({
        [routeKey]: { position: 220, containerId: null, updatedAt: Date.now() },
      }),
    );

    const restoreSpy = vi
      .spyOn(ScrollRestoreService.prototype, 'restore')
      .mockImplementation(() => undefined);

    const { unmount } = render(
      <MemoryRouter initialEntries={['/feed']}>
        <ScrollRestoreProvider>
          <div>Child</div>
        </ScrollRestoreProvider>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(restoreSpy).not.toHaveBeenCalled();
    });

    navigationType = 'POP';

    await act(async () => {
      window.history.back();
    });

    unmount();

    render(
      <MemoryRouter initialEntries={['/feed']}>
        <ScrollRestoreProvider>
          <div>Child</div>
        </ScrollRestoreProvider>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(restoreSpy).toHaveBeenCalledTimes(1);
    });
  });
});
