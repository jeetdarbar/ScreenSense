import os
import wave
import math
import struct
import random

def generate_wav(filename, num_channels, sample_rate, duration_sec, generate_sample_func):
    num_samples = int(duration_sec * sample_rate)
    max_amplitude = 32767
    
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(num_channels)
        wav_file.setsampwidth(2) # 16 bits
        wav_file.setframerate(sample_rate)
        
        for i in range(num_samples):
            t = float(i) / sample_rate
            samples = generate_sample_func(t)
            
            # Pack samples for interleaving channels
            packed_frames = b''
            for sample in samples:
                # Clamp amplitude
                val = max(-max_amplitude, min(int(sample * max_amplitude), max_amplitude))
                packed_frames += struct.pack('<h', val)
                
            wav_file.writeframesraw(packed_frames)

def init():
    audio_dir = os.path.join(os.path.dirname(__file__), 'app', 'static', 'audio')
    os.makedirs(audio_dir, exist_ok=True)
    
    sample_rate = 44100
    duration = 30 # 30 seconds, enough to loop
    
    # 1. Binaural Delta (100Hz Left, 103Hz Right) -> 3Hz Delta Beat
    binaural_path = os.path.join(audio_dir, 'binaural_delta.wav')
    print(f"Generating {binaural_path}...")
    def gen_binaural(t):
        volume = 0.5
        # Soft fade in/out
        env = 1.0 - math.cos(math.pi * min(t, 2.0)/2.0) if t < 2.0 else 1.0
        left = math.sin(2.0 * math.pi * 100.0 * t) * volume * env
        right = math.sin(2.0 * math.pi * 103.0 * t) * volume * env
        return [left, right]
    generate_wav(binaural_path, 2, sample_rate, duration, gen_binaural)
    
    # 2. Brown Noise (Low pass filtered random)
    brown_path = os.path.join(audio_dir, 'brown_noise.wav')
    print(f"Generating {brown_path}...")
    brown_state = [0.0, 0.0]
    def gen_brown(t):
        volume = 0.1
        # Simple integrator for brown noise
        white_l = random.uniform(-1.0, 1.0)
        white_r = random.uniform(-1.0, 1.0)
        brown_state[0] = (brown_state[0] + (0.02 * white_l)) / 1.02
        brown_state[1] = (brown_state[1] + (0.02 * white_r)) / 1.02
        # Fades
        env = 1.0 - math.cos(math.pi * min(t, 2.0)/2.0) if t < 2.0 else 1.0
        return [brown_state[0] * volume * env * 2.0, brown_state[1] * volume * env * 2.0]
    generate_wav(brown_path, 2, sample_rate, duration, gen_brown)
    
    # 3. Acoustic 60 BPM (Simple synth tones repeating every 1 second)
    acoustic_path = os.path.join(audio_dir, 'rhythm_60bpm.wav')
    print(f"Generating {acoustic_path}...")
    def gen_60bpm(t):
        volume = 0.3
        # Beat triggers every 1.0 seconds
        phrase_t = t % 1.0
        # Envelope for pluck: fast attack, exponential decay
        pluck_env = math.exp(-6.0 * phrase_t)
        
        # Minor 7th chord approximation for acoustic feels (A2, C3, E3, G3)
        freqs = [110.0, 130.81, 164.81, 196.00]
        chord = sum([math.sin(2.0 * math.pi * f * t) for f in freqs]) / 4.0
        
        sample = chord * pluck_env * volume
        # Fades
        env = 1.0 - math.cos(math.pi * min(t, 2.0)/2.0) if t < 2.0 else 1.0
        return [sample * env, sample * env]
    generate_wav(acoustic_path, 2, sample_rate, duration, gen_60bpm)
    
    # 4. Ambient Nature (Simulated Wind/Waves)
    nature_path = os.path.join(audio_dir, 'nature_ambient.wav')
    print(f"Generating {nature_path}...")
    nature_state = [0.0, 0.0]
    def gen_nature(t):
        volume = 0.15
        white_l = random.uniform(-1.0, 1.0)
        white_r = random.uniform(-1.0, 1.0)
        # Pinkish noise algorithm
        nature_state[0] = 0.99 * nature_state[0] + 0.05 * white_l
        nature_state[1] = 0.99 * nature_state[1] + 0.05 * white_r
        
        # Modulate amplitude with a slow LFO for wave/wind effect (approx 0.12 Hz = ~8 second cycles)
        lfo = 0.5 + 0.5 * math.sin(2.0 * math.pi * 0.12 * t)
        
        env = 1.0 - math.cos(math.pi * min(t, 2.0)/2.0) if t < 2.0 else 1.0
        return [nature_state[0] * volume * lfo * env, nature_state[1] * volume * lfo * env]
    generate_wav(nature_path, 2, sample_rate, duration, gen_nature)
    
    print("Audio assets generated successfully in app/static/audio!")

if __name__ == "__main__":
    init()
