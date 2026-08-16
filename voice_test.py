import subprocess
import tempfile
import sounddevice as sd
import soundfile as sf

SAMPLE_RATE = 44100

print("Enterを押すと録音開始")
input()

print("録音中...")

audio = sd.rec(
    int(1.0 * SAMPLE_RATE),
    samplerate=SAMPLE_RATE,
    channels=1,
    dtype="float32",
)

sd.wait()

print("録音終了")

with tempfile.TemporaryDirectory() as tmp:

    input_file = f"{tmp}/input.wav"
    output_file = f"{tmp}/output.wav"

    sf.write(input_file, audio, SAMPLE_RATE)

    subprocess.run([
        "sox",
        input_file,
        output_file,
        "pitch",
        "700"
    ])

    data, fs = sf.read(output_file, dtype="float32")

    print("再生")

    sd.play(data, fs)
    sd.wait()

print("終了")