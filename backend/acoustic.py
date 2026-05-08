import librosa
import numpy as np

def extract_acoustic_features(audio_path):
    y, sr = librosa.load(audio_path, sr = None)

    pitches, magnitudes = librosa.piptrack(y=y, sr=sr)

    pitch_values = pitches[magnitudes > np.median(magnitudes)]

    avg_pitch = np.mean(pitch_values) if len(pitch_values) > 0 else 0

    rms = librosa.feature.rms(y=y)
    energy = float(np.mean(rms))

    zcr = librosa.feature.zero_crossing_rate(y=y)

    speech_rate = float(np.mean(zcr))


    return {

        "pitch" : float(avg_pitch),
        "energy" : energy,
        "speech_rate" : speech_rate
    }