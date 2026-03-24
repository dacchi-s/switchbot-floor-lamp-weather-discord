# SwitchBot Floor Lamp Rainy

SwitchBot RGBICWW Floor Lamp を、その日の降水確率に基づいて自動的に色または色温度を変えて点灯する Python スクリプトです。

## 機能

- つくみ島天気APIから3日分（当日・翌日・明後日）の天気予報を取得
- 当日の降水確率（T06_12/T12_18/T18_24 の最大値）に応じてランプの色または色温度を自動調整
- Discord に3日分の天気予報を通知（オプション）
  - 天気に応じた絵文字表示
  - 降水確率に応じた絵文字（☀️⛅🌧️⛈️）

## インストール

### 仮想環境の構築（推奨）

```bash
# プロジェクトディレクトリへ移動
cd /path/to/switchbot_floor_lamp_rainy

# 仮想環境を作成
python3 -m venv venv

# 仮想環境を有効化
source venv/bin/activate

# 依存関係をインストール
pip install -r requirements.txt
```

### 仮想環境の終了

```bash
deactivate
```

## 設定

1. `.env.example` を `.env` にコピー
2. 以下の環境変数を設定

```bash
cp .env.example .env
```

### 環境変数

| 変数 | 説明 | 例 |
|------|------|------|
| `SWITCHBOT_ACCESS_TOKEN` | SwitchBot API のアクセストークン | - |
| `SWITCHBOT_SECRET` | SwitchBot API のシークレットキー | - |
| `SWITCHBOT_FLOOR_LAMP_DEVICE_ID` | Floor Lamp のデバイスID | - |
| `WEATHER_CITY_CODE` | 天気取得対象の都市コード（JMA） | 130010（東京） |
| `USE_COLOR_TEMPERATURE` | 色温度モードを使用（1）または RGB モード（0） | 0 |
| `DISCORD_WEBHOOK_URL` | Discord Webhook URL（オプション） | - |
| `DISCORD_ENABLED` | Discord 通知を有効にする（1）または無効（0） | 1 |
| `DISCORD_TIMEOUT` | Discord API のタイムアウト（秒） | 10 |

### SwitchBot API 認証情報の取得

1. [SwitchBot App](https://switch-bot.app/) をインストール
2. アカウントにログイン
3. プロフィール → 設定 → 開発者向けオプション から Access Token と Secret を取得

### 都市コード

- [つくみ島天気API - 都市一覧](https://weather.tsukumijima.net/api/forecast/cities)
- よく使うコード: `130010`（東京）、`270000`（大阪）、`400000`（福岡）

## 色マッピング

### RGB モード (`USE_COLOR_TEMPERATURE=0`)

| 降水確率 | 色 | RGB 値 |
|----------|------|--------|
| 0% | オレンジ | (255, 127, 0) |
| ≤20% | 黄色 | (255, 255, 0) |
| ≤40% | 黄緑 | (127, 255, 0) |
| ≤60% | シアン | (0, 255, 255) |
| ≤80% | 青寄り | (0, 127, 255) |
| >80% | 濃い青 | (0, 0, 255) |

### 色温度モード (`USE_COLOR_TEMPERATURE=1`)

| 降水確率 | 色温度 |
|----------|--------|
| 0% | 2700K（暖色） |
| 100% | 6500K（寒色） |
| その他 | 線形補間 |

## 使い方

### 手動実行

```bash
# 仮想環境を有効化
source venv/bin/activate

# スクリプトを実行
python switchbot_floor_lamp_rainy.py
```

### 自動実行（cron）

#### cron の設定

```bash
# crontab を編集
crontab -e
```

#### 毎日6時に実行する例

```
0 6 * * * cd /path/to/switchbot_floor_lamp_rainy && /path/to/switchbot_floor_lamp_rainy/venv/bin/python switchbot_floor_lamp_rainy.py
```

#### cron の書式

```
# 書式: 分 時 日 月 曜日 コマンド
0 6 * * *                    # 毎日6時
0 */6 * * *                  # 6時間おき
0 6,18 * * *                 # 6時と18時
```

#### cron ログの確認

```bash
# cron のログを確認（Ubuntu/Debianの場合）
grep CRON /var/log/syslog

# または、実行ログをファイルに出力する場合
*/5 * * * * cd /path/to/switchbot_floor_lamp_rainy && /path/to/venv/bin/python switchbot_floor_lamp_rainy.py >> /var/log/switchbot_lamp.log 2>&1
```

## Discord 通知例

3日分の天気予報が通知されます:

```
┌─────────────────────────────────────────────┐
│ 🌤️ 3-Day Weather Forecast - 東京都 東京      │
├─────────────────────────────────────────────┤
│ 【今日】☀️ 晴れ - 千代田区                   │
│ ☀️ Precipitation (Max) │ 0%                 │
│ ☀️ 06-12               │ 0%                 │
│ ☀️ 12-18               │ 0%                 │
│ ☀️ 18-24               │ 0%                 │
│ 🌡️ Temperature          │ 10C / 18C         │
│ 💡 Lamp Setting         │ RGB(255,127,0)    │
├─────────────────────────────────────────────┤
│ 【明日】⛅ くもり - 千代田区                 │
│ 🌧️ Precipitation (Max) │ 35%                │
│ ⛅ 06-12               │ 10%                │
│ ⛅ 12-18               │ 20%                │
│ 🌧️ 18-24               │ 35%                │
│ 🌡️ Temperature          │ 12C / 20C         │
├─────────────────────────────────────────────┤
│ 【明後日】🌧️ 雨 - 千代田区                  │
│ ⛈️ Precipitation (Max) │ 75%                │
│ 🌧️ 06-12               │ 50%                │
│ 🌧️ 12-18               │ 60%                │
│ ⛈️ 18-24               │ 75%                │
│ 🌡️ Temperature          │ 15C / 22C         │
├─────────────────────────────────────────────┤
│ Details: 高気圧に覆われて晴れるでしょう      │
└─────────────────────────────────────────────┘
```

### 絵文字マッピング

**天気絵文字:**
| 天気 | 絵文字 |
|------|--------|
| 晴れ | ☀️ |
| くもり | ⛅ |
| 雨 | 🌧️ |
| 雪 | ❄️ |
| 雷 | ⛈️ |

**降水確率絵文字:**
| 降水確率 | 絵文字 |
|----------|--------|
| 0% | ☀️ |
| 1-30% | ⛅ |
| 31-60% | 🌧️ |
| 61-100% | ⛈️ |

## トラブルシューティング

### 仮想環境が動作しない場合

```bash
# 仮想環境を削除して再作成
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### cron が動作しない場合

```bash
# cron サービスの状態を確認
sudo systemctl status cron

# cron のログを確認
sudo tail -f /var/log/syslog | grep CRON
```

## ライセンス

MIT License

---

# SwitchBot Floor Lamp Rainy

A Python script that automatically controls a SwitchBot RGBICWW Floor Lamp based on the day's precipitation probability.

## Features

- Fetches 3-day weather forecast (today, tomorrow, day after tomorrow) from Tsukumijima Weather API
- Automatically adjusts lamp color or color temperature based on today's precipitation probability (max of T06_12/T12_18/T18_24)
- Sends 3-day weather notifications to Discord (optional)
  - Weather emojis based on forecast
  - Precipitation emojis (☀️⛅🌧️⛈️) based on probability

## Installation

### Create Virtual Environment (Recommended)

```bash
# Navigate to project directory
cd /path/to/switchbot_floor_lamp_rainy

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Deactivate Virtual Environment

```bash
deactivate
```

## Configuration

1. Copy `.env.example` to `.env`
2. Configure the following environment variables

```bash
cp .env.example .env
```

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SWITCHBOT_ACCESS_TOKEN` | SwitchBot API access token | - |
| `SWITCHBOT_SECRET` | SwitchBot API secret key | - |
| `SWITCHBOT_FLOOR_LAMP_DEVICE_ID` | Device ID of Floor Lamp | - |
| `WEATHER_CITY_CODE` | JMA city code for weather | 130010 (Tokyo) |
| `USE_COLOR_TEMPERATURE` | Use color temperature mode (1) or RGB mode (0) | 0 |
| `DISCORD_WEBHOOK_URL` | Discord Webhook URL (optional) | - |
| `DISCORD_ENABLED` | Enable Discord notifications (1) or disable (0) | 1 |
| `DISCORD_TIMEOUT` | Discord API timeout in seconds | 10 |

### Getting SwitchBot API Credentials

1. Install [SwitchBot App](https://switch-bot.app/)
2. Log in to your account
3. Get Access Token and Secret from Profile → Settings → Developer Options

### City Codes

- [Tsukumijima Weather API - City List](https://weather.tsukumijima.net/api/forecast/cities)
- Common codes: `130010` (Tokyo), `270000` (Osaka), `400000` (Fukuoka)

## Color Mapping

### RGB Mode (`USE_COLOR_TEMPERATURE=0`)

| Precipitation | Color | RGB Value |
|---------------|-------|-----------|
| 0% | Orange | (255, 127, 0) |
| ≤20% | Yellow | (255, 255, 0) |
| ≤40% | Lime | (127, 255, 0) |
| ≤60% | Cyan | (0, 255, 255) |
| ≤80% | Blue-ish | (0, 127, 255) |
| >80% | Deep Blue | (0, 0, 255) |

### Color Temperature Mode (`USE_COLOR_TEMPERATURE=1`)

| Precipitation | Color Temperature |
|---------------|-------------------|
| 0% | 2700K (Warm) |
| 100% | 6500K (Cool) |
| Other | Linear interpolation |

## Usage

### Manual Execution

```bash
# Activate virtual environment
source venv/bin/activate

# Run script
python switchbot_floor_lamp_rainy.py
```

### Automation (cron)

#### Configure cron

```bash
# Edit crontab
crontab -e
```

#### Example: Run daily at 6 AM

```
0 6 * * * cd /path/to/switchbot_floor_lamp_rainy && /path/to/switchbot_floor_lamp_rainy/venv/bin/python switchbot_floor_lamp_rainy.py
```

#### Cron Format

```
# Format: minute hour day month weekday command
0 6 * * *                    # Daily at 6 AM
0 */6 * * *                  # Every 6 hours
0 6,18 * * *                 # 6 AM and 6 PM
```

#### Check Cron Logs

```bash
# Check cron logs (Ubuntu/Debian)
grep CRON /var/log/syslog

# Or redirect output to log file
*/5 * * * * cd /path/to/switchbot_floor_lamp_rainy && /path/to/venv/bin/python switchbot_floor_lamp_rainy.py >> /var/log/switchbot_lamp.log 2>&1
```

## Discord Notification Example

3-day weather forecast notification:

```
┌─────────────────────────────────────────────┐
│ 🌤️ 3-Day Weather Forecast - Tokyo           │
├─────────────────────────────────────────────┤
│ 【Today】☀️ Sunny - Chiyoda                  │
│ ☀️ Precipitation (Max) │ 0%                 │
│ ☀️ 06-12               │ 0%                 │
│ ☀️ 12-18               │ 0%                 │
│ ☀️ 18-24               │ 0%                 │
│ 🌡️ Temperature          │ 10C / 18C         │
│ 💡 Lamp Setting         │ RGB(255,127,0)    │
├─────────────────────────────────────────────┤
│ 【Tomorrow】⛅ Cloudy - Chiyoda              │
│ 🌧️ Precipitation (Max) │ 35%                │
│ ⛅ 06-12               │ 10%                │
│ ⛅ 12-18               │ 20%                │
│ 🌧️ 18-24               │ 35%                │
│ 🌡️ Temperature          │ 12C / 20C         │
├─────────────────────────────────────────────┤
│ 【Day After】🌧️ Rain - Chiyoda              │
│ ⛈️ Precipitation (Max) │ 75%                │
│ 🌧️ 06-12               │ 50%                │
│ 🌧️ 12-18               │ 60%                │
│ ⛈️ 18-24               │ 75%                │
│ 🌡️ Temperature          │ 15C / 22C         │
├─────────────────────────────────────────────┤
│ Details: High pressure brings clear skies   │
└─────────────────────────────────────────────┘
```

### Emoji Mapping

**Weather Emojis:**
| Weather | Emoji |
|---------|-------|
| Sunny/Clear | ☀️ |
| Cloudy | ⛅ |
| Rain | 🌧️ |
| Snow | ❄️ |
| Thunder | ⛈️ |

**Precipitation Emojis:**
| Probability | Emoji |
|-------------|-------|
| 0% | ☀️ |
| 1-30% | ⛅ |
| 31-60% | 🌧️ |
| 61-100% | ⛈️ |

## Troubleshooting

### Virtual Environment Issues

```bash
# Delete and recreate virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Cron Not Working

```bash
# Check cron service status
sudo systemctl status cron

# Check cron logs
sudo tail -f /var/log/syslog | grep CRON
```

## License

MIT License
