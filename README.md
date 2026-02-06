# SwitchBot Floor Lamp Rainy

SwitchBot RGBICWW Floor Lamp を、その日の降水確率に基づいて自動的に色または色温度を変えて点灯する Python スクリプトです。

## 機能

- つくみ島天気APIから当日の降水確率を取得（T06_12/T12_18/T18_24 の最大値）
- 降水確率に応じてランプの色または色温度を自動調整
- Discord に天気通知を送信（オプション）

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

通知には以下が含まれます:
- 予報タイトルとアイコン
- 降水確率（最大）と各時間帯の確率
- 予想気温
- ランプ設定（RGB または 色温度）
- 天気の詳細

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

- Fetches daily precipitation probability from Tsukumijima Weather API (max of T06_12/T12_18/T18_24)
- Automatically adjusts lamp color or color temperature based on rain probability
- Sends weather notifications to Discord (optional)

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

The notification includes:
- Forecast title and icon
- Precipitation probability (max) and per-time-slot probabilities
- Forecast temperature
- Lamp setting (RGB or Color Temperature)
- Weather details

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
