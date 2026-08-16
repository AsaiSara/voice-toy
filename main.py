import sounddevice as sd
import config

from effects import normal, robot, tremolo, low_voice, high_voice, noise_gate, gain, limiter
import sys
import tty
import termios

mode = "normal"

INPUT_DEVICE = 2
OUTPUT_DEVICE = 1


def callback(indata, outdata, frames, time, status):

    global mode

    if status:
        print(status)

    clean = noise_gate(indata)
    # clean = indata
    clean = clean * 0.7

    if mode == "normal":
        effect = normal(clean)

    elif mode == "robot":
        effect = robot(clean)

    elif mode == "tremolo":
        effect = tremolo(clean)

    elif mode == "low":
        effect = low_voice(clean)
    
    elif mode == "high":
        effect = high_voice(clean)

    outdata[:] = limiter(effect) 

print("1 Normal")
print("2 Robot")
print("3 Tremolo")
print("4 Low Voice")
print("5 High Voice")


def get_key():

    fd = sys.stdin.fileno()

    old_settings = termios.tcgetattr(fd)

    try:
        tty.setcbreak(fd)   # setrawではなくcbreak
        key = sys.stdin.read(1)

    finally:
        termios.tcsetattr(
            fd,
            termios.TCSADRAIN,
            old_settings
        )

    return key


def keyboard():

    global mode

    while True:

        key = get_key()

        if key == "1":
            mode = "normal"
            print("\nNormal")

        elif key == "2":
            mode = "robot"
            print("\nRobot")

        elif key == "3":
            mode = "tremolo"
            print("\nTremolo")

        elif key == "4":
            mode = "low"
            print("\nLow Voice")

        elif key == "5":
            mode = "high"
            print("\nHigh Voice")

import threading

if sys.stdin.isatty():
    threading.Thread(
        target=keyboard,
        daemon=True
    ).start()


with sd.Stream(
    samplerate=config.SAMPLE_RATE,
    device=(INPUT_DEVICE, OUTPUT_DEVICE),
    channels=1,
    blocksize=config.BLOCKSIZE,
    dtype="float32",
    callback=callback,
):


    while True:
        sd.sleep(1000)
