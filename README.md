# Weather Station Dual Coordinate Visualization Project

## 專案概述
這是一個氣象站雙坐標系統視覺化專案，主要功能包括：
- 串接中央氣象署 (CWA) 自動氣象站觀測 API
- 解析每個測站的兩套坐標系統（TWD67 和 WGS84）
- 計算兩套坐標系統之間的距離差異
- 使用 Folium 進行互動式地圖視覺化
- 依氣溫進行分色標示，並用不同圖標區分坐標系統

## 專案結構
```
Exercise-2/
├── outputs/                # 分析結果輸出
│   ├── weather_stations_*.csv        # 氣象站資料（含雙坐標）
│   ├── weather_map_*.html           # 氣象地圖（雙坐標視覺化）
│   ├── weather_heatmap_*.html        # 溫度熱力圖
│   └── station_distances_*.csv      # 測站坐標距離明細
├── scripts/                # 分析腳本
│   ├── cwa_weather_api.py           # CWA API 串接與坐標解析
│   ├── debug_api.py                # API 調試工具
│   └── weather_map_visualization.py # 雙坐標地圖視覺化
├── .env                    # API 金鑰設定
├── .gitignore              # Git 忽略檔案
├── requirements.txt        # Python 套件依賴
└── README.md              # 專案說明文件
```

## 安裝與設定

### 1. 安裝依賴套件
```bash
pip install -r requirements.txt
```

### 2. 設定 API 金鑰
在 `.env` 檔案中加入您的中央氣象署 API 金鑰：
```
CWA_API_KEY=your_cwa_api_key_here
```

### 3. 執行腳本

#### 獲取氣象資料
```bash
python scripts/cwa_weather_api.py
```
這會解析每個測站的 TWD67 和 WGS84 坐標，並儲存到 CSV。

#### 生成雙坐標地圖視覺化
```bash
python scripts/weather_map_visualization.py
```
這會生成包含兩套坐標系統的互動式地圖。

## 功能特色

### 雙坐標系統解析
- **TWD67 坐標**：台灣舊版二度分帶坐標系統
- **WGS84 坐標**：世界大地坐標系統（GPS 標準）
- 每個測站同時包含兩套坐標的完整資訊

### 地圖視覺化
- **圓形標記**：TWD67 坐標系統
- **三角形標記**：WGS84 坐標系統
- **溫度分色**：
  - 🔵 藍色：氣溫 < 20°C
  - 🟢 綠色：20°C ≤ 氣溫 ≤ 28°C
  - 🟠 橘色：氣溫 > 28°C
  - ⚫ 灰色：無溫度資料
- **灰色連線**：連接同一測站的兩套坐標
- **點擊連線**：顯示兩坐標系統的距離差異

### 距離分析
- 計算每個測站 TWD67 ↔ WGS84 的距離差異
- 使用 Haversine 公式計算球面距離
- 統計分析：平均距離、中位數、最大/最小距離
- 輸出詳細的距離明細 CSV 檔案

### 互動功能
- **自動縮放**：地圖自動調整以顯示所有測站
- **彈出視窗**：點擊標記顯示完整測站資訊
- **坐標系統標示**：彈出視窗顯示使用的坐標系統（TWD67/WGS84）
- **距離資訊**：點擊連線查看具體距離數值

## 資料統計輸出

執行後會顯示：
- 溫度分佈統計（低溫/適中/高溫測站數量）
- 坐標距離統計：
  - 平均距離：約 850 公尺
  - 距離範圍：670-963 公尺
  - 有效測站數量：336 個

## 技術棧
- **Python 3.10+**
- **Requests** - HTTP 請求處理
- **Pandas** - 資料處理與分析
- **Folium** - 互動式地圖視覺化
- **Math** - Haversine 距離計算
- **Base64** - 自定義圖標編碼

## API 資料來源
- 中央氣象署開放資料平台
- API: O-A0003-001 (自動氣象站觀測資料)
- 坐標系統：TWD67 和 WGS84 雙坐標
- 更新頻率：每小時

## 輸出檔案說明
- `weather_stations_*.csv` - 完整測站資料（含 coord0/coord1 坐標）
- `weather_map_*.html` - 雙坐標系統互動式地圖
- `weather_heatmap_*.html` - 溫度熱力圖
- `station_distances_*.csv` - 各測站坐標距離明細

## 使用場景
1. **坐標系統比較研究**：分析 TWD67 和 WGS84 的實際差異
2. **氣象監測**：查看全台氣象站即時溫度分佈
3. **地理資訊系統**：理解不同坐標系統的轉換關係
4. **教育展示**：視覺化展示台灣坐標系統的演進

## 注意事項
- 請確保 `.env` 檔案中的 API 金鑰正確設定
- 地圖檔案可在現代瀏覽器中直接開啟查看
- 兩套坐標系統的距離差異約為 850 公尺（因坐標系統不同）
- 建議定期更新氣象資料以獲取最新資訊

## 授權
MIT License
