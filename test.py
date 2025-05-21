from typing import Any
import httpx #异步HTTP客户端库
from mcp.server.fastmcp import FastMCP #FastMCP框架的核心类，轻量级RPC框架，用于注册和调用工具函数

# Initialize FastMCP server
mcp = FastMCP("weather") #创建FastMCP服务实例，名称为"weather"，后续工具函数将通过该实例注册

# Constants
NWS_API_BASE = "https://api.weather.gov" #NWS API基础URL
USER_AGENT = "weather-app/1.0" #符合NWS要求的User-Agent

#发起异步请求
async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""
    headers = {
        "User-Agent": USER_AGENT, #必须的请求头
        "Accept": "application/geo+json" #指定返回geoJSON格式
    }
    async with httpx.AsyncClient() as client: #创建异步客户端
        try:
            response = await client.get(url, headers=headers, timeout=30.0) #发起GET请求，超时30秒
            response.raise_for_status() #如果HTTP状态码非2xx，抛出异常
            return response.json() #解析响应为JSON字典
        except Exception:
            return None

#格式化单一的天气警报
def format_alert(feature: dict) -> str:
    """Format an alert feature into a readable string."""
    props = feature["properties"]  #提取警报属性
    return f"""
Event: {props.get('event', 'Unknown')}
Area: {props.get('areaDesc', 'Unknown')}
Severity: {props.get('severity', 'Unknown')}
Description: {props.get('description', 'No description available')}
Instructions: {props.get('instruction', 'No specific instructions provided')}
"""

@mcp.tool() #注册为FastMCP可调用工具
#获取指定州的天气预警
async def get_alerts(state: str) -> str:
    """Get weather alerts for a US state.

    Args:
        state: Two-letter US state code (e.g. CA, NY)
    """
    url = f"{NWS_API_BASE}/alerts/active/area/{state}" #指定州的API URL
    data = await make_nws_request(url) #发起异步请求

    if not data or "features" not in data: #检查数据有效性
        return "Unable to fetch alerts or no alerts found."

    if not data["features"]:  #无警报时的处理
        return "No active alerts for this state."

    alerts = [format_alert(feature) for feature in data["features"]] #格式化所有警报
    return "\n---\n".join(alerts) #用分隔符连接多个警报

@mcp.tool()
#获取经纬度的天气预报
async def get_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location.

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
    """
    #步骤1: 获取网格点数据
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)

    if not points_data:  #检查数据是否有效
        return "Unable to fetch forecast data for this location."

    #步骤2: 提取预报URL
    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await make_nws_request(forecast_url)

    if not forecast_data:
        return "Unable to fetch detailed forecast."

    #步骤3: 格式化预报数据
    periods = forecast_data["properties"]["periods"]  #获取预报时段列表
    forecasts = []
    for period in periods[:5]:  #只处理前5个时段
        forecast = f"""
{period['name']}:
Temperature: {period['temperature']}°{period['temperatureUnit']}
Wind: {period['windSpeed']} {period['windDirection']}
Forecast: {period['detailedForecast']}
"""
        forecasts.append(forecast)

    return "\n---\n".join(forecasts) #连接多个预报时段

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')