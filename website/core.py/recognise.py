import os
import logging
from multiprocessing import Pool, Lock, current_process
import numpy as np
from tinytag import TinyTag
import settings
from record import record_audio
from fingerprint import fingerprint_file, fingerprint_audio
from storage import store_song, get_matches, get_info_for_song_id, song_in_db, checkpoint_db

KNOWN_EXTENSIONS = ["mp3", "wav", "flac", "m4a"]


def get_song_info(filename):
    """Obtiene las etiquetas ID3 para un archivo. Devuelve 'None' para los valores de tupla que no existen.
    :param filename: ruta al archivo con etiquetas para leer
    :returns: (artista, álbum, título)
    :rtype: tuple(str/Ninguno, str/Ninguno, str/Ninguno)
    """

    tag = TinyTag.get(filename)
    artist = tag.artist if tag.albumartist is None else tag.albumartist
    return print((artist, tag.album, tag.title))


def register_song(filename):
    """Registrar una sola canción.
    Comprueba si la canción ya está registrada en función de la ruta proporcionada e ignora
    los que ya están registrados.
    :param filename: Ruta al archivo a registrar"""

    if song_in_db(filename):
        return
    hashes = fingerprint_file(filename)
    song_info = get_song_info(filename)
    try:
        logging.info(f"{current_process().name} waiting to write {filename}")
        with lock:
            logging.info(f"{current_process().name} writing {filename}")
            store_song(hashes, song_info)
            logging.info(f"{current_process().name} wrote {filename}")
    except NameError:
        logging.info(f"Single-threaded write of {filename}")
        # running single-threaded, no lock needed
        store_song(hashes, song_info)


def register_directory(path):
    """Registra recursivamente canciones en un directorio.
    Utiliza :data:`~abracadabra.settings.NUM_WORKERS` trabajadores en un grupo para registrar canciones en un
    directorio.
    :param path: Ruta del directorio a registrar
    """

    def pool_init(l):
        """Función init que pone a disposición una llave a cada uno de los trabajadores en
        el grupo. Permite la sincronización de escrituras de db ya que SQLite solo admite
        un escritor a la vez.
        """

        global lock
        lock = l
        logging.info(f"Pool init in {current_process().name}")

    to_register = []
    for root, _, files in os.walk(path):
        for f in files:
            if f.split('.')[-1] not in KNOWN_EXTENSIONS:
                continue
            file_path = os.path.join(path, root, f)
            to_register.append(file_path)
    l = Lock()
    with Pool(settings.NUM_WORKERS, initializer=pool_init, initargs=(l,)) as p:
        p.map(register_song, to_register)
    # speed up future reads
    checkpoint_db()


def score_match(offsets):
    """Encontrar una cancion que coincide.
    Calcula un histograma de los deltas entre las distancias de tiempo de los hash de la
    muestra grabada y las distancias de tiempo de los hashes coincidentes en la base de datos para una canción.
    Luego, la función devuelve el tamaño del contenedor más grande en este histograma como una puntuación.
    :param offsets: Lista de pares de distancias para hashes coincidentes
    :returns: El pico más alto en un histograma de deltas de tiempo
    :rtipo: int
    """

    # Use bins spaced 0.5 seconds apart
    binwidth = 0.5
    tks = list(map(lambda x: x[0] - x[1], offsets))
    hist, _ = np.histogram(tks,
                           bins=np.arange(int(min(tks)),
                                          int(max(tks)) + binwidth + 1,
                                          binwidth))
    return np.max(hist)


def best_match(matches):
    """Para un diccionario de song_id: distancias, devuelve el mejor song_id.
    Califica cada canción en el diccionario de coincidencias y luego devuelve el song_id con la mejor puntuación.
    :param matches: diccionario de song_id a la lista de pares distancias ​​(db_offset, sample_offset)
       como lo devuelve :func:`~abracadabra.Storage.storage.get_matches`.
    :returns: song_id con la mejor puntuación.
    :rtype: str
    """

    matched_song = None
    best_score = 0
    for song_id, offsets in matches.items():
        if len(offsets) < best_score:
            # can't be best score, avoid expensive histogram
            continue
        score = score_match(offsets)
        if score > best_score:
            best_score = score
            matched_song = song_id
    return matched_song


def recognise_song(filename):
    """Reconoce una muestra pregrabada.
    Reconoce la muestra almacenada en la ruta ``filename``. La muestra puede estar en cualquiera de los
    formatos en :data:`recognise.KNOWN_FORMATS`.
    :param filename: Ruta del archivo a reconocer.
    :returns: :func:`~abracadabra.recognise.get_song_info` resultado de la canción coincidente o Ninguno.
    :rtipo: tupla(cadena, cadena, cadena)
    """

    hashes = fingerprint_file(filename)
    matches = get_matches(hashes)
    matched_song = best_match(matches)
    info = get_info_for_song_id(matched_song)
    if info is not None:
        return print(info)
    else:
        print("Did not find a result")
    return matched_song


def listen_to_song(filename=None):
    """Reconoce una canción usando el micrófono.
    Opcionalmente, guarda la muestra registrada utilizando la ruta proporcionada para su uso en futuras pruebas.
    Esta función es buena para reconocimientos únicos, para generar un conjunto de pruebas completo, mire
    en :func:`~abracadabra.record.gen_many_tests`.
    :param filename: La ruta para almacenar la muestra grabada (opcional)
    :returns: :func:`~abracadabra.recognise.get_song_info` resultado de la canción coincidente o Ninguno.
    :rtipo: tupla(cadena, cadena, cadena)
    """

    audio = record_audio(filename=filename)
    hashes = fingerprint_audio(audio)
    matches = get_matches(hashes)
    matched_song = best_match(matches)
    info = get_info_for_song_id(matched_song)
    if info is not None:
        return print(info)
    else:
        print("Did not find a result")
    return matched_song

#recognise_song("static/trim/test.mp3")
listen_to_song()

#register_directory("../Fantasy")