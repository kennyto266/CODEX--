# Web Exploration Specification - Chrome MCP Integration

## Overview

Define the integration of Chrome MCP (Model Context Protocol) for automated web exploration to discover and analyze potential data sources for the gov_crawler system.

## ADDED Requirements

### Requirement: Chrome MCP Browser Automation

Implement automated web browsing and analysis using Chrome DevTools MCP for discovering data sources.

#### Scenario: Exploring Hong Kong Government Data Portal
- **Given**: Target website https://data.gov.hk/ for data discovery
- **When**: `WebExplorer.explore_site(url)` is executed using Chrome MCP
- **Then**: Browser navigates to the site, analyzes page structure, identifies data APIs
- **And**: System catalogs available datasets, formats, and access methods

#### Scenario: API Endpoint Detection
- **Given**: Web page containing data tables or API documentation
- **When**: Chrome MCP performs automated analysis
- **Then**: System detects API endpoints, data formats (JSON/CSV/XML), and authentication requirements
- **And**: Generates API specification report with usage examples

#### Scenario: Dynamic Content Analysis
- **Given**: Website with JavaScript-rendered content or AJAX-loaded data
- **When**: Chrome MCP waits for dynamic content to load
- **Then**: System captures full page state including dynamically loaded data
- **And**: Extracts data sources not visible in initial HTML

### Requirement: Multi-Site Data Source Discovery

Systematically explore multiple Hong Kong government and institutional websites to find relevant data sources.

#### Scenario: Financial Institution Website Analysis
- **Given**: Websites like HKMA (https://www.hkma.gov.hk/), C&SD (https://www.censtatd.gov.hk/)
- **When**: `WebExplorer.analyze_institutional_site(url)` runs
- **Then**: System identifies statistical releases, data APIs, downloadable reports
- **And**: Prioritizes sources based on data relevance to trading strategies

#### Scenario: Transportation and Border Data Discovery
- **Given**: Sites like MTR (https://www.mtr.com.hk/), Immigration (https://www.immd.gov.hk/)
- **When**: Automated exploration is performed
- **Then**: System discovers passenger statistics, border crossing data, traffic patterns
- **And**: Documents data update frequencies and access procedures

#### Scenario: Tourism and Visitor Data Sources
- **Given**: Tourism Board website (https://www.discoverhongkong.com/)
- **When**: Data exploration is executed
- **Then**: System locates visitor arrival statistics, hotel occupancy data, tourism trends
- **And**: Identifies both official APIs and downloadable datasets

### Requirement: Data Extraction Strategy Generation

Generate automated extraction strategies based on discovered website structures.

#### Scenario: API-First Strategy
- **Given**: Website with documented REST API
- **When**: Chrome MCP analyzes API documentation
- **Then**: System generates code snippet for API access
- **And**: Documents required parameters, authentication, and rate limits

#### Scenario: HTML Scraping Strategy
- **Given**: Website with data in HTML tables without API
- **When**: Analysis reveals table structures
- **Then**: System generates HTML parsing code using BeautifulSoup/Selenium
- **And**: Documents CSS selectors and data extraction patterns

#### Scenario: Download Link Detection
- **Given**: Website offering periodic CSV/Excel downloads
- **When**: Download links are identified
- **Then**: System catalogs direct download URLs and update schedules
- **And**: Generates automated download and processing scripts

#### Scenario: Webhook/Feed Discovery
- **Given**: Website offering RSS feeds or webhooks for data updates
- **When**: Feed URLs are discovered
- **Then**: System documents webhook endpoints and feed formats
- **And**: Creates integration code for real-time data subscriptions

### Requirement: Data Source Quality Assessment

Evaluate discovered data sources based on multiple criteria to prioritize implementation efforts.

#### Scenario: Completeness Assessment
- **Given**: Multiple potential sources for the same type of data
- **When**: Quality assessment is performed
- **Then**: System evaluates data completeness, historical coverage, update frequency
- **And**: Assigns quality scores to rank sources

#### Scenario: Accessibility Evaluation
- **Given**: Various data sources with different access requirements
- **When**: Accessibility analysis is done
- **Then**: System checks for free access, API keys needed, rate limits, authentication
- **And**: Documents barriers to access and mitigation strategies

#### Scenario: Reliability Scoring
- **Given**: Data sources with different reliability characteristics
- **When**: Reliability assessment runs
- **Then**: System evaluates historical uptime, data consistency, official backing
- **And**: Calculates reliability scores for source prioritization

#### Scenario: Relevance Scoring
- **Given**: Wide range of available data sources
- **When**: Relevance analysis is performed
- **Then**: System scores each source based on relevance to quantitative trading
- **And**: Creates ranked list of sources by trading relevance

### Requirement: Automated Documentation Generation

Generate comprehensive documentation for discovered data sources.

#### Scenario: Data Source Report Generation
- **Given**: Results from web exploration of multiple sites
- **When**: Report generation is triggered
- **Then**: System creates detailed report with source URLs, data types, access methods
- **And**: Includes sample data formats, update frequencies, and implementation notes

#### Scenario: Code Example Generation
- **Given**: Discovered API endpoints and data formats
- **When**: Code generation runs
- **Then**: System produces sample Python code for data access
- **And**: Includes error handling, rate limiting, and data processing examples

#### Scenario: Integration Roadmap Creation
- **Given**: Comprehensive list of discovered data sources
- **When**: Roadmap generation executes
- **Then**: System creates phased implementation plan
- **And**: Prioritizes sources by difficulty, value, and dependencies

## Technical Specifications

### Chrome MCP Integration

```python
class WebExplorer:
    """Web exploration using Chrome MCP"""

    async def explore_site(self, url: str) -> ExplorationResult:
        """Explore a website and discover data sources"""
        pass

    async def analyze_api_documentation(self, url: str) -> APISpec:
        """Analyze API documentation and extract specifications"""
        pass

    async def extract_data_samples(self, url: str) -> List[DataSample]:
        """Extract sample data from various sources on the page"""
        pass

    def generate_extraction_strategy(self, site_analysis: SiteAnalysis) -> ExtractionStrategy:
        """Generate data extraction strategy based on site analysis"""
        pass
```

### Exploration Output Format

```json
{
  "url": "https://example.gov.hk/data",
  "exploration_date": "2025-10-27",
  "data_sources": [
    {
      "name": "HIBOR Rates",
      "type": "API",
      "endpoint": "https://api.hkma.gov.hk/rates",
      "format": "JSON",
      "authentication": "none",
      "rate_limit": "1000/hour",
      "update_frequency": "daily",
      "sample_data": {...},
      "relevance_score": 9.5,
      "accessibility_score": 10,
      "reliability_score": 10
    }
  ],
  "extraction_strategies": [...],
  "documentation_links": [...],
  "implementation_notes": [...]
}
```

### Target Websites for Exploration

1. **data.gov.hk** - Hong Kong Government Open Data Portal
2. **hkma.gov.hk** - Hong Kong Monetary Authority
3. **censtatd.gov.hk** - Census and Statistics Department
4. **immd.gov.hk** - Immigration Department
5. **discoverhongkong.com** - Hong Kong Tourism Board
6. **mtr.com.hk** - MTR Corporation
7. **landreg.gov.hk** - Land Registry
8. **info.gov.hk** - Hong Kong Government News
9. **shd.com.hk** - Social Welfare Department (welfare indicators)
10. **tib.gov.hk** - Treasury (fiscal data)
11. **estb.gov.hk** - Education Bureau (education statistics)
12. **labour.gov.hk** - Labour Department (employment data)
13. **tcd.gov.hk** - Transport and Logistics (traffic data)
14. **thedg.org.hk** - Development Bureau (infrastructure data)
15. **housingauthority.gov.hk** - Housing Authority (housing data)

### Data Source Categories

1. **Financial Data** (HIGH PRIORITY)
   - Interest rates (HIBOR, LIBOR)
   - Exchange rates
   - Banking statistics
   - Market indices

2. **Economic Indicators** (HIGH PRIORITY)
   - GDP components
   - Inflation rates
   - Employment statistics
   - Trade statistics

3. **Real Estate** (MEDIUM PRIORITY)
   - Property prices
   - Transaction volumes
   - Rental yields
   - Construction activity

4. **Transportation** (MEDIUM PRIORITY)
   - Traffic volumes
   - Public transport usage
   - Border crossings
   - Aviation statistics

5. **Social Indicators** (LOW-MEDIUM PRIORITY)
   - Population statistics
   - Tourism arrivals
   - Retail sales
   - Consumer confidence

### Performance Requirements

- **Exploration Speed**: < 30 seconds per website
- **Concurrent Exploration**: Support 5 websites simultaneously
- **Data Source Discovery**: Identify minimum 50 data sources
- **Quality Assessment**: Score all discovered sources
- **Documentation**: Generate complete documentation for all sources
- **Automation**: Fully automated, no manual intervention required

### Output Deliverables

1. **Web Exploration Report** (PDF/Markdown)
   - Executive summary of findings
   - Detailed analysis of each website
   - Data source catalog with scores
   - Prioritized implementation roadmap

2. **Data Source Specifications** (JSON/YAML)
   - Structured format for programmatic use
   - API specifications
   - Access requirements
   - Sample data

3. **Extraction Code Templates** (Python)
   - Ready-to-use code snippets
   - Error handling examples
   - Best practices documentation

4. **Integration Guide** (Markdown)
   - Step-by-step implementation instructions
   - Dependency management
   - Testing strategies
