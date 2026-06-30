import { render, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

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

afterEach(() => {
  vi.restoreAllMocks();
  sessionStorage.clear();
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

    render(
      <ScrollRestoreProvider>
        <div>Child</div>
      </ScrollRestoreProvider>,
    );

    await waitFor(() => {
      expect(restoreSpy).toHaveBeenCalledTimes(1);
    });

    restoreSpy.mockClear();
    navigationType = 'PUSH';

    render(
      <ScrollRestoreProvider>
        <div>Child</div>
      </ScrollRestoreProvider>,
    );

    await waitFor(() => {
      expect(restoreSpy).not.toHaveBeenCalled();
    });
  });
});
