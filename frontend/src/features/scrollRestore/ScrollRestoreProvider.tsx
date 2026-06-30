import { type PropsWithChildren, useEffect } from 'react';
import { NavigationType, useLocation, useNavigationType } from 'react-router-dom';

import { getScrollContainer } from './containers';
import { isScrollRestoreEnabled, scrollRestoreConfig } from './flags';
import { buildRouteKey } from './routeKey';
import { ScrollRestoreService } from './service';
import { ScrollRestoreStorage } from './storage';

export const ScrollRestoreProvider = ({ children }: PropsWithChildren) => {
  const location = useLocation();
  const navigationType = useNavigationType();

  useEffect(() => {
    if (!isScrollRestoreEnabled()) {
      return;
    }

    if (navigationType !== NavigationType.Pop) {
      return;
    }

    const storage = ScrollRestoreStorage.hydrate({
      ttlMs: scrollRestoreConfig.ttlMs,
      maxEntries: scrollRestoreConfig.maxEntries,
      storageKey: 'scrollRestore:v1',
    });
    const key = buildRouteKey({
      pathname: location.pathname,
      search: location.search,
    });
    const entry = storage.get(key);
    if (!entry) {
      return;
    }

    const service = new ScrollRestoreService();
    const container = entry.containerId ? getScrollContainer(entry.containerId) : null;
    void service.restore({ container, position: entry.position });
  }, [location.pathname, location.search, navigationType]);

  return <>{children}</>;
};
