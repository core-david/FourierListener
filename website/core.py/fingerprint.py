import uuid
import numpy as np
import settings
from pydub import AudioSegment
from scipy.signal import spectrogram
from scipy.ndimage import maximum_filter


def my_spectrogram(audio):
    """Funcion auxiliar que realiza el espectrograma con los valores dentro de los ajustes"""
    nperseg = int(settings.SAMPLE_RATE * settings.FFT_WINDOW_SIZE)
    return spectrogram(audio, settings.SAMPLE_RATE, nperseg=nperseg)


def file_to_spectrogram(filename):
    """ Calcula el espectrograma del archivo
    Convierte un archivo a mono y hace un remuestreo a :data:`~abracadabra.settings.SAMPLE_RATE` anntes de calcular.Usa :data:`~abracadabra.settings.FFT_WINDOW_SIZE` para tamaño de pantalla.
    :param filename: ruta al archivo para el espectrograma.
    :returns: * f - lista de frecuencias
              * t - lista de tiempos
              * Sxx - Valor de potencia para cada par tiempo/frecuencia
    """

    a = AudioSegment.from_file(filename).set_channels(1).set_frame_rate(settings.SAMPLE_RATE)
    audio = np.frombuffer(a.raw_data, np.int16)
    return my_spectrogram(audio)


def find_peaks(Sxx):

    """Encuentra los picos en el espectograma. 
    Usa :data:`~abracadabra.settings.PEAK_BOX_SIZE` como el tamaño de la región alrededor de cada
    pico. Calcula el número de picos a devolver en función de cuántos picos podrían teóricamente
    encajar en el espectrograma y el :data:`~abracadabra.settings.POINT_EFFICIENCY`.
    Insipirado por 
    `photutils
    <https://photutils.readthedocs.io/en/stable/_modules/photutils/detection/core.html#find_peaks>`_.
    :param Sxx: El espectrograma.
    :returns: Una lista de picos en el espectrograma.
    """


    data_max = maximum_filter(Sxx, size=settings.PEAK_BOX_SIZE, mode='constant', cval=0.0)
    peak_goodmask = (Sxx == data_max)  # good pixels are True
    y_peaks, x_peaks = peak_goodmask.nonzero()
    peak_values = Sxx[y_peaks, x_peaks]
    i = peak_values.argsort()[::-1]
    # get co-ordinates into arr
    j = [(y_peaks[idx], x_peaks[idx]) for idx in i]
    total = Sxx.shape[0] * Sxx.shape[1]
    # in a square with a perfectly spaced grid, we could fit area / PEAK_BOX_SIZE^2 points
    # use point efficiency to reduce this, since it won't be perfectly spaced
    # accuracy vs speed tradeoff
    peak_target = int((total / (settings.PEAK_BOX_SIZE**2)) * settings.POINT_EFFICIENCY)
    return j[:peak_target]


def idxs_to_tf_pairs(idxs, t, f):
    """Funcion Auxiliar para convertir índices de tiempo/frecuencia en valores."""
    return np.array([(f[i[0]], t[i[1]]) for i in idxs])


def hash_point_pair(p1, p2):
    """Funcion auxiliar para generar un hash a partir de dos puntos de tiempo/frecuencia. """
    return hash((p1[0], p2[0], p2[1]-p2[1]))


def target_zone(anchor, points, width, height, t):
    """Genera una zona de objetivo como se describe en `el documento de Shazam
    <https://www.ee.columbia.edu/~dpwe/papers/Wang03-shazam.pdf>`_.
    Dado un punto de anclaje, produce todos los puntos dentro de un cuadro que comienza `t` segundos después del punto,
    y tiene ancho `ancho` y alto `alto`.
    :param anchor: El punto de anclaje
    :param points: La lista de puntos a buscar
    :param width: El ancho de la zona de destino
    :param height: La altura de la zona objetivo
    :param t: Cuántos segundos después del punto de anclaje debe comenzar la zona objetivo
    :returns: Da todos los puntos dentro de la zona de objetivo.
    """

    x_min = anchor[1] + t
    x_max = x_min + width
    y_min = anchor[0] - (height*0.5)
    y_max = y_min + height
    for point in points:
        if point[0] < y_min or point[0] > y_max:
            continue
        if point[1] < x_min or point[1] > x_max:
            continue
        yield point


def hash_points(points, filename):
    """Genera todos los valores hash para una lista de picos.
    Itera a través de los picos, generando un hash para cada pico dentro de la zona de objetivo de ese pico.
    :param points: La lista de picos.
    :param filename: El nombre de archivo de la canción, usado para generar song_id.
    :returns: Una lista de tuplas de la forma (hash, time offset, song_id).
    """

    hashes = []
    song_id = uuid.uuid5(uuid.NAMESPACE_OID, filename).int
    for anchor in points:
        for target in target_zone(
            anchor, points, settings.TARGET_T, settings.TARGET_F, settings.TARGET_START
        ):
            hashes.append((
                # hash
                hash_point_pair(anchor, target),
                # time offset
                anchor[1],
                # filename
                str(song_id)
            ))
    return hashes


def fingerprint_file(filename):
    """Genera hashes para un archivo.
    Dado un archivo, lo ejecuta a través del proceso de huella digital para producir una lista de hashes a partir de él.
    :param filename: La ruta al archivo.
    :returns: La salida de :func:`hash_points`.
    """

    f, t, Sxx = file_to_spectrogram(filename)
    peaks = find_peaks(Sxx)
    peaks = idxs_to_tf_pairs(peaks, t, f)
    return hash_points(peaks, filename)


def fingerprint_audio(frames):
    """Genera hashes para una serie de marcos de audio.
    Se utiliza al grabar audio.
    :param frames: Un flujo de audio mono. El tipo de datos es cualquiera que acepte ``scipy.signal.spectrogram``.
    :returns: La salida de :func:`hash_points`.
    """

    f, t, Sxx = my_spectrogram(frames)
    peaks = find_peaks(Sxx)
    peaks = idxs_to_tf_pairs(peaks, t, f)
    return hash_points(peaks, "recorded")