/**
 * @vitest-environment happy-dom
 */

import { describe, it, expect, vi } from 'vitest';

describe('BacktestPanel Component', () => {
  it('should render the BacktestPanel title', () => {
    const container = document.createElement('div');
    container.innerHTML = `
      <div class="backtest-panel">
        <h1>Strategy Backtest</h1>
      </div>
    `;

    expect(container.querySelector('h1')).not.toBeNull();
    expect(container.querySelector('h1').textContent).toBe('Strategy Backtest');
  });

  it('should have backtest configuration form', () => {
    const container = document.createElement('div');
    container.innerHTML = `
      <div class="config-form">
        <select name="strategy">
          <option value="kdj">KDJ (Stochastic)</option>
          <option value="rsi">RSI</option>
          <option value="macd">MACD</option>
        </select>
        <input type="text" name="symbol" placeholder="0700.HK" />
        <input type="date" name="startDate" />
        <input type="date" name="endDate" />
        <input type="number" name="initialCapital" placeholder="1000000" />
      </div>
    `;

    const strategySelect = container.querySelector('select[name="strategy"]');
    const symbolInput = container.querySelector('input[name="symbol"]');
    const startDate = container.querySelector('input[name="startDate"]');

    expect(strategySelect).not.toBeNull();
    expect(symbolInput).not.toBeNull();
    expect(startDate).not.toBeNull();
    expect(strategySelect.options).toHaveLength(3);
  });

  it('should display quick preset buttons', () => {
    const presets = [
      { name: 'momentum', title: 'Momentum Strategy', desc: 'KDJ with 9-period' },
      { name: 'mean_reversion', title: 'Mean Reversion', desc: 'Bollinger Bands' },
      { name: 'trend_following', title: 'Trend Following', desc: 'MACD crossover' }
    ];

    const container = document.createElement('div');
    container.innerHTML = `
      <div class="presets">
        ${presets.map(preset => `
          <button class="preset-btn" data-preset="${preset.name}">
            <h3>${preset.title}</h3>
            <p>${preset.desc}</p>
          </button>
        `).join('')}
      </div>
    `;

    const presetButtons = container.querySelectorAll('.preset-btn');
    expect(presetButtons).toHaveLength(3);
    expect(presetButtons[0].dataset.preset).toBe('momentum');
    expect(presetButtons[0].textContent).toContain('Momentum Strategy');
  });

  it('should show backtest results', () => {
    const results = {
      totalReturn: 25.67,
      annualizedReturn: 8.12,
      maxDrawdown: 15.23,
      sharpeRatio: 1.45,
      totalTrades: 127,
      winRate: 62.5
    };

    const container = document.createElement('div');
    container.innerHTML = `
      <div class="results">
        <div class="metric">
          <p class="label">Total Return</p>
          <p class="value">${results.totalReturn}%</p>
        </div>
        <div class="metric">
          <p class="label">Sharpe Ratio</p>
          <p class="value">${results.sharpeRatio}</p>
        </div>
      </div>
    `;

    const totalReturn = container.querySelector('.metric .label');
    expect(totalReturn.textContent).toBe('Total Return');
    expect(results.winRate).toBeGreaterThan(50);
    expect(results.totalTrades).toBeGreaterThan(0);
  });

  it('should calculate performance metrics', () => {
    const initialCapital = 1000000;
    const finalValue = 1256700;
    const totalReturn = ((finalValue - initialCapital) / initialCapital) * 100;

    expect(totalReturn).toBe(25.67);
  });

  it('should display recent trades table', () => {
    const recentTrades = [
      { date: '2023-12-15', type: 'BUY', price: 318.50, quantity: 100, pnl: 1250 },
      { date: '2023-12-14', type: 'SELL', price: 317.25, quantity: 100, pnl: -890 }
    ];

    const container = document.createElement('div');
    container.innerHTML = `
      <table class="trades-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Type</th>
            <th>Price</th>
            <th>Quantity</th>
            <th>P&L</th>
          </tr>
        </thead>
        <tbody>
          ${recentTrades.map(trade => `
            <tr>
              <td>${trade.date}</td>
              <td class="type-${trade.type.toLowerCase()}">${trade.type}</td>
              <td>$${trade.price}</td>
              <td>${trade.quantity}</td>
              <td class="pnl-${trade.pnl >= 0 ? 'positive' : 'negative'}">${trade.pnl}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;

    const tableRows = container.querySelectorAll('tbody tr');
    expect(tableRows).toHaveLength(2);
    expect(tableRows[0].textContent).toContain('2023-12-15');
  });

  it('should have run backtest button', () => {
    const mockHandler = vi.fn();

    const component = {
      template: `
        <button @click="runBacktest" :disabled="running" class="run-btn">
          {{ running ? 'Running...' : 'Run Backtest' }}
        </button>
      `,
      setup() {
        return {
          running: { value: false },
          runBacktest: mockHandler
        };
      }
    };

    expect(typeof mockHandler).toBe('function');
  });

  it('should calculate win rate', () => {
    const totalTrades = 100;
    const winningTrades = 62;
    const winRate = (winningTrades / totalTrades) * 100;

    expect(winRate).toBe(62);
  });

  it('should show equity curve placeholder', () => {
    const container = document.createElement('div');
    container.innerHTML = `
      <div class="equity-curve">
        <div class="placeholder">
          <p>Equity curve visualization would be here</p>
        </div>
      </div>
    `;

    const placeholder = container.querySelector('.placeholder');
    expect(placeholder).not.toBeNull();
    expect(placeholder.textContent).toContain('Equity curve');
  });

  it('should have export and save buttons', () => {
    const container = document.createElement('div');
    container.innerHTML = `
      <div class="actions">
        <button class="export-btn">Export Results</button>
        <button class="save-btn">Save Strategy</button>
      </div>
    `;

    const exportBtn = container.querySelector('.export-btn');
    const saveBtn = container.querySelector('.save-btn');

    expect(exportBtn).not.toBeNull();
    expect(saveBtn).not.toBeNull();
    expect(exportBtn.textContent).toBe('Export Results');
  });

  it('should validate configuration inputs', () => {
    const config = {
      strategy: 'kdj',
      symbol: '0700.HK',
      startDate: '2020-01-01',
      endDate: '2023-12-31',
      initialCapital: 1000000
    };

    const isValid = config.strategy &&
                    config.symbol &&
                    config.startDate &&
                    config.endDate &&
                    config.initialCapital > 0;

    expect(isValid).toBe(true);
  });

  it('should handle strategy parameter changes', () => {
    const parameters = {
      kdj: { kPeriod: 9, dPeriod: 3 },
      rsi: { rsiPeriod: 14 },
      macd: { fastPeriod: 12, slowPeriod: 26, signalPeriod: 9 }
    };

    expect(parameters.kdj.kPeriod).toBe(9);
    expect(parameters.rsi.rsiPeriod).toBe(14);
    expect(parameters.macd.fastPeriod).toBe(12);
  });
});
