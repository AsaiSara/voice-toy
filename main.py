import config
import sounddevice as sd
import numpy as np
import threading
import os
import signal
import sys
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


# ============================================================
# モード
# ============================================================

mode = "normal"

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


            # ------------------------------------------------
            # エフェクト
            # ------------------------------------------------

            if current_mode == "normal":

                effect = normal(clean)

            elif current_mode == "robot":

                effect = robot(
                    clean,
                    config.SAMPLE_RATE
                )

            elif current_mode == "tremolo":

                effect = tremolo(
                    clean,
                    config.SAMPLE_RATE
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
