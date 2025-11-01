# Specification: Dashboard Agent Management

**Capability ID**: `dashboard-agent-management`

## ADDED Requirements

### Requirement: Agent Status Monitoring

The system SHALL provide users with real-time status and metrics of all 7 AI agents

#### Scenario: User monitors agent health
```
Given: User on Agents tab
When: Page loads
Then: Displays grid of 7 agent cards showing:
  - Agent name, role, status (online/offline)
  - CPU%, memory%, message queue depth
  - Last message timestamp
```

### Requirement: Agent Control

The system SHALL allow users to start, stop, and restart agents

#### Scenario: User stops a misbehaving agent
```
Given: Agent is running and processing slowly
When: User clicks "Stop" button on agent card
Then: Agent stops gracefully
  And: Status changes to "offline"
  And: Remaining messages are queued
```

### Requirement: Real-time Log Streaming

The system SHALL provide a WebSocket endpoint for real-time agent output

#### Scenario: User monitors agent logs
```
Given: Agent is running
When: User opens LogViewer for agent
Then: WebSocket /ws/agents/{id} connects
  And: Receives real-time log entries
  And: Displays in scrollable log viewer
```

## API Endpoints

- `GET /api/agents/list`
- `GET /api/agents/{id}/status`
- `POST /api/agents/{id}/start`
- `POST /api/agents/{id}/stop`
- `WS /ws/agents/{id}`

## Dependencies

- `src/agents/coordinator.py` (existing agent system)
- Database table: `agent_logs`
