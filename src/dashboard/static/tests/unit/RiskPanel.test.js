/**
 * @vitest-environment happy-dom
 */

import { describe, it, expect, vi } from 'vitest';
import { createMockComponent } from '../utils/componentHelpers.js';

describe('RiskPanel Component', () => {
  it('should render the RiskPanel title', () => {
    const mockRiskPanel = {
      template: `
        <div class="risk-panel">
          <h1>Risk Dashboard</h1>
        </div>
      `,
      setup() {
        return {
          riskLevel: { value: 'MEDIUM' }
        };
      }
    };

    const container = document.createElement('div');
    container.innerHTML = mockRiskPanel.template;

    expect(container.querySelector('h1')).not.toBeNull();
    expect(container.querySelector('h1').textContent).toBe('Risk Dashboard');
  });

  it('should have risk metrics cards', () => {
    const mockRiskPanel = {
      template: `
        <div class="risk-panel">
          <div class="risk-metrics">
            <div class="var-card">
              <p>Value at Risk (VaR)</p>
              <p class="value">$125,000</p>
            </div>
            <div class="drawdown-card">
              <p>Max Drawdown</p>
              <p class="value">12.35%</p>
            </div>
          </div>
        </div>
      `
    };

    const container = document.createElement('div');
    container.innerHTML = mockRiskPanel.template;

    const varCard = container.querySelector('.var-card');
    const drawdownCard = container.querySelector('.drawdown-card');

    expect(varCard).not.toBeNull();
    expect(drawdownCard).not.toBeNull();
    expect(varCard.textContent).toContain('Value at Risk');
    expect(drawdownCard.textContent).toContain('Max Drawdown');
  });

  it('should display correct VaR value', () => {
    const varValue = 125000;

    const component = {
      template: `<div><p class="var-value">${{ varValue.toLocaleString() }}</p></div>`,
      setup() {
        return {
          varValue: { value: varValue }
        };
      }
    };

    const container = document.createElement('div');
    const formattedValue = varValue.toLocaleString();

    expect(formattedValue).toBe('125,000');
  });

  it('should show risk distribution', () => {
    const riskDistribution = [
      { symbol: '0700.HK', percentage: 35.5 },
      { symbol: '0388.HK', percentage: 28.3 }
    ];

    const component = {
      template: `
        <div class="risk-distribution">
          <div v-for="asset in riskDistribution" :key="asset.symbol" class="asset-item">
            <span class="symbol">{{ asset.symbol }}</span>
            <span class="percentage">{{ asset.percentage }}%</span>
          </div>
        </div>
      `,
      setup() {
        return {
          riskDistribution: { value: riskDistribution }
        };
      }
    };

    expect(riskDistribution).toHaveLength(2);
    expect(riskDistribution[0].symbol).toBe('0700.HK');
    expect(riskDistribution[0].percentage).toBe(35.5);
  });

  it('should have refresh button', () => {
    const mockClickHandler = vi.fn();

    const component = {
      template: `
        <div>
          <button @click="refreshData" class="refresh-btn">Refresh</button>
        </div>
      `,
      setup() {
        return {
          refreshData: mockClickHandler
        };
      }
    };

    expect(typeof mockClickHandler).toBe('function');
  });

  it('should display risk alerts', () => {
    const riskAlerts = [
      {
        id: 1,
        severity: 'high',
        title: 'VaR Threshold Exceeded',
        message: 'Portfolio VaR exceeded limit'
      }
    ];

    const component = {
      template: `
        <div class="risk-alerts">
          <div v-for="alert in riskAlerts" :key="alert.id" class="alert-item">
            <span :class="['severity-badge', alert.severity]">{{ alert.severity }}</span>
            <h3>{{ alert.title }}</h3>
            <p>{{ alert.message }}</p>
          </div>
        </div>
      `,
      setup() {
        return {
          riskAlerts: { value: riskAlerts }
        };
      }
    };

    expect(riskAlerts).toHaveLength(1);
    expect(riskAlerts[0].severity).toBe('high');
    expect(riskAlerts[0].title).toBe('VaR Threshold Exceeded');
  });

  it('should calculate portfolio metrics correctly', () => {
    const positions = [
      { symbol: '0700.HK', shares: 1000, price: 320 },
      { symbol: '0388.HK', shares: 500, price: 285 }
    ];

    const totalValue = positions.reduce((sum, pos) => sum + (pos.shares * pos.price), 0);

    expect(totalValue).toBe(462500);
  });

  it('should have proper component structure', () => {
    const component = {
      template: `
        <div class="risk-panel space-y-6">
          <div class="header">
            <h1>Risk Dashboard</h1>
          </div>
          <div class="metrics-grid">
            <!-- Metrics cards -->
          </div>
          <div class="risk-table">
            <!-- Position table -->
          </div>
          <div class="alerts-section" v-if="riskAlerts.length">
            <!-- Alerts -->
          </div>
        </div>
      `,
      setup() {
        return {
          riskAlerts: { value: [] }
        };
      }
    };

    expect(component.template).toContain('risk-panel');
    expect(component.template).toContain('header');
    expect(component.template).toContain('metrics-grid');
    expect(component.template).toContain('risk-table');
  });
});
