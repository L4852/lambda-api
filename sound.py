import numpy as np
import pyttsx3
import sounddevice as sd


class Sound:
    def __init__(self):
        pass

    def beep(self, frequency: float, duration: float, volume: float = 0.5):
        sample_rate = 44100

        time_points = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)

        wave = volume * np.sin(2 * np.pi * frequency * time_points)

        sd.play(wave)
        sd.wait()

    def say(self, text: str):
        tts_engine = pyttsx3.init()

        voices = tts_engine.getProperty("voices")

        tts_engine.setProperty("voice", voices[22].id)
        tts_engine.say(text)
        tts_engine.runAndWait()
        tts_engine.stop()

    def list_voices(self):
        tts_engine = pyttsx3.init()

        voices = tts_engine.getProperty("voices")

        for index, voice in enumerate(voices):
            # Print the index, name, and languages of each voice
            print(f"Index: {index} | Name: {voice.name} | Languages: {voice.languages}")

    def play_error_sound(self):
        self.beep(440, 0.15)
        self.beep(535.25, 0.15)
        self.beep(622.25, 0.15)

    def play_setup_sound(self):
        self.beep(440, 0.2)
        self.beep(554.37, 0.2)
        self.beep(659.25, 0.2)

    def play_disconnect_sound(self):
        self.beep(659.25, 0.2)
        self.beep(554.37, 0.2)
        self.beep(440, 0.2)

    def play_connecting_progress_sound(self):
        self.beep(329.63, 0.1)
        self.beep(329.63, 0.1)
        self.beep(329.63, 0.1)

    def play_connected_sound(self):
        self.beep(261.33, 0.1)
        self.beep(522.66, 0.1)

    def play_ping_sound(self):
        self.beep(880, 0.1)

    def play_ping2_sound(self):
        self.beep(493.88, 0.1)

    def play_generic_task_sound(self):
        self.beep(261.33, 0.1)


if __name__ == "__main__":
    snd = Sound()

    snd.play_setup_sound()
    snd.play_error_sound()

    for i in range(2):
        snd.play_ping_sound()
        snd.play_generic_task_sound()

    snd.play_connecting_progress_sound()
    snd.say("Connecting...")
    snd.say("Setting homing mask...")
