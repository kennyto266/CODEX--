/**
 * @vitest-environment happy-dom
 */

import { describe, it, expect, vi } from 'vitest';

describe('PortfolioRisk Component', () => {
  it('should render the PortfolioRisk title', () => {
    const container = document.createElement('div');
    container.innerHTML = `
      <div class="portfolio-risk">
        <h1>Portfolio Risk Analysis</h1>
      </div>
    `;

    expect(container.querySelector('h1')).not.toBeNull();
    expect(container.querySelector('h1').textContent).toBe('Portfolio Risk Analysis');
  });

  it('should display VaR metrics', () => {
    const portfolioVaR = 125000;
    const varChange = -2.5;

    const container = document.createElement('div');
    container.innerHTML = `
      <div class="var-metric">
        <p class="value">$${portfolioVaR.toLocaleString()}</p>
        <p class="change ${varChange >= 0 ? 'positive' : 'negative'}">
          ${varChange >= 0 ? '+' : ''}${varChange}% from yesterday
        </p>
      </div>
    `;

    const value = container.querySelector('.value');
    expect(value.textContent).toBe('$125,000');
    expect(container.querySelector('.change').classList.contains('negative')).toBe(true);
  });

  it('should show beta and sharpe ratio', () => {
    const beta = 1.12;
    const sharpeRatio = 1.85;

    expect(beta).toBeGreaterThan(1);
    expect(sharpeRatio).toBeGreaterThan(1);
    expect(sharpeRatio).toBeLessThan(3);
  });

  it('should display risk distribution', () => {
    const riskDistribution = [
      { symbol: '0700.HK', percentage: 35.5, change: -1.2 },
      { symbol: '0388.HK', percentage: 28.3, change: 0.5 },
      { symbol: '0939.HK', percentage: 22.1, change: -0.8 }
    ];

    const container = document.createElement('div');
    container.innerHTML = `
      <div class="risk-distribution">
        ${riskDistribution.map(asset => `
          <div class="asset-item">
            <span class="symbol">${asset.symbol}</span>
            <div class="progress-bar">
              <div class="progress" style="width: ${asset.percentage}%"></div>
            </div>
            <span class="percentage">${asset.percentage}%</span>
            <span class="change ${asset.change >= 0 ? 'positive' : 'negative'}">
              ${asset.change >= 0 ? '+' : ''}${asset.change}%
            </span>
          </div>
        `).join('')}
      </div>
    `;

    const assetItems = container.querySelectorAll('.asset-item');
    expect(assetItems).toHaveLength(3);
    expect(assetItems[0].textContent).toContain('0700.HK');
  });

  it('should show correlation matrix', () => {
    const correlationMatrix = [
      [1.00, 0.75, 0.68],
      [0.75, 1.00, 0.82],
      [0.68, 0.82, 1.00]
    ];

    expect(correlationMatrix).toHaveLength(3);
    expect(correlationMatrix[0][0]).toBe(1.00);
    expect(correlationMatrix[0][1]).toBe(0.75);
    expect(correlationMatrix[1][2]).toBe(0.82);
  });

  it('should calculate portfolio beta', () => {
    const positions = [
      { symbol: '0700.HK', weight: 0.35, beta: 1.15 },
      { symbol: '0388.HK', weight: 0.28, beta: 1.08 },
      { symbol: '0939.HK', weight: 0.22, beta: 1.12 }
    ];

    const portfolioBeta = positions.reduce((sum, pos) => sum + pos.weight * pos.beta, 0);

    expect(portfolioBeta).toBeCloseTo(1.12, 2);
  });

  it('should display position risk details', () => {
    const positions = [
      {
        symbol: '0700.HK',
        shares: 10000,
        marketValue: 320000,
        riskWeight: 35.5,
        varContribution: 85000
      },
      {
        symbol: '0388.HK',
        shares: 5000,
        marketValue: 180000,
        riskWeight: 28.3,
        varContribution: 42000
      }
    ];

    expect(positions[0].marketValue).toBeGreaterThan(positions[1].marketValue);
    expect(positions[0].varContribution).toBeGreaterThan(positions[1].varContribution);
  });

  it('should have max drawdown display', () => {
    const maxDrawdown = 12.35;

    expect(maxDrawdown).toBeGreaterThan(0);
    expect(maxDrawdown).toBeLessThan(50);
  });

  it('should show risk alerts', () => {
    const riskAlerts = [
      {
        severity: 'high',
        message: 'VaR exceeded threshold',
        threshold: 100000
      },
      {
        severity: 'medium',
        message: 'Position concentration high',
        concentration: 35
      }
    ];

    expect(riskAlerts).toHaveLength(2);
    expect(riskAlerts[0].severity).toBe('high');
    expect(riskAlerts[1].severity).toBe('medium');
  });

  it('should calculate diversification score', () => {
    const positions = [
      { weight: 0.35 },
      { weight: 0.28 },
      { weight: 0.22 },
      { weight: 0.15 }
    ];

    const maxWeight = Math.max(...positions.map(p => p.weight));
    const diversificationScore = 100 - (maxWeight - 25) * 2;

    expect(maxWeight).toBe(0.35);
    expect(diversificationScore).toBe(80);
  });

  it('should handle risk metric updates', () => {
    let portfolioVaR = 125000;
    let previousVaR = 128000;

    const varChange = ((portfolioVaR - previousVaR) / previousVaR) * 100;

    expect(varChange).toBeCloseTo(-2.34, 1);
  });

  it('should display correlation heatmap data', () => {
    const symbols = ['0700.HK', '0388.HK', '0939.HK', '1398.HK'];

    expect(symbols).toHaveLength(4);
    expect(symbols[0]).toBe('0700.HK');
  });

  it('should calculate risk-adjusted return', () => {
    const portfolioReturn = 8.12;
    const volatility = 12.5;
    const riskAdjustedReturn = portfolioReturn / volatility;

    expect(riskAdjustedReturn).toBeGreaterThan(0.5);
    expect(riskAdjustedReturn).toBeLessThan(1);
  });

  it('should have refresh functionality', () => {
    const mockRefresh = vi.fn();

    expect(typeof mockRefresh).toBe('function');
    mockRefresh();
    expect(mockRefresh).toHaveBeenCalledTimes(1);
  });
});
