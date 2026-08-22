import config
import sounddevice as sd
import numpy as np
import threading
import os
import signal
import sys
import serial
from evdev import InputDevice, ecodes

from effects import (
    normal,
    robot,
    tremolo,
    low_voice,
    high_voice,
    noise_gate,
    limiter,
)


# ============================================================
# 設定
# ============================================================

# PulseAudio
AUDIO_DEVICE = "default"

# キーボード
KEYBOARD_DEVICE = "/dev/input/by-id/usb-_mini_keyboard-event-kbd"

# シリアル通信
SERIAL_PORT = "/dev/ttyACM0"
SERIAL_BAUDRATE = 9600

# ============================================================
# モード
# ============================================================

mode = "normal"
fan_speed = 0
mode_lock = threading.Lock()

running = True

# ============================================================
# モード変更
# ============================================================

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
# キーボード
# ============================================================

def keyboard_worker():

    global running

    try:

        keyboard = InputDevice(KEYBOARD_DEVICE)

        print(
            "Keyboard:",
            KEYBOARD_DEVICE,
            flush=True
        )

        print(
            "Keyboard input ready.",
            flush=True
        )

        for event in keyboard.read_loop():

            if not running:
                break

            if event.type != ecodes.EV_KEY:
                continue

            # value:
            # 0 = release
            # 1 = press
            # 2 = repeat
            if event.value != 1:
                continue

            if event.code == ecodes.KEY_1:

                set_mode("normal")

            elif event.code == ecodes.KEY_2:

                set_mode("robot")

            elif event.code == ecodes.KEY_3:

                set_mode("tremolo")

            elif event.code == ecodes.KEY_4:

                set_mode("low")

            elif event.code == ecodes.KEY_5:

                set_mode("high")

    except Exception as e:

        print(
            "Keyboard error:",
            repr(e),
            flush=True
        )


# ============================================================
# シリアル通信
# ============================================================

def serial_worker():

    global running

    try:

        ser = serial.Serial(
            port=SERIAL_PORT,
            baudrate=SERIAL_BAUDRATE,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1,
        )

        print(
            "Serial started:",
            SERIAL_PORT,
            flush=True
        )

        while running:

            raw = ser.readline()

            if not raw:
                continue

            try:
                data = raw.decode(
                    "ascii"
                ).strip()

            except UnicodeDecodeError:

                print(
                    "Serial decode error:",
                    repr(raw),
                    flush=True
                )

                continue

            print(
                "Serial:",
                data,
                flush=True
            )

            # --------------------------------------------
            # タグ情報
            # --------------------------------------------

            if data.startswith("f") and len(data) == 3:

                tag = data[1:]

                if tag == "00":

                    set_mode("normal")

                elif tag == "01":

                    set_mode("robot")

                elif tag == "02":

                    set_mode("tremolo")

                elif tag == "03":

                    set_mode("low")

                elif tag == "04":

                    set_mode("high")

                elif tag == "05":

                    set_mode("normal")

                else:

                    print(
                        "Unknown tag:",
                        tag,
                        flush=True
                    )

            # --------------------------------------------
            # 風量
            # --------------------------------------------

            elif data.startswith("p") and len(data) == 3:

                try:

                    speed = int(data[1:])

                    if 0 <= speed <= 8:

                        set_fan_speed(speed)

                    else:

                        print(
                            "Invalid fan speed:",
                            speed,
                            flush=True
                        )

                except ValueError:

                    print(
                        "Invalid fan data:",
                        data,
                        flush=True
                    )

            # --------------------------------------------
            # LED
            # --------------------------------------------

            elif data.startswith("l") and len(data) == 3:

                led = data[1:]

                print(
                    "LED:",
                    led,
                    flush=True
                )

        ser.close()

    except Exception as e:

        print(
            "Serial error:",
            repr(e),
            flush=True
        )

# ============================================================
# 終了処理
# ============================================================

def signal_handler(signum, frame):

    global running

    print(
        "\nStopping...",
        flush=True
    )

    running = False


signal.signal(
    signal.SIGINT,
    signal_handler
)

signal.signal(
    signal.SIGTERM,
    signal_handler
)


# ============================================================
# メイン
# ============================================================

print("1 Normal")
print("2 Robot")
print("3 Tremolo")
print("4 Low Voice")
print("5 High Voice")
print()

print(
    "Audio device:",
    AUDIO_DEVICE,
    flush=True
)


# キーボードスレッド開始

keyboard_thread = threading.Thread(
    target=keyboard_worker,
    daemon=True
)

keyboard_thread.start()

serial_thread = threading.Thread(
    target=serial_worker,
    daemon=True
)

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

        print(
            "Voice Toy started.",
            flush=True
        )

        while running:

            # ------------------------------------------------
            # マイク入力
            # ------------------------------------------------

            audio, overflowed = stream.read(
                config.BLOCKSIZE
            )

            if overflowed:

                print(
                    "Input overflow",
                    flush=True
                )


            # ------------------------------------------------
            # ノイズゲート
            # ------------------------------------------------

            clean = noise_gate(audio)

            clean = clean * 0.7


            # ------------------------------------------------
            # 現在のモード取得
            # ------------------------------------------------

            current_mode = get_mode()
            current_fan_speed = get_fan_speed()

            # ------------------------------------------------
            # エフェクト
            # ------------------------------------------------

            if current_mode == "normal":

                effect = normal(clean)

            elif current_mode == "robot":

                effect = robot(
                    clean,
                    config.SAMPLE_RATE,
                    current_fan_speed
                )

            elif current_mode == "tremolo":

                effect = tremolo(
                    clean,
                    config.SAMPLE_RATE,
                    current_fan_speed
                )

            elif current_mode == "low":

                effect = low_voice(clean)

            elif current_mode == "high":

                effect = high_voice(clean)

            else:

                effect = clean


            # ------------------------------------------------
            # リミッター
            # ------------------------------------------------

            effect = limiter(effect)


            # ------------------------------------------------
            # スピーカー出力
            # ------------------------------------------------

            stream.write(effect)


except KeyboardInterrupt:

    pass


except Exception as e:

    print(
        "Audio error:",
        repr(e),
        flush=True
    )


finally:

    running = False

    print(
        "Voice Toy stopped.",
        flush=True
    )
