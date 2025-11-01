#!/usr/bin/env python3
"""
股票熱力圖服務模組
生成股票市場熱力圖分析
"""

import os
import logging
import asyncio
import io
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class StockHeatmapService:
    """股票熱力圖服務"""

    def __init__(self):
        self.cache_file = "data/heatmap_cache.json"
        self.cache_duration = 900  # 15分鐘緩存
        self.last_update = None
        self.heatmap_data = None

    async def generate_heatmap(self, stock_codes: Optional[List[str]] = None) -> bytes:
        """生成股票熱力圖"""
        try:
            # 如果沒有指定股票，使用默認股票列表
            if not stock_codes:
                stock_codes = self._get_default_stocks()

            # 獲取股票數據
            stocks_data = await self._fetch_stocks_data(stock_codes)

            if not stocks_data:
                raise Exception("無法獲取股票數據")

            # 生成熱力圖
            return self._create_heatmap_image(stocks_data)

        except ImportError:
            logger.error("matplotlib未安裝，無法生成熱力圖")
            raise
        except Exception as e:
            logger.error(f"生成熱力圖失敗: {e}")
            raise

    def _get_default_stocks(self) -> List[str]:
        """獲取默認的股票列表（港股市場主要股票）"""
        return [
            "0700.HK",  # 騰訊控股
            "0388.HK",  # 香港交易所
            "1398.HK",  # 工商銀行
            "0939.HK",  # 建設銀行
            "3988.HK",  # 中國銀行
            "2800.HK",  # 恆生ETF
            "1299.HK",  # 友邦保險
            "2318.HK",  # 中國平安
            "0883.HK",  # 中國海洋石油
            "0823.HK",  # 領展房產基金
            "1928.HK",  # 金沙中國
            "0016.HK",  # 新鴻基地產
            "1038.HK",  # 長江基建集團
            "1109.HK",  # 華潤置地
            "0762.HK",  # 中國聯通
        ]

    async def _fetch_stocks_data(self, stock_codes: List[str]) -> List[Dict]:
        """獲取股票數據"""
        stocks_data = []

        # 嘗試批量獲取股票數據
        try:
            from telegram_quant_bot import get_stock_data

            for stock_code in stock_codes:
                try:
                    data = get_stock_data(stock_code)
                    if data and len(data) > 0:
                        latest = data[-1]
                        prev = data[-2] if len(data) > 1 else latest

                        current_price = float(latest.get('close', 0))
                        prev_price = float(prev.get('close', 0))
                        change = current_price - prev_price
                        change_pct = (change / prev_price * 100) if prev_price > 0 else 0

                        stocks_data.append({
                            'code': stock_code,
                            'price': current_price,
                            'change': change,
                            'change_pct': change_pct,
                            'volume': float(latest.get('volume', 0))
                        })
                except Exception as e:
                    logger.warning(f"獲取股票 {stock_code} 數據失敗: {e}")
                    # 使用模擬數據
                    stocks_data.append(self._generate_mock_data(stock_code))

        except ImportError:
            logger.warning("無法導入量化系統，使用模擬數據")
            for stock_code in stock_codes:
                stocks_data.append(self._generate_mock_data(stock_code))

        return stocks_data

    def _generate_mock_data(self, stock_code: str) -> Dict:
        """生成模擬股票數據"""
        import random
        from datetime import datetime

        # 根據股票代碼生成穩定數據
        seed = int(sum(ord(c) for c in stock_code) + datetime.now().day)
        random.seed(seed)

        # 模擬價格範圍
        base_price = {
            '0700': 380.0,
            '0388': 320.0,
            '1398': 5.2,
            '0939': 6.5,
            '3988': 3.8,
            '2800': 22.5,
            '1299': 55.0,
            '2318': 42.0,
            '0883': 15.5,
            '0823': 65.0,
            '1928': 28.0,
            '0016': 105.0,
            '1038': 52.0,
            '1109': 32.0,
            '0762': 8.5,
        }.get(stock_code[:4], 100.0)

        # 生成價格波動
        price = base_price * (0.98 + random.random() * 0.04)  # ±2%
        change_pct = random.uniform(-3, 3)

        return {
            'code': stock_code,
            'price': round(price, 2),
            'change': round(price * change_pct / 100, 2),
            'change_pct': round(change_pct, 2),
            'volume': random.randint(1000000, 50000000)
        }

    def _create_heatmap_image(self, stocks_data: List[Dict]) -> bytes:
        """創建熱力圖"""
        try:
            import matplotlib
            matplotlib.use('Agg')  # 使用非交互式後端
            import matplotlib.pyplot as plt
            import matplotlib.patches as patches
            import numpy as np

            # 創建圖形
            fig, ax = plt.subplots(1, 1, figsize=(16, 10))
            ax.set_xlim(0, 10)
            ax.set_ylim(0, 6)
            ax.axis('off')

            # 標題
            plt.title(
                f"港股市場熱力圖 - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                fontsize=20,
                fontweight='bold',
                pad=20
            )

            # 計算網格布局
            num_stocks = len(stocks_data)
            cols = 5
            rows = (num_stocks + cols - 1) // cols

            # 設置格子大小和間距
            cell_width = 1.8
            cell_height = 1.0
            x_spacing = 0.2
            y_spacing = 0.15

            start_x = 0.5
            start_y = 4.5

            # 繪製每個股票
            for i, stock in enumerate(stocks_data):
                row = i // cols
                col = i % cols

                x = start_x + col * (cell_width + x_spacing)
                y = start_y - row * (cell_height + y_spacing)

                # 根據漲跌幅設置顏色
                change_pct = stock['change_pct']
                if change_pct > 2:
                    color = '#d32f2f'  # 深紅
                elif change_pct > 0:
                    color = '#ff9800'  # 橙色
                elif change_pct == 0:
                    color = '#9e9e9e'  # 灰色
                elif change_pct > -2:
                    color = '#4caf50'  # 綠色
                else:
                    color = '#2e7d32'  # 深綠

                # 繪製矩形
                rect = patches.Rectangle(
                    (x, y), cell_width, cell_height,
                    linewidth=2,
                    edgecolor='white',
                    facecolor=color,
                    alpha=0.8
                )
                ax.add_patch(rect)

                # 添加股票代碼
                ax.text(
                    x + cell_width / 2, y + cell_height * 0.7,
                    stock['code'].replace('.HK', ''),
                    fontsize=12,
                    fontweight='bold',
                    ha='center',
                    va='center',
                    color='white'
                )

                # 添加價格
                ax.text(
                    x + cell_width / 2, y + cell_height * 0.5,
                    f"{stock['price']:.2f}",
                    fontsize=11,
                    ha='center',
                    va='center',
                    color='white'
                )

                # 添加漲跌幅
                change_str = f"+{stock['change_pct']:.2f}%" if stock['change_pct'] > 0 else f"{stock['change_pct']:.2f}%"
                color = 'white' if abs(stock['change_pct']) < 2 else 'yellow'
                ax.text(
                    x + cell_width / 2, y + cell_height * 0.3,
                    change_str,
                    fontsize=10,
                    fontweight='bold',
                    ha='center',
                    va='center',
                    color=color
                )

            # 添加圖例
            legend_x = 0.5
            legend_y = 0.5

            # 圖例標題
            ax.text(legend_x, legend_y + 0.4, "圖例:", fontsize=12, fontweight='bold')

            # 圖例框
            legend_items = [
                ('+2%以上', '#d32f2f'),
                ('0%到+2%', '#ff9800'),
                ('0%', '#9e9e9e'),
                ('-2%到0%', '#4caf50'),
                ('-2%以下', '#2e7d32'),
            ]

            for i, (label, color) in enumerate(legend_items):
                y_pos = legend_y + 0.2 - i * 0.1
                rect = patches.Rectangle(
                    (legend_x, y_pos), 0.15, 0.05,
                    linewidth=1,
                    edgecolor='white',
                    facecolor=color,
                    alpha=0.8
                )
                ax.add_patch(rect)
                ax.text(
                    legend_x + 0.2, y_pos + 0.025,
                    label,
                    fontsize=10,
                    va='center'
                )

            # 保存為字節流
            buffer = io.BytesIO()
            plt.savefig(
                buffer,
                format='png',
                bbox_inches='tight',
                dpi=150,
                facecolor='white',
                edgecolor='none'
            )
            plt.close()

            buffer.seek(0)
            return buffer.getvalue()

        except Exception as e:
            logger.error(f"創建熱力圖圖像失敗: {e}")
            raise

    def format_heatmap_message(self, stock_count: int) -> str:
        """格式化熱力圖說明消息"""
        message = (
            f"📊 股票熱力圖已生成\n\n"
            f"包含 {stock_count} 隻港股\n"
            f"數據時間：{datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
            f"🔴 紅色 = 大漲\n"
            f"🟠 橙色 = 小漲\n"
            f"⚪ 灰色 = 平盤\n"
            f"🟢 綠色 = 小跌\n"
            f"🟫 深綠 = 大跌\n\n"
            f"每個方塊顯示：\n"
            f"• 股票代碼\n"
            f"• 當前價格\n"
            f"• 漲跌幅百分比"
        )
        return message

# 創建全局實例
heatmap_service = StockHeatmapService()
