import { act, render, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { NavigationType, type Location } from 'react-router-dom';
import type * as ReactRouterDom from 'react-router-dom';

import { ScrollRestoreProvider } from '../ScrollRestoreProvider';
import { buildRouteKey } from '../routeKey';
import { ScrollRestoreService } from '../service';

type ReactRouterDomModule = typeof ReactRouterDom;

let navigationType: NavigationType = NavigationType.Push;

vi.mock('react-router-dom', async (): Promise<ReactRouterDomModule> => {
  const actual = await Promise.resolve(
    vi.importActual<ReactRouterDomModule>('react-router-dom'),
  );
  const location: Location = {
    pathname: '/feed',
    search: '',
    hash: '',
    state: null,
    key: 'scroll-restore-key',
  };

  const mockedModule: ReactRouterDomModule = {
    ...actual,
    useLocation: () => location,
    useNavigationType: () => navigationType,
  };

  return mockedModule;
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
  navigationType = NavigationType.Push;
  clearScrollRestoreFlag();
});

describe('ScrollRestoreProvider', () => {
  it('restores scroll on POP navigation only', async () => {
    setScrollRestoreFlag(true);
    navigationType = NavigationType.Pop;

    const routeKey = buildRouteKey({ pathname: '/feed', search: '' });
    sessionStorage.setItem(
      'scrollRestore:v1',
      JSON.stringify({
        [routeKey]: { position: 120, containerId: null, updatedAt: Date.now() },
      }),
    );

    const restoreSpy = vi
      .spyOn(ScrollRestoreService.prototype, 'restore')
      .mockImplementation(() => Promise.resolve(undefined));

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
    navigationType = NavigationType.Push;
    unmount();

    render(
      <MemoryRouter initialEntries={['/feed']}>
        <ScrollRestoreProvider>
          <div>Child</div>
        </ScrollRestoreProvider>
      </MemoryRouter>,
    );

    await new Promise((resolve) => {
      setTimeout(resolve, 0);
    });

    await waitFor(() => {
      expect(restoreSpy).not.toHaveBeenCalled();
    });
  });

  it('restores scroll after POP navigation asynchronously', async () => {
    setScrollRestoreFlag(true);
    navigationType = NavigationType.Push;

    const routeKey = buildRouteKey({ pathname: '/feed', search: '' });
    sessionStorage.setItem(
      'scrollRestore:v1',
      JSON.stringify({
        [routeKey]: { position: 220, containerId: null, updatedAt: Date.now() },
      }),
    );

    const restoreSpy = vi
      .spyOn(ScrollRestoreService.prototype, 'restore')
      .mockImplementation(() => Promise.resolve(undefined));

    const { unmount } = render(
      <MemoryRouter initialEntries={['/feed']}>
        <ScrollRestoreProvider>
          <div>Child</div>
        </ScrollRestoreProvider>
      </MemoryRouter>,
    );

    await new Promise((resolve) => {
      setTimeout(resolve, 0);
    });

    await waitFor(() => {
      expect(restoreSpy).not.toHaveBeenCalled();
    });

    navigationType = NavigationType.Pop;

    await act(async () => {
      window.history.back();
      await Promise.resolve();
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
