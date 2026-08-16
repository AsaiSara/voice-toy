import sounddevice as sd

def callback(indata, outdata, frames, time, status):
    if status:
        print(status)
    outdata[:] = indata

print("話してください（Ctrl+Cで終了）")

with sd.Stream(
    samplerate=44100,
    channels=1,
    callback=callback,
):
    while True:
        sd.sleep(1000)