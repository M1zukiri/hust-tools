import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

# ==========================================
# 1. Model Layer: 标准化数据结构
# ==========================================

@dataclass
class GeoPoint:
    """基础地理点模型：代表地图API返回的一个POI（兴趣点）"""
    lat: float
    lng: float
    name: str           # 地点名称，如 "上海东方明珠塔"
    source_keyword: str # 来源关键词，如 "东方明珠"
    
    def __repr__(self):
        return f"<{self.name} ({self.lat:.4f}, {self.lng:.4f})>"

@dataclass
class WeightedPoint:
    """带权重的计算点：核心算法使用的内部结构"""
    point: GeoPoint
    weight: float       # 基于稀缺性的权重

@dataclass
class LocalizationResult:
    """最终定位结果"""
    center_lat: float
    center_lng: float
    radius_meters: float
    confidence_score: float
    matched_keywords: List[str] # 命中了哪些关键词
    description: str            # 对定位结果的文本描述

# ==========================================
# 2. Provider Layer: 数据接口与模拟实现
# ==========================================

class MapDataProvider(ABC):
    """抽象基类：强制规范所有地图API必须实现的方法"""
    
    @abstractmethod
    def search_keyword(self, keyword: str) -> List[GeoPoint]:
        """输入关键词，返回一系列地理坐标点"""
        pass

import requests
# 引入之前定义的类 (假设你在同一个文件中，如果分文件了请 import 进来)
# from fuzzy_locator import MapDataProvider, GeoPoint, FuzzyLocationEngine

class AmapServiceProvider(MapDataProvider):
    """
    真实的高德地图数据提供者
    文档参考: https://lbs.amap.com/api/webservice/guide/api/search
    """
    
    def __init__(self, api_key: str, city_limit: bool = False):
        self.api_key = api_key
        self.base_url = "https://restapi.amap.com/v3/place/text"
        self.city_limit = city_limit

    def search_keyword(self, keyword: str) -> List[GeoPoint]:
        """
        实现接口：调用高德 API 获取数据并转化为 GeoPoint 列表
        """
        # 1. 构建请求参数
        params = {
            "key": self.api_key,
            "keywords": keyword,
            "city": "全国",        # 默认搜索全国，你也可以指定具体城市编码
            "offset": 20,         # 每页记录数据：默认20，最大25
            "page": 1,            # 当前页数：为了演示我们只取第一页（Top 20）
            "extensions": "base"  # 返回基本信息
        }

        try:
            # 2. 发送 HTTP GET 请求
            response = requests.get(self.base_url, params=params, timeout=5)
            data = response.json()

            # 3. 错误处理
            if data.get("status") != "1":
                print(f"[API Error] 高德接口返回错误: {data.get('info')}")
                return []

            pois = data.get("pois", [])
            geo_points = []

            # 4. 数据清洗与转化
            for poi in pois:
                # 高德返回的 location 格式为 "经度,纬度" (例如 "116.481488,39.990464")
                location_str = poi.get("location", "")
                if not location_str:
                    continue
                
                try:
                    lng_str, lat_str = location_str.split(",")
                    lng, lat = float(lng_str), float(lat_str)
                    
                    # 创建我们的标准数据对象
                    # 注意：高德使用的是 GCJ-02 坐标系
                    geo_points.append(GeoPoint(
                        lat=lat,
                        lng=lng,
                        name=poi.get("name"),
                        source_keyword=keyword
                    ))
                except ValueError:
                    continue # 忽略坐标解析失败的点

            return geo_points

        except requests.exceptions.RequestException as e:
            print(f"[Network Error] 请求高德API失败: {e}")
            return []


# ==========================================
# 3. Utilities: 地理计算工具
# ==========================================

class GeoUtils:
    """地理计算工具类"""
    
    EARTH_RADIUS = 6371000  # 地球半径 (米)

    @staticmethod
    def haversine_distance(lat1, lon1, lat2, lon2) -> float:
        """计算两点间的球面距离 (单位: 米)"""
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) * math.sin(dlat / 2) +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) * math.sin(dlon / 2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return GeoUtils.EARTH_RADIUS * c

# ==========================================
# 4. Core Layer: 模糊定位引擎
# ==========================================

class FuzzyLocationEngine:
    def __init__(self, provider: MapDataProvider):
        self.provider = provider

    def _calculate_weights(self, keyword_counts: Dict[str, int]) -> Dict[str, float]:
        """
        计算权重策略：
        稀缺性越高，权重越大。
        这里使用了归一化的倒数逻辑，并做了一个简单的平滑处理。
        """
        weights = {}
        total_points = sum(keyword_counts.values())
        
        for kw, count in keyword_counts.items():
            if count == 0:
                weights[kw] = 0
                continue
            # 逻辑：权重 = (总点数 / 该词点数) 的对数。
            # 加上 1.0 防止 log(1) = 0 导致权重消失
            weights[kw] = math.log((total_points / count) + 1.0)
            
        return weights

    def solve(self, keywords: List[str], search_radius_meters: float = 2000.0) -> Optional[LocalizationResult]:
        """
        核心执行函数
        1. 获取数据
        2. 计算权重
        3. 密度搜索
        """
        all_points: List[GeoPoint] = []
        keyword_point_map: Dict[str, List[GeoPoint]] = {}
        
        # --- 步骤 1: 数据获取 ---
        print(">> 正在从 API 获取数据...")
        for kw in keywords:
            points = self.provider.search_keyword(kw)
            keyword_point_map[kw] = points
            all_points.extend(points)
            print(f"   关键词 '{kw}' 检索到 {len(points)} 个位置。")

        if not all_points:
            return None

        # --- 步骤 2: 权重计算 ---
        # 统计每个关键词出现的总次数，以此决定稀缺性
        counts = {kw: len(pts) for kw, pts in keyword_point_map.items()}
        weight_map = self._calculate_weights(counts)
        
        # 将原始点转换为带权重点
        weighted_points: List[WeightedPoint] = []
        for p in all_points:
            w = weight_map.get(p.source_keyword, 0.0)
            weighted_points.append(WeightedPoint(p, w))
            
        print(f">> 权重计算完成: {weight_map}")

        # --- 步骤 3: 密度极大值搜索 (Density Maximization) ---
        # 策略：以“高权重”的点作为锚点(Candidate Anchor)，画圆搜索
        
        best_score = -1.0
        best_anchor = None
        best_covered_keywords = set()
        
        # 优化：为了演示，我们简单遍历所有点作为圆心。
        # 在生产环境中，应该只选取 weight > threshold 的点作为圆心候选，减少计算量。
        for anchor in weighted_points:
            current_score = 0.0
            current_keywords = set()
            
            # 计算该圆心周围所有点的权重和
            # 注意：这里是 O(N^2) 的暴力实现。
            # 生产环境请务必使用 KDTree 或 R-Tree 进行 range_query 优化到 O(N log N)
            for neighbor in weighted_points:
                dist = GeoUtils.haversine_distance(
                    anchor.point.lat, anchor.point.lng,
                    neighbor.point.lat, neighbor.point.lng
                )
                
                if dist <= search_radius_meters:
                    current_score += neighbor.weight
                    current_keywords.add(neighbor.point.source_keyword)
            
            # 记录最佳结果
            if current_score > best_score:
                best_score = current_score
                best_anchor = anchor.point
                best_covered_keywords = current_keywords

        # --- 步骤 4: 结果封装 ---
        if best_anchor:
            return LocalizationResult(
                center_lat=best_anchor.lat,
                center_lng=best_anchor.lng,
                radius_meters=search_radius_meters,
                confidence_score=best_score,
                matched_keywords=list(best_covered_keywords),
                description=f"定位中心位于: {best_anchor.name} 附近"
            )
        return None

# ==========================================
# 5. Main: 运行演示
# ==========================================


if __name__ == "__main__":
    # 【重要】请在这里填入你申请的高德 Web服务 Key
    AMAP_KEY = "0d897626ef902be828e71678b9d849c6"
    
    if AMAP_KEY == "":
        print("请先在代码中填入高德地图 API Key！")
    else:
        # 1. 实例化真实的数据提供者
        real_provider = AmapServiceProvider(api_key=AMAP_KEY)
        
        # 2. 实例化引擎 (完全不需要修改核心逻辑)
        engine = FuzzyLocationEngine(provider=real_provider)
        
        # 3. 真实测试
        # 场景：我们在描述上海陆家嘴附近
        user_inputs = ["世界城广场", "佳园路", "皇冠幸福里", "猪猪很忙"]
        
        print(f"用户输入: {user_inputs}")
        print("-" * 30)
      
        # 注意：真实地图数据量大，建议适当减小半径以提高精度，或增大半径以提高容错
        result = engine.solve(user_inputs, search_radius_meters=5000)
        
        print("-" * 30)
        if result:
            print("【定位成功】")
            print(f"描述: {result.description}")
            print(f"坐标: ({result.center_lat:.6f}, {result.center_lng:.6f})")
            print(f"置信度得分: {result.confidence_score:.2f}")
            print(f"匹配到的关键词: {result.matched_keywords}")
            
            # 这里可以生成一个高德地图链接方便查看
            print(f"查看地图: https://uri.amap.com/marker?position={result.center_lng},{result.center_lat}&name=Result")
        else:
            print("【定位失败】API 未返回足够数据或没有重叠区域。")