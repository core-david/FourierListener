import wave
import pyaudio
import numpy as np

CHUNK = 1024
"""Numero de marcos para almacenar antes de escribir."""
FORMAT = pyaudio.paInt16
"""El tipo de datos utilizado para grabar audio. Ver ``pyaudio`` para las constantes."""
CHANNELS = 1
"""El número de canales para grabar."""
RATE = 44100
"""La frecuencia de muestreo."""
RECORD_SECONDS = 7
"""Número de segundos para grabar."""



def record_audio(filename=None):
    """ Graba 10 segundos de audio y, opcionalmente, guárdelo en un archivo
    :param filename: La ruta para guardar el audio (opcional).
    :returns: El flujo de audio con los parámetros definidos en este módulo.
    """
    p = pyaudio.PyAudio()

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print("* recording")

    frames = []
    write_frames = []

    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(np.frombuffer(data, dtype=np.int16))
        if filename is not None:
            write_frames.append(data)

    print("* done recording")

    stream.stop_stream()
    stream.close()
    p.terminate()

    if filename is not None:
        wf = wave.open(filename, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()

    
    return np.hstack(frames)


