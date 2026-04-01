'use client';

import { useMemo } from 'react';
import { css } from '@emotion/css';
import theme, { Theme } from './theme';

interface StyleObject {
  [key: string]: any;
}

interface Props {
  name?: string;
  params?: any;
}

function mergeMediaQuery(obj: StyleObject): StyleObject {
  for (const [key, value] of Object.entries(obj)) {
    if (key.startsWith('@media') && typeof value === 'object') {
      for (const [innerKey, innerValue] of Object.entries(value)) {
        obj[innerKey] = {
          ...obj[innerKey],
          [key]: { ...(innerValue as any) },
        };
      }
      delete obj[key];
    }
  }
  return obj;
}

const useClasses = (
  stylesElement: ((theme: Theme, params?: any) => StyleObject) | StyleObject,
  props?: Props
) => {
  // theme is imported directly as a static constant

  return useMemo(() => {
    const rawClasses =
      typeof stylesElement === 'function'
        ? stylesElement(theme, props?.params)
        : stylesElement;
    const prepared: StyleObject = {};
    const rawClassesMerged = mergeMediaQuery(rawClasses);

    Object.entries(rawClassesMerged).forEach(([key, value = {}]) => {
      prepared[key] = css(
        process.env.NODE_ENV !== 'production'
          ? { ...value, label: key }
          : value
      );
    });

    return prepared;
  }, [props?.name, props?.params, stylesElement, theme]);
};

export default useClasses;
