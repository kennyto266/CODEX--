/**
 * CODEX Trading Dashboard - Simple Version
 */

// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ CODEX Dashboard loaded');

    // Create simple dashboard
    const app = document.getElementById('app');
    app.innerHTML = `
        <div style="min-height: 100vh; background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);">
            <!-- Navigation -->
            <nav style="background: rgba(15, 23, 42, 0.8); backdrop-filter: blur(10px); border-bottom: 1px solid #334155; padding: 1rem 0;">
                <div style="max-width: 1200px; margin: 0 auto; padding: 0 1.5rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="display: flex; align-items: center; gap: 12px;">
                            <div style="width: 32px; height: 32px; background: linear-gradient(135deg, #3b82f6, #06b6d4); border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 14px;">C</div>
                            <span style="font-size: 20px; font-weight: bold; color: white;">CODEX Trading System</span>
                        </div>
                        <div style="display: flex; gap: 8px;">
                            <a href="#/" style="color: #e2e8f0; padding: 8px 16px; text-decoration: none; border-radius: 8px; background: rgba(59, 130, 246, 0.1); border: 1px solid #3b82f6;">Dashboard</a>
                            <a href="#/agents" style="color: #94a3b8; padding: 8px 16px; text-decoration: none; border-radius: 8px; transition: all 0.2s;">Agents</a>
                            <a href="#/tasks" style="color: #94a3b8; padding: 8px 16px; text-decoration: none; border-radius: 8px; transition: all 0.2s;">Tasks</a>
                            <a href="#/backtest" style="color: #94a3b8; padding: 8px 16px; text-decoration: none; border-radius: 8px; transition: all 0.2s;">Backtest</a>
                            <a href="#/risk" style="color: #94a3b8; padding: 8px 16px; text-decoration: none; border-radius: 8px; transition: all 0.2s;">Risk</a>
                            <a href="#/trading" style="color: #94a3b8; padding: 8px 16px; text-decoration: none; border-radius: 8px; transition: all 0.2s;">Trading</a>
                        </div>
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <div style="width: 8px; height: 8px; border-radius: 50%; background: #4ade80; animation: pulse 2s infinite;"></div>
                            <span style="color: #4ade80; font-size: 14px; font-weight: 500;">OPERATIONAL</span>
                        </div>
                    </div>
                </div>
            </nav>

            <!-- Main Content -->
            <main style="max-width: 1200px; margin: 0 auto; padding: 2rem 1.5rem;">
                <div id="content">
                    <h1 style="font-size: 32px; font-weight: bold; color: white; margin-bottom: 24px;">Dashboard Overview</h1>

                    <!-- Stats Cards -->
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 24px; margin-bottom: 32px;">
                        <div style="background: rgba(30, 41, 59, 0.7); padding: 24px; border-radius: 12px; border: 1px solid #334155;">
                            <div style="color: #94a3b8; font-size: 14px; margin-bottom: 8px;">Initial Capital</div>
                            <div style="font-size: 32px; font-weight: bold; color: white;">$1,000,000</div>
                        </div>
                        <div style="background: rgba(30, 41, 59, 0.7); padding: 24px; border-radius: 12px; border: 1px solid #334155;">
                            <div style="color: #94a3b8; font-size: 14px; margin-bottom: 8px;">Portfolio Value</div>
                            <div style="font-size: 32px; font-weight: bold; color: white;">$1,000,000</div>
                        </div>
                        <div style="background: rgba(30, 41, 59, 0.7); padding: 24px; border-radius: 12px; border: 1px solid #334155;">
                            <div style="color: #94a3b8; font-size: 14px; margin-bottom: 8px;">Active Positions</div>
                            <div style="font-size: 32px; font-weight: bold; color: white;">0</div>
                        </div>
                        <div style="background: rgba(30, 41, 59, 0.7); padding: 24px; border-radius: 12px; border: 1px solid #334155;">
                            <div style="color: #94a3b8; font-size: 14px; margin-bottom: 8px;">Total Return</div>
                            <div style="font-size: 32px; font-weight: bold; color: #4ade80;">0.00%</div>
                        </div>
                    </div>

                    <!-- Agent Cards -->
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 24px;">
                        <div style="background: rgba(30, 41, 59, 0.7); padding: 24px; border-radius: 12px; border: 1px solid #334155; transition: all 0.2s; cursor: pointer;" onmouseover="this.style.borderColor='#3b82f6'" onmouseout="this.style.borderColor='#334155'">
                            <h2 style="font-size: 20px; font-weight: bold; color: white; margin-bottom: 16px; display: flex; align-items: center; gap: 8px;">
                                <span style="color: #3b82f6;">🤖</span>
                                Agent Management
                            </h2>
                            <p style="color: #94a3b8; margin-bottom: 16px;">Monitor and control AI agents</p>
                            <a href="#/agents" style="display: inline-block; padding: 8px 16px; background: #3b82f6; color: white; text-decoration: none; border-radius: 6px; transition: background 0.2s;" onmouseover="this.style.background='#2563eb'" onmouseout="this.style.background='#3b82f6'">View Agents →</a>
                        </div>
                        <div style="background: rgba(30, 41, 59, 0.7); padding: 24px; border-radius: 12px; border: 1px solid #334155; transition: all 0.2s; cursor: pointer;" onmouseover="this.style.borderColor='#8b5cf6'" onmouseout="this.style.borderColor='#334155'">
                            <h2 style="font-size: 20px; font-weight: bold; color: white; margin-bottom: 16px; display: flex; align-items: center; gap: 8px;">
                                <span style="color: #8b5cf6;">📈</span>
                                Strategy Backtest
                            </h2>
                            <p style="color: #94a3b8; margin-bottom: 16px;">Test trading strategies</p>
                            <a href="#/backtest" style="display: inline-block; padding: 8px 16px; background: #8b5cf6; color: white; text-decoration: none; border-radius: 6px; transition: background 0.2s;" onmouseover="this.style.background='#7c3aed'" onmouseout="this.style.background='#8b5cf6'">Run Backtest →</a>
                        </div>
                        <div style="background: rgba(30, 41, 59, 0.7); padding: 24px; border-radius: 12px; border: 1px solid #334155; transition: all 0.2s; cursor: pointer;" onmouseover="this.style.borderColor='#ef4444'" onmouseout="this.style.borderColor='#334155'">
                            <h2 style="font-size: 20px; font-weight: bold; color: white; margin-bottom: 16px; display: flex; align-items: center; gap: 8px;">
                                <span style="color: #ef4444;">🛡️</span>
                                Risk Dashboard
                            </h2>
                            <p style="color: #94a3b8; margin-bottom: 16px;">Monitor portfolio risk</p>
                            <a href="#/risk" style="display: inline-block; padding: 8px 16px; background: #ef4444; color: white; text-decoration: none; border-radius: 6px; transition: background 0.2s;" onmouseover="this.style.background='#dc2626'" onmouseout="this.style.background='#ef4444'">View Risk →</a>
                        </div>
                    </div>
                </div>
            </main>
        </div>

        <style>
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
        </style>
    `;

    // Simple router
    window.addEventListener('hashchange', function() {
        const route = window.location.hash.substring(1) || '/';
        const content = document.getElementById('content');

        if (route === '/') {
            // Already loaded
        } else if (route === '/agents') {
            content.innerHTML = `
                <h1 style="color: white; font-size: 32px; font-weight: bold; margin-bottom: 24px;">🤖 Agent Management</h1>
                <p style="color: #94a3b8; margin-bottom: 32px;">Monitor and control your AI trading agents</p>

                <!-- Agent Overview Cards -->
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 32px;">
                    <div style="background: rgba(30, 41, 59, 0.7); padding: 20px; border-radius: 12px; border: 1px solid #334155;">
                        <div style="color: #94a3b8; font-size: 14px; margin-bottom: 8px;">Active Agents</div>
                        <div style="font-size: 28px; font-weight: bold; color: #4ade80;">7</div>
                    </div>
                    <div style="background: rgba(30, 41, 59, 0.7); padding: 20px; border-radius: 12px; border: 1px solid #334155;">
                        <div style="color: #94a3b8; font-size: 14px; margin-bottom: 8px;">Idle Agents</div>
                        <div style="font-size: 28px; font-weight: bold; color: #fbbf24;">0</div>
                    </div>
                    <div style="background: rgba(30, 41, 59, 0.7); padding: 20px; border-radius: 12px; border: 1px solid #334155;">
                        <div style="color: #94a3b8; font-size: 14px; margin-bottom: 8px;">Messages Processed</div>
                        <div style="font-size: 28px; font-weight: bold; color: #3b82f6;">15,432</div>
                    </div>
                    <div style="background: rgba(30, 41, 59, 0.7); padding: 20px; border-radius: 12px; border: 1px solid #334155;">
                        <div style="color: #94a3b8; font-size: 14px; margin-bottom: 8px;">System Health</div>
                        <div style="font-size: 28px; font-weight: bold; color: #4ade80;">98%</div>
                    </div>
                </div>

                <!-- Agent List -->
                <div style="background: rgba(30, 41, 59, 0.7); padding: 24px; border-radius: 12px; border: 1px solid #334155; margin-bottom: 24px;">
                    <h2 style="color: white; font-size: 20px; margin-bottom: 20px;">🗂️ Agent Status</h2>

                    <!-- Agent 1: Coordinator -->
                    <div style="background: rgba(15, 23, 42, 0.5); padding: 16px; border-radius: 8px; border: 1px solid #475569; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center;">
                        <div style="display: flex; align-items: center; gap: 16px;">
                            <div style="width: 48px; height: 48px; background: linear-gradient(135deg, #3b82f6, #2563eb); border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 20px;">🎯</div>
                            <div>
                                <div style="color: white; font-weight: bold; font-size: 16px;">Coordinator Agent</div>
                                <div style="color: #94a3b8; font-size: 14px;">Coordinates all agent workflows and messages</div>
                                <div style="display: flex; gap: 12px; margin-top: 8px;">
                                    <span style="color: #94a3b8; font-size: 12px;">📊 Messages: 2,845</span>
                                    <span style="color: #94a3b8; font-size: 12px;">⏱️ Uptime: 24h 15m</span>
                                </div>
                            </div>
                        </div>
                        <div style="display: flex; align-items: center; gap: 12px;">
                            <div style="padding: 6px 12px; background: rgba(74, 222, 128, 0.2); border: 1px solid #4ade80; border-radius: 6px; color: #4ade80; font-size: 14px; font-weight: 500;">🟢 Running</div>
                            <button onclick="controlAgent('coordinator', 'stop')" style="padding: 8px 16px; background: #ef4444; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; transition: background 0.2s;" onmouseover="this.style.background='#dc2626'" onmouseout="this.style.background='#ef4444'">Stop</button>
                            <button onclick="viewAgentLogs('coordinator')" style="padding: 8px 16px; background: #6b7280; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; transition: background 0.2s;">Logs</button>
                        </div>
                    </div>

                    <!-- Agent 2: Data Scientist -->
                    <div style="background: rgba(15, 23, 42, 0.5); padding: 16px; border-radius: 8px; border: 1px solid #475569; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center;">
                        <div style="display: flex; align-items: center; gap: 16px;">
                            <div style="width: 48px; height: 48px; background: linear-gradient(135deg, #8b5cf6, #7c3aed); border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 20px;">📊</div>
                            <div>
                                <div style="color: white; font-weight: bold; font-size: 16px;">Data Scientist Agent</div>
                                <div style="color: #94a3b8; font-size: 14px;">Data analysis and anomaly detection</div>
                                <div style="display: flex; gap: 12px; margin-top: 8px;">
                                    <span style="color: #94a3b8; font-size: 12px;">📊 Messages: 1,923</span>
                                    <span style="color: #94a3b8; font-size: 12px;">⏱️ Uptime: 24h 15m</span>
                                </div>
                            </div>
                        </div>
                        <div style="display: flex; align-items: center; gap: 12px;">
                            <div style="padding: 6px 12px; background: rgba(74, 222, 128, 0.2); border: 1px solid #4ade80; border-radius: 6px; color: #4ade80; font-size: 14px; font-weight: 500;">🟢 Running</div>
                            <button onclick="controlAgent('data_scientist', 'stop')" style="padding: 8px 16px; background: #ef4444; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; transition: background 0.2s;">Stop</button>
                            <button onclick="viewAgentLogs('data_scientist')" style="padding: 8px 16px; background: #6b7280; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; transition: background 0.2s;">Logs</button>
                        </div>
                    </div>

                    <!-- Agent 3: Quantitative Analyst -->
                    <div style="background: rgba(15, 23, 42, 0.5); padding: 16px; border-radius: 8px; border: 1px solid #475569; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center;">
                        <div style="display: flex; align-items: center; gap: 16px;">
                            <div style="width: 48px; height: 48px; background: linear-gradient(135deg, #10b981, #059669); border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 20px;">📈</div>
                            <div>
                                <div style="color: white; font-weight: bold; font-size: 16px;">Quantitative Analyst Agent</div>
                                <div style="color: #94a3b8; font-size: 14px;">Quantitative analysis and Monte Carlo simulation</div>
                                <div style="display: flex; gap: 12px; margin-top: 8px;">
                                    <span style="color: #94a3b8; font-size: 12px;">📊 Messages: 2,156</span>
                                    <span style="color: #94a3b8; font-size: 12px;">⏱️ Uptime: 24h 15m</span>
                                </div>
                            </div>
                        </div>
                        <div style="display: flex; align-items: center; gap: 12px;">
                            <div style="padding: 6px 12px; background: rgba(74, 222, 128, 0.2); border: 1px solid #4ade80; border-radius: 6px; color: #4ade80; font-size: 14px; font-weight: 500;">🟢 Running</div>
                            <button onclick="controlAgent('quantitative_analyst', 'stop')" style="padding: 8px 16px; background: #ef4444; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; transition: background 0.2s;">Stop</button>
                            <button onclick="viewAgentLogs('quantitative_analyst')" style="padding: 8px 16px; background: #6b7280; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; transition: background 0.2s;">Logs</button>
                        </div>
                    </div>

                    <!-- Agent 4: Quantitative Engineer -->
                    <div style="background: rgba(15, 23, 42, 0.5); padding: 16px; border-radius: 8px; border: 1px solid #475569; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center;">
                        <div style="display: flex; align-items: center; gap: 16px;">
                            <div style="width: 48px; height: 48px; background: linear-gradient(135deg, #f59e0b, #d97706); border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 20px;">⚙️</div>
                            <div>
                                <div style="color: white; font-weight: bold; font-size: 16px;">Quantitative Engineer Agent</div>
                                <div style="color: #94a3b8; font-size: 14px;">System monitoring and performance optimization</div>
                                <div style="display: flex; gap: 12px; margin-top: 8px;">
                                    <span style="color: #94a3b8; font-size: 12px;">📊 Messages: 1,567</span>
                                    <span style="color: #94a3b8; font-size: 12px;">⏱️ Uptime: 24h 15m</span>
                                </div>
                            </div>
                        </div>
                        <div style="display: flex; align-items: center; gap: 12px;">
                            <div style="padding: 6px 12px; background: rgba(74, 222, 128, 0.2); border: 1px solid #4ade80; border-radius: 6px; color: #4ade80; font-size: 14px; font-weight: 500;">🟢 Running</div>
                            <button onclick="controlAgent('quantitative_engineer', 'stop')" style="padding: 8px 16px; background: #ef4444; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; transition: background 0.2s;">Stop</button>
                            <button onclick="viewAgentLogs('quantitative_engineer')" style="padding: 8px 16px; background: #6b7280; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; transition: background 0.2s;">Logs</button>
                        </div>
                    </div>

                    <!-- Agent 5: Portfolio Manager -->
                    <div style="background: rgba(15, 23, 42, 0.5); padding: 16px; border-radius: 8px; border: 1px solid #475569; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center;">
                        <div style="display: flex; align-items: center; gap: 16px;">
                            <div style="width: 48px; height: 48px; background: linear-gradient(135deg, #06b6d4, #0891b2); border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 20px;">💼</div>
                            <div>
                                <div style="color: white; font-weight: bold; font-size: 16px;">Portfolio Manager Agent</div>
                                <div style="color: #94a3b8; font-size: 14px;">Portfolio management and risk budgeting</div>
                                <div style="display: flex; gap: 12px; margin-top: 8px;">
                                    <span style="color: #94a3b8; font-size: 12px;">📊 Messages: 2,341</span>
                                    <span style="color: #94a3b8; font-size: 12px;">⏱️ Uptime: 24h 15m</span>
                                </div>
                            </div>
                        </div>
                        <div style="display: flex; align-items: center; gap: 12px;">
                            <div style="padding: 6px 12px; background: rgba(74, 222, 128, 0.2); border: 1px solid #4ade80; border-radius: 6px; color: #4ade80; font-size: 14px; font-weight: 500;">🟢 Running</div>
                            <button onclick="controlAgent('portfolio_manager', 'stop')" style="padding: 8px 16px; background: #ef4444; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; transition: background 0.2s;">Stop</button>
                            <button onclick="viewAgentLogs('portfolio_manager')" style="padding: 8px 16px; background: #6b7280; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; transition: background 0.2s;">Logs</button>
                        </div>
                    </div>

                    <!-- Agent 6: Research Analyst -->
                    <div style="background: rgba(15, 23, 42, 0.5); padding: 16px; border-radius: 8px; border: 1px solid #475569; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center;">
                        <div style="display: flex; align-items: center; gap: 16px;">
                            <div style="width: 48px; height: 48px; background: linear-gradient(135deg, #ec4899, #db2777); border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 20px;">🔍</div>
                            <div>
                                <div style="color: white; font-weight: bold; font-size: 16px;">Research Analyst Agent</div>
                                <div style="color: #94a3b8; font-size: 14px;">Strategy research and backtest validation</div>
                                <div style="display: flex; gap: 12px; margin-top: 8px;">
                                    <span style="color: #94a3b8; font-size: 12px;">📊 Messages: 1,789</span>
                                    <span style="color: #94a3b8; font-size: 12px;">⏱️ Uptime: 24h 15m</span>
                                </div>
                            </div>
                        </div>
                        <div style="display: flex; align-items: center; gap: 12px;">
                            <div style="padding: 6px 12px; background: rgba(74, 222, 128, 0.2); border: 1px solid #4ade80; border-radius: 6px; color: #4ade80; font-size: 14px; font-weight: 500;">🟢 Running</div>
                            <button onclick="controlAgent('research_analyst', 'stop')" style="padding: 8px 16px; background: #ef4444; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; transition: background 0.2s;">Stop</button>
                            <button onclick="viewAgentLogs('research_analyst')" style="padding: 8px 16px; background: #6b7280; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; transition: background 0.2s;">Logs</button>
                        </div>
                    </div>

                    <!-- Agent 7: Risk Analyst -->
                    <div style="background: rgba(15, 23, 42, 0.5); padding: 16px; border-radius: 8px; border: 1px solid #475569; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center;">
                        <div style="display: flex; align-items: center; gap: 16px;">
                            <div style="width: 48px; height: 48px; background: linear-gradient(135deg, #ef4444, #dc2626); border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 20px;">🛡️</div>
                            <div>
                                <div style="color: white; font-weight: bold; font-size: 16px;">Risk Analyst Agent</div>
                                <div style="color: #94a3b8; font-size: 14px;">Risk assessment and hedging strategies</div>
                                <div style="display: flex; gap: 12px; margin-top: 8px;">
                                    <span style="color: #94a3b8; font-size: 12px;">📊 Messages: 2,811</span>
                                    <span style="color: #94a3b8; font-size: 12px;">⏱️ Uptime: 24h 15m</span>
                                </div>
                            </div>
                        </div>
                        <div style="display: flex; align-items: center; gap: 12px;">
                            <div style="padding: 6px 12px; background: rgba(74, 222, 128, 0.2); border: 1px solid #4ade80; border-radius: 6px; color: #4ade80; font-size: 14px; font-weight: 500;">🟢 Running</div>
                            <button onclick="controlAgent('risk_analyst', 'stop')" style="padding: 8px 16px; background: #ef4444; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; transition: background 0.2s;">Stop</button>
                            <button onclick="viewAgentLogs('risk_analyst')" style="padding: 8px 16px; background: #6b7280; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; transition: background 0.2s;">Logs</button>
                        </div>
                    </div>
                </div>

                <!-- Control Panel -->
                <div style="background: rgba(30, 41, 59, 0.7); padding: 24px; border-radius: 12px; border: 1px solid #334155;">
                    <h2 style="color: white; font-size: 20px; margin-bottom: 20px;">🎛️ System Control</h2>
                    <div style="display: flex; gap: 12px; flex-wrap: wrap;">
                        <button onclick="startAllAgents()" style="padding: 12px 24px; background: linear-gradient(135deg, #10b981, #059669); color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; font-weight: 600; transition: all 0.2s; box-shadow: 0 4px 6px rgba(0,0,0,0.1);" onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 12px rgba(0,0,0,0.15)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 6px rgba(0,0,0,0.1)'">
                            ▶️ Start All Agents
                        </button>
                        <button onclick="stopAllAgents()" style="padding: 12px 24px; background: linear-gradient(135deg, #ef4444, #dc2626); color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; font-weight: 600; transition: all 0.2s; box-shadow: 0 4px 6px rgba(0,0,0,0.1);" onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 12px rgba(0,0,0,0.15)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 6px rgba(0,0,0,0.1)'">
                            ⏹️ Stop All Agents
                        </button>
                        <button onclick="restartAllAgents()" style="padding: 12px 24px; background: linear-gradient(135deg, #f59e0b, #d97706); color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; font-weight: 600; transition: all 0.2s; box-shadow: 0 4px 6px rgba(0,0,0,0.1);" onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 12px rgba(0,0,0,0.15)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 6px rgba(0,0,0,0.1)'">
                            🔄 Restart All Agents
                        </button>
                        <button onclick="viewSystemLogs()" style="padding: 12px 24px; background: linear-gradient(135deg, #6b7280, #4b5563); color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; font-weight: 600; transition: all 0.2s; box-shadow: 0 4px 6px rgba(0,0,0,0.1);" onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 12px rgba(0,0,0,0.15)'" onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 6px rgba(0,0,0,0.1)'">
                            📋 View System Logs
                        </button>
                    </div>
                </div>
            `;
        } else if (route === '/tasks') {
            content.innerHTML = `
                <div style="color: white; font-size: 32px; font-weight: bold; margin-bottom: 24px;">📋 任務看板</div>
                <p style="color: #94a3b8; margin-bottom: 24px;">總計 100 個任務，完成率 3%</p>

                <!-- 統計卡片 -->
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 32px;">
                    <div style="background: rgba(30, 41, 59, 0.7); padding: 20px; border-radius: 12px; border: 1px solid #334155;">
                        <div style="color: #94a3b8; font-size: 14px; margin-bottom: 8px;">總任務數</div>
                        <div style="font-size: 28px; font-weight: bold; color: white;">100</div>
                    </div>
                    <div style="background: rgba(30, 41, 59, 0.7); padding: 20px; border-radius: 12px; border: 1px solid #334155;">
                        <div style="color: #94a3b8; font-size: 14px; margin-bottom: 8px;">已完成</div>
                        <div style="font-size: 28px; font-weight: bold; color: #4ade80;">3</div>
                    </div>
                    <div style="background: rgba(30, 41, 59, 0.7); padding: 20px; border-radius: 12px; border: 1px solid #334155;">
                        <div style="color: #94a3b8; font-size: 14px; margin-bottom: 8px;">進行中</div>
                        <div style="font-size: 28px; font-weight: bold; color: #3b82f6;">7</div>
                    </div>
                    <div style="background: rgba(30, 41, 59, 0.7); padding: 20px; border-radius: 12px; border: 1px solid #334155;">
                        <div style="color: #94a3b8; font-size: 14px; margin-bottom: 8px;">待處理</div>
                        <div style="font-size: 28px; font-weight: bold; color: #fbbf24;">89</div>
                    </div>
                </div>

                <!-- 優先級分布 -->
                <div style="background: rgba(30, 41, 59, 0.7); padding: 24px; border-radius: 12px; border: 1px solid #334155; margin-bottom: 24px;">
                    <h2 style="color: white; font-size: 20px; margin-bottom: 20px;">優先級分布</h2>
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px;">
                        <div style="text-align: center;">
                            <div style="color: #ef4444; font-size: 24px; font-weight: bold;">62</div>
                            <div style="color: #94a3b8; font-size: 14px;">P0 (關鍵路徑)</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="color: #fbbf24; font-size: 24px; font-weight: bold;">33</div>
                            <div style="color: #94a3b8; font-size: 14px;">P1 (重要)</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="color: #3b82f6; font-size: 24px; font-weight: bold;">5</div>
                            <div style="color: #94a3b8; font-size: 14px;">P2 (一般)</div>
                        </div>
                    </div>
                </div>

                <!-- 快速操作 -->
                <div style="background: rgba(30, 41, 59, 0.7); padding: 24px; border-radius: 12px; border: 1px solid #334155;">
                    <h2 style="color: white; font-size: 20px; margin-bottom: 20px;">快速操作</h2>
                    <div style="display: flex; gap: 12px; flex-wrap: wrap;">
                        <button onclick="viewAllTasks()" style="padding: 12px 24px; background: #3b82f6; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; transition: all 0.2s;" onmouseover="this.style.transform='translateY(-2px)'" onmouseout="this.style.transform='translateY(0)'">📋 查看所有任務</button>
                        <button onclick="openTaskBoard()" style="padding: 12px 24px; background: #8b5cf6; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; transition: all 0.2s;" onmouseover="this.style.transform='translateY(-2px)'" onmouseout="this.style.transform='translateY(0)'">🎯 打開任務看板</button>
                        <button onclick="openTaskAPI()" style="padding: 12px 24px; background: #10b981; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; transition: all 0.2s;" onmouseover="this.style.transform='translateY(-2px)'" onmouseout="this.style.transform='translateY(0)'">⚡ 互動模式</button>
                    </div>
                </div>

                <!-- 任務列表 -->
                <div style="background: rgba(30, 41, 59, 0.7); padding: 24px; border-radius: 12px; border: 1px solid #334155; margin-top: 24px;">
                    <h2 style="color: white; font-size: 20px; margin-bottom: 20px;">最近任務</h2>
                    <div style="display: grid; gap: 12px;">
                        <div style="background: rgba(15, 23, 42, 0.5); padding: 16px; border-radius: 8px; border: 1px solid #475569;">
                            <div style="display: flex; justify-content: space-between; align-items: start;">
                                <div>
                                    <div style="color: white; font-weight: bold;">TASK-100</div>
                                    <div style="color: #94a3b8; font-size: 14px; margin-top: 4px;">創建任務數據模型</div>
                                </div>
                                <div style="display: flex; gap: 8px; align-items: center;">
                                    <span style="padding: 4px 8px; background: rgba(239, 68, 68, 0.2); border: 1px solid #ef4444; border-radius: 4px; color: #ef4444; font-size: 12px;">P0</span>
                                    <span style="padding: 4px 8px; background: rgba(59, 130, 246, 0.2); border: 1px solid #3b82f6; border-radius: 4px; color: #3b82f6; font-size: 12px;">進行中</span>
                                </div>
                            </div>
                        </div>
                        <div style="background: rgba(15, 23, 42, 0.5); padding: 16px; border-radius: 8px; border: 1px solid #475569;">
                            <div style="display: flex; justify-content: space-between; align-items: start;">
                                <div>
                                    <div style="color: white; font-weight: bold;">TASK-101</div>
                                    <div style="color: #94a3b8; font-size: 14px; margin-top: 4px;">創建Sprint數據模型</div>
                                </div>
                                <div style="display: flex; gap: 8px; align-items: center;">
                                    <span style="padding: 4px 8px; background: rgba(239, 68, 68, 0.2); border: 1px solid #ef4444; border-radius: 4px; color: #ef4444; font-size: 12px;">P0</span>
                                    <span style="padding: 4px 8px; background: rgba(251, 191, 36, 0.2); border: 1px solid #fbbf24; border-radius: 4px; color: #fbbf24; font-size: 12px;">待開始</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        } else if (route === '/backtest') {
            content.innerHTML = `
                <h1 style="color: white; font-size: 32px; font-weight: bold; margin-bottom: 24px;">Strategy Backtest</h1>
                <p style="color: #94a3b8; margin-bottom: 32px;">Run and analyze trading strategy performance</p>

                <!-- Backtest Form -->
                <div style="background: rgba(30, 41, 59, 0.7); padding: 32px; border-radius: 12px; border: 1px solid #334155; margin-bottom: 24px;">
                    <h2 style="color: white; font-size: 24px; margin-bottom: 24px;">📊 Backtest Configuration</h2>

                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 24px; margin-bottom: 24px;">
                        <!-- Stock Input -->
                        <div style="display: flex; flex-direction: column;">
                            <label style="color: #94a3b8; font-size: 14px; margin-bottom: 8px;">Stock Symbol</label>
                            <input type="text" id="stockSymbol" placeholder="e.g., 0700.HK, 0388.HK" value="0700.HK"
                                style="background: rgba(15, 23, 42, 0.5); border: 1px solid #475569; border-radius: 8px; padding: 12px; color: white; font-size: 16px; outline: none; transition: border-color 0.2s;"
                                onfocus="this.style.borderColor='#3b82f6'"
                                onblur="this.style.borderColor='#475569'">
                        </div>

                        <!-- Strategy Selection -->
                        <div style="display: flex; flex-direction: column;">
                            <label style="color: #94a3b8; font-size: 14px; margin-bottom: 8px;">Strategy</label>
                            <select id="strategy" style="background: rgba(15, 23, 42, 0.5); border: 1px solid #475569; border-radius: 8px; padding: 12px; color: white; font-size: 16px; outline: none; transition: border-color 0.2s;"
                                onfocus="this.style.borderColor='#3b82f6'"
                                onblur="this.style.borderColor='#475569'">
                                <optgroup label="📈 基础指标">
                                    <option value="ma">MA (Moving Average)</option>
                                    <option value="rsi">RSI (Relative Strength Index)</option>
                                    <option value="macd">MACD</option>
                                    <option value="bollinger">BB (Bollinger Bands)</option>
                                </optgroup>
                                <optgroup label="🎯 高级指标">
                                    <option value="kdj">KDJ (Stochastic)</option>
                                    <option value="cci">CCI (Commodity Channel Index)</option>
                                    <option value="adx">ADX (Average Directional Index)</option>
                                    <option value="atr">ATR (Average True Range)</option>
                                    <option value="obv">OBV (On-Balance Volume)</option>
                                    <option value="ichimoku">Ichimoku Cloud</option>
                                    <option value="parabolic_sar">Parabolic SAR</option>
                                </optgroup>
                            </select>
                        </div>
                    </div>

                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 24px; margin-bottom: 24px;">
                        <!-- Start Date -->
                        <div style="display: flex; flex-direction: column;">
                            <label style="color: #94a3b8; font-size: 14px; margin-bottom: 8px;">Start Date</label>
                            <input type="date" id="startDate" value="2022-01-01"
                                style="background: rgba(15, 23, 42, 0.5); border: 1px solid #475569; border-radius: 8px; padding: 12px; color: white; font-size: 16px; outline: none; transition: border-color 0.2s;">
                        </div>

                        <!-- End Date -->
                        <div style="display: flex; flex-direction: column;">
                            <label style="color: #94a3b8; font-size: 14px; margin-bottom: 8px;">End Date</label>
                            <input type="date" id="endDate" value="2024-01-01"
                                style="background: rgba(15, 23, 42, 0.5); border: 1px solid #475569; border-radius: 8px; padding: 12px; color: white; font-size: 16px; outline: none; transition: border-color 0.2s;">
                        </div>

                        <!-- Initial Capital -->
                        <div style="display: flex; flex-direction: column;">
                            <label style="color: #94a3b8; font-size: 14px; margin-bottom: 8px;">Initial Capital</label>
                            <input type="number" id="capital" value="1000000" placeholder="1000000"
                                style="background: rgba(15, 23, 42, 0.5); border: 1px solid #475569; border-radius: 8px; padding: 12px; color: white; font-size: 16px; outline: none; transition: border-color 0.2s;">
                        </div>
                    </div>

                    <!-- Advanced Options -->
                    <div style="background: rgba(15, 23, 42, 0.3); padding: 20px; border-radius: 8px; border: 1px solid #475569; margin-bottom: 24px;">
                        <h3 style="color: white; font-size: 18px; margin-bottom: 16px;">⚙️ Advanced Options</h3>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 16px;">
                            <!-- Parameter Optimization -->
                            <label style="display: flex; align-items: center; gap: 12px; cursor: pointer;">
                                <input type="checkbox" id="optimizeParams" style="width: 20px; height: 20px; cursor: pointer;">
                                <span style="color: #94a3b8; font-size: 14px;">🔧 Optimize Parameters</span>
                            </label>

                            <!-- Show Trade Details -->
                            <label style="display: flex; align-items: center; gap: 12px; cursor: pointer;">
                                <input type="checkbox" id="showTradeDetails" checked style="width: 20px; height: 20px; cursor: pointer;">
                                <span style="color: #94a3b8; font-size: 14px;">📋 Show Trade Details</span>
                            </label>

                            <!-- Include Non-Price Data -->
                            <label style="display: flex; align-items: center; gap: 12px; cursor: pointer;">
                                <input type="checkbox" id="includeNonPrice" checked style="width: 20px; height: 20px; cursor: pointer;">
                                <span style="color: #94a3b8; font-size: 14px;">📊 Include Non-Price Data (GOV/HKEX)</span>
                            </label>
                        </div>
                    </div>

                    <!-- Run Button -->
                    <button onclick="runBacktest()" id="runButton"
                        style="width: 100%; padding: 14px 24px; background: linear-gradient(135deg, #8b5cf6, #a78bfa); color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; transition: all 0.2s; box-shadow: 0 4px 6px rgba(0,0,0,0.1);"
                        onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 12px rgba(0,0,0,0.15)'"
                        onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 6px rgba(0,0,0,0.1)'">
                        🚀 Run Backtest
                    </button>
                </div>

                <!-- Results Container -->
                <div id="resultsContainer" style="display: none;">
                    <h2 style="color: white; font-size: 24px; margin-bottom: 16px;">📈 Backtest Results</h2>
                    <div id="results"></div>
                </div>
            `;
        } else if (route === '/risk') {
            content.innerHTML = `
                <h1 style="color: white; font-size: 32px; font-weight: bold; margin-bottom: 24px;">Risk Management</h1>
                <p style="color: #94a3b8; margin-bottom: 32px;">Monitor portfolio risk metrics</p>
                <div style="background: rgba(30, 41, 59, 0.7); padding: 24px; border-radius: 12px; border: 1px solid #334155;">
                    <h2 style="color: white; font-size: 20px; margin-bottom: 16px;">🛡️ Risk Metrics</h2>
                    <p style="color: #94a3b8;">Risk management interface will be available here.</p>
                </div>
            `;
        } else if (route === '/trading') {
            content.innerHTML = `
                <h1 style="color: white; font-size: 32px; font-weight: bold; margin-bottom: 24px;">Trading Interface</h1>
                <p style="color: #94a3b8; margin-bottom: 32px;">Execute trades and manage positions</p>
                <div style="background: rgba(30, 41, 59, 0.7); padding: 24px; border-radius: 12px; border: 1px solid #334155;">
                    <h2 style="color: white; font-size: 20px; margin-bottom: 16px;">📊 Trading Panel</h2>
                    <p style="color: #94a3b8;">Trading interface will be available here.</p>
                </div>
            `;
        } else {
            content.innerHTML = '<h1 style="color: white;">404 - Page Not Found</h1>';
        }
    });

    // Backtest function
    window.runBacktest = function() {
        const button = document.getElementById('runButton');
        const resultsContainer = document.getElementById('resultsContainer');
        const resultsDiv = document.getElementById('results');

        // Get form values
        const symbol = document.getElementById('stockSymbol').value;
        const strategy = document.getElementById('strategy').value;
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;
        const capital = parseFloat(document.getElementById('capital').value);

        // Get advanced options
        const optimizeParams = document.getElementById('optimizeParams').checked;
        const showTradeDetails = document.getElementById('showTradeDetails').checked;
        const includeNonPrice = document.getElementById('includeNonPrice').checked;

        // Validate input
        if (!symbol || !startDate || !endDate || !capital) {
            alert('Please fill in all fields');
            return;
        }

        // Show loading
        button.innerHTML = optimizeParams ? '🔧 Optimizing Parameters...' : '⏳ Running Backtest...';
        button.disabled = true;
        button.style.opacity = '0.7';

        // Simulate backtest with longer delay for optimization
        const delay = optimizeParams ? 4000 : 2000;
        setTimeout(() => {
            // Generate simulated results
            const finalValue = capital * (1 + (Math.random() * 0.3 - 0.1));
            const totalReturn = ((finalValue - capital) / capital * 100).toFixed(2);
            const trades = Math.floor(Math.random() * 50) + 10;
            const wins = Math.floor(trades * (0.4 + Math.random() * 0.3));
            const winRate = (wins / trades * 100).toFixed(1);

            let resultsHTML = `
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 24px;">
                    <div style="background: rgba(30, 41, 59, 0.7); padding: 20px; border-radius: 12px; border: 1px solid #334155;">
                        <div style="color: #94a3b8; font-size: 14px; margin-bottom: 8px;">Final Value</div>
                        <div style="font-size: 28px; font-weight: bold; color: ${totalReturn >= 0 ? '#4ade80' : '#ef4444'}">$${finalValue.toLocaleString('en-US', {maximumFractionDigits: 2})}</div>
                    </div>
                    <div style="background: rgba(30, 41, 59, 0.7); padding: 20px; border-radius: 12px; border: 1px solid #334155;">
                        <div style="color: #94a3b8; font-size: 14px; margin-bottom: 8px;">Total Return</div>
                        <div style="font-size: 28px; font-weight: bold; color: ${totalReturn >= 0 ? '#4ade80' : '#ef4444'}">${totalReturn}%</div>
                    </div>
                    <div style="background: rgba(30, 41, 59, 0.7); padding: 20px; border-radius: 12px; border: 1px solid #334155;">
                        <div style="color: #94a3b8; font-size: 14px; margin-bottom: 8px;">Total Trades</div>
                        <div style="font-size: 28px; font-weight: bold; color: white">${trades}</div>
                    </div>
                    <div style="background: rgba(30, 41, 59, 0.7); padding: 20px; border-radius: 12px; border: 1px solid #334155;">
                        <div style="color: #94a3b8; font-size: 14px; margin-bottom: 8px;">Win Rate</div>
                        <div style="font-size: 28px; font-weight: bold; color: #3b82f6">${winRate}%</div>
                    </div>
                </div>

                <div style="background: rgba(30, 41, 59, 0.7); padding: 24px; border-radius: 12px; border: 1px solid #334155; margin-bottom: 24px;">
                    <h3 style="color: white; font-size: 18px; margin-bottom: 16px;">📊 Backtest Summary</h3>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; color: #94a3b8;">
                        <div><strong style="color: white;">Stock:</strong> ${symbol}</div>
                        <div><strong style="color: white;">Strategy:</strong> ${strategy.toUpperCase()}</div>
                        <div><strong style="color: white;">Period:</strong> ${startDate} to ${endDate}</div>
                        <div><strong style="color: white;">Initial Capital:</strong> $${capital.toLocaleString()}</div>
                    </div>
                </div>
            `;

            // Parameter Optimization Results
            if (optimizeParams) {
                resultsHTML += `
                    <div style="background: rgba(16, 185, 129, 0.1); padding: 24px; border-radius: 12px; border: 1px solid #10b981; margin-bottom: 24px;">
                        <h3 style="color: #10b981; font-size: 20px; margin-bottom: 16px;">🔧 Parameter Optimization Results</h3>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px;">
                            <div style="background: rgba(15, 23, 42, 0.5); padding: 16px; border-radius: 8px;">
                                <div style="color: #94a3b8; font-size: 12px; margin-bottom: 4px;">Best Parameters</div>
                                <div style="color: white; font-weight: 600;">${getOptimalParams(strategy)}</div>
                            </div>
                            <div style="background: rgba(15, 23, 42, 0.5); padding: 16px; border-radius: 8px;">
                                <div style="color: #94a3b8; font-size: 12px; margin-bottom: 4px;">Combinations Tested</div>
                                <div style="color: white; font-weight: 600;">${getCombinationCount(strategy)}</div>
                            </div>
                            <div style="background: rgba(15, 23, 42, 0.5); padding: 16px; border-radius: 8px;">
                                <div style="color: #94a3b8; font-size: 12px; margin-bottom: 4px;">Best Sharpe Ratio</div>
                                <div style="color: #10b981; font-weight: 600;">${(1.2 + Math.random() * 0.8).toFixed(2)}</div>
                            </div>
                        </div>
                    </div>
                `;
            }

            // Trade Details
            if (showTradeDetails) {
                resultsHTML += `
                    <div style="background: rgba(30, 41, 59, 0.7); padding: 24px; border-radius: 12px; border: 1px solid #334155; margin-bottom: 24px;">
                        <h3 style="color: white; font-size: 20px; margin-bottom: 16px;">📋 Trade Details</h3>
                        <div style="overflow-x: auto;">
                            <table style="width: 100%; border-collapse: collapse;">
                                <thead>
                                    <tr style="background: rgba(15, 23, 42, 0.5);">
                                        <th style="padding: 12px; text-align: left; color: #94a3b8; font-size: 12px;">#</th>
                                        <th style="padding: 12px; text-align: left; color: #94a3b8; font-size: 12px;">Date/Time</th>
                                        <th style="padding: 12px; text-align: left; color: #94a3b8; font-size: 12px;">Type</th>
                                        <th style="padding: 12px; text-align: right; color: #94a3b8; font-size: 12px;">Price</th>
                                        <th style="padding: 12px; text-align: right; color: #94a3b8; font-size: 12px;">Qty</th>
                                        <th style="padding: 12px; text-align: right; color: #94a3b8; font-size: 12px;">PnL</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${generateTradeDetails(trades, startDate, endDate)}
                                </tbody>
                            </table>
                        </div>
                    </div>
                `;
            }

            // Non-Price Data
            if (includeNonPrice) {
                resultsHTML += `
                    <div style="background: rgba(59, 130, 246, 0.1); padding: 24px; border-radius: 12px; border: 1px solid #3b82f6; margin-bottom: 24px;">
                        <h3 style="color: #3b82f6; font-size: 20px; margin-bottom: 16px;">📊 Non-Price Data (GOV/HKEX)</h3>
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px;">
                            ${generateNonPriceData()}
                        </div>
                    </div>
                `;
            }

            resultsDiv.innerHTML = resultsHTML;
            resultsContainer.style.display = 'block';
            resultsContainer.scrollIntoView({ behavior: 'smooth' });

            // Reset button
            button.innerHTML = '🚀 Run Backtest';
            button.disabled = false;
            button.style.opacity = '1';

        }, delay);
    };

    // Helper function to get optimal parameters
    function getOptimalParams(strategy) {
        const params = {
            'ma': 'Period: 20, Signal: 50',
            'rsi': 'Period: 14, Overbought: 70, Oversold: 30',
            'macd': 'Fast: 12, Slow: 26, Signal: 9',
            'bollinger': 'Period: 20, StdDev: 2',
            'kdj': 'K: 9, D: 3, Overbought: 80, Oversold: 20',
            'cci': 'Period: 20, Overbought: 100, Oversold: -100',
            'adx': 'Period: 14, Threshold: 25',
            'atr': 'Period: 14, Multiplier: 2.0',
            'obv': 'Period: 20',
            'ichimoku': 'Conv: 9, Base: 26, Span: 52',
            'parabolic_sar': 'AF: 0.02, Max AF: 0.2'
        };
        return params[strategy] || 'Default Parameters';
    }

    // Helper function to get combination count
    function getCombinationCount(strategy) {
        const counts = {
            'ma': '120',
            'rsi': '80',
            'macd': '60',
            'bollinger': '40',
            'kdj': '400',
            'cci': '100',
            'adx': '32',
            'atr': '50',
            'obv': '10',
            'ichimoku': '27',
            'parabolic_sar': '150'
        };
        return counts[strategy] || '100';
    }

    // Helper function to generate trade details
    function generateTradeDetails(tradeCount, startDate, endDate) {
        let trades = '';
        const start = new Date(startDate);
        const end = new Date(endDate);
        const timeDiff = end.getTime() - start.getTime();

        for (let i = 1; i <= Math.min(tradeCount, 10); i++) {
            const tradeDate = new Date(start.getTime() + (timeDiff * i / tradeCount));
            const type = i % 2 === 0 ? 'SELL' : 'BUY';
            const price = (350 + Math.random() * 100).toFixed(2);
            const qty = Math.floor(1000 + Math.random() * 5000);
            const pnl = ((Math.random() - 0.3) * 10000).toFixed(0);
            const pnlColor = pnl >= 0 ? '#4ade80' : '#ef4444';

            trades += `
                <tr style="border-bottom: 1px solid #334155;">
                    <td style="padding: 12px; color: #94a3b8; font-size: 13px;">${i}</td>
                    <td style="padding: 12px; color: #e2e8f0; font-size: 13px;">${tradeDate.toLocaleDateString()} ${tradeDate.toLocaleTimeString()}</td>
                    <td style="padding: 12px; font-size: 13px;">
                        <span style="color: ${type === 'BUY' ? '#3b82f6' : '#ef4444'}; font-weight: 600;">${type}</span>
                    </td>
                    <td style="padding: 12px; color: #e2e8f0; font-size: 13px; text-align: right;">$${price}</td>
                    <td style="padding: 12px; color: #e2e8f0; font-size: 13px; text-align: right;">${qty.toLocaleString()}</td>
                    <td style="padding: 12px; color: ${pnlColor}; font-size: 13px; text-align: right; font-weight: 600;">${pnl >= 0 ? '+' : ''}$${pnl}</td>
                </tr>
            `;
        }

        if (tradeCount > 10) {
            trades += `
                <tr>
                    <td colspan="6" style="padding: 12px; text-align: center; color: #94a3b8; font-size: 12px;">
                        ... and ${tradeCount - 10} more trades
                    </td>
                </tr>
            `;
        }

        return trades;
    }

    // Helper function to generate non-price data
    function generateNonPriceData() {
        return `
            <div style="background: rgba(15, 23, 42, 0.5); padding: 16px; border-radius: 8px;">
                <h4 style="color: white; font-size: 14px; margin-bottom: 12px;">🏛️ GOV Data</h4>
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span style="color: #94a3b8; font-size: 12px;">Interest Rate:</span>
                    <span style="color: white; font-size: 12px;">5.25%</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span style="color: #94a3b8; font-size: 12px;">Inflation Rate:</span>
                    <span style="color: white; font-size: 12px;">2.1%</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: #94a3b8; font-size: 12px;">GDP Growth:</span>
                    <span style="color: #4ade80; font-size: 12px;">+3.5%</span>
                </div>
            </div>

            <div style="background: rgba(15, 23, 42, 0.5); padding: 16px; border-radius: 8px;">
                <h4 style="color: white; font-size: 14px; margin-bottom: 12px;">📈 HKEX Data</h4>
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span style="color: #94a3b8; font-size: 12px;">Volume:</span>
                    <span style="color: white; font-size: 12px;">125.6B</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span style="color: #94a3b8; font-size: 12px;">Turnover:</span>
                    <span style="color: white; font-size: 12px;">$89.2B</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: #94a3b8; font-size: 12px;">HSI:</span>
                    <span style="color: #4ade80; font-size: 12px;">17,245</span>
                </div>
            </div>

            <div style="background: rgba(15, 23, 42, 0.5); padding: 16px; border-radius: 8px;">
                <h4 style="color: white; font-size: 14px; margin-bottom: 12px;">💰 HIBOR Rates</h4>
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span style="color: #94a3b8; font-size: 12px;">Overnight:</span>
                    <span style="color: white; font-size: 12px;">3.85%</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span style="color: #94a3b8; font-size: 12px;">1M:</span>
                    <span style="color: white; font-size: 12px;">4.12%</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: #94a3b8; font-size: 12px;">3M:</span>
                    <span style="color: white; font-size: 12px;">4.35%</span>
                </div>
            </div>

            <div style="background: rgba(15, 23, 42, 0.5); padding: 16px; border-radius: 8px;">
                <h4 style="color: white; font-size: 14px; margin-bottom: 12px;">🏘️ Property Data</h4>
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span style="color: #94a3b8; font-size: 12px;">Price Index:</span>
                    <span style="color: white; font-size: 12px;">165.3</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span style="color: #94a3b8; font-size: 12px;">Transactions:</span>
                    <span style="color: white; font-size: 12px;">8,542</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: #94a3b8; font-size: 12px;">YoY Change:</span>
                    <span style="color: #4ade80; font-size: 12px;">+5.2%</span>
                </div>
            </div>
        `;
    };

    // ============================================================================
    // Agent Management Functions
    // ============================================================================

    // Control individual agent
    window.controlAgent = function(agentId, action) {
        const agentNames = {
            'coordinator': 'Coordinator Agent',
            'data_scientist': 'Data Scientist Agent',
            'quantitative_analyst': 'Quantitative Analyst Agent',
            'quantitative_engineer': 'Quantitative Engineer Agent',
            'portfolio_manager': 'Portfolio Manager Agent',
            'research_analyst': 'Research Analyst Agent',
            'risk_analyst': 'Risk Analyst Agent'
        };

        const agentName = agentNames[agentId] || agentId;
        const actionText = action === 'stop' ? 'stopped' : 'started';

        if (confirm(`Are you sure you want to ${action} ${agentName}?`)) {
            console.log(`✅ ${agentName} ${actionText} successfully`);

            // Show temporary notification
            const notification = document.createElement('div');
            notification.style.cssText = `
                position: fixed; top: 20px; right: 20px; z-index: 9999;
                background: rgba(16, 185, 129, 0.9); color: white;
                padding: 16px 24px; border-radius: 8px; font-weight: 600;
                box-shadow: 0 4px 12px rgba(0,0,0,0.2); animation: slideIn 0.3s ease;
            `;
            notification.textContent = `✅ ${agentName} ${actionText} successfully!`;
            document.body.appendChild(notification);

            // Remove notification after 3 seconds
            setTimeout(() => {
                notification.style.animation = 'slideOut 0.3s ease';
                setTimeout(() => notification.remove(), 300);
            }, 3000);
        }
    };

    // View agent logs
    window.viewAgentLogs = function(agentId) {
        const agentNames = {
            'coordinator': 'Coordinator Agent',
            'data_scientist': 'Data Scientist Agent',
            'quantitative_analyst': 'Quantitative Analyst Agent',
            'quantitative_engineer': 'Quantitative Engineer Agent',
            'portfolio_manager': 'Portfolio Manager Agent',
            'research_analyst': 'Research Analyst Agent',
            'risk_analyst': 'Risk Analyst Agent'
        };

        const agentName = agentNames[agentId] || agentId;
        console.log(`📋 Viewing logs for ${agentName}`);

        // Simulate log display
        const logs = [
            `[${new Date().toLocaleTimeString()}] INFO: Agent ${agentName} initialized`,
            `[${new Date().toLocaleTimeString()}] INFO: Connected to message queue`,
            `[${new Date().toLocaleTimeString()}] INFO: Processing messages...`,
            `[${new Date().toLocaleTimeString()}] DEBUG: Heartbeat sent`,
            `[${new Date().toLocaleTimeString()}] INFO: Status: Running`
        ];

        const logWindow = window.open('', '_blank', 'width=600,height=400');
        logWindow.document.write(`
            <html>
                <head>
                    <title>${agentName} Logs</title>
                    <style>
                        body { background: #1e293b; color: #e2e8f0; font-family: 'Courier New', monospace; padding: 20px; margin: 0; }
                        h2 { color: #3b82f6; margin-top: 0; }
                        .log-entry { margin-bottom: 8px; }
                        .info { color: #3b82f6; }
                        .debug { color: #94a3b8; }
                        .error { color: #ef4444; }
                    </style>
                </head>
                <body>
                    <h2>📋 ${agentName} Logs</h2>
                    ${logs.map(log => `<div class="log-entry info">${log}</div>`).join('')}
                </body>
            </html>
        `);
    };

    // Start all agents
    window.startAllAgents = function() {
        if (confirm('Are you sure you want to start all agents?')) {
            console.log('✅ All agents started successfully');

            const notification = document.createElement('div');
            notification.style.cssText = `
                position: fixed; top: 20px; right: 20px; z-index: 9999;
                background: rgba(16, 185, 129, 0.9); color: white;
                padding: 16px 24px; border-radius: 8px; font-weight: 600;
                box-shadow: 0 4px 12px rgba(0,0,0,0.2); animation: slideIn 0.3s ease;
            `;
            notification.textContent = '✅ All agents started successfully!';
            document.body.appendChild(notification);

            setTimeout(() => {
                notification.style.animation = 'slideOut 0.3s ease';
                setTimeout(() => notification.remove(), 300);
            }, 3000);
        }
    };

    // Stop all agents
    window.stopAllAgents = function() {
        if (confirm('Are you sure you want to stop all agents? This will halt all trading operations.')) {
            console.log('⏹️ All agents stopped');

            const notification = document.createElement('div');
            notification.style.cssText = `
                position: fixed; top: 20px; right: 20px; z-index: 9999;
                background: rgba(239, 68, 68, 0.9); color: white;
                padding: 16px 24px; border-radius: 8px; font-weight: 600;
                box-shadow: 0 4px 12px rgba(0,0,0,0.2); animation: slideIn 0.3s ease;
            `;
            notification.textContent = '⏹️ All agents stopped!';
            document.body.appendChild(notification);

            setTimeout(() => {
                notification.style.animation = 'slideOut 0.3s ease';
                setTimeout(() => notification.remove(), 300);
            }, 3000);
        }
    };

    // Restart all agents
    window.restartAllAgents = function() {
        if (confirm('Are you sure you want to restart all agents? This will reset all agent states.')) {
            console.log('🔄 All agents restarting...');

            const notification = document.createElement('div');
            notification.style.cssText = `
                position: fixed; top: 20px; right: 20px; z-index: 9999;
                background: rgba(245, 158, 11, 0.9); color: white;
                padding: 16px 24px; border-radius: 8px; font-weight: 600;
                box-shadow: 0 4px 12px rgba(0,0,0,0.2); animation: slideIn 0.3s ease;
            `;
            notification.textContent = '🔄 All agents restarting...';
            document.body.appendChild(notification);

            setTimeout(() => {
                notification.style.animation = 'slideOut 0.3s ease';
                setTimeout(() => notification.remove(), 300);
            }, 3000);
        }
    };

    // View system logs
    window.viewSystemLogs = function() {
        console.log('📋 Viewing system logs');

        const logs = [
            `[${new Date().toLocaleTimeString()}] INFO: CODEX Trading System initialized`,
            `[${new Date().toLocaleTimeString()}] INFO: Loading 7 AI agents`,
            `[${new Date().toLocaleTimeString()}] INFO: Coordinator Agent started`,
            `[${new Date().toLocaleTimeString()}] INFO: Data Scientist Agent started`,
            `[${new Date().toLocaleTimeString()}] INFO: Quantitative Analyst Agent started`,
            `[${new Date().toLocaleTimeString()}] INFO: Quantitative Engineer Agent started`,
            `[${new Date().toLocaleTimeString()}] INFO: Portfolio Manager Agent started`,
            `[${new Date().toLocaleTimeString()}] INFO: Research Analyst Agent started`,
            `[${new Date().toLocaleTimeString()}] INFO: Risk Analyst Agent started`,
            `[${new Date().toLocaleTimeString()}] INFO: All agents operational`,
            `[${new Date().toLocaleTimeString()}] DEBUG: Message queue initialized`,
            `[${new Date().toLocaleTimeString()}] INFO: System health: 98%`
        ];

        const logWindow = window.open('', '_blank', 'width=800,height=600');
        logWindow.document.write(`
            <html>
                <head>
                    <title>System Logs</title>
                    <style>
                        body { background: #1e293b; color: #e2e8f0; font-family: 'Courier New', monospace; padding: 20px; margin: 0; }
                        h2 { color: #3b82f6; margin-top: 0; }
                        .log-entry { margin-bottom: 8px; }
                        .info { color: #3b82f6; }
                        .debug { color: #94a3b8; }
                        .error { color: #ef4444; }
                        .warning { color: #fbbf24; }
                    </style>
                </head>
                <body>
                    <h2>📋 System Logs - CODEX Trading System</h2>
                    ${logs.map(log => `<div class="log-entry info">${log}</div>`).join('')}
                </body>
            </html>
        `);
    };

    // ========================================================================
    // 任務看板實際功能
    // ========================================================================

    // 查看所有任務
    window.viewAllTasks = function() {
        console.log('📋 正在獲取所有任務...');
        fetch('http://localhost:8000/tasks')
            .then(response => response.json())
            .then(tasks => {
                const taskList = tasks.map(task => `
                    <tr style="border-bottom: 1px solid #334155;">
                        <td style="padding: 8px; color: #94a3b8; font-size: 12px;">${task.id}</td>
                        <td style="padding: 8px; color: #e2e8f0; font-size: 13px;">${task.title}</td>
                        <td style="padding: 8px; font-size: 12px;">
                            <span style="padding: 2px 6px; border-radius: 4px; background: ${task.priority === 'P0' ? 'rgba(239,68,68,0.2)' : task.priority === 'P1' ? 'rgba(251,191,36,0.2)' : 'rgba(59,130,246,0.2)'}; color: ${task.priority === 'P0' ? '#ef4444' : task.priority === 'P1' ? '#fbbf24' : '#3b82f6'}">${task.priority}</span>
                        </td>
                        <td style="padding: 8px; font-size: 12px;">
                            <span style="padding: 2px 6px; border-radius: 4px; background: ${task.is_completed ? 'rgba(74,222,128,0.2)' : task.status === '進行中' ? 'rgba(59,130,246,0.2)' : 'rgba(251,191,36,0.2)'}; color: ${task.is_completed ? '#4ade80' : task.status === '進行中' ? '#3b82f6' : '#fbbf24'}">${task.is_completed ? '已完成' : task.status}</span>
                        </td>
                    </tr>
                `).join('');

                const modal = window.open('', '_blank', 'width=1000,height=600,scrollbars=yes');
                modal.document.write(`
                    <html>
                        <head>
                            <title>所有任務列表</title>
                            <style>
                                body { background: #1e293b; color: #e2e8f0; font-family: 'Inter', sans-serif; padding: 20px; margin: 0; }
                                h1 { color: #3b82f6; margin-top: 0; }
                                table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                                th { background: rgba(15, 23, 42, 0.5); padding: 12px; text-align: left; color: #94a3b8; font-size: 12px; font-weight: 600; }
                                tr:hover { background: rgba(59, 130, 246, 0.1); }
                                .close-btn { position: fixed; top: 20px; right: 20px; padding: 10px 20px; background: #ef4444; color: white; border: none; border-radius: 6px; cursor: pointer; }
                            </style>
                        </head>
                        <body>
                            <button class="close-btn" onclick="window.close()">✕ 關閉</button>
                            <h1>📋 所有任務列表 (${tasks.length}個)</h1>
                            <table>
                                <thead>
                                    <tr>
                                        <th>任務ID</th>
                                        <th>標題</th>
                                        <th>優先級</th>
                                        <th>狀態</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${taskList}
                                </tbody>
                            </table>
                        </body>
                    </html>
                `);
            })
            .catch(error => {
                alert('❌ 獲取任務失敗: ' + error.message);
            });
    };

    // 打開任務看板 (跳轉到演示版)
    window.openTaskBoard = function() {
        console.log('🎯 正在打開任務看板...');
        window.open('http://localhost:8001/task-board-demo.html', '_blank');
    };

    // 打開互動模式 (跳轉到API版)
    window.openTaskAPI = function() {
        console.log('⚡ 正在打開互動模式...');
        window.open('http://localhost:8001/task-board-api.html', '_blank');
    };
});
