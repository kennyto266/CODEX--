## ADDED Requirements

### Requirement: System MUST Bot MUST support new commands
Telegram Bot MUST support 7 new commands including portfolio management, analysis features, notification system, AI CLI, web scraping, weather query, and auto-reply.

#### Scenario: User queries help information
- **WHEN** user sends `/help` command
- **THEN** system returns complete help information with all 14 original and 7 new commands

#### Scenario: Register new Bot commands
- **WHEN** Bot initializes
- **THEN** system MUST register 21 commands (14 original + 7 new) to Telegram

### Requirement: System MUST System MUST detect message types
Bot MUST be able to detect different types of messages including commands, tags (@username), reply messages, etc.

#### Scenario: Detect tag messages
- **WHEN** user tags @penguin8n in a group
- **THEN** Bot detects the tag and triggers auto-reply functionality

#### Scenario: Process command messages
- **WHEN** user sends command starting with `/`
- **THEN** Bot parses the command and routes to the appropriate handler

### Requirement: System MUST System MUST enhance error handling
Bot MUST provide comprehensive error handling mechanisms for new features.

#### Scenario: API call failure
- **WHEN** external API call times out or returns error
- **THEN** Bot logs the error and returns a user-friendly error message

#### Scenario: Missing dependencies
- **WHEN** user tries to use features requiring optional dependencies (e.g., Chrome MCP)
- **THEN** Bot detects and prompts user to install necessary dependencies

## MODIFIED Requirements

### Requirement: System MUST help_cmd function MUST be extended
Existing help_cmd function MUST be extended to include descriptions of new commands.

#### Scenario: Display new command help
- **WHEN** user executes `/help` command
- **THEN** system MUST display descriptions of the following new commands:
  - `/portfolio` - Portfolio management
  - `/heatmap` - Stock heatmap analysis
  - `/alert` - Price alert setup
  - `/ai` - AI CLI command
  - `/tft` - TFT rankings
  - `/weather` - Hong Kong weather

### Requirement: System MUST post_init function MUST be extended
post_init function MUST be extended to register new BotCommand entries.

#### Scenario: Register all commands
- **WHEN** Bot starts and executes post_init
- **THEN** system MUST register all 21 commands (14 original + 7 new) to Telegram

### Requirement: Message processing flow MUST support new types
Message processing flow MUST support new message types (tag detection, reply detection).

#### Scenario: Process tag messages
- **WHEN** message containing @penguin8n is received
- **THEN** system MUST trigger auto-reply and send AI agent message

#### Scenario: Process normal messages
- **WHEN** message that doesn't match any command or tag is received
- **THEN** system MUST ignore the message or return default reply
