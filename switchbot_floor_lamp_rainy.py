#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automatically controls a SwitchBot RGBICWW Floor Lamp based on today's
maximum precipitation probability from the Tsukumijima Weather API
(T00_06/T06_12/T12_18/T18_24 max value).

- USE_COLOR_TEMPERATURE=0: RGB mapping (original color scheme)
- USE_COLOR_TEMPERATURE=1: Linear mapping 0%->2700K (warm) ~ 100%->6500K (cool)
"""

import base64
import hashlib
import hmac
import json
import logging
import os
import re
import time
import uuid
from typing import Tuple, Optional, Dict

import requests
from dotenv import load_dotenv

# ------------------------------
# Logging
# ------------------------------
formatter = "[%(levelname)-8s] %(asctime)s %(name)-12s %(message)s"
logging.basicConfig(level=logging.INFO, format=formatter)
logger = logging.getLogger("switchbot-floor-lamp")

# ------------------------------
# Env
# ------------------------------
load_dotenv()

ACCESS_TOKEN = os.environ["SWITCHBOT_ACCESS_TOKEN"]
SECRET = os.environ["SWITCHBOT_SECRET"]
DEVICE_ID = os.environ["SWITCHBOT_FLOOR_LAMP_DEVICE_ID"]  # Set Floor Lamp Device ID
CITY_CODE = os.environ["WEATHER_CITY_CODE"]    # Example: 130010 = Tokyo (Tokyo area)

# Set to 1 for color temperature mode (any value other than 0/false is treated as true)
USE_COLOR_TEMPERATURE = os.getenv("USE_COLOR_TEMPERATURE", "0").lower() in ("1", "true", "t", "yes", "y")

# Discord settings
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
DISCORD_ENABLED = os.getenv("DISCORD_ENABLED", "1").lower() in ("1", "true", "t", "yes", "y")
DISCORD_TIMEOUT = int(os.getenv("DISCORD_TIMEOUT", "10"))

API_BASE_URL = "https://api.switch-bot.com"
WEATHER_URL = "https://weather.tsukumijima.net/api/forecast/city"
HTTP_TIMEOUT = 10  # seconds

# ------------------------------
# Weather helpers
# ------------------------------
def _to_int_pct(s: str) -> int:
    """Safely convert '40%' or empty string '' to int"""
    return int(re.sub(r"\D", "", s or "") or 0)

def get_today_rain_percent_max_all(city_code: str) -> Tuple[int, dict]:
    """
    Get today's maximum precipitation probability from Tsukumijima API
    across 3 time slots T06_12/T12_18/T18_24 (T00_06 excluded).
    Returns: (max precipitation probability, weather data dict)
    Returns (0, {}) on failure.
    """
    url = f"{WEATHER_URL}/{city_code}"
    try:
        r = requests.get(url, timeout=HTTP_TIMEOUT)
        r.raise_for_status()
        data = r.json()
        rain: Dict[str, str] = data["forecasts"][0]["chanceOfRain"]  # 0: today
    except Exception as e:
        logger.error(f"Weather API error: {e}")
        return 0, {}

    slots = {
        "T06_12": _to_int_pct(rain.get("T06_12", "")),
        "T12_18": _to_int_pct(rain.get("T12_18", "")),
        "T18_24": _to_int_pct(rain.get("T18_24", "")),
    }
    val = max(slots.values())
    logger.info(f"[max_daylight] slots={slots} -> use {val}%")
    return val, data

# ------------------------------
# SwitchBot auth & command
# ------------------------------
def generate_sign(token: str, secret: str, nonce: Optional[str] = None) -> Tuple[str, str, str]:
    """Generate SwitchBot API v1.1 signature"""
    if nonce is None:
        nonce = str(uuid.uuid4())
    t = str(int(round(time.time() * 1000)))
    msg = f"{token}{t}{nonce}".encode("utf-8")
    secret_bytes = secret.encode("utf-8")
    sign = base64.b64encode(hmac.new(secret_bytes, msg=msg, digestmod=hashlib.sha256).digest()).decode("utf-8")
    return t, sign, nonce

def post_command(
    device_id: str,
    command: str,
    parameter: str = "default",
    command_type: str = "command",
) -> Optional[dict]:
    """
    Send command to specified device. Logs success/failure, returns JSON (None on failure).
    """
    t, sign, nonce = generate_sign(ACCESS_TOKEN, SECRET)
    headers = {
        "Content-Type": "application/json; charset=utf8",
        "Authorization": ACCESS_TOKEN,
        "t": t,
        "sign": sign,
        "nonce": nonce,
    }
    url = f"{API_BASE_URL}/v1.1/devices/{device_id}/commands"
    body = {"command": command, "parameter": parameter, "commandType": command_type}
    data = json.dumps(body)

    try:
        logger.info(f"POST {url} {data}")
        r = requests.post(url, data=data, headers=headers, timeout=HTTP_TIMEOUT)
        r.raise_for_status()
        payload = r.json()
        if payload.get("statusCode") != 100:
            logger.error(f"SwitchBot error: {payload}")
        else:
            logger.info(f"SwitchBot OK: {payload}")
        return payload
    except requests.exceptions.RequestException as e:
        logger.error(f"SwitchBot request error: {e}")
        return None

# ------------------------------
# Floor Lamp operations
# ------------------------------
def clamp_brightness(brightness: int) -> int:
    try:
        b = int(brightness)
    except Exception:
        b = 100
    return max(1, min(100, b))

def set_lamp_rgb(device_id: str, color: Tuple[int, int, int], brightness: int = 100):
    """
    Turn on Floor Lamp in RGB mode.
    - color: (R,G,B) each 0-255
    - brightness: 1-100
    """
    (r, g, b) = [max(0, min(255, int(v))) for v in color]
    brightness = clamp_brightness(brightness)

    post_command(device_id, "setBrightness", str(brightness))
    post_command(device_id, "setColor", f"{r}:{g}:{b}")
    post_command(device_id, "turnOn")

def set_lamp_ct(device_id: str, color_temperature: int, brightness: int = 100):
    """
    Turn on Floor Lamp in color temperature (CT) mode.
    - color_temperature: 2700-6500 K
    - brightness: 1-100
    """
    ct = max(2700, min(6500, int(color_temperature)))
    brightness = clamp_brightness(brightness)

    post_command(device_id, "setBrightness", str(brightness))
    post_command(device_id, "setColorTemperature", str(ct))
    post_command(device_id, "turnOn")

# ------------------------------
# Mapping: rain% -> RGB / CT
# ------------------------------
def map_rain_to_rgb(rain: int) -> Tuple[int, int, int]:
    """
    Map precipitation probability (%) to RGB color (original scheme).
      0%      -> orange   (255,127,0)
      ≤20%    -> yellow   (255,255,0)
      ≤40%    -> lime     (127,255,0)
      ≤60%    -> cyan     (0,255,255)
      ≤80%    -> blue-ish (0,127,255)
      >80%    -> deep blue (0,0,255)
    """
    if rain == 0:
        return (255, 127, 0)
    if rain <= 20:
        return (255, 255, 0)
    if rain <= 40:
        return (127, 255, 0)
    if rain <= 60:
        return (0, 255, 255)
    if rain <= 80:
        return (0, 127, 255)
    return (0, 0, 255)

def map_rain_to_ct(rain: int) -> int:
    """
    Linear transformation from precipitation probability (%) to color temperature (K).
      0% -> 2700K (warm) ... 100% -> 6500K (cool)
    """
    rain = max(0, min(100, int(rain)))
    ct_min, ct_max = 2700, 6500
    return int(ct_min + (ct_max - ct_min) * (rain / 100.0))

# ------------------------------
# Discord helpers
# ------------------------------
def rgb_to_decimal(rgb: Tuple[int, int, int]) -> int:
    """Convert RGB tuple to Discord color integer value (decimal)"""
    r, g, b = rgb
    return (r << 16) + (g << 8) + b

def format_temperature(temp: dict) -> str:
    """Format temperature data to string (e.g., "9C / 15C", "Max 15C", or "--")"""
    if not temp or "min" not in temp or "max" not in temp:
        return "--"

    min_data = temp.get("min", {})
    max_data = temp.get("max", {})

    # celsius is string or null
    min_c = min_data.get("celsius") if isinstance(min_data, dict) else None
    max_c = max_data.get("celsius") if isinstance(max_data, dict) else None

    # Exclude empty strings or null/None
    min_c = min_c if min_c and min_c.strip() else None
    max_c = max_c if max_c and max_c.strip() else None

    # If both exist, "9C / 15C"
    if min_c and max_c:
        return f"{min_c}C / {max_c}C"
    # If only max temp, "Max 15C"
    if max_c:
        return f"Max {max_c}C"
    # If only min temp, "Min 9C"
    if min_c:
        return f"Min {min_c}C"
    # If neither, "--"
    return "--"

def build_discord_embed(weather_data: dict, lamp_setting: dict) -> dict:
    """Build Discord Embed object"""
    if not weather_data:
        return {}

    forecast = weather_data.get("forecasts", [{}])[0]
    location = weather_data.get("location", {})
    publishing_office = forecast.get("publishingOffice", "")
    # Use location.district or location.city as area name
    area = location.get("district") or location.get("city", "")

    # Title and URL
    title = f"🌤️ Today's Weather - {location.get('prefecture', '')} {location.get('city', '')}"
    jma_url = forecast.get("linkUrl", "")
    url = jma_url if jma_url else f"https://www.jma.go.jp/bosai/map.html#contents=forecast_map&lat={location.get('lat', '')}&lon={location.get('lon', '')}&zoom=8"

    # Color setting (same as lamp color)
    color = rgb_to_decimal(lamp_setting.get("rgb", (255, 127, 0)))

    # Precipitation probability
    rain = forecast.get("chanceOfRain", {})
    t00_06 = rain.get("T00_06", "--")
    t06_12 = rain.get("T06_12", "--")
    t12_18 = rain.get("T12_18", "--")
    t18_24 = rain.get("T18_24", "--")
    max_rain = lamp_setting.get("max_rain", 0)

    # Get icon URL from weather code
    telop = forecast.get("telop", "")
    icon_url = forecast.get("image", {}).get("url", "")

    # Temperature
    temperature = forecast.get("temperature", {})
    temp_str = format_temperature(temperature)

    # Detail text
    detail_text = forecast.get("detail", {})

    # description: telop only if area is empty
    desc = f"{telop} - {area}" if area else telop

    embed = {
        "title": title,
        "url": url,
        "description": desc,
        "color": color,
        "fields": [
            {
                "name": "Precipitation (Max)",
                "value": f"{max_rain}%",
                "inline": True
            },
            {
                "name": "06-12",
                "value": t06_12 if t06_12 else "--%",
                "inline": True
            },
            {
                "name": "12-18",
                "value": t12_18 if t12_18 else "--%",
                "inline": True
            },
            {
                "name": "18-24",
                "value": t18_24 if t18_24 else "--%",
                "inline": True
            },
            {
                "name": "Temperature",
                "value": temp_str,
                "inline": True
            },
        ],
        "thumbnail": {
            "url": icon_url
        } if icon_url else {},
        "footer": {
            "text": f"{publishing_office} / Tsukumijima Weather API"
        }
    }

    # Add lamp setting to fields
    if USE_COLOR_TEMPERATURE:
        ct = lamp_setting.get("ct", 0)
        embed["fields"].append({
            "name": "Lamp Setting",
            "value": f"Color Temp: {ct}K",
            "inline": True
        })
    else:
        r, g, b = lamp_setting.get("rgb", (0, 0, 0))
        embed["fields"].append({
            "name": "Lamp Setting",
            "value": f"RGB({r},{g},{b})",
            "inline": True
        })

    # Add weatherDetail if available
    if detail_text:
        weather_detail = detail_text.get("weatherDetail", "")
        if weather_detail:
            # Add detail to existing fields
            embed["fields"].append({
                "name": "Details",
                "value": weather_detail,
                "inline": False
            })

    return embed

def send_discord_notification(weather_data: dict, lamp_setting: dict) -> bool:
    """POST to Discord Webhook. Returns True on success, False on failure"""
    if not DISCORD_ENABLED:
        logger.info("Discord notification is disabled")
        return True

    if not DISCORD_WEBHOOK_URL:
        logger.warning("DISCORD_WEBHOOK_URL is not set")
        return False

    embed = build_discord_embed(weather_data, lamp_setting)
    if not embed:
        logger.warning("Failed to build Discord embed")
        return False

    payload = {"embeds": [embed]}

    try:
        response = requests.post(
            DISCORD_WEBHOOK_URL,
            json=payload,
            timeout=DISCORD_TIMEOUT
        )
        response.raise_for_status()
        logger.info("Discord notification sent successfully")
        return True
    except requests.exceptions.RequestException as e:
        logger.warning(f"Discord notification failed: {e}")
        return False

# ------------------------------
# Main
# ------------------------------
def main() -> bool:
    # Use max value from today's 4 slots (T00_06/T06_12/T12_18/T18_24)
    rain, weather_data = get_today_rain_percent_max_all(CITY_CODE)
    logger.info(f"Rain chance used: {rain}%")

    brightness = 100  # Fixed. Can be changed by logic if needed

    lamp_setting = {"max_rain": rain}

    if USE_COLOR_TEMPERATURE:
        ct = map_rain_to_ct(rain)
        lamp_setting["ct"] = ct
        logger.info(f"Set CT: {ct}K, Brightness: {brightness}")
        set_lamp_ct(DEVICE_ID, ct, brightness=brightness)
    else:
        rgb = map_rain_to_rgb(rain)
        lamp_setting["rgb"] = rgb
        logger.info(f"Set RGB: {rgb}, Brightness: {brightness}")
        set_lamp_rgb(DEVICE_ID, rgb, brightness=brightness)

    # Send Discord notification (failure doesn't affect lamp control)
    send_discord_notification(weather_data, lamp_setting)

    return True

if __name__ == "__main__":
    main()
