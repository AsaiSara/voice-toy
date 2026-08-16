# Voice Toy

Raspberry Pi上で動作する音声変換プログラムです。

USBマイクから入力した音声にエフェクトをかけ、
スピーカーから出力します。

キーボードの数字キーによって音声モードを切り替えます。

## 音声モード

1. Normal
2. Robot
3. Tremolo
4. Low Voice
5. High Voice

---

## 動作環境

- Raspberry Pi
- Raspberry Pi OS
- Python 3.7
- USBマイク
- USBスピーカー
- USBミニキーボード

---

## Raspberry Pi セットアップ

### 1. リポジトリを取得

```bash
git clone <リポジトリURL>
cd voice-toy
````

### 2. Python仮想環境を作成

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Pythonパッケージをインストール

```bash
pip install -r requirements.txt
```

---

## USBデバイス

### キーボード

キーボードは `/dev/input/by-id/` の固定名を使用します。

以下で確認できます。

```bash
ls -l /dev/input/by-id/
```

現在の設定：

```text
usb-_mini_keyboard-event-kbd
```

`main.py` では以下のように指定しています。

```python
KEYBOARD_DEVICE = "/dev/input/by-id/usb-_mini_keyboard-event-kbd"
```

`event6` などのデバイス番号ではなく、
`/dev/input/by-id/` のデバイス名を使用することで、
USBポート変更時の番号変化の影響を受けにくくしています。

---

## オーディオデバイス

USBオーディオデバイスは、USBポートを変更すると
ALSAのカード番号が変わる場合があります。

そのため、`hw:2,0` のような固定デバイス番号ではなく、
PulseAudioの `default` デバイスを使用します。

音声デバイスの確認：

```bash
python -m sounddevice
```

または、

```bash
python -c "import sounddevice as sd; print(sd.query_devices())"
```

入力デバイスの確認：

```bash
python -c "import sounddevice as sd; print(sd.query_devices(kind='input'))"
```

出力デバイスの確認：

```bash
python -c "import sounddevice as sd; print(sd.query_devices(kind='output'))"
```

---

## 手動起動

プロジェクトディレクトリに移動します。

```bash
cd ~/Desktop/KadoMakers/voice-toy
```

仮想環境を有効にします。

```bash
source .venv/bin/activate
```

プログラムを起動します。

```bash
python main.py
```

---

## 自動起動

systemdを使用してRaspberry Pi起動時に
Voice Toyを自動起動します。

設定ファイル：

```text
systemd/voice-toy.service
```

### systemd設定

```bash
sudo cp systemd/voice-toy.service /etc/systemd/system/
```

設定を反映します。

```bash
sudo systemctl daemon-reload
```

自動起動を有効にします。

```bash
sudo systemctl enable voice-toy.service
```

起動します。

```bash
sudo systemctl start voice-toy.service
```

---

## 自動起動の確認

サービスの状態を確認します。

```bash
sudo systemctl status voice-toy.service
```

以下のようになっていれば起動しています。

```text
Active: active (running)
```

ログを確認する場合：

```bash
sudo journalctl -u voice-toy.service -n 100 --no-pager
```

---

## Raspberry Pi再起動後の確認

```bash
sudo reboot
```

SSHで再接続した後、

```bash
sudo systemctl status voice-toy.service
```

でサービスが起動していることを確認します。

---

## USBデバイスの確認

### USBキーボード

```bash
ls -l /dev/input/by-id/
```

### USBマイク

```bash
arecord -l
```

### オーディオ出力

```bash
aplay -l
```

### PulseAudio入力デバイス

```bash
pactl list short sources
```

### PulseAudio出力デバイス

```bash
pactl list short sinks
```

---

## キーボード入力の確認

キーボードのイベントデバイスを確認します。

```bash
ls -l /dev/input/by-id/
```

以下のようなデバイスを使用します。

```text
usb-_mini_keyboard-event-kbd
```

`evdev` を使用してキーボード入力を取得しています。

---

## トラブルシューティング

### マイクが認識されない場合

```bash
arecord -l
```

でUSBマイクが表示されるか確認します。

### スピーカーが認識されない場合

```bash
aplay -l
```

で出力デバイスを確認します。

### PulseAudioの状態確認

```bash
systemctl --user status pulseaudio
```

### PulseAudioの入力デバイス確認

```bash
pactl list short sources
```

### PulseAudioの出力デバイス確認

```bash
pactl list short sinks
```

### Voice Toyのログ確認

```bash
sudo journalctl -u voice-toy.service -n 100 --no-pager
```

---

## シリアル通信

今後、UARTを使用して以下の情報を取得する予定です。

* タグ情報
* LED設定
* 扇風機の風量設定

現時点では通信仕様は未確定です。

通信仕様書または通信フォーマットを受領後、
Pythonのシリアル通信ライブラリを使用して実装予定です。


