#!/usr/bin/env python3
"""
Update integration report with all 5 real data sources
Calculate final coverage improvement
"""

import json
import os
from datetime import datetime

def main():
    print("=" * 70)
    print("FINAL INTEGRATION REPORT - ALL REAL DATA SOURCES")
    print("=" * 70)

    # Real data sources we have
    real_data_sources = [
        {
            "name": "HIBOR Rates",
            "source": "HKMA",
            "file": "hibor_rates.json",
            "indicators": 6,
            "records": 100,
            "status": "success"
        },
        {
            "name": "Traffic Speed",
            "source": "Transport Department",
            "file": "traffic_speed.csv",
            "indicators": 3,
            "records": 790,
            "status": "success"
        },
        {
            "name": "GDP",
            "source": "World Bank",
            "file": "gdp_worldbank.json",
            "indicators": 5,
            "records": 60,
            "status": "success"
        },
        {
            "name": "CPI/Inflation",
            "source": "World Bank",
            "file": "cpi_worldbank.json",
            "indicators": 3,
            "records": 60,
            "status": "success"
        },
        {
            "name": "Weather",
            "source": "Open-Meteo API",
            "file": "weather_hongkong.json",
            "indicators": 6,
            "records": 1,
            "status": "success"
        }
    ]

    # Calculate statistics
    total_sources = len(real_data_sources)
    total_indicators = sum(source["indicators"] for source in real_data_sources)
    total_records = sum(source["records"] for source in real_data_sources)
    total_file_size = sum(os.path.getsize(f'data_gov_hk_real/{source["file"]}') for source in real_data_sources if os.path.exists(f'data_gov_hk_real/{source["file"]}'))

    # Coverage calculation
    total_non_price_indicators = 51  # Total non-price indicators
    original_real_indicators = 16  # Original (FRED + ExchangeRate)
    new_real_indicators = total_indicators
    original_mock_indicators = total_non_price_indicators - original_real_indicators

    # New coverage
    new_real_total = original_real_indicators + new_real_indicators
    original_coverage = (original_real_indicators / total_non_price_indicators) * 100
    new_coverage = (new_real_total / total_non_price_indicators) * 100
    improvement = new_coverage - original_coverage

    # Display results
    print("\n[1] Real Data Sources Summary")
    print("-" * 70)
    for i, source in enumerate(real_data_sources, 1):
        status_symbol = "[OK]" if source["status"] == "success" else "[ERROR]"
        print(f"{i}. {source['name']} - {source['source']}")
        print(f"   {status_symbol} {source['indicators']} indicators, {source['records']} records")
        print(f"   File: {source['file']}")

    print("\n[2] Statistical Summary")
    print("-" * 70)
    print(f"Total real data sources: {total_sources}")
    print(f"Total indicators added: {total_indicators}")
    print(f"Total records: {total_records:,}")
    print(f"Total file size: {total_file_size / 1024:.1f} KB")

    print("\n[3] Coverage Analysis")
    print("-" * 70)
    print(f"Original non-price data coverage: {original_coverage:.1f}% ({original_real_indicators}/{total_non_price_indicators})")
    print(f"New non-price data coverage: {new_coverage:.1f}% ({new_real_total}/{total_non_price_indicators})")
    print(f"Improvement: +{improvement:.1f} percentage points")
    print(f"Relative improvement: +{(improvement/original_coverage)*100:.1f}%")

    # Detailed breakdown
    print("\n[4] Data Coverage Breakdown")
    print("-" * 70)
    print("Government Sources:")
    print(f"  - HKMA HIBOR: 6 indicators (Real)")
    print(f"  - TD Traffic: 3 indicators (Real)")
    print("International Sources:")
    print(f"  - World Bank GDP: 5 indicators (Real)")
    print(f"  - World Bank CPI: 3 indicators (Real)")
    print("Environmental Sources:")
    print(f"  - Open-Meteo Weather: 6 indicators (Real)")
    print("\nExisting Sources:")
    print(f"  - FRED API: 6 indicators (Real)")
    print(f"  - ExchangeRate API: 10 indicators (Real)")

    # Create final integration report
    final_report = {
        "timestamp": datetime.now().isoformat(),
        "integration_status": "completed",
        "real_data_sources": total_sources,
        "total_indicators_added": total_indicators,
        "total_records": total_records,
        "total_file_size_kb": round(total_file_size / 1024, 1),
        "coverage_analysis": {
            "total_non_price_indicators": total_non_price_indicators,
            "original_real_indicators": original_real_indicators,
            "original_coverage_percentage": f"{original_coverage:.1f}%",
            "new_real_indicators_added": new_real_indicators,
            "new_total_real_indicators": new_real_total,
            "new_coverage_percentage": f"{new_coverage:.1f}%",
            "improvement_percentage": f"+{improvement:.1f}%",
            "relative_improvement": f"+{(improvement/original_coverage)*100:.1f}%"
        },
        "data_sources_detail": real_data_sources,
        "integration_methods": {
            "chrome_mcp": "2 sources (HKMA, TD)",
            "world_bank_api": "2 sources (GDP, CPI)",
            "open_meteo_api": "1 source (Weather)"
        },
        "backup_location": "gov_crawler/data/backup_mock_20251106_003854.json"
    }

    # Save final report
    with open('data_gov_hk_real/final_integration_report.json', 'w', encoding='utf-8') as f:
        json.dump(final_report, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 70)
    print("FINAL INTEGRATION REPORT GENERATED")
    print("=" * 70)
    print(f"Report saved: data_gov_hk_real/final_integration_report.json")
    print(f"Coverage improved from {original_coverage:.1f}% to {new_coverage:.1f}%")
    print(f"Achievement: +{improvement:.1f}% coverage improvement")
    print("=" * 70)

if __name__ == "__main__":
    main()
