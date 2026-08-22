import numpy as np


ring_phase = 0


def normal(audio):
    return audio

def robot(audio, sample_rate=44100, fan_speed=0):

    global ring_phase

    # 風量に応じて変調周波数を変える
    frequency = 100 + fan_speed * 40

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

def tremolo(audio, sample_rate=44100, fan_speed=0):

    global phase

    depth = 0.5 + fan_speed * 0.06
    frequency = 8 + fan_speed * 1.5

    depth = min(depth, 0.7)

    n = len(audio)

    t = (
        np.arange(n) + phase
    ) / sample_rate

    lfo = (
        1 - depth
        + depth *
        (
            0.5
            + 0.5 *
            np.sin(
                2 * np.pi * frequency * t
            )
        )
    )

    phase += n

    return (
        audio * lfo.reshape(-1, 1)
    ).astype(np.float32)


# effects.py に追加・修正

def shift_pitch(audio, semitones):
    """
    ピッチを半音単位で変更する（正: 高く、負: 低く）
    """
    factor = 2.0 ** (semitones / 12.0)
    x = audio[:, 0]
    n = len(x)
    
    # リサンプリングによるピッチ変更
    indices = np.arange(0, n, factor)
    indices = indices[indices < n]
    
    y = np.interp(indices, np.arange(n), x)
    
    # バッファサイズを元と合わせる（補正）
    if len(y) < n:
        y = np.pad(y, (0, n - len(y)), mode='constant')
    else:
        y = y[:n]
        
    return y.reshape(-1, 1).astype(np.float32)

def low_voice(audio, fan_speed=0):
    # 風量(0〜8)に応じてピッチを落とす（0で-2半音、8で-10半音）
    semitones = -2 - (fan_speed * 1.0)
    return shift_pitch(audio, semitones)

def high_voice(audio, fan_speed=0):
    # 風量(0〜8)に応じてピッチを上げる（0で+2半音、8で+10半音）
    semitones = 2 + (fan_speed * 1.0)
    return shift_pitch(audio, semitones)

#low_phase = 0

#def low_voice(audio):
#
#    global low_phase
#
#    ratio = 1.5  # 高さ
#
#    x = audio[:, 0]
#
#    n = len(x)
#
#    # 元データから1.5倍速で読む
#    indices = (
#        np.arange(n) * ratio
#    )
#
#    indices = np.clip(
#        indices,
#        0,
#        n - 1
#    )
#
#    y = np.interp(
#        np.arange(n),
#        indices,
#        x
#    )
#
#    return (
#        y.reshape(-1, 1)
#        .astype(np.float32)
#    )
#
#def high_voice(audio):
#
#    ratio = 0.7  # 1より小さくすると高くなる
#
#    x = audio[:, 0]
#
#    n = len(x)
#
#    indices = (
#        np.arange(n) * ratio
#    )
#
#    indices = np.clip(
#        indices,
#        0,
#        n - 1
#    )
#
#    y = np.interp(
#        np.arange(n),
#        indices,
#        x
#    )
#
#    return (
#        y.reshape(-1, 1)
#        .astype(np.float32)
#    )

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
