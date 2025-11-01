# 體育賽程查詢功能規格

## 概述

本規格定義了體育賽程查詢功能的實現，支持查看未來賽程、過去結果和比賽提醒功能。

## ADDED Requirements

### Requirement: System MUST provide schedule query interface
系統必須提供統一的賽程查詢界面，支持多種查詢方式。

#### Scenario: 查看今日賽程
- **WHEN** 用戶執行 `/schedule` 且無其他參數時
- **THEN** 系統返回：
  - 今日所有運動類型的賽程
  - 按照運動類型分組顯示
  - 顯示開賽時間、對戰隊伍、現場
  - 標記重要比賽

#### Scenario: 查看指定運動類型賽程
- **WHEN** 用戶執行 `/schedule nba` 時
- **THEN** 系統返回：
  - 未來 7 天的 NBA 賽程
  - 按日期排序
  - 顯示開賽時間 (本地時間)
  - 顯示對戰隊伍
  - 顯示現場和直播信息

#### Scenario: 查看指定日期賽程
- **WHEN** 用戶執行 `/schedule 2024-03-20` 時
- **THEN** 系統返回：
  - 指定日期的所有體育賽程
  - 按時間排序
  - 如果無比賽，顯示最近比賽日期
  - 支持多種日期格式 (YYYY-MM-DD, MM-DD, 今日, 明日等)

#### Scenario: 查看指定球隊賽程
- **WHEN** 用戶執行 `/schedule lakers` 時
- **THEN** 系統返回：
  - 指定球隊的未來 10 場比賽
  - 顯示主場/客場
  - 顯示對手戰績
  - 標記重要對手 (同城德比、季后賽對手等)

### Requirement: System MUST aggregate schedules from multiple sources
系統必須從多個數據源聚合賽程信息。

#### Scenario: NBA 賽程聚合
- **WHEN** 獲取 NBA 賽程時
- **THEN** 系統從以下來源聚合：
  - ESPN NBA 賽程頁面
  - NBA.com 官方賽程
  - 緩存的歷史數據
  - 整合後去重並排序

#### Scenario: 足球賽程聚合
- **WHEN** 獲取足球賽程時
- **THEN** 系統從以下來源聚合：
  - 馬會足球頁面 (香港比賽)
  - ESPN 足球賽程 (國際比賽)
  - 聯賽官網 (如果可爬取)
  - 整合後按重要性排序

#### Scenario: 賽程數據去重
- **WHEN** 聚合多個數據源時
- **THEN** 系統執行：
  - 比較比賽時間、對戰隊伍
  - 識別重複記錄並合併
  - 選擇最完整的記錄
  - 記錄數據來源

#### Scenario: 補全缺失信息
- **WHEN** 賽程信息不完整時
- **THEN** 系統執行：
  - 從多個來源補全信息
  - 標記補全的字段
  - 如果無法補全，使用 "待定" 標記
  - 記錄補全嘗試次數

### Requirement: System MUST schedule upcoming matches
系統必須支持查看未來比賽安排。

#### Scenario: 顯示未來 7 天賽程
- **WHEN** 用戶查詢未來賽程時
- **THEN** 系統顯示：
  - 按日期分組
  - 每組內按時間排序
  - 包含完整對戰信息
  - 標記主場/客場
  - 顯示預計比賽時長

#### Scenario: 重要比賽標記
- **WHEN** 顯示賽程時
- **THEN** 系統標記以下重要比賽：
  - 開幕戰/閉幕戰
  - 季后賽/決賽
  - 德比戰 (同城、宿敵)
  - 排名關鍵戰
  - 回歸戰 (球員對陣舊主)

#### Scenario: 賽程熱力圖
- **WHEN** 顯示一週賽程概覽時
- **THEN** 系統可以生成熱力圖：
  - 每天比賽數量
  - 重要比賽密度
  - 黃金時間比賽標記
  - 用戶可快速識別精彩比賽日

#### Scenario: 賽程提醒設置
- **WHEN** 用戶想設置比賽提醒時
- **THEN** 系統支持：
  - 開賽前 15 分鐘提醒
  - 開賽前 1 小時提醒
  - 比賽開始時提醒
  - 點擊提醒按鈕或發送 `/remind 球隊名 時間`

### Requirement: System MUST display past results
系統必須支持查看過去的比賽結果。

#### Scenario: 查看昨日比賽結果
- **WHEN** 用戶執行 `/results yesterday` 時
- **THEN** 系統返回：
  - 昨日所有體育比賽結果
  - 顯示最終比分
  - 顯示比賽摘要 (最高分球員等)
  - 顯示比賽精彩片段 (如果可獲取)

#### Scenario: 查看過去 7 天結果
- **WHEN** 用戶執行 `/results` 時
- **THEN** 系統返回：
  - 過去 7 天的比賽結果
  - 按日期分組
  - 包含比分和統計
  - 標記爆冷門結果

#### Scenario: 查看特定球隊歷史
- **WHEN** 用戶執行 `/results lakers` 時
- **THEN** 系統返回：
  - 該球隊過去 10 場比賽
  - 顯示對手、比分、勝負
  - 顯示主客場表現
  - 顯示連勝/連敗記錄

#### Scenario: 結果統計
- **WHEN** 顯示結果統計時
- **THEN** 系統提供：
  - 勝率統計
  - 平均得分
  - 最大勝分差
  - 與特定對手的歷史戰績

### Requirement: System MUST handle schedule changes
系統必須檢測和處理賽程變更。

#### Scenario: 檢測賽程延期
- **WHEN** 檢測到比賽延期時
- **THEN** 系統執行：
  - 比較最新賽程和歷史記錄
  - 識別延期比賽
  - 更新賽程顯示
  - 通知相關用戶
  - 記錄延期原因

#### Scenario: 檢測比賽取消
- **WHEN** 檢測到比賽取消時
- **THEN** 系統執行：
  - 標記比賽為 "已取消"
  - 顯示取消原因 (如果可獲取)
  - 檢查是否有補賽計劃
  - 通知訂閱用戶

#### Scenario: 檢測時間變更
- **WHEN** 檢測到開賽時間變更時
- **THEN** 系統執行：
  - 記錄原時間和新時間
  - 更新賽程顯示
  - 重新計算提醒時間
  - 通知設置提醒的用戶

#### Scenario: 自動更新賽程
- **WHEN** 定期檢查賽程變更時
- **THEN** 系統執行：
  - 每小時檢查一次賽程變更
  - 比較最新數據
  - 自動更新數據庫
  - 生成變更報告

### Requirement: System MUST provide calendar integration
系統必須支持日曆集成功能。

#### Scenario: 導出賽程到日曆
- **WHEN** 用戶執行 `/export_schedule` 時
- **THEN** 系統執行：
  - 生成 iCalendar (.ics) 格式文件
  - 包含未來 30 天的賽程
  - 包含比賽時間、對戰、現場
  - 提供下載鏈接

#### Scenario: 生成 Google Calendar 鏈接
- **WHEN** 用戶需要 Google Calendar 集成時
- **THEN** 系統生成：
  - Google Calendar 添加鏈接
  - 包含所有必要信息
  - 支持單個事件添加
  - 提供批量添加選項

#### Scenario: 賽程分享
- **WHEN** 用戶想分享賽程時
- **THEN** 系統支持：
  - 生成賽程分享鏈接
  - 包含賽程摘要圖片
  - 發送到其他平台 (WhatsApp, Email)
  - 生成專屬分享頁面

### Requirement: System MUST implement schedule caching
系統必須實現賽程數據的緩存策略。

#### Scenario: 緩存未來賽程
- **WHEN** 緩存賽程數據時
- **THEN** 系統執行：
  - 未來 1 周內的比賽：緩存 6 小時
  - 未來 2-4 周的比赛：緩存 24 小時
  - 未來 1-3 個月的比赛：緩存 48 小時
  - 季后賽賽程：緩存時間加倍

#### Scenario: 緩存歷史結果
- **WHEN** 緩存比賽結果時
- **THEN** 系統執行：
  - 昨日比赛：緩存 12 小時
  - 過去 7 天：緩存 24 小時
  - 過去 30 天：緩存 72 小時
  - 更早結果：緩存 168 小時

#### Scenario: 緩存失效策略
- **WHEN** 緩存過期時
- **THEN** 系統執行：
  - 自動重新獲取數據
  - 如果獲取失敗，使用舊緩存
  - 標記數據為 "可能過期"
  - 記錄緩存失效次數

### Requirement: System MUST provide intelligent scheduling suggestions
系統必須提供智能賽程建議。

#### Scenario: 推薦精彩比賽
- **WHEN** 用戶查詢賽程時
- **THEN** 系統可以推薦：
  - 戰績接近的比赛
  - 明星球員對決
  - 德比戰
  - 季后賽預演

#### Scenario: 比賽重要性評分
- **WHEN** 評估比賽重要性時
- **THEN** 系統考慮：
  - 球隊戰績差距
  - 排名影響
  - 球員恩怨情仇
  - 歷史對戰記錄
  - 計算 1-10 重要性分數

#### Scenario: 個性化推薦
- **WHEN** 為用戶推薦時
- **THEN** 系統基於：
  - 用戶收藏的球隊
  - 過往查詢記錄
  - 互動偏好
  - 時間可用性
  - 生成個性化推薦列表

### Requirement: System MUST support notification scheduling
系統必須支持賽程通知功能。

#### Scenario: 設置開賽提醒
- **WHEN** 用戶設置提醒時
- **THEN** 系統記錄：
  - 比賽信息
  - 提醒時間 (開賽前 X 分鐘)
  - 通知方式
  - 重複設置 (如果適用)

#### Scenario: 發送提醒通知
- **WHEN** 到達提醒時間時
- **THEN** 系統執行：
  - 檢查比賽狀態 (是否延期/取消)
  - 發送提醒消息
  - 包含比賽信息和觀看方式
  - 記錄發送結果

#### Scenario: 管理提醒
- **WHEN** 用戶管理提醒時
- **THEN** 系統支持：
  - 查看所有提醒：`/reminders`
  - 取消提醒：`/cancel_reminder 提醒ID`
  - 修改提醒時間：`/update_reminder`
  - 清空所有提醒：`/clear_reminders`

## 數據模型

### SportsSchedule
```python
@dataclass
class SportsSchedule:
    match_id: str
    sport_type: str  # 'nba', 'soccer'
    home_team: str
    away_team: str
    start_time: datetime
    venue: Optional[str] = None
    competition: Optional[str] = None
    importance_score: float = 0.0  # 1-10
    is_playoff: bool = False
    is_national: bool = False  # 是否為國際比賽
    last_updated: datetime = field(default_factory=datetime.now)

    @property
    def days_until_match(self) -> int:
        """返回距離比賽的天數"""
        delta = self.start_time - datetime.now()
        return max(0, delta.days)
```

### MatchResult
```python
@dataclass
class MatchResult:
    match_id: str
    sport_type: str
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    start_time: datetime
    end_time: datetime
    venue: Optional[str] = None
    attendance: Optional[int] = None
    competition: Optional[str] = None
    highlights: Optional[List[str]] = None  # 精彩片段

    @property
    def winner(self) -> str:
        """返回勝隊名稱"""
        if self.home_score > self.away_score:
            return self.home_team
        elif self.away_score > self.home_score:
            return self.away_team
        return "平局"

    @property
    def margin(self) -> int:
        """返回勝分差"""
        return abs(self.home_score - self.away_score)
```

### ScheduleNotification
```python
@dataclass
class ScheduleNotification:
    notification_id: str
    user_id: int
    match_id: str
    reminder_time: datetime
    created_at: datetime
    status: NotificationStatus = NotificationStatus.ACTIVE
    message_sent: bool = False

    @property
    def is_due(self) -> bool:
        """檢查是否到達提醒時間"""
        return datetime.now() >= self.reminder_time
```

### NotificationStatus
```python
from enum import Enum

class NotificationStatus(Enum):
    ACTIVE = "active"
    SENT = "sent"
    CANCELLED = "cancelled"
    FAILED = "failed"
```

## 性能要求

- **查詢響應時間**: < 2 秒
- **賽程聚合時間**: < 5 秒
- **緩存更新時間**: < 10 分鐘
- **提醒發送時間**: < 5 秒
- **數據覆蓋率**: > 95%
- **準確率**: > 98%

## 監控指標

1. 賽程查詢頻率
2. 緩存命中率
3. 提醒發送成功率
4. 賽程變更檢測率
5. 數據準確性
6. 用戶滿意度
7. 系統響應時間
8. 資源使用率

## 限制策略

- 每個用戶最多設置 20 個提醒
- 每分鐘最多查詢 5 次賽程
- 導出功能每小時最多 3 次
- 批量操作最多 100 場比賽

## 相關規格

- `specs/sports-scoring` - 體育比分核心框架
- `specs/nba-scoring` - NBA 比分特定實現
- `specs/football-scoring` - 足球比分特定實現
- `specs/telegram-bot` - Telegram Bot 集成
- `specs/web-scraping` - 網頁爬取基礎
