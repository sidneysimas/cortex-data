// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import { en, zh, pt } from './locales';

// NOTE: locale JSON is ingested into the i18next store once, here, at init().
// Adding keys to a locale file requires a full page reload (not just HMR) for
// the running app to pick them up, since HMR won't re-run this init().
const resources = {
  en: { translation: en },
  zh: { translation: zh },
  pt: { translation: pt },
};

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'en',
    // Strips region subtags (pt-BR -> pt, zh-CN -> zh, ...) before matching
    // against `resources` above. Without this, a browser reporting pt-BR
    // (the common case in Brazil) would silently miss the "pt" bundle and
    // fall back to English, even though a Portuguese translation exists.
    load: 'languageOnly',
    interpolation: {
      escapeValue: false,
    },
    detection: {
      order: ['localStorage', 'navigator'],
      caches: ['localStorage'],
    },
  });

export default i18n;
