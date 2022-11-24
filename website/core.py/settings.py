SAMPLE_RATE = 44100
""" Cuando se toma la huella digital de un archivo, es remuestreado a SAMPLE_RATE Hz.
Frecuencias de muestreo más altas significan una mayor precisión en el reconocimiento, pero también un reconocimiento más lento
y tamaños de archivo de base de datos más grandes. Configurándolo más alto que la frecuencia de muestreo para su
los archivos de entrada podrían causar problemas.
"""

PEAK_BOX_SIZE = 30
""" El número de puntos en un espectrograma alrededor de un pico para que se considere un pico.
Configurarlo más alto reduce la cantidad de huellas dactilares generadas, pero también reduce la precisión.
Establecerlo demasiado bajo puede reducir severamente la velocidad y la precisión del reconocimiento.
"""

POINT_EFFICIENCY = 0.8
""" Un factor entre 0 y 1 que determina el número de picos encontrados para cada archivo.
Afecta el tamaño y la precisión de la base de datos.
"""

TARGET_START = 0.05
""" Cuántos segundos después de un punto de anclaje para iniciar la zona de objetivo para el emparejamiento.
"""

TARGET_T = 1.8
""" El ancho de la zona de destino en segundos. Más ancho conduce a más huellas dactilares y mayor precisión
hasta cierto punto, pero luego comienza a perder precisión.
"""

TARGET_F = 4000
""" La altura de la zona de objetivo en Hz. Más alto significa mayor precisión.
Puede oscilar entre 0 y (0,5 * SAMPLE_RATE).
"""

FFT_WINDOW_SIZE = 0.2
""" La cantidad de segundos de audio que se usarán en cada segmento del espectrograma. Las ventanas más grandes significan una mayor
resolución de frecuencia pero menor resolución de tiempo en el espectrograma.
"""

DB_PATH = "hash.db"
""" Ruta al archivo de base de datos a utilizar. """

NUM_WORKERS = 24
""" Número de trabajadores a utilizar al registrar canciones. """