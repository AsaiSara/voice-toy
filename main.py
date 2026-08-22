import config
import sounddevice as sd
import numpy as np
import threading
import os
import signal
import sys
import serial
from evdev import InputDevice, ecodes

# 新しいエフェクト関数名をインポート
from effects import (
    tremolo,
    high_tremolo,
    robot,
    low,
    high,
    kuri,
    noise_gate,
    limiter,
)

# ============================================================
# 設定
# ============================================================

AUDIO_DEVICE = "default"
KEYBOARD_DEVICE = "/dev/input/by-id/usb-_mini_keyboard-event-kbd"
SERIAL_PORT = "/dev/ttyACM0"
SERIAL_BAUDRATE = 9600

# ============================================================
# 状態管理
# ============================================================

mode = "tremolo"
fan_speed = 0
mode_lock = threading.Lock()
running = True

def set_mode(new_mode):
    global mode
    with mode_lock:
        mode = new_mode
    print("Mode changed:", new_mode, flush=True)

def get_mode():
    with mode_lock:
        return mode

def set_fan_speed(speed):
    global fan_speed
    with mode_lock:
        fan_speed = speed
    print("Fan speed changed:", speed, flush=True)

def get_fan_speed():
    with mode_lock:
        return fan_speed

# ============================================================
# キーボードスレッド (デバッグ・テスト用)
# ============================================================

def keyboard_worker():
    global running
    try:
        keyboard = InputDevice(KEYBOARD_DEVICE)
        print("Keyboard input ready:", KEYBOARD_DEVICE, flush=True)

        for event in keyboard.read_loop():
            if not running:
                break
            if event.type != ecodes.EV_KEY or event.value != 1:  # Pressのみ
                continue

            if event.code == ecodes.KEY_1:
                set_mode("tremolo")       # f01: チームロゴ
            elif event.code == ecodes.KEY_2:
                set_mode("high_tremolo")  # f02: 赤い「あ」
            elif event.code == ecodes.KEY_3:
                set_mode("robot")         # f03: ロボットの絵
            elif event.code == ecodes.KEY_4:
                set_mode("low")           # f04: はげのおじさん
            elif event.code == ecodes.KEY_5:
                set_mode("high")          # f05: おばさん
            elif event.code == ecodes.KEY_6:
                set_mode("kuri")          # f06: 栗まんじゅう
    except Exception as e:
        print("Keyboard error:", repr(e), flush=True)

# ============================================================
# シリアル通信スレッド (タグ読み取り & 風量データ)
# ============================================================

def serial_worker():
    global running
    
    # タグ番号とモード名の対応表
    TAG_MAP = {
        "f01": "tremolo",
        "f02": "high_tremolo",
        "f03": "robot",
        "f04": "low",
        "f05": "high",
        "f06": "kuri",
    }

    try:
        ser = serial.Serial(
            port=SERIAL_PORT,
            baudrate=SERIAL_BAUDRATE,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1,
        )
        print("Serial started:", SERIAL_PORT, flush=True)

        while running:
            raw = ser.readline()
            if not raw:
                continue

            try:
                data = raw.decode("ascii").strip()
            except UnicodeDecodeError:
                print("Serial decode error:", repr(raw), flush=True)
                continue

            print("Serial:", data, flush=True)

            # タグ判定 (f01 ~ f06)
            if data in TAG_MAP:
                set_mode(TAG_MAP[data])
            elif data.startswith("f"):
                print("Unknown tag:", data, flush=True)

            # 風量データ (p00 ~ p08)
            elif data.startswith("p") and len(data) == 3:
                try:
                    speed = int(data[1:])
                    if 0 <= speed <= 8:
                        set_fan_speed(speed)
                    else:
                        print("Invalid fan speed:", speed, flush=True)
                except ValueError:
                    print("Invalid fan data:", data, flush=True)

            # LED制御
            elif data.startswith("l") and len(data) == 3:
                print("LED:", data[1:], flush=True)

        ser.close()
    except Exception as e:
        print("Serial error:", repr(e), flush=True)

# ============================================================
# シグナルハンドラ
# ============================================================

def signal_handler(signum, frame):
    global running
    print("\nStopping...", flush=True)
    running = False

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# ============================================================
# メイン処理
# ============================================================

print("Maker Faire Voice Toy Demo Started!")
print("1: tremolo (チームロゴ)")
print("2: high_tremolo (「あ」)")
print("3: robot (ロボット)")
print("4: low (はげのおじさん)")
print("5: high (おばさん)")
print("6: kuri (栗まんじゅう)")
print()
print("Audio device:", AUDIO_DEVICE, flush=True)

keyboard_thread = threading.Thread(target=keyboard_worker, daemon=True)
keyboard_thread.start()

serial_thread = threading.Thread(target=serial_worker, daemon=True)
serial_thread.start()

# ============================================================
# オーディオストリーム
# ============================================================

try:
    with sd.Stream(
        samplerate=config.SAMPLE_RATE,
        device=(AUDIO_DEVICE, AUDIO_DEVICE),
        channels=1,
        blocksize=config.BLOCKSIZE,
        dtype="float32",
    ) as stream:
        print("Voice Toy audio stream started.", flush=True)

        while running:
            # 1. マイク入力
            audio, overflowed = stream.read(config.BLOCKSIZE)
            if overflowed:
                print("Input overflow", flush=True)

            # 2. ノイズゲート処理
            clean = noise_gate(audio, threshold=0.015)
            clean = clean * 0.8  # 音量調整

            # 3. モードと風量を取得
            current_mode = get_mode()
            current_fan_speed = get_fan_speed()

            # 4. エフェクト処理
            if current_mode == "tremolo":
                effect = tremolo(clean, current_fan_speed)
            elif current_mode == "high_tremolo":
                effect = high_tremolo(clean, current_fan_speed)
            elif current_mode == "robot":
                effect = robot(clean, config.SAMPLE_RATE, current_fan_speed)
            elif current_mode == "low":
                effect = low(clean, current_fan_speed)
            elif current_mode == "high":
                effect = high(clean, current_fan_speed)
            elif current_mode == "kuri":
                effect = kuri(clean, current_fan_speed)
            else:
                effect = clean

            # 5. リミッター処理
            effect = limiter(effect, threshold=0.8)

            # 6. スピーカー出力
            stream.write(effect)

except KeyboardInterrupt:
    pass
except Exception as e:
    print("Audio error:", repr(e), flush=True)
finally:
    running = False
    print("Voice Toy stopped.", flush=True)
