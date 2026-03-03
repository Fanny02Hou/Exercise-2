#!/usr/bin/env python3
"""
氣象站地圖視覺化腳本
使用 folium 在地圖上標示測站位置，依氣溫進行分色顯示
"""

import pandas as pd
import folium
from folium.plugins import HeatMap
from folium.plugins import MarkerCluster
import branca.colormap as cm
import os
from datetime import datetime
import math
import base64

class WeatherMapVisualizer:
    def __init__(self):
        self.temperature_colors = {
            'cold': '#0000FF',      # 藍色 - 氣溫 < 20°C
            'normal': '#00FF00',    # 綠色 - 20°C ≤ 氣溫 ≤ 28°C  
            'hot': '#FFA500'        # 橘色 - 氣溫 > 28°C
        }
    
    def get_temperature_color(self, temperature):
        """根據氣溫回傳對應顏色"""
        if temperature is None:
            return '#808080'  # 灰色 - 無資料
        
        if temperature < 20:
            return self.temperature_colors['cold']
        elif temperature <= 28:
            return self.temperature_colors['normal']
        else:
            return self.temperature_colors['hot']
    
    def create_popup_content(self, station_data):
        """建立彈出視窗內容"""
        temp = station_data['temperature']
        humidity = station_data['humidity']
        weather = station_data['weather']
        wind_speed = station_data['wind_speed']
        wind_direction = station_data['wind_direction']
        air_pressure = station_data['air_pressure']
        obs_time = station_data['observation_time']
        
        # 格式化觀測時間
        try:
            formatted_time = pd.to_datetime(obs_time).strftime('%Y-%m-%d %H:%M')
        except:
            formatted_time = obs_time
        
        popup_html = f"""
        <div style="font-family: Arial, sans-serif; width: 250px;">
            <h4 style="margin: 0 0 10px 0; color: #333;">{station_data['station_name']}</h4>
            <p style="margin: 5px 0;"><strong>地點:</strong> {station_data['location']}</p>
            <p style="margin: 5px 0;"><strong>溫度:</strong> <span style="font-size: 16px; font-weight: bold; color: {self.get_temperature_color(temp)};">{temp}°C</span></p>
            <p style="margin: 5px 0;"><strong>濕度:</strong> {humidity}%</p>
            <p style="margin: 5px 0;"><strong>天氣:</strong> {weather}</p>
            <p style="margin: 5px 0;"><strong>風速:</strong> {wind_speed} m/s</p>
            <p style="margin: 5px 0;"><strong>風向:</strong> {wind_direction}°</p>
            <p style="margin: 5px 0;"><strong>氣壓:</strong> {air_pressure} hPa</p>
            <p style="margin: 5px 0; font-size: 12px; color: #666;"><strong>觀測時間:</strong> {formatted_time}</p>
        </div>
        """
        
        return popup_html

    def _haversine_meters(self, lat1, lon1, lat2, lon2):
        if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
            return None
        if pd.isna(lat1) or pd.isna(lon1) or pd.isna(lat2) or pd.isna(lon2):
            return None

        r = 6371008.8
        phi1 = math.radians(float(lat1))
        phi2 = math.radians(float(lat2))
        dphi = math.radians(float(lat2) - float(lat1))
        dlambda = math.radians(float(lon2) - float(lon1))

        a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * (math.sin(dlambda / 2.0) ** 2)
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return r * c
    
    def create_weather_map(self, csv_file, output_file=None):
        """建立氣象地圖"""
        # 讀取 CSV 資料
        try:
            df = pd.read_csv(csv_file)
            print(f"成功讀取 {len(df)} 筆測站資料")
        except Exception as e:
            print(f"讀取 CSV 檔案失敗: {e}")
            return None
        
        # 過濾有效座標資料
        coord0_available = 'coord0_latitude' in df.columns and 'coord0_longitude' in df.columns
        coord1_available = 'coord1_latitude' in df.columns and 'coord1_longitude' in df.columns

        if coord0_available:
            valid0 = df.dropna(subset=['coord0_latitude', 'coord0_longitude'])
        else:
            valid0 = df.iloc[0:0]

        if coord1_available:
            valid1 = df.dropna(subset=['coord1_latitude', 'coord1_longitude'])
        else:
            valid1 = df.dropna(subset=['latitude', 'longitude'])

        valid_df = pd.concat([valid0, valid1], ignore_index=True)
        print(f"有效座標資料: coord0={len(valid0)} 筆, coord1={len(valid1)} 筆")
        
        if len(valid_df) == 0:
            print("沒有有效的座標資料")
            return None
        
        # 計算地圖中心點（台灣中心）
        center_lat = pd.concat([
            valid0.get('coord0_latitude', pd.Series(dtype=float)),
            valid1.get('coord1_latitude', valid1.get('latitude', pd.Series(dtype=float)))
        ], ignore_index=True).mean()
        center_lon = pd.concat([
            valid0.get('coord0_longitude', pd.Series(dtype=float)),
            valid1.get('coord1_longitude', valid1.get('longitude', pd.Series(dtype=float)))
        ], ignore_index=True).mean()
        
        # 建立地圖
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=7,
            tiles='OpenStreetMap'
        )

        # 直接使用非群集圖層，不加入圖層控制
        fg0_plain = folium.FeatureGroup(name='TWD67', show=True)
        fg1_plain = folium.FeatureGroup(name='WGS84', show=True)
        fg0_plain.add_to(m)
        fg1_plain.add_to(m)
        
        # 加入溫度色階圖例
        colormap = cm.LinearColormap(
            colors=['#0000FF', '#00FF00', '#FFA500'],
            vmin=0,
            vmax=35,
            caption='氣溫 (°C)'
        )
        colormap.add_to(m)
        
        # 統計資料
        temp_stats = {
            'cold': 0,
            'normal': 0, 
            'hot': 0,
            'no_data': 0
        }

        distances = []
        station_distances = []

        all_points = []

        for idx, row in valid0.iterrows():
            lat = row['coord0_latitude']
            lon = row['coord0_longitude']
            temp = row.get('temperature')
            if pd.isna(temp):
                color = '#808080'
                temp_stats['no_data'] += 1
            elif temp < 20:
                color = self.temperature_colors['cold']
                temp_stats['cold'] += 1
            elif temp <= 28:
                color = self.temperature_colors['normal']
                temp_stats['normal'] += 1
            else:
                color = self.temperature_colors['hot']
                temp_stats['hot'] += 1

            popup_content = self.create_popup_content(row)
            popup_content += f"<p style='margin:5px 0; font-size:12px; color:#666;'><strong>座標系統:</strong> {row['coord0_crs']}</p>"

            # Coordinates[0] 使用圓形
            marker = folium.CircleMarker(
                location=[lat, lon],
                radius=8,
                popup=folium.Popup(popup_content, max_width=300),
                color='black',
                weight=1,
                fillColor=color,
                fillOpacity=0.8
            )
            marker.add_to(fg0_plain)

            all_points.append([lat, lon])

        for idx, row in valid1.iterrows():
            lat = row['coord1_latitude'] if coord1_available else row['latitude']
            lon = row['coord1_longitude'] if coord1_available else row['longitude']
            temp = row.get('temperature')
            if pd.isna(temp):
                color = '#808080'
                temp_stats['no_data'] += 1
            elif temp < 20:
                color = self.temperature_colors['cold']
                temp_stats['cold'] += 1
            elif temp <= 28:
                color = self.temperature_colors['normal']
                temp_stats['normal'] += 1
            else:
                color = self.temperature_colors['hot']
                temp_stats['hot'] += 1

            popup_content = self.create_popup_content(row)
            popup_content += f"<p style='margin:5px 0; font-size:12px; color:#666;'><strong>座標系統:</strong> {row['coord1_crs']}</p>"

            # Coordinates[1] 使用三角形
            # 創建自定義三角形 SVG 圖標
            triangle_svg = f'''
            <svg width="20" height="20" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                <polygon points="10,2 18,18 2,18" fill="{color}" stroke="black" stroke-width="1"/>
            </svg>
            '''
            
            triangle_icon = folium.features.CustomIcon(
                icon_image='data:image/svg+xml;base64,' + base64.b64encode(triangle_svg.encode()).decode(),
                icon_size=(20, 20)
            )
            
            marker = folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_content, max_width=300),
                icon=triangle_icon
            )
            marker.add_to(fg1_plain)

            all_points.append([lat, lon])

        for idx, row in df.iterrows():
            if coord0_available and not pd.isna(row['coord0_latitude']) and not pd.isna(row['coord0_longitude']) and not pd.isna(row['coord1_latitude']) and not pd.isna(row['coord1_longitude']):
                dist = self._haversine_meters(row['coord0_latitude'], row['coord0_longitude'], row['coord1_latitude'], row['coord1_longitude'])
                if dist is not None:
                    distances.append(dist)
                    station_distances.append({
                        'station_id': row['station_id'],
                        'station_name': row['station_name'],
                        'coord0_latitude': row['coord0_latitude'],
                        'coord0_longitude': row['coord0_longitude'],
                        'coord1_latitude': row['coord1_latitude'],
                        'coord1_longitude': row['coord1_longitude'],
                        'distance_meters': dist
                    })
                    
                    # 計算連線中點
                    mid_lat = (float(row['coord0_latitude']) + float(row['coord1_latitude'])) / 2
                    mid_lon = (float(row['coord0_longitude']) + float(row['coord1_longitude'])) / 2
                    
                    # 建立連線（移除距離標籤，避免堆疊問題）
                    line = folium.PolyLine(
                        locations=[[row['coord0_latitude'], row['coord0_longitude']], [row['coord1_latitude'], row['coord1_longitude']]],
                        color='gray',
                        weight=2,
                        opacity=0.6,
                        popup=folium.Popup(f"""
                        <div style="font-size: 12px;">
                            <strong>{row['station_name']}</strong><br>
                            TWD67 ↔ WGS84 距離差異<br>
                            <strong>{dist:.2f} 公尺</strong><br>
                            <small style="color: #666;">點擊連線查看距離資訊</small>
                        </div>
                        """, max_width=200)
                    )
                    line.add_to(m)
                    
        # 移除 JavaScript 控制邏輯，因為已經沒有距離標籤了

        if all_points:
            m.fit_bounds(all_points)
        
        # 加入統計資訊
        stats_html = f"""
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 240px; height: 140px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <h4 style="margin: 0 0 10px 0;">氣溫分佈統計</h4>
        <p style="margin: 5px 0;"><span style="color: #0000FF;">●</span> 低溫 (&lt;20°C): {temp_stats['cold']}</p>
        <p style="margin: 5px 0;"><span style="color: #00FF00;">●</span> 適中 (20-28°C): {temp_stats['normal']}</p>
        <p style="margin: 5px 0;"><span style="color: #FFA500;">●</span> 高溫 (&gt;28°C): {temp_stats['hot']}</p>
        <p style="margin: 5px 0;"><span style="color: #808080;">●</span> 無資料: {temp_stats['no_data']}</p>
        </div>
        """
        
        m.get_root().html.add_child(folium.Element(stats_html))

        legend_html = """
        <div style="position: fixed; 
                    bottom: 50px; right: 50px; width: 200px; height: 120px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <h4 style="margin: 0 0 10px 0;">圖示說明</h4>
        <p style="margin: 5px 0;"><span style="color: #000000;">●</span> TWD67 (圓形)</p>
        <p style="margin: 5px 0;"><span style="color: #000000;">▲</span> WGS84 (三角形)</p>
        <p style="margin: 5px 0; font-size:12px; color:#666;">點選測站連線查看距離差異</p>
        </div>
        """
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # 儲存地圖
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"outputs/weather_map_{timestamp}.html"
        
        m.save(output_file)
        print(f"地圖已儲存至: {output_file}")
        
        # 顯示統計資訊
        print(f"\n=== 氣溫分佈統計 ===")
        print(f"低溫測站 (<20°C): {temp_stats['cold']}")
        print(f"適中測站 (20-28°C): {temp_stats['normal']}")
        print(f"高溫測站 (>28°C): {temp_stats['hot']}")
        print(f"無資料測站: {temp_stats['no_data']}")

        if distances:
            import numpy as np
            distances_arr = np.array(distances)
            print(f"\n=== 座標距離統計 (coord0 vs coord1) ===")
            print(f"測站數量: {len(distances)}")
            print(f"平均距離: {distances_arr.mean():.2f} 公尺")
            print(f"中位數距離: {np.median(distances_arr):.2f} 公尺")
            print(f"最大距離: {distances_arr.max():.2f} 公尺")
            print(f"最小距離: {distances_arr.min():.2f} 公尺")

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            distance_detail_csv = f"outputs/station_distances_{timestamp}.csv"
            pd.DataFrame(station_distances).to_csv(distance_detail_csv, index=False, encoding='utf-8-sig')
            print(f"各測站座標距離明細已儲存至: {distance_detail_csv}")
        else:
            print("\n=== 座標距離統計 ===")
            print("無法計算座標距離（缺少有效座標資料）")

        print(f"\n=== 圖層說明 ===")
        print(f"- TWD67: 第一組座標（圓形標記）")
        print(f"- WGS84: 第二組座標（三角形標記）")
        print(f"- 灰色連線: 顯示同一測站兩組座標的連線")
        
        return output_file
    
    def create_heatmap(self, csv_file, output_file=None):
        """建立溫度熱力圖"""
        try:
            df = pd.read_csv(csv_file)
            print(f"成功讀取 {len(df)} 筆測站資料")
        except Exception as e:
            print(f"讀取 CSV 檔案失敗: {e}")
            return None
        
        # 過濾有效溫度和座標資料
        valid_df = df.dropna(subset=['latitude', 'longitude', 'temperature'])
        print(f"有效溫度資料: {len(valid_df)} 筆")
        
        if len(valid_df) == 0:
            print("沒有有效的溫度資料")
            return None
        
        # 計算地圖中心點
        center_lat = valid_df['latitude'].mean()
        center_lon = valid_df['longitude'].mean()
        
        # 建立地圖
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=7,
            tiles='OpenStreetMap'
        )
        
        # 準備熱力圖資料
        heat_data = [[row['latitude'], row['longitude'], row['temperature']] 
                    for idx, row in valid_df.iterrows()]
        
        # 加入熱力圖
        HeatMap(
            heat_data,
            min_opacity=0.4,
            radius=15,
            blur=10,
            gradient={0.0: 'blue', 0.3: 'cyan', 0.5: 'lime', 0.7: 'yellow', 1.0: 'red'}
        ).add_to(m)
        
        # 儲存熱力圖
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"outputs/weather_heatmap_{timestamp}.html"
        
        m.save(output_file)
        print(f"熱力圖已儲存至: {output_file}")
        
        return output_file

def main():
    """主程式"""
    # 查找最新的 CSV 檔案
    output_dir = "outputs"
    csv_files = [f for f in os.listdir(output_dir) if f.startswith('weather_stations_') and f.endswith('.csv')]
    
    if not csv_files:
        print("找不到氣象站 CSV 資料檔，請先執行 cwa_weather_api.py")
        return
    
    # 使用最新的檔案
    latest_csv = max(csv_files, key=lambda x: os.path.getmtime(os.path.join(output_dir, x)))
    csv_path = os.path.join(output_dir, latest_csv)
    print(f"使用資料檔案: {csv_path}")
    
    # 建立視覺化器
    visualizer = WeatherMapVisualizer()
    
    # 建立氣象地圖
    print("\n正在建立氣象地圖...")
    map_file = visualizer.create_weather_map(csv_path)
    
    # 建立熱力圖
    print("\n正在建立溫度熱力圖...")
    heatmap_file = visualizer.create_heatmap(csv_path)
    
    if map_file and heatmap_file:
        print(f"\n=== 地圖檔案 ===")
        print(f"氣象地圖: {map_file}")
        print(f"溫度熱力圖: {heatmap_file}")
        print("\n可以在瀏覽器中開啟 HTML 檔案查看地圖")

if __name__ == "__main__":
    main()
