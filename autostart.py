from main import callback
import sounddevice as sd
import config

def main():
    with sd.Stream(
        samplerate=config.SAMPLERATE,
        channels=config.CHANNELS,
        callback=callback,
    ):
        while True:
            sd.sleep(1000)

if __name__ == "__main__":
    main()
