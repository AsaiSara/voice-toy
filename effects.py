import numpy as np


ring_phase = 0


def normal(audio):
    return audio


def robot(audio, sample_rate=44100):

    global ring_phase

    frequency = 80

    n = len(audio)

    t = (
        np.arange(n) + ring_phase
    ) / sample_rate

    carrier = np.sin(
        2 * np.pi * frequency * t
    )

    ring_phase += n

    output = audio[:, 0] * carrier

    return output.reshape(-1, 1).astype(np.float32)


phase = 0


def tremolo(audio, sample_rate=44100):

    global phase

    depth = 0.7
    frequency = 15

    n = len(audio)

    t = (
        np.arange(n) + phase
    ) / sample_rate

    lfo = (
        1 - depth
        + depth *
        (0.5 + 0.5 *
         np.sin(2*np.pi*frequency*t))
    )

    phase += n

    return (
        audio * lfo.reshape(-1, 1)
    ).astype(np.float32)

    low_phase = 0


def low_voice(audio):

    global low_phase

    ratio = 1.5  # 高さ

    x = audio[:, 0]

    n = len(x)

    # 元データから1.5倍速で読む
    indices = (
        np.arange(n) * ratio
    )

    indices = np.clip(
        indices,
        0,
        n - 1
    )

    y = np.interp(
        np.arange(n),
        indices,
        x
    )

    return (
        y.reshape(-1, 1)
        .astype(np.float32)
    )

def high_voice(audio):

    ratio = 0.7  # 1より小さくすると高くなる

    x = audio[:, 0]

    n = len(x)

    indices = (
        np.arange(n) * ratio
    )

    indices = np.clip(
        indices,
        0,
        n - 1
    )

    y = np.interp(
        np.arange(n),
        indices,
        x
    )

    return (
        y.reshape(-1, 1)
        .astype(np.float32)
    )

def noise_gate(audio, threshold=0.015):

    volume = np.abs(audio)

    gain = np.ones_like(volume)

    # 小さい音だけ徐々に下げる
    gain[volume < threshold] = 0.1

    return (
        audio * gain
    ).astype(np.float32)

def gain(audio, volume=1.2):
    return np.clip(
        audio * volume,
        -1.0,
        1.0
    )

def limiter(audio, threshold=0.7):

    peak = np.max(np.abs(audio))

    if peak > threshold:
        audio = audio * (threshold / peak)

    return audio.astype(np.float32)