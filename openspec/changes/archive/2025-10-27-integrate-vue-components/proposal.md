# OpenSpec Proposal: Integrate Vue Components into Dashboard

**Change ID**: `integrate-vue-components`
**Status**: COMPLETED
**Priority**: CRITICAL
**Scope**: Frontend + Backend
**Estimated Duration**: 3-5 days
**Created**: 2025-10-27
**Author**: Claude Code

## Why

The CODEX Trading Dashboard has a **critical functionality gap**: while 19 Vue components (~147 KB) have been implemented for advanced features (backtesting, agent management, risk dashboard, trading interface), they are **not integrated into the HTML page**. Currently, the dashboard only shows 7 basic features using vanilla JavaScript, representing **70% functionality loss**.

## What Changes

This proposal implements a **complete Vue 3 application** that integrates all existing components and unlocks 16 missing features:

### 1. Vue Application Integration
- Initialize Vue 3 application with Composition API
- Integrate all 19 existing Vue components
- Configure Vue Router for navigation
- Set up Pinia for state management

### 2. Static File Service Configuration
- Configure FastAPI StaticFiles middleware
- Enable serving of `.vue` components and assets
- Support for ES6 modules and Vue SFC

## Status
✅ IMPLEMENTED AND ARCHIVED

