"""Voice Manager for VT Manager.
Handles local microphone recording, Whisper STT, and TTS synthesis via Lily-TTS (gTTS + pydub) or Windows SAPI5 fallback.
"""
import os
import time
import socket
import threading
import subprocess
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import requests
import queue

logger = logging.getLogger("VTManager.Voice")

class VADDetector:
    """Simple energy-based Voice Activity Detector (VAD)."""
    def __init__(self, threshold=500, silence_duration=1.5, sample_rate=16000):
        self.threshold = threshold
        self.silence_duration = silence_duration
        self.sample_rate = sample_rate
        # Calculate limit in chunks of 1024 frames
        self.silence_chunks_limit = int((silence_duration * sample_rate) / 1024)
        self.reset()

    def reset(self):
        self.speaking = False
        self.silence_chunks = 0
        self.recorded_chunks = []

    def process_chunk(self, chunk) -> Tuple[bool, bool]:
        """
        Process a chunk of int16 audio (shape: [chunk_size, 1]).
        Returns (is_speaking, finished_speaking).
        """
        import numpy as np
        if len(chunk) == 0:
            return self.speaking, False

        # Calculate Root-Mean-Square (RMS)
        data = chunk.astype(np.float32)
        rms = np.sqrt(np.mean(data**2))

        is_speech = rms > self.threshold

        if is_speech:
            if not self.speaking:
                logger.info("VAD: Speech started (RMS: %.1f > Threshold: %.1f)", rms, self.threshold)
            self.speaking = True
            self.silence_chunks = 0
            self.recorded_chunks.append(chunk)
            return True, False
        else:
            if self.speaking:
                self.recorded_chunks.append(chunk)
                self.silence_chunks += 1
                if self.silence_chunks >= self.silence_chunks_limit:
                    logger.info("VAD: Speech ended (Silence limit reached)")
                    self.speaking = False
                    return False, True
                return True, False
            return False, False

class VoiceManager:
    """Manages audio recording, Speech-to-Text, and Text-to-Speech synthesis."""
    
    def __init__(self, config):
        self.config = config
        self._recording = False
        self._record_thread = None
        self._playback_thread = None
        self._audio_frames = []
        self._sd_stream = None
        
        # Audio directory
        self.temp_dir = Path(__file__).parent.parent / "data" / "audio"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.input_wav = self.temp_dir / "user_input.wav"
        self.output_wav = self.temp_dir / "astra_output.wav"

        # Load configs
        self.stt_enabled = self.config.get("voice.stt_enabled", False)
        self.tts_enabled = self.config.get("voice.tts_enabled", False)
        self.tts_engine = self.config.get("voice.tts_engine", "lily-tts") # "lily-tts"
        self.language = self.config.get("voice.language", "auto") # "auto", "es", "en", "ja"

        # S2S Hands-Free config
        self._hands_free_running = False
        self._hands_free_thread = None
        self._hands_free_state = "idle"
        self._is_speaking = False
        self.vad_threshold = self.config.get("voice.vad_threshold", 500)
        self.wake_word = self.config.get("voice.wake_word", "astra")

        # Try to pre-load whisper if library is installed
        self.whisper_model = None
        self._whisper_loaded = False

        self._cancel_speech = False
        self._text_queue = queue.Queue()
        self._audio_queue = queue.Queue()
        self._synthesis_thread = None
        self._playback_thread = None
        self._temp_file_counter = 0

    def start_recording(self) -> bool:
        """Start recording audio from microphone in a background thread."""
        if self._recording:
            return False
        
        self._recording = True
        self._audio_frames = []
        
        try:
            import sounddevice as sd
            import numpy as np
            
            self._audio_frames = []
            def callback(indata, frames, time_info, status):
                if status:
                    logger.warning("Sounddevice status: %s", status)
                self._audio_frames.append(indata.copy())
            
            # 16kHz, Mono, Int16 (Whisper standard)
            self._sd_stream = sd.InputStream(
                samplerate=16000,
                channels=1,
                dtype='int16',
                callback=callback
            )
            self._sd_stream.start()
            logger.info("Started microphone recording via sounddevice.")
            return True
        except ImportError:
            # Fallback to simulated recording thread
            logger.warning("sounddevice or numpy not installed. Running in SIMULATED voice recording mode.")
            self._record_thread = threading.Thread(target=self._simulated_record, daemon=True)
            self._record_thread.start()
            return True
        except Exception as e:
            logger.error("Failed to start voice recording: %s", e)
            self._recording = False
            return False

    def stop_recording(self) -> Tuple[bool, str]:
        """Stop recording and save output to WAV. Returns (success, wav_path_or_error)."""
        if not self._recording:
            return False, "Not recording"

        self._recording = False

        if self._sd_stream:
            try:
                self._sd_stream.stop()
                self._sd_stream.close()
                self._sd_stream = None
                
                # Save WAV file
                import numpy as np
                import soundfile as sf
                
                if not self._audio_frames:
                    return False, "No audio recorded"
                
                audio_data = np.concatenate(self._audio_frames, axis=0)
                sf.write(str(self.input_wav), audio_data, 16000)
                logger.info("Saved recorded audio to %s", self.input_wav)
                return True, str(self.input_wav)
            except Exception as e:
                logger.error("Failed to save audio file: %s", e)
                return False, str(e)
        else:
            # Simulated recording returns a demo question
            time.sleep(1.0)
            return True, "simulated"

    def is_recording(self) -> bool:
        return self._recording

    def _simulated_record(self):
        """Simulated audio recorder loop."""
        while self._recording:
            time.sleep(0.1)

    def transcribe_audio(self, wav_path: str) -> Tuple[str, str]:
        """Transcribe WAV audio. Returns (transcribed_text, detected_lang)."""
        if wav_path == "simulated":
            # Return a default mock speech input
            return "Astra, ¿cómo va el directo y cuántos espectadores tenemos?", "es"

        # Check local Whisper model
        try:
            from faster_whisper import WhisperModel
            if not self._whisper_loaded:
                # Load tiny model for low latency
                model_dir = self.config.get("voice.whisper_model_path", "tiny")
                self.whisper_model = WhisperModel(model_dir, device="cpu", compute_type="int8")
                self._whisper_loaded = True
            
            segments, info = self.whisper_model.transcribe(wav_path, beam_size=5)
            text = " ".join([segment.text for segment in segments]).strip()
            return text, info.language
        except Exception as e:
            logger.warning("Local faster-whisper not available or failed: %s. Using simulation.", e)
            return "Astra, ¿cómo va el directo?", "es"

    def speak(self, text: str, lang: str, emotion: str = "seria"):
        """Synthesize and play the text response asynchronously."""
        self.stop_speaking()
        self.speak_chunk(text, lang, emotion)

    def speak_chunk(self, text: str, lang: str, emotion: str = "seria"):
        """Append a text chunk to the real-time speech queue."""
        if not self.tts_enabled:
            return

        # Reset cancel flag so new chunks are processed
        self._cancel_speech = False

        # Split text into sentences
        import re
        raw_sentences = re.split(r'(?<=[.!?。！？\n])\s+', text)
        sentences = [s.strip() for s in raw_sentences if s.strip()]

        for s in sentences:
            self._text_queue.put((s, lang, emotion))

        # Start synthesis worker if not running or dead
        if not self._synthesis_thread or not self._synthesis_thread.is_alive():
            self._is_speaking = True
            self._synthesis_thread = threading.Thread(
                target=self._synthesis_worker,
                daemon=True
            )
            self._synthesis_thread.start()

        # Start playback worker if not running or dead
        if not self._playback_thread or not self._playback_thread.is_alive():
            self._is_speaking = True
            self._playback_thread = threading.Thread(
                target=self._playback_worker,
                daemon=True
            )
            self._playback_thread.start()

    def stop_speaking(self):
        """Instantly stop all active speech and clear the queue."""
        self._cancel_speech = True
        try:
            import sounddevice as sd
            sd.stop()
        except:
            pass

        # Empty the queues
        import queue
        while not self._text_queue.empty():
            try:
                self._text_queue.get_nowait()
            except:
                break
        while not self._audio_queue.empty():
            try:
                path = self._audio_queue.get_nowait()
                if path.exists():
                    path.unlink()
            except:
                break
        self._cleanup_stream_files()

    def _cleanup_stream_files(self):
        """Delete all temporary streaming wav files in temp_dir."""
        for f in self.temp_dir.glob("astra_stream_*.wav"):
            try:
                f.unlink()
            except Exception:
                pass

    def _synthesis_worker(self):
        """Consumes text chunks and synthesizes them to unique wav files."""
        self._temp_file_counter = 0
        while True:
            item = self._text_queue.get()
            if len(item) == 3:
                text, lang, emotion = item
            else:
                text, lang = item
                emotion = "seria"
            
            if self._cancel_speech:
                self._text_queue.task_done()
                continue
                
            culture = self._get_culture_code(lang)
            
            self._temp_file_counter += 1
            out_path = self.temp_dir / f"astra_stream_{self._temp_file_counter}.wav"
            
            if self.tts_engine == "sapi5":
                success = self._synthesize_sapi5(text, culture, output_path=out_path)
            elif self.tts_engine == "kokoro":
                success = self._synthesize_kokoro(text, culture, emotion, output_path=out_path)
            else:
                success = self._synthesize_lily_tts(text, culture, emotion, output_path=out_path)
            
            if self._cancel_speech:
                try:
                    out_path.unlink()
                except:
                    pass
                self._text_queue.task_done()
                continue
                
            if success and out_path.exists():
                self._audio_queue.put(out_path)
            else:
                logger.error("Failed to synthesize stream chunk: %s", text)
            self._text_queue.task_done()

    def _synthesize_sapi5(self, text: str, culture: str, output_path: Path) -> bool:
        """Synthesize audio using Windows SAPI5 natively."""
        import re
        # Clean text from raw markdown lists and brackets so SAPI5 reads them naturally
        cleaned_text = re.sub(r'(?m)^\s*[-*•+]\s+', '', text)
        cleaned_text = re.sub(r'(?m)^\s*\d+[\b.)]\s+', '', cleaned_text)
        cleaned_text = re.sub(r'\[EMOCION:\s*[a-zA-Z]+\]', '', cleaned_text)
        # Escape quotes for PowerShell cmd fallback
        escaped_text = cleaned_text.replace('"', '""').replace("'", "''")

        lang_hex = "409"
        if "es" in culture.lower():
            lang_hex = "40a"
        elif "ja" in culture.lower():
            lang_hex = "411"

        # Try using win32com first
        try:
            import win32com.client
            sp = win32com.client.Dispatch("SAPI.SpVoice")
            stream = win32com.client.Dispatch("SAPI.SpFileStream")
            
            # Try to select the correct voice
            try:
                voices = sp.GetVoices()
                for i in range(voices.Count):
                    v = voices.Item(i)
                    if v.GetAttribute("Language") == lang_hex:
                        sp.Voice = v
                        break
            except Exception as ve:
                logger.warning("Could not filter SAPI5 voice: %s", ve)
                
            stream.Open(str(output_path), 3, False)  # 3 = SSFMCreateForWrite
            sp.AudioOutputStream = stream
            sp.Speak(cleaned_text)
            stream.Close()
            logger.info("SAPI5 synthesized chunk (win32com): '%s'", cleaned_text[:30])
            return True
        except Exception as e:
            logger.warning("SAPI5 via win32com failed or not installed: %s. Falling back to PowerShell subprocess.", e)
            # Fallback to PowerShell
            try:
                ps_cmd = (
                    f"$sp = New-Object -ComObject SAPI.SpVoice; "
                    f"$lang_hex = '{lang_hex}'; "
                    f"foreach ($v in $sp.GetVoices()) {{ "
                    f"  if ($v.GetAttribute('Language') -eq $lang_hex) {{ "
                    f"    $sp.Voice = $v; break; "
                    f"  }} "
                    f"}}; "
                    f"$stream = New-Object -ComObject SAPI.SpFileStream; "
                    f"$stream.Open('{str(output_path)}', 3, $false); "
                    f"$sp.AudioOutputStream = $stream; "
                    f"$sp.Speak('{escaped_text}'); "
                    f"$stream.Close()"
                )
                res = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", ps_cmd],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=10.0
                )
                if res.returncode == 0 and output_path.exists():
                    logger.info("SAPI5 synthesized chunk (PowerShell): '%s'", cleaned_text[:30])
                    return True
                else:
                    logger.error("PowerShell SAPI5 synthesis failed with return code %s", res.returncode)
                    return False
            except Exception as pe:
                logger.error("SAPI5 fallback via PowerShell failed: %s", pe)
                return False


    def _synthesize_lily_tts(self, text: str, culture: str, emotion: str, output_path: Path) -> bool:
        """Synthesize audio using gTTS and apply Lily-style emotional modulation with pydub."""
        try:
            from gtts import gTTS
            from pydub import AudioSegment
        except ImportError:
            logger.error("gtts or pydub is not installed. Please install them to use Lily-TTS.")
            return False

        lang_short = culture.split("-")[0] # "es", "en", "ja"
        temp_mp3 = self.temp_dir / f"lily_temp_{self._temp_file_counter}.mp3"
        
        # Clean text from raw markdown lists and brackets so gTTS reads them naturally
        import re
        cleaned_text = re.sub(r'(?m)^\s*[-*•+]\s+', '', text)
        cleaned_text = re.sub(r'(?m)^\s*\d+[\b.)]\s+', '', cleaned_text)
        # Ensure we remove any raw emotion brackets if they leaked into speech text
        cleaned_text = re.sub(r'\[EMOCION:\s*[a-zA-Z]+\]', '', cleaned_text)
        
        try:
            tts = gTTS(text=cleaned_text, lang=lang_short, slow=False)
            tts.save(str(temp_mp3))
            
            if not temp_mp3.exists():
                logger.error("gTTS failed to save temporary MP3 file")
                return False
                
            audio = AudioSegment.from_mp3(str(temp_mp3))
            
            lily_modifiers = {
                "feliz": {"speed": 1.15, "vol": 2},
                "divertida": {"speed": 1.2, "vol": 2},
                "triste": {"speed": 0.9, "vol": -2},
                "enojada": {"speed": 1.2, "vol": 3},
                "sorprendida": {"speed": 1.15, "vol": 4},
                "neutral": {"speed": 1.1, "vol": 0},
                "seria": {"speed": 1.1, "vol": 0}
            }
            
            params = lily_modifiers.get(emotion.lower(), lily_modifiers["neutral"])
            speed_factor = params["speed"]
            vol_change = params["vol"]
            
            if speed_factor != 1.0:
                audio = audio._spawn(
                    audio.raw_data,
                    overrides={"frame_rate": int(audio.frame_rate * speed_factor)}
                ).set_frame_rate(audio.frame_rate)
                
            if vol_change != 0:
                audio = audio + vol_change
                
            audio.export(str(output_path), format="wav")
            logger.info("Lily-TTS synthesized chunk: '%s' (Lang: %s, Emotion: %s, Speed: %.2f)", text, lang_short, emotion, speed_factor)
            return True
            
        except Exception as e:
            logger.error("Failed to synthesize audio with Lily-TTS: %s", e)
            return False
        finally:
            if temp_mp3.exists():
                try:
                    temp_mp3.unlink()
                except:
                    pass

    def _synthesize_kokoro(self, text: str, culture: str, emotion: str, output_path: Path) -> bool:
        """Synthesize audio using Kokoro TTS from fastrtc."""
        try:
            from fastrtc import get_tts_model, KokoroTTSOptions
            import soundfile as sf
            import numpy as np
            import re
        except ImportError:
            logger.error("fastrtc or soundfile is not installed. Please install them to use Kokoro TTS.")
            return False

        # Clean text from raw markdown lists and brackets so Kokoro reads them naturally
        cleaned_text = re.sub(r'(?m)^\s*[-*•+]\s+', '', text)
        cleaned_text = re.sub(r'(?m)^\s*\d+[\b.)]\s+', '', cleaned_text)
        cleaned_text = re.sub(r'\[EMOCION:\s*[a-zA-Z]+\]', '', cleaned_text)

        try:
            # Map culture to Kokoro lang code
            lang = "es"
            if "en" in culture.lower():
                lang = "en-us"
            elif "ja" in culture.lower():
                lang = "ja"
            elif "es" in culture.lower():
                lang = "es"

            # Determine voice (default is ef_dora for Spanish, af_heart/af_bella for English)
            voice = self.config.get("voice.kokoro_voice", "ef_dora")

            # Initialize/get the model (fastrtc caches the model object and downloads/warms it up automatically)
            tts_model = get_tts_model()
            options = KokoroTTSOptions(voice=voice, lang=lang)

            # Collect audio chunks
            audio_data = []
            sr = 24000
            
            for chunk in tts_model.stream_tts_sync(cleaned_text, options=options):
                if chunk is not None:
                    # chunk is a tuple (sample_rate, ndarray)
                    sr, data = chunk
                    audio_data.append(data)
            
            if not audio_data:
                logger.error("Kokoro TTS returned no audio data")
                return False

            # Concatenate all chunks into one continuous array
            full_audio = np.concatenate(audio_data, axis=0)

            # Save as WAV file
            sf.write(str(output_path), full_audio, sr)
            logger.info("Kokoro-TTS synthesized chunk: '%s' (Voice: %s, Lang: %s)", cleaned_text[:30], voice, lang)
            return True

        except Exception as e:
            logger.error("Failed to synthesize audio with Kokoro-TTS: %s", e)
            return False

    def _playback_worker(self):
        """Consumes synthesized wav files and plays them sequentially with a pause."""
        import time
        sentence_pause = 1.0
        
        while True:
            audio_path = self._audio_queue.get()
            
            if self._cancel_speech:
                self._audio_queue.task_done()
                continue
                
            if audio_path.exists():
                self._is_speaking = True
                self._play_wav(str(audio_path))
                try:
                    audio_path.unlink()
                except:
                    pass
                    
            self._audio_queue.task_done()
            
            # If all queues are empty, we are done speaking
            if self._audio_queue.empty() and self._text_queue.empty():
                self._is_speaking = False
            
            if not self._cancel_speech and (not self._text_queue.empty() or not self._audio_queue.empty()):
                time.sleep(sentence_pause)



    def _play_wav(self, wav_path: str):
        """Play WAV audio file using sounddevice (if available) or SAPI5/PowerShell player."""
        self._is_speaking = True
        try:
            import sounddevice as sd
            import soundfile as sf
            data, fs = sf.read(wav_path)
            sd.play(data, fs)
            duration = len(data) / fs
            import time
            start_time = time.time()
            while time.time() - start_time < duration:
                if self._cancel_speech:
                    sd.stop()
                    break
                time.sleep(0.05)
            logger.info("Played audio via sounddevice.")
        except:
            # Fallback: Play asynchronously using Windows Media SoundPlayer in PowerShell
            try:
                ps_cmd = f'$player = New-Object Media.SoundPlayer "{wav_path}"; $player.PlaySync()'
                subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception as e:
                logger.error("Failed to play WAV file: %s", e)
        finally:
            self._is_speaking = False

    def _get_culture_code(self, lang: str) -> str:
        """Translates basic language codes to Windows Culture tags."""
        l = lang.lower().strip()
        if "es" in l:
            return "es-ES"
        elif "en" in l:
            return "en-US"
        elif "ja" in l:
            return "ja-JP"
        
        # Default based on user config language
        config_lang = self.language.lower()
        if "es" in config_lang:
            return "es-ES"
        elif "en" in config_lang:
            return "en-US"
        elif "ja" in config_lang:
            return "ja-JP"
        return "es-ES" # Fallback

    def start_hands_free(self, state_callback, text_received_callback) -> bool:
        """Start the Speech-to-Speech hands-free loop in a background thread."""
        if self._hands_free_running:
            return False
            
        self._hands_free_running = True
        self._hands_free_thread = threading.Thread(
            target=self._hands_free_loop,
            args=(state_callback, text_received_callback),
            daemon=True
        )
        self._hands_free_thread.start()
        return True

    def stop_hands_free(self):
        """Stop the Speech-to-Speech hands-free loop."""
        self._hands_free_running = False
        self._hands_free_state = "idle"
        # Beep to confirm deactivation
        self._play_beep(600, 150)

    def is_hands_free_running(self) -> bool:
        return self._hands_free_running

    def get_hands_free_state(self) -> str:
        return self._hands_free_state

    def _play_beep(self, frequency: int, duration: int):
        """Play a local system beep chime."""
        try:
            import winsound
            winsound.Beep(frequency, duration)
        except Exception:
            pass

    def _hands_free_loop(self, state_callback, text_received_callback):
        """The background S2S hands-free state machine loop."""
        import numpy as np
        import queue
        
        has_sounddevice = False
        try:
            import sounddevice as sd
            import soundfile as sf
            # Try opening a dummy stream to verify the audio input hardware is active
            test_stream = sd.InputStream(samplerate=16000, channels=1, dtype='int16')
            test_stream.start()
            test_stream.stop()
            test_stream.close()
            has_sounddevice = True
        except Exception as e:
            logger.warning("sounddevice failed to open input stream (%s). Falling back to SIMULATION mode.", e)

        # 1. Calibration state
        self._hands_free_state = "calibrating"
        state_callback("calibrating")
        
        logger.info("Hands-free: Starting calibration of VAD threshold...")
        
        calib_threshold = 500
        if has_sounddevice:
            try:
                # Record 1.0 second of silence to calibrate noise threshold
                calib_queue = queue.Queue()
                def calib_callback(indata, frames, time_info, status):
                    calib_queue.put(indata.copy())
                
                calib_stream = sd.InputStream(samplerate=16000, channels=1, dtype='int16', callback=calib_callback)
                rms_vals = []
                with calib_stream:
                    start_time = time.time()
                    while time.time() - start_time < 1.0:
                        try:
                            chunk = calib_queue.get(timeout=0.1)
                            rms = np.sqrt(np.mean(chunk.astype(np.float32)**2))
                            rms_vals.append(rms)
                        except queue.Empty:
                            continue
                if rms_vals:
                    avg_rms = np.mean(rms_vals)
                    # Set threshold to avg noise + 250 (tuned for good sensitivity)
                    calib_threshold = max(200, int(avg_rms + 250))
                    logger.info("Hands-free: Calibrated VAD threshold to %d (Avg Noise RMS: %.1f)", calib_threshold, avg_rms)
            except Exception as e:
                logger.error("Hands-free calibration failed: %s. Using default threshold 500", e)
                calib_threshold = self.config.get("voice.vad_threshold", 500)
                has_sounddevice = False
        else:
            time.sleep(1.0)
            logger.info("Hands-free: Simulation calibration finished. Using threshold 500")

        self.vad_threshold = calib_threshold
        
        # Chime to signal ready
        self._play_beep(1200, 100)
        self._play_beep(1500, 100)

        # 2. Main loop
        while self._hands_free_running:
            self._hands_free_state = "waiting_wake_word"
            state_callback("waiting_wake_word")
            logger.info("Hands-free: Waiting for wake word 'Astra'...")
            
            wake_word_detected = False
            
            if has_sounddevice:
                try:
                    q = queue.Queue()
                    def callback(indata, frames, time_info, status):
                        q.put(indata.copy())
                    
                    # 16kHz, Mono, Int16
                    stream = sd.InputStream(samplerate=16000, channels=1, dtype='int16', callback=callback)
                    
                    rolling_buffer = []
                    # 2 seconds of audio at 16kHz is 32000 samples.
                    max_buffer_samples = 32000
                    
                    with stream:
                        last_transcribe_time = time.time()
                        while self._hands_free_running and self._hands_free_state == "waiting_wake_word":
                            try:
                                chunk = q.get(timeout=0.1)
                                rolling_buffer.append(chunk)
                                
                                # Flatten and trim rolling buffer to keep last 2 seconds
                                total_samples = sum(len(c) for c in rolling_buffer)
                                if total_samples > max_buffer_samples:
                                    # Concatenate and trim
                                    flat = np.concatenate(rolling_buffer, axis=0)
                                    flat = flat[-max_buffer_samples:]
                                    rolling_buffer = [flat]
                                
                                # Transcribe every 1.2 seconds if there's enough audio
                                if time.time() - last_transcribe_time >= 1.2 and total_samples >= 16000:
                                    last_transcribe_time = time.time()
                                    flat = np.concatenate(rolling_buffer, axis=0)
                                    
                                    # Write temp wake audio file
                                    wake_wav = self.temp_dir / "wake_temp.wav"
                                    sf.write(str(wake_wav), flat, 16000)
                                    
                                    # Transcribe
                                    text, lang = self.transcribe_audio(str(wake_wav))
                                    try:
                                        wake_wav.unlink()
                                    except:
                                        pass
                                        
                                    text_lower = text.lower()
                                    logger.debug("Hands-free wake monitor transcription: '%s'", text)
                                    if self.wake_word.lower() in text_lower or "valeria" in text_lower or "hola astra" in text_lower:
                                        logger.info("Hands-free: Wake word detected! Transcribed: '%s'", text)
                                        wake_word_detected = True
                                        break
                            except queue.Empty:
                                continue
                except Exception as e:
                    logger.error("Hands-free wake monitor error: %s. Falling back to simulation.", e)
                    has_sounddevice = False
                    time.sleep(2.0)
            else:
                # Simulated wake word detection
                start_wait = time.time()
                while self._hands_free_running and time.time() - start_wait < 4.0:
                    time.sleep(0.1)
                if self._hands_free_running:
                    logger.info("Hands-free: Simulated wake word detected!")
                    wake_word_detected = True
            
            if not wake_word_detected or not self._hands_free_running:
                continue
                
            # Activation Chime
            self._play_beep(1000, 200)
            
            # 3. Active Conversation Loop
            active_conversation = True
            empty_turns = 0
            
            while active_conversation and self._hands_free_running:
                self._hands_free_state = "listening"
                state_callback("listening")
                logger.info("Hands-free: Active conversation - Listening...")
                
                user_audio_path = None
                
                if has_sounddevice:
                    try:
                        # Record using VAD
                        vad = VADDetector(self.vad_threshold)
                        q = queue.Queue()
                        def callback(indata, frames, time_info, status):
                            q.put(indata.copy())
                            
                        stream = sd.InputStream(samplerate=16000, channels=1, dtype='int16', callback=callback)
                        
                        audio_chunks = []
                        start_time = time.time()
                        last_speech_time = time.time()
                        
                        # Wait for user to start speaking
                        speech_started = False
                        finished = False
                        
                        with stream:
                            # Timeout if they don't start speaking in 8 seconds
                            while self._hands_free_running and not finished and (time.time() - start_time < 8.0):
                                try:
                                    chunk = q.get(timeout=0.1)
                                    is_speaking, finished_speaking = vad.process_chunk(chunk)
                                    
                                    if is_speaking:
                                        speech_started = True
                                        last_speech_time = time.time()
                                        audio_chunks.append(chunk)
                                    elif speech_started:
                                        # Silence buffer
                                        audio_chunks.append(chunk)
                                        
                                    if finished_speaking:
                                        finished = True
                                        break
                                except queue.Empty:
                                    continue
                        
                        if speech_started and audio_chunks:
                            audio_data = np.concatenate(audio_chunks, axis=0)
                            # Write wav
                            sf.write(str(self.input_wav), audio_data, 16000)
                            user_audio_path = str(self.input_wav)
                        else:
                            user_audio_path = None # timeout/no audio
                            
                    except Exception as e:
                        logger.error("Hands-free VAD recording error: %s. Falling back to simulation.", e)
                        has_sounddevice = False
                        time.sleep(1.0)
                else:
                    # Simulated user speech
                    time.sleep(3.0)
                    if self._hands_free_running:
                        user_audio_path = "simulated"
                
                if not self._hands_free_running:
                    break
                    
                if user_audio_path is None:
                    # No speech detected (silence timeout)
                    empty_turns += 1
                    logger.info("Hands-free: Silence detected (Turn %d/3)", empty_turns)
                    if empty_turns >= 3:
                        logger.info("Hands-free: Silence limit reached. Exiting active conversation.")
                        self._play_beep(600, 300)
                        # Speak goodbye
                        self.speak("Hasta luego, estaré atenta si me necesitas.", "es")
                        # Wait for speaking to finish
                        while self._is_speaking and self._hands_free_running:
                            time.sleep(0.1)
                        active_conversation = False
                    continue
                
                # Transcribe
                self._hands_free_state = "processing"
                state_callback("processing")
                
                text, lang = self.transcribe_audio(user_audio_path)
                logger.info("Hands-free: User said: '%s' (Lang: %s)", text, lang)
                
                if not text.strip():
                    empty_turns += 1
                    if empty_turns >= 3:
                        logger.info("Hands-free: Empty transcription limit reached. Exiting.")
                        self._play_beep(600, 300)
                        self.speak("Hasta luego.", "es")
                        while self._is_speaking and self._hands_free_running:
                            time.sleep(0.1)
                        active_conversation = False
                    continue
                
                # Reset empty turns on successful input
                empty_turns = 0
                
                # Send text to GUI callback
                text_received_callback(text)
                
                # Wait for assistant to finish processing and speaking (or interrupt if user speaks)
                time.sleep(0.5) # Give it a moment to change speaking state
                interrupted = False
                if has_sounddevice:
                    try:
                        # Light VAD loop to check if user talks while Astra speaks
                        # We use a slightly higher threshold to ignore system audio/echo
                        interrupt_vad = VADDetector(self.vad_threshold + 150)
                        q_inter = queue.Queue()
                        def callback_inter(indata, frames, time_info, status):
                            q_inter.put(indata.copy())
                            
                        stream_inter = sd.InputStream(samplerate=16000, channels=1, dtype='int16', callback=callback_inter)
                        speech_frames_count = 0
                        
                        with stream_inter:
                            while (self._is_speaking or (self._playback_thread and self._playback_thread.is_alive())) and self._hands_free_running:
                                try:
                                    chunk = q_inter.get(timeout=0.05)
                                    is_speaking, _ = interrupt_vad.process_chunk(chunk)
                                    if is_speaking:
                                        speech_frames_count += 1
                                        if speech_frames_count >= 5: # Continuous speech for 250ms
                                            logger.info("Hands-free: User interruption detected! Stopping active speaking.")
                                            self.stop_speaking()
                                            interrupted = True
                                            break
                                    else:
                                        speech_frames_count = max(0, speech_frames_count - 1)
                                except queue.Empty:
                                    continue
                    except Exception as e:
                        logger.error("Error in hands-free interruption monitor: %s", e)
                        while (self._is_speaking or (self._playback_thread and self._playback_thread.is_alive())) and self._hands_free_running:
                            time.sleep(0.1)
                else:
                    # Simulation mode
                    while (self._is_speaking or (self._playback_thread and self._playback_thread.is_alive())) and self._hands_free_running:
                        time.sleep(0.1)
                        
                # Short delay to prevent feedback loop
                time.sleep(0.8)

    def reconfigure_tts(self, stt_enabled, tts_enabled, tts_engine, language, wake_word, vad_threshold):
        self.stt_enabled = stt_enabled
        self.tts_enabled = tts_enabled
        self.tts_engine = tts_engine
        self.language = language
        self.wake_word = wake_word
        self.vad_threshold = vad_threshold
