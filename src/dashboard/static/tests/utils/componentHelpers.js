/**
 * Test utilities for Vue component testing
 */

/**
 * Simulate a Vue component object
 * @param {Object} options - Component options
 * @returns {Object} - Mock Vue component
 */
export function createMockComponent(options) {
  return {
    template: options.template || '<div></div>',
    setup: options.setup || (() => ({})),
    ...options
  };
}

/**
 * Simulate Vue ref
 * @param {*} value - Initial value
 * @returns {Object} - Mock ref object
 */
export function mockRef(value) {
  return {
    value: value,
    _isRef: true
  };
}

/**
 * Simulate Vue computed
 * @param {Function} getter - Computed getter
 * @returns {Object} - Mock computed object
 */
export function mockComputed(getter) {
  return {
    value: getter(),
    _isComputed: true
  };
}

/**
 * Create a mock DOM element
 * @param {string} tag - HTML tag
 * @param {Object} props - Element properties
 * @returns {Object} - Mock DOM element
 */
export function createMockElement(tag = 'div', props = {}) {
  return {
    tag,
    props,
    attributes: {},
    children: [],
    text: '',
    innerHTML: '',
    className: '',
    style: {},
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    setAttribute: vi.fn(),
    getAttribute: vi.fn(),
    click: vi.fn(),
    querySelector: vi.fn(),
    querySelectorAll: vi.fn(() => [])
  };
}

/**
 * Mock the global Vue object for testing
 */
export function mockVue() {
  return {
    ref: mockRef,
    computed: mockComputed,
    onMounted: vi.fn(),
    watch: vi.fn(),
    nextTick: vi.fn(() => Promise.resolve())
  };
}
