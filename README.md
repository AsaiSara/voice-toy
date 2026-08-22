# Voice Toy

Raspberry Pi 上で動作する体感型音声変換（ボイスチェンジャー）プログラムです。

Maker Faire や展示イベント用に開発されており、RFIDタグ（またはUSBキーボード）でキャラクター/モードを切り替え、吹き込む風量（センサデータ）に連動してリアルタイムに音声エフェクトが変化します。

---

## 🎤 音声モード・タグ・キーボード対応表

| キーボード | タグ ID | モード名 (内部変数) | キャラクター / 設定 | 声の特徴 & 風量連動エフェクト |
| :---: | :---: | :--- | :--- | :--- |
| **1** | `f01` | `tremolo` | チームロゴ | 定番の扇風機「あ〜〜〜」体験。風量で波の速度が変化 |
| **2** | `f02` | `high_tremolo` | 赤い「あ」 | 高音 × トレモロ（目立つアニメ系ボイス） |
| **3** | `f03` | `robot` | ロボットの絵 | 金属的なロボット声。無音時のノイズカット処理付き |
| **4** | `f04` | `low` | はげのおじさん | ダンディな低音。風量を上げるにつれて1音ずつ低くなる |
| **5** | `f05` | `high` | 上品なおばさん | 高音(+14.5～+18.5半音)。ノイズフィルター(LPF)付き |
| **6** | `f06` | `kuri` | 栗まんじゅう | どっしり低音(-5半音) ＋ 風量で炭酸シュワシュワ（激しさ）増大 |

---

## 🔌 シリアル通信仕様

Arduino 等からシリアルポート（標準: `/dev/ttyACM0`, Baudrate: `9600`）経由で以下のテキストデータを受信して制御します。

### 1. タグ情報 (`f01` 〜 `f06`)
* `f01`: `tremolo` モードへ変更
* `f02`: `high_tremolo` モードへ変更
* `f03`: `robot` モードへ変更
* `f04`: `low` モードへ変更
* `f05`: `high` モードへ変更
* `f06`: `kuri` モードへ変更

### 2. 風量データ (`p00` 〜 `p08`)
* `p00` 〜 `p08`: 0〜8 の 9 段階で風量レベルを設定。音声エフェクトのリアルタイムパラメーターに反映されます。

### 3. LED 制御データ (`l00` 〜)
* シリアル経由で受信した LED 制御コマンドの出力用。

---

## 💻 動作環境

- Raspberry Pi (Raspberry Pi OS)
- Python 3.7+
- USB マイク
- USB スピーカー
- USB ミニキーボード（デバッグ・テスト用）
- マイコンボード等（シリアル通信用 / Arduino 等）

---

## ⚙️ Raspberry Pi セットアップ

### 1. リポジトリの取得

```bash
git clone <リポジトリURL>
cd voice-toy
```

### 2. Python 仮想環境の作成と有効化

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

---

## 🛠️ ハードウェア・デバイス設定

### USB キーボード設定
キーボードデバイスは `/dev/input/by-id/` の固定名を使用します。

```bash
ls -l /dev/input/by-id/
```

`main.py` の設定項目：
```python
KEYBOARD_DEVICE = "/dev/input/by-id/usb-_mini_keyboard-event-kbd"
```

### シリアルポート設定
`main.py` の設定項目：
```python
SERIAL_PORT = "/dev/ttyACM0"
SERIAL_BAUDRATE = 9600
```

### オーディオデバイス設定
SoundDevice の default デバイス（PulseAudio / PipeWire）を使用します。

```bash
python -c "import sounddevice as sd; print(sd.query_devices())"
```

---

## 🚀 実行・起動方法

### 手動起動（デバッグ時）

```bash
cd ~/Desktop/KadoMakers/voice-toy
source .venv/bin/activate
python main.py
```

### 自動起動 (systemd)

Raspberry Pi 起動時に自動実行させる設定です。

```bash
# systemd サービスファイルのコピー
sudo cp systemd/voice-toy.service /etc/systemd/system/

# 設定の反映と有効化
sudo systemctl daemon-reload
sudo systemctl enable voice-toy.service
sudo systemctl start voice-toy.service
```

ステータスおよびログの確認：
```bash
# ステータス確認
sudo systemctl status voice-toy.service

# リアルタイムログ確認
sudo journalctl -u voice-toy.service -n 100 --no-pager
```

---

## 🔍 トラブルシューティング

* **マイク/スピーカーが認識されない場合**
  * `arecord -l`（マイク確認）
  * `aplay -l`（スピーカー確認）
  * `pactl list short sources` / `pactl list short sinks`
* **シリアル通信エラーが出る場合**
  * `/dev/ttyACM0` のパーミッションを確認（`sudo usermod -a -G dialout pi`）
* **キーボードが反応しない場合**
  * `ls -l /dev/input/by-id/` で指定した識別子が存在するか確認
