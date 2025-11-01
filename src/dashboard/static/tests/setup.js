import { beforeAll, vi } from 'vitest';
import { createTestingPinia } from '@pinia/testing';

// Mock Vue global
global.Vue = {
  ref: (val) => ({ value: val }),
  computed: (fn) => ({ value: fn() }),
  onMounted: (fn) => fn(),
  watch: () => {}
};

// Mock Font Awesome
document.body.innerHTML = '<div id="app"></div>';

Object.defineProperty(window, 'alert', {
  writable: true,
  value: vi.fn()
});

Object.defineProperty(window, 'confirm', {
  writable: true,
  value: vi.fn(() => true)
});

Object.defineProperty(window, 'console', {
  writable: true,
  value: {
    ...console,
    log: vi.fn(),
    error: vi.fn(),
    warn: vi.fn()
  }
});
