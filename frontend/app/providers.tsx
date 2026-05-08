'use client';

import { ReactNode, useEffect } from 'react';
import { Provider } from 'react-redux';
import store from '@/store';
import { installFetchInterceptor } from '@/utils/apiFetch';

// Run on module load so the interceptor is in place before any component
// fires its first fetch (route prefetch, RSC hydration, etc.).
if (typeof window !== 'undefined') {
  installFetchInterceptor();
}

export function Providers({ children }: { children: ReactNode }) {
  // Re-assert after hydration in case the script-load timing missed it.
  useEffect(() => {
    installFetchInterceptor();
  }, []);
  return <Provider store={store}>{children}</Provider>;
}
