import { scrollRestoreConfig } from './flags';

type Outcome = 'restored' | 'missing' | 'failed';

export function logScrollRestoreMetric({
  key,
  outcome,
}: {
  key: string;
  outcome: Outcome;
}): void {
  if (Math.random() > scrollRestoreConfig.sampleRate) {
    return;
  }
  console.info('[scroll-restore]', outcome, key);
}
