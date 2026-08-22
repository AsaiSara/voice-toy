import numpy as np

# 状態保持用グローバル変数
ring_phase = 0
tremolo_phase = 0

# ============================================================
# 高品質ピッチシフター (FFT & Overlap-Add 方式)
# ============================================================

class OLAFFTPitchShifter:
    def __init__(self):
        self.prev_x = None
        self.overlap_out = None
        self.window = None

    def process(self, audio, semitones, lpf_cutoff=None, sample_rate=44100):
        x = audio[:, 0]
        n = len(x)
        
        if self.prev_x is None or len(self.prev_x) != n:
            self.prev_x = np.zeros(n, dtype=np.float32)
            self.overlap_out = np.zeros(n, dtype=np.float32)
            self.window = np.hanning(2 * n)
            
        factor = 2.0 ** (semitones / 12.0)
        
        frame = np.concatenate([self.prev_x, x])
        frame_windowed = frame * self.window
        
        X = np.fft.rfft(frame_windowed)
        num_bins = len(X)
        
        orig_bins = np.arange(num_bins)
        target_bins = orig_bins / factor
        valid_mask = target_bins < num_bins
        
        new_X = np.zeros(num_bins, dtype=np.complex64)
        
        # 1. 補間処理による高音ノイズ・歪みの抑制 (np.interp)
        real_part = np.interp(target_bins[valid_mask], orig_bins, X.real)
        imag_part = np.interp(target_bins[valid_mask], orig_bins, X.imag)
        new_X[valid_mask] = real_part + 1j * imag_part
        
        # 2. FFT領域での急峻ローパスフィルター (デジタルノイズを完全カット)
        if lpf_cutoff is not None:
            freqs = np.fft.rfftfreq(2 * n, d=1.0/sample_rate)
            new_X[freqs > lpf_cutoff] = 0
            
        y = np.fft.irfft(new_X, 2 * n)
        
        out = y[:n] + self.overlap_out
        self.overlap_out = y[n:]
        self.prev_x = x
        
        out = out * 0.8
        return out.reshape(-1, 1).astype(np.float32)

# ピッチシフター用インスタンス
shifter_high_tremolo = OLAFFTPitchShifter()
shifter_low = OLAFFTPitchShifter()
shifter_high = OLAFFTPitchShifter()
shifter_kuri = OLAFFTPitchShifter()

# 内部用トレモロ共通処理
def apply_tremolo(audio, frequency, depth=0.75):
    global tremolo_phase
    n = len(audio)
    t = (np.arange(n) + tremolo_phase) / 44100.0
    lfo = (1.0 - depth) + depth * (0.5 + 0.5 * np.sin(2 * np.pi * frequency * t))
    tremolo_phase += n
    return (audio * lfo.reshape(-1, 1)).astype(np.float32)


# ============================================================
# 各タグ・モード対応エフェクト関数
# ============================================================

def tremolo(audio, fan_speed=0):
    """
    【f01: チームロゴ】 モード名: tremolo
    定番の扇風機「あ〜〜〜」体験。風量で波の速度が変化。
    """
    freq = 6.0 + (fan_speed * 1.5)
    return apply_tremolo(audio, frequency=freq, depth=0.75)


def high_tremolo(audio, fan_speed=0):
    """
    【f02: 「あ」】 モード名: high_tremolo
    高音 × トレモロ（目立つアニメ系ボイス）。
    """
    semitones = 7.0 + (fan_speed * 0.875)
    shifted = shifter_high_tremolo.process(audio, semitones)
    
    freq = 8.0 + (fan_speed * 2.0)
    return apply_tremolo(shifted, frequency=freq, depth=0.8)


def robot(audio, sample_rate=44100, fan_speed=0):
    """
    【f03: ロボットの絵】 モード名: robot
    金属的なロボット声。無音時の「ピー/ブーン」ノイズを完全にカットする処理を追加。
    """
    global ring_phase
    
    # --- ノイズ対策: 無音時はキャリア波を鳴らさずに完全消音 ---
    peak = np.max(np.abs(audio))
    if peak < 0.02:
        return np.zeros_like(audio, dtype=np.float32)
    # -----------------------------------------------------------

    base_freq = 120 + fan_speed * 40
    jitter = np.sin(ring_phase * 0.001) * (fan_speed * 15)
    frequency = base_freq + jitter

    n = len(audio)
    t = (np.arange(n) + ring_phase) / sample_rate
    carrier = np.sin(2 * np.pi * frequency * t)

    ring_phase += n
    output = audio[:, 0] * carrier
    return output.reshape(-1, 1).astype(np.float32)


def low(audio, fan_speed=0):
    """
    【f04: はげのおじさん】 モード名: low
    風量を上げるにつれて1音ずつ低くなる（現状維持）。
    """
    semitones = -2.0 - (fan_speed * 1.0)
    return shifter_low.process(audio, semitones)

def high(audio, fan_speed=0):
    """
    【f05: おばさん】
    ・基本ピッチ: +14.5半音 (風量0) -> +18.5半音 (風量8) で女性らしい高さをキープ
    ・lpf_cutoff=4800Hz でデジタルサーノイズ・金属音を完全に除去
    """
    semitones = 14.5 + (fan_speed * 0.5)
    
    # 4800Hz以上の高音ノイズを物理的にシャットアウト
    return shifter_high.process(audio, semitones, lpf_cutoff=4800)

def kuri(audio, fan_speed=0):
    """
    【f06: 栗まんじゅう（案1: 固定おじさん声 ＋ 炭酸シュワシュワ）】
    声は渋い低音(-5半音)で固定。
    風量が上がるとシュワシュワ感（トレモロ）だけが速く・激しくなる設定。
    """
    semitones = -5.0  # ピッチは栗まんじゅう風の低音で固定
    shifted = shifter_kuri.process(audio, semitones)
    
    # 風量に応じて炭酸感（激しさ）だけを変化させる
    freq = 5.0 + (fan_speed * 2.5)   # 5Hz (ゆったり) -> 25Hz (激しい炭酸)
    depth = 0.5 + (fan_speed * 0.05)  # 風量が上がるとシュワシュワが深く
    return apply_tremolo(shifted, frequency=freq, depth=depth)

# ============================================================
# 音質調整（ノイズゲート / リミッター）
# ============================================================

def noise_gate(audio, threshold=0.015):
    peak = np.max(np.abs(audio))
    if peak < threshold:
        return np.zeros_like(audio, dtype=np.float32)  # 無音時は完全にクリアに
    return audio.astype(np.float32)

def limiter(audio, threshold=0.8):
    peak = np.max(np.abs(audio))
    if peak > threshold:
        audio = audio * (threshold / peak)
    return audio.astype(np.float32)
