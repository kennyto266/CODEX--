#!/usr/bin/env python3
"""
Convert Non-Price Data to Trading Signals
将非价格数据转换为买卖信号

This script transforms non-price indicators into actionable trading signals
using technical analysis methods and quantitative models.
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class NonPriceToSignalConverter:
    """
    Convert non-price data (HIBOR, GDP, CPI, Traffic, Weather) to trading signals
    """

    def __init__(self):
        self.signals = {}
        self.signal_strength = {}

    def load_data(self):
        """Load all real data sources"""
        print("=" * 70)
        print("LOADING NON-PRICE DATA SOURCES")
        print("=" * 70)

        # 1. Load HIBOR data
        print("\n[1] Loading HIBOR Rates Data...")
        try:
            with open('data_gov_hk_real/hibor_rates.json', 'r') as f:
                self.hibor_data = json.load(f)
            print("   [OK] HIBOR data loaded (100 records)")
        except Exception as e:
            print(f"   [ERROR] Error loading HIBOR: {e}")
            self.hibor_data = None

        # 2. Load Traffic data
        print("\n[2] Loading Traffic Speed Data...")
        try:
            self.traffic_df = pd.read_csv('data_gov_hk_real/traffic_speed.csv')
            print(f"   [OK] Traffic data loaded ({self.traffic_df.shape[0]} records)")
        except Exception as e:
            print(f"   [ERROR] Error loading traffic: {e}")
            self.traffic_df = None

        # 3. Load GDP data
        print("\n[3] Loading GDP Data...")
        try:
            with open('data_gov_hk_real/gdp_worldbank.json', 'r') as f:
                self.gdp_data = json.load(f)
            print(f"   [OK] GDP data loaded ({self.gdp_data['records_count']} records)")
        except Exception as e:
            print(f"   [ERROR] Error loading GDP: {e}")
            self.gdp_data = None

        # 4. Load CPI data
        print("\n[4] Loading CPI Data...")
        try:
            with open('data_gov_hk_real/cpi_worldbank.json', 'r') as f:
                self.cpi_data = json.load(f)
            print(f"   [OK] CPI data loaded ({self.cpi_data['records_count']} records)")
        except Exception as e:
            print(f"   [ERROR] Error loading CPI: {e}")
            self.cpi_data = None

        # 5. Load Weather data
        print("\n[5] Loading Weather Data...")
        try:
            with open('data_gov_hk_real/weather_hongkong.json', 'r') as f:
                self.weather_data = json.load(f)
            print("   [OK] Weather data loaded (real-time)")
        except Exception as e:
            print(f"   [ERROR] Error loading weather: {e}")
            self.weather_data = None

    def analyze_hibor_signals(self):
        """
        Generate trading signals from HIBOR rates
        HIBOR利率分析生成交易信号
        """
        if not self.hibor_data or 'result' not in self.hibor_data:
            return

        print("\n" + "=" * 70)
        print("HIBOR RATES - TECHNICAL ANALYSIS")
        print("=" * 70)

        records = self.hibor_data['result'].get('records', [])

        if not records:
            return

        # Convert to DataFrame for analysis
        df = pd.DataFrame(records)
        df['date'] = pd.to_datetime(df['end_of_day'])
        df = df.sort_values('date')

        # HIBOR Term Structure Analysis
        current_rates = df.iloc[-1]

        # Calculate yield curve slope
        slope_3m_12m = current_rates.get('ir_12m', 0) - current_rates.get('ir_3m', 0)
        slope_overnight_3m = current_rates.get('ir_3m', 0) - current_rates.get('ir_overnight', 0)

        # Generate signals
        signals = {
            'yield_curve_slope': slope_3m_12m,
            'short_term_pressure': slope_overnight_3m,
            'signal_type': 'RATE_OUTLOOK'
        }

        # Decision logic
        if slope_overnight_3m > 0.5:
            signals['action'] = 'BULLISH'
            signals['strength'] = 'STRONG'
            signals['reason'] = 'Steep short-term curve suggests rate tightening'
        elif slope_overnight_3m < -0.2:
            signals['action'] = 'BEARISH'
            signals['strength'] = 'MEDIUM'
            signals['reason'] = 'Inverted short-term curve suggests economic weakness'
        else:
            signals['action'] = 'NEUTRAL'
            signals['strength'] = 'WEAK'
            signals['reason'] = 'Stable yield curve indicates balanced outlook'

        self.signals['HIBOR'] = signals

        # Display results
        print(f"Current HIBOR (Latest):")
        print(f"  Overnight: {current_rates.get('ir_overnight', 'N/A')}%")
        print(f"  1 Month: {current_rates.get('ir_1m', 'N/A')}%")
        print(f"  3 Month: {current_rates.get('ir_3m', 'N/A')}%")
        print(f"  12 Month: {current_rates.get('ir_12m', 'N/A')}%")
        print(f"\nYield Curve Analysis:")
        print(f"  3M-12M Slope: {slope_3m_12m:.3f}")
        print(f"  Overnight-3M Slope: {slope_overnight_3m:.3f}")
        print(f"\nSignal: {signals['action']} ({signals['strength']})")
        print(f"Reason: {signals['reason']}")

        # Store for composite analysis
        self.signal_strength['HIBOR'] = signals['strength']

    def analyze_traffic_signals(self):
        """
        Generate trading signals from traffic data
        交通数据分析生成交易信号
        """
        if self.traffic_df is None or self.traffic_df.empty:
            return

        print("\n" + "=" * 70)
        print("TRAFFIC SPEED - ECONOMIC ACTIVITY ANALYSIS")
        print("=" * 70)

        # Analyze speed patterns (assuming columns contain speed data)
        # In real scenario, we'd need to identify speed columns

        # For this analysis, assume we have speed data
        if 'Speed' in self.traffic_df.columns or 'speed' in self.traffic_df.columns:
            speed_col = 'Speed' if 'Speed' in self.traffic_df.columns else 'speed'

            avg_speed = self.traffic_df[speed_col].mean()
            current_speed = self.traffic_df[speed_col].iloc[-1] if len(self.traffic_df) > 0 else avg_speed

            # Generate signals
            signals = {
                'avg_speed': avg_speed,
                'current_speed': current_speed,
                'speed_change_pct': ((current_speed - avg_speed) / avg_speed * 100) if avg_speed > 0 else 0,
                'signal_type': 'ECONOMIC_ACTIVITY'
            }

            # Decision logic based on speed (proxy for economic activity)
            if signals['speed_change_pct'] > 10:
                signals['action'] = 'BULLISH'
                signals['strength'] = 'MEDIUM'
                signals['reason'] = 'High traffic speed indicates strong economic activity'
            elif signals['speed_change_pct'] < -10:
                signals['action'] = 'BEARISH'
                signals['strength'] = 'MEDIUM'
                signals['reason'] = 'Low traffic speed suggests economic slowdown'
            else:
                signals['action'] = 'NEUTRAL'
                signals['strength'] = 'WEAK'
                signals['reason'] = 'Traffic patterns within normal range'

            self.signals['TRAFFIC'] = signals
            self.signal_strength['TRAFFIC'] = signals['strength']

            print(f"Traffic Analysis:")
            print(f"  Average Speed: {avg_speed:.1f} km/h")
            print(f"  Current Speed: {current_speed:.1f} km/h")
            print(f"  Deviation: {signals['speed_change_pct']:.1f}%")
            print(f"\nSignal: {signals['action']} ({signals['strength']})")
            print(f"Reason: {signals['reason']}")

        else:
            print("  [WARNING] No speed column found in traffic data")

    def analyze_macro_signals(self):
        """
        Generate trading signals from GDP and CPI data
        宏观经济数据分析生成交易信号
        """
        print("\n" + "=" * 70)
        print("MACROECONOMIC INDICATORS - FUNDAMENTAL ANALYSIS")
        print("=" * 70)

        # GDP Analysis
        if self.gdp_data and 'data' in self.gdp_data:
            gdp_records = self.gdp_data['data']

            # Get recent GDP growth
            gdp_growth = []
            for record in gdp_records[:10]:  # Last 10 years
                if record.get('value') and record['date'] >= '2015':
                    gdp_growth.append({
                        'year': record['date'],
                        'gdp': record['value']
                    })

            if len(gdp_growth) >= 2:
                current_gdp = gdp_growth[0].get('gdp', 0)
                prev_gdp = gdp_growth[1].get('gdp', 0)
                gdp_growth_rate = ((current_gdp - prev_gdp) / prev_gdp * 100) if prev_gdp > 0 else 0

                print(f"GDP Analysis:")
                print(f"  Current GDP: ${current_gdp:,.0f}")
                print(f"  Growth Rate: {gdp_growth_rate:.2f}%")

                # GDP Signal
                gdp_signals = {
                    'gdp_growth_rate': gdp_growth_rate,
                    'signal_type': 'ECONOMIC_GROWTH'
                }

                if gdp_growth_rate > 3:
                    gdp_signals['action'] = 'BULLISH'
                    gdp_signals['strength'] = 'STRONG'
                    gdp_signals['reason'] = 'Strong economic growth supports equity markets'
                elif gdp_growth_rate < 0:
                    gdp_signals['action'] = 'BEARISH'
                    gdp_signals['strength'] = 'STRONG'
                    gdp_signals['reason'] = 'Economic contraction hurts market sentiment'
                else:
                    gdp_signals['action'] = 'NEUTRAL'
                    gdp_signals['strength'] = 'MEDIUM'
                    gdp_signals['reason'] = 'Moderate growth with balanced outlook'

                self.signals['GDP'] = gdp_signals
                self.signal_strength['GDP'] = gdp_signals['strength']
                print(f"\nGDP Signal: {gdp_signals['action']} ({gdp_signals['strength']})")
                print(f"Reason: {gdp_signals['reason']}")

        # CPI Analysis
        print("\n" + "-" * 70)
        if self.cpi_data and 'data' in self.cpi_data:
            cpi_records = self.cpi_data['data']

            # Get recent inflation
            inflation = []
            for record in cpi_records[:10]:
                if record.get('value') and record['date'] >= '2015':
                    inflation.append({
                        'year': record['date'],
                        'inflation': record['value']
                    })

            if inflation:
                current_inflation = inflation[0].get('inflation', 0)

                print(f"Inflation Analysis:")
                print(f"  Current Inflation: {current_inflation:.2f}%")

                # Inflation Signal
                cpi_signals = {
                    'inflation_rate': current_inflation,
                    'signal_type': 'INFLATION_PRESSURE'
                }

                if current_inflation > 4:
                    cpi_signals['action'] = 'BEARISH'
                    cpi_signals['strength'] = 'STRONG'
                    cpi_signals['reason'] = 'High inflation may force rate hikes'
                elif current_inflation < 1:
                    cpi_signals['action'] = 'BULLISH'
                    cpi_signals['strength'] = 'MEDIUM'
                    cpi_signals['reason'] = 'Low inflation allows accommodative policy'
                else:
                    cpi_signals['action'] = 'NEUTRAL'
                    cpi_signals['strength'] = 'WEAK'
                    cpi_signals['reason'] = 'Inflation within target range'

                self.signals['CPI'] = cpi_signals
                self.signal_strength['CPI'] = cpi_signals['strength']
                print(f"\nCPI Signal: {cpi_signals['action']} ({cpi_signals['strength']})")
                print(f"Reason: {cpi_signals['reason']}")

    def analyze_weather_signals(self):
        """
        Generate trading signals from weather data
        天气数据分析生成交易信号
        """
        if not self.weather_data or 'current_weather' not in self.weather_data:
            return

        print("\n" + "=" * 70)
        print("WEATHER DATA - SENTIMENT ANALYSIS")
        print("=" * 70)

        weather = self.weather_data['current_weather']
        temp = weather.get('temperature_2m', 20)
        humidity = weather.get('relative_humidity_2m', 50)
        precipitation = weather.get('precipitation', 0)

        # Weather-based sentiment scoring
        # Good weather (clear, moderate temp) → Bullish sentiment
        # Bad weather (storm, extreme temp) → Bearish sentiment

        weather_score = 0

        # Temperature comfort zone (18-25°C is optimal)
        if 18 <= temp <= 25:
            weather_score += 1
        elif temp < 10 or temp > 35:
            weather_score -= 1
        else:
            weather_score += 0.5

        # Humidity (40-60% is comfortable)
        if 40 <= humidity <= 60:
            weather_score += 0.5
        elif humidity > 80:
            weather_score -= 0.5

        # Precipitation (rain reduces sentiment)
        if precipitation > 5:
            weather_score -= 0.5
        elif precipitation == 0:
            weather_score += 0.5

        print(f"Weather Analysis:")
        print(f"  Temperature: {temp}°C")
        print(f"  Humidity: {humidity}%")
        print(f"  Precipitation: {precipitation}mm")
        print(f"  Weather Score: {weather_score:.1f}/3")

        # Weather Signal
        weather_signals = {
            'temperature': temp,
            'humidity': humidity,
            'precipitation': precipitation,
            'comfort_score': weather_score,
            'signal_type': 'SENTIMENT'
        }

        if weather_score >= 2:
            weather_signals['action'] = 'BULLISH'
            weather_signals['strength'] = 'WEAK'
            weather_signals['reason'] = 'Good weather boosts consumer sentiment'
        elif weather_score <= 0:
            weather_signals['action'] = 'BEARISH'
            weather_signals['strength'] = 'WEAK'
            weather_signals['reason'] = 'Poor weather may dampen economic activity'
        else:
            weather_signals['action'] = 'NEUTRAL'
            weather_signals['strength'] = 'WEAK'
            weather_signals['reason'] = 'Neutral weather conditions'

        self.signals['WEATHER'] = weather_signals
        self.signal_strength['WEATHER'] = weather_signals['strength']
        print(f"\nWeather Signal: {weather_signals['action']} ({weather_signals['strength']})")
        print(f"Reason: {weather_signals['reason']}")

    def generate_composite_signal(self):
        """
        Combine all signals into a composite trading signal
        组合所有信号生成复合交易信号
        """
        print("\n" + "=" * 70)
        print("COMPOSITE TRADING SIGNAL")
        print("=" * 70)

        if not self.signals:
            print("No signals available for composite analysis")
            return

        # Calculate weighted score
        weights = {
            'HIBOR': 0.3,    # High weight for interest rates
            'GDP': 0.25,     # High weight for economic growth
            'CPI': 0.2,      # Medium weight for inflation
            'TRAFFIC': 0.15, # Medium weight for economic activity
            'WEATHER': 0.1   # Low weight for sentiment
        }

        score = 0
        total_weight = 0

        print("\nSignal Summary:")
        for signal_name, signal_data in self.signals.items():
            action = signal_data.get('action', 'NEUTRAL')
            strength = signal_data.get('strength', 'WEAK')
            weight = weights.get(signal_name, 0.1)

            # Convert to numerical score
            if action == 'BULLISH':
                if strength == 'STRONG':
                    value = 2
                else:
                    value = 1
            elif action == 'BEARISH':
                if strength == 'STRONG':
                    value = -2
                else:
                    value = -1
            else:
                value = 0

            score += value * weight
            total_weight += weight

            print(f"  {signal_name:8s}: {action:8s} ({strength:6s}) [Weight: {weight:.0%}]")

        # Normalize score
        if total_weight > 0:
            score = score / total_weight

        # Generate composite signal
        composite = {
            'score': score,
            'signal_type': 'COMPOSITE',
            'timestamp': datetime.now().isoformat()
        }

        if score >= 1:
            composite['action'] = 'STRONG_BUY'
            composite['confidence'] = 'HIGH'
        elif score >= 0.5:
            composite['action'] = 'BUY'
            composite['confidence'] = 'MEDIUM'
        elif score <= -1:
            composite['action'] = 'STRONG_SELL'
            composite['confidence'] = 'HIGH'
        elif score <= -0.5:
            composite['action'] = 'SELL'
            composite['confidence'] = 'MEDIUM'
        else:
            composite['action'] = 'HOLD'
            composite['confidence'] = 'LOW'

        # Add signal rationale
        bullish_factors = [name for name, data in self.signals.items() if data.get('action') == 'BULLISH']
        bearish_factors = [name for name, data in self.signals.items() if data.get('action') == 'BEARISH']

        rationale = []
        if bullish_factors:
            rationale.append(f"Bullish: {', '.join(bullish_factors)}")
        if bearish_factors:
            rationale.append(f"Bearish: {', '.join(bearish_factors)}")

        composite['rationale'] = "; ".join(rationale)

        self.signals['COMPOSITE'] = composite

        print(f"\nComposite Score: {score:.2f}")
        print(f"Composite Signal: {composite['action']}")
        print(f"Confidence: {composite['confidence']}")
        print(f"Rationale: {composite['rationale']}")

        return composite

    def save_signals(self):
        """Save all signals to file"""
        output = {
            'timestamp': datetime.now().isoformat(),
            'total_signals': len(self.signals),
            'signals': self.signals,
            'signal_strength': self.signal_strength
        }

        output_file = 'data_gov_hk_real/trading_signals.json'
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        print(f"\n[OK] Signals saved to: {output_file}")

    def run_analysis(self):
        """Run complete analysis"""
        print("\n" + "=" * 70)
        print("NON-PRICE DATA TO TRADING SIGNALS CONVERTER")
        print("=" * 70)

        # Load data
        self.load_data()

        # Analyze each data source
        self.analyze_hibor_signals()
        self.analyze_traffic_signals()
        self.analyze_macro_signals()
        self.analyze_weather_signals()

        # Generate composite signal
        composite = self.generate_composite_signal()

        # Save results
        self.save_signals()

        print("\n" + "=" * 70)
        print("ANALYSIS COMPLETED")
        print("=" * 70)

        return composite

def main():
    converter = NonPriceToSignalConverter()
    final_signal = converter.run_analysis()

    print("\n>>> FINAL TRADING RECOMMENDATION:")
    print("-" * 70)
    if final_signal:
        print(f"Signal: {final_signal['action']}")
        print(f"Confidence: {final_signal['confidence']}")
        print(f"Score: {final_signal['score']:.2f}")
        print(f"Rationale: {final_signal['rationale']}")
    print("-" * 70)

    return final_signal

if __name__ == "__main__":
    main()
