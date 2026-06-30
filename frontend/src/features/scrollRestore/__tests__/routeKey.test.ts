import { describe, expect, it } from 'vitest';

import { buildRouteKey } from '../routeKey';

describe('buildRouteKey', () => {
  it('includes pathname and stable query keys', () => {
    const key = buildRouteKey({
      pathname: '/feed',
      search: '?q=films&cursor=abc123',
      allowedQueryKeys: ['q'],
    });

    expect(key).toBe('/feed|query:q=films');
  });

  it('includes route params deterministically', () => {
    const key = buildRouteKey({
      pathname: '/lists/42',
      params: { listId: '42', ownerId: '7' },
    });

    expect(key).toBe('/lists/42|params:listId=42&ownerId=7');
  });

  it('omits empty query values and orders keys', () => {
    const key = buildRouteKey({
      pathname: '/feed',
      search: '?b=2&a=&c=3',
      allowedQueryKeys: ['c', 'a', 'b'],
    });

    expect(key).toBe('/feed|query:b=2&c=3');
  });
});
