# Phase 1 Quick Reference Guide

## 3-Component System for data.gov.hk Crawling

### Component 1: API Handler - Connection & Caching
**File**: `src/api_handler.py` | **Class**: `DataGovHKAPI`

#### Quick Start
```python
from src.api_handler import DataGovHKAPI

api = DataGovHKAPI(config)

# Check API is working
api.check_connectivity()  # ✓ True / ✗ False

# Crawl data (auto-caches responses)
result = api.crawl_finance_data()

# Get performance stats
stats = api.get_api_statistics()
print(f"Requests: {stats['total_requests']}, Cache: {stats['cached_responses']}")

# Clean shutdown
api.close()
```

#### Features
- ✅ Response caching (5-min TTL)
- ✅ Rate limiting (0.5s min between requests)
- ✅ Connection health checks
- ✅ Automatic retries (up to 3 attempts)
- ✅ Performance statistics

#### Key Methods
```python
api.check_connectivity()              # Validate API availability
api.fetch_data_from_url(name, url, format)  # Get data from URL
api.crawl_dataset_category(category)  # Crawl by category
api.search_datasets(query)            # Search available datasets
api.get_api_statistics()              # Get performance metrics
api.clear_cache()                     # Clear cached responses
api.close()                           # Graceful shutdown
```

---

### Component 2: Data Registry - Discovery & Search
**File**: `src/data_registry.py` | **Class**: `DataRegistry`

#### Quick Start
```python
from src.data_registry import DataRegistry

registry = DataRegistry()

# Discover all resources (one-time, or periodic refresh)
discovered = registry.discover_all_datasets()
print(f"Found {discovered} new resources")

# Check which ones are accessible
accessibility = registry.check_resource_availability(limit=50)
print(f"Available: {sum(accessibility.values())}/{len(accessibility)}")

# Search for specific data
housing = registry.search_resources("housing", by_field="title")

# Get overview
stats = registry.get_registry_statistics()
print(f"Total resources: {stats['total_resources']}")
print(f"Formats: {stats['formats']}")
```

#### Features
- ✅ Auto-discover all data.gov.hk resources
- ✅ Check resource availability (URLs work?)
- ✅ Search by name, title, description, format
- ✅ Filter by data format (CSV, JSON, XML)
- ✅ Persistent registry storage
- ✅ Export to JSON

#### Key Methods
```python
registry.discover_all_datasets(max_rows=1000)       # Scan all resources
registry.check_resource_availability(limit=50)      # Test URL accessibility
registry.search_resources(query, by_field="name")   # Find by keyword
registry.get_resources_by_format("CSV")             # Get all CSVs
registry.get_accessible_resources()                 # Only working links
registry.get_registry_statistics()                  # Summary stats
registry.export_registry("output.json")             # Save registry
```

#### Usage Pattern
```python
# One-time discovery
if not os.path.exists('data/registry/registry.json'):
    registry.discover_all_datasets()
    registry.check_resource_availability(limit=100)

# Later queries (uses cached registry)
housing = registry.search_resources("housing")
csv_files = registry.get_resources_by_format("CSV")
```

---

### Component 3: Crawler Monitor - Tracking & Reporting
**File**: `src/crawler_monitor.py` | **Class**: `CrawlerMonitor`

#### Quick Start
```python
from src.crawler_monitor import CrawlerMonitor

monitor = CrawlerMonitor()

# Start tracking a crawl session
session = monitor.start_session("crawl_001", "finance")

try:
    # Record what you crawled
    monitor.record_crawl_result("stocks", total=1500, failed=0, data_size_mb=12.5)
    monitor.record_crawl_result("trades", total=5000, failed=10, data_size_mb=28.3)

    # Check data freshness
    freshness = monitor.check_data_freshness(max_age_hours=24)
    if freshness['stale_resources']:
        print(f"⚠️ {len(freshness['stale_resources'])} stale resources")

    # End successfully
    monitor.end_session(status="success")
except Exception as e:
    # End with error
    monitor.end_session(status="failed", error_message=str(e))

# Generate reports
print(monitor.get_session_report())
print(monitor.get_performance_report())

# Export for analysis
monitor.export_report("report.json")
```

#### Features
- ✅ Session tracking (start/end)
- ✅ Result recording per resource
- ✅ Performance metrics (requests, data size, success rate)
- ✅ Data freshness monitoring
- ✅ Detailed session & performance reports
- ✅ Persistent history storage
- ✅ JSON export for analysis

#### Key Methods
```python
monitor.start_session(session_id, category)         # Begin crawl
monitor.record_crawl_result(name, total, failed, size_mb)  # Log results
monitor.end_session(status, error_message)          # End crawl
monitor.check_data_freshness(max_age_hours=24)      # Check staleness
monitor.get_session_report()                        # Generate report
monitor.get_performance_report()                    # Performance stats
monitor.get_monitoring_statistics()                 # Overall metrics
monitor.export_report("output.json")                # Save to file
```

#### Output Examples
```python
# Session Report
print(monitor.get_session_report())
# ============================================================
# 爬蟲會話報告
# ============================================================
# 會話 ID: crawl_001
# 類別: finance
# 狀態: success
# 持續時間: 456.23秒
# 記錄數: 8500
# 失敗數: 0
# 資源數: 2
# ============================================================

# Freshness Check
freshness = monitor.check_data_freshness()
# {
#   'freshness_status': {
#     'resource_1': {'last_update': '...', 'age_hours': 5.5, 'is_fresh': True},
#     'resource_2': {'last_update': '...', 'age_hours': 48.0, 'is_fresh': False}
#   },
#   'stale_resources': [
#     {'resource': 'resource_2', 'age_hours': 48.0}
#   ]
# }
```

---

## Integration Pattern

### Typical Crawl Workflow
```python
from src.api_handler import DataGovHKAPI
from src.data_registry import DataRegistry
from src.crawler_monitor import CrawlerMonitor

# Setup all 3 components
api = DataGovHKAPI(config)
registry = DataRegistry()
monitor = CrawlerMonitor()

# Pre-flight checks
if not api.check_connectivity():
    exit("API unavailable")

# Start monitoring
monitor.start_session("main", "all")

try:
    # Discover available resources
    registry.discover_all_datasets(max_rows=1000)
    registry.check_resource_availability(limit=100)

    # Crawl by category
    categories = ['finance', 'real_estate', 'business']
    for cat in categories:
        result = api.crawl_dataset_category(cat)
        if result:
            monitor.record_crawl_result(
                resource_name=cat,
                total=result['total_resources'],
                failed=0,
                data_size_mb=0
            )

    # Check data quality
    freshness = monitor.check_data_freshness()

    # Success
    monitor.end_session(status="success")

except Exception as e:
    monitor.end_session(status="failed", error_message=str(e))
    raise

finally:
    # Statistics
    print(monitor.get_performance_report())
    api.close()
```

---

## Performance Tips

### 1. Minimize API Calls
```python
# BAD: Creates new API instance each time (no cache)
for category in categories:
    api = DataGovHKAPI(config)  # ❌ No cache reuse
    api.crawl_dataset_category(category)

# GOOD: Reuse instance to leverage caching
api = DataGovHKAPI(config)
for category in categories:
    api.crawl_dataset_category(category)  # ✓ Uses cache
```

### 2. Smart Registry Queries
```python
# BAD: Discovers every time
registry = DataRegistry()
registry.discover_all_datasets()  # ❌ Slow
housing = registry.search_resources("housing")

# GOOD: Discover once, search many times
registry = DataRegistry()
if not registry.resources:  # Only if empty
    registry.discover_all_datasets()
housing = registry.search_resources("housing")  # ✓ Fast
```

### 3. Batch Record Operations
```python
# BAD: Multiple sessions for small batches
for resource in resources:
    monitor.start_session(f"crawl_{i}", "data")
    monitor.record_crawl_result(...)
    monitor.end_session()

# GOOD: Single session for batch
monitor.start_session("batch_crawl", "data")
for resource in resources:
    monitor.record_crawl_result(...)
monitor.end_session()  # ✓ Better reporting
```

---

## Common Patterns

### Health Check Before Crawl
```python
api = DataGovHKAPI(config)
if api.check_connectivity():
    # Safe to crawl
    data = api.crawl_finance_data()
else:
    logger.error("API unhealthy, retry later")
```

### Find All CSVs
```python
registry = DataRegistry()
csv_files = registry.get_resources_by_format("CSV")
for csv in csv_files:
    print(f"{csv.name}: {csv.url}")
```

### Monitor Long-Running Crawl
```python
monitor = CrawlerMonitor()
monitor.start_session("long_crawl", "all")

for batch in batches:
    results = process_batch(batch)
    monitor.record_crawl_result(
        resource_name=batch['name'],
        total=len(results['success']),
        failed=len(results['failed']),
        data_size_mb=calculate_size(results)
    )

monitor.end_session(status="success")
stats = monitor.get_monitoring_statistics()
logger.info(f"Crawled {stats['total_sessions']} batches")
```

### Check Data Freshness Alert
```python
monitor = CrawlerMonitor()
freshness = monitor.check_data_freshness(max_age_hours=12)

for stale in freshness['stale_resources']:
    send_alert(f"Data stale: {stale['resource']} ({stale['age_hours']:.1f}h)")
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| API returns 429 errors | Rate limiting working - data is throttled, retry later |
| Registry not updating | Call `registry.discover_all_datasets()` manually |
| Cache not working | Ensure `api` instance is reused across calls |
| Monitor not saving | Check `data/monitoring/` directory exists and writable |
| Search returns empty | Try different `by_field` parameter or broader query |
| Stale data alerts | Update with `registry.check_resource_availability()` |

---

## Phase 1 File Structure
```
gov_crawler/
├── src/
│   ├── api_handler.py          ← DataGovHKAPI (Connection, Caching)
│   ├── data_registry.py        ← DataRegistry (Discovery, Search)
│   ├── crawler_monitor.py      ← CrawlerMonitor (Tracking, Reporting)
│   ├── data_processor.py       (Phase 2)
│   └── storage_manager.py      (Phase 2)
├── data/
│   ├── registry/
│   │   └── registry.json       ← Auto-generated resource catalog
│   └── monitoring/
│       └── session_history.json ← Auto-generated session logs
└── PHASE1_IMPLEMENTATION_GUIDE.md ← Full documentation
```

---

## Quick Command Reference

```bash
# Test Phase 1 components
python -m pytest tests/test_api_handler.py -v
python -m pytest tests/test_data_registry.py -v
python -m pytest tests/test_crawler_monitor.py -v

# Discover resources
python examples/discover_resources.py

# Run integrated crawl
python main_crawler.py --mode phase1

# Check system health
python -c "from src.api_handler import DataGovHKAPI; api=DataGovHKAPI({}); print('✓ Healthy' if api.check_connectivity() else '✗ Unhealthy')"
```

---

**Phase 1 Status**: ✅ Complete
**Ready for**: Phase 2 (Data Processing, Storage Optimization)
**Last Updated**: 2025-10-23
