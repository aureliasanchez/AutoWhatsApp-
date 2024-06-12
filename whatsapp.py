from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv
import random
import threading
import traceback

# Función para leer la lista de destinatarios y mensajes desde un archivo CSV
def leer_datos(csv_file):
    numeros = []
    mensajes = []
    imagenes = []
    with open(csv_file, newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)  # Omitir la fila de encabezado
        for row in reader:
            numeros.append(row[0])
            mensajes.append(row[1])
            imagenes.append(row[2] if len(row) > 2 else None)
    return numeros, mensajes, imagenes

# Función para enviar un mensaje a través de un navegador
def enviar_mensaje(navegador, numero, mensaje, imagen=None):
    navegador.get(f'https://web.whatsapp.com/send?phone={numero}')
    try:
        # Esperar hasta que el elemento de entrada de texto esté presente y visible
        caja_mensaje = WebDriverWait(navegador, 20).until(
            EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="1"]'))
        )
        time.sleep(random.uniform(1, 3))  # Espera adicional para asegurar la carga completa
        caja_mensaje.send_keys(mensaje)
        caja_mensaje.send_keys(Keys.ENTER)
        time.sleep(random.uniform(1, 20))  # Esperar un tiempo aleatorio antes de enviar el siguiente mensaje
        if imagen:
            clip_button = WebDriverWait(navegador, 20).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "span[data-icon='clip']"))
            )
            clip_button.click()
            time.sleep(random.uniform(2, 5))
            attach_input = WebDriverWait(navegador, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
            )
            attach_input.send_keys(imagen)
            time.sleep(random.uniform(2, 5))
            send_button = WebDriverWait(navegador, 20).until(
                EC.element_to_be_clickable((By.XPATH, '//span[@data-icon="send"]'))
            )
            send_button.click()
            time.sleep(random.uniform(5, 10))
    except Exception as e:
        print(f"Error al enviar mensaje a {numero}: {e}")
        print(traceback.format_exc())

# Función para enviar mensajes en lotes
def enviar_mensajes_en_lote(navegador, numeros, mensajes, imagenes):
    for numero, mensaje, imagen in zip(numeros, mensajes, imagenes):
        try:
            enviar_mensaje(navegador, numero, mensaje, imagen)
        except Exception as e:
            print(f"Error al procesar número {numero}: {e}")
            print(traceback.format_exc())
        time.sleep(random.uniform(1, 20))  # Espera aleatoria entre mensajes

# Ruta al chromedriver
chromedriver_path = r'C:\Users\Administrator\Downloads\chromedriver-win64\chromedriver.exe'

# Inicialización del servicio de chromedriver
servicio = Service(chromedriver_path)

# Lista compartida para almacenar las instancias de los navegadores
navegadores = []

# Función para inicializar navegador y verificar sesión
def inicializar_y_verificar(nombre):
    navegador = webdriver.Chrome(service=servicio)
    navegador.get("https://web.whatsapp.com")
    print(f"Por favor, inicia sesión en WhatsApp Web en el navegador {nombre}.")
    try:
        WebDriverWait(navegador, 60).until(
            EC.presence_of_element_located((By.XPATH, '//canvas[@aria-label="Scan me!"]'))
        )
        print(f"Código QR encontrado en {nombre}. Esperando que desaparezca...")
        WebDriverWait(navegador, 300).until_not(
            EC.presence_of_element_located((By.XPATH, '//canvas[@aria-label="Scan me!"]'))
        )
        print(f"Sesión iniciada correctamente en {nombre}.")
    except:
        print(f"No se encontró el código QR en {nombre}. Es posible que la sesión ya esté iniciada.")
    navegadores.append(navegador)

# Inicializar navegadores en hilos
nombres_navegadores = ['navegador1', 'navegador2', 'navegador3']
hilos_inicializacion = []

for nombre in nombres_navegadores:
    hilo = threading.Thread(target=inicializar_y_verificar, args=(nombre,))
    hilos_inicializacion.append(hilo)
    hilo.start()

# Esperar a que todos los hilos de inicialización terminen
for hilo in hilos_inicializacion:
    hilo.join()

# Asegurarse de que tengamos tres navegadores inicializados
if len(navegadores) < 3:
    print("Error al inicializar los navegadores. Asegúrate de que las sesiones de WhatsApp estén iniciadas.")
    exit()

# Cargar los datos
numeros, mensajes, imagenes = leer_datos('datos.csv')

# Dividir la lista de destinatarios entre los tres navegadores
divisor = len(numeros) // 3
listas = [numeros[:divisor], numeros[divisor:2*divisor], numeros[2*divisor:]]
mensajes_listas = [mensajes[:divisor], mensajes[divisor:2*divisor], mensajes[2*divisor:]]
imagenes_listas = [imagenes[:divisor], imagenes[divisor:2*divisor], imagenes[2*divisor:]]

# Crear hilos para enviar los mensajes en paralelo
hilos_envio = [
    threading.Thread(target=enviar_mensajes_en_lote, args=(navegadores[0], listas[0], mensajes_listas[0], imagenes_listas[0])),
    threading.Thread(target=enviar_mensajes_en_lote, args=(navegadores[1], listas[1], mensajes_listas[1], imagenes_listas[1])),
    threading.Thread(target=enviar_mensajes_en_lote, args=(navegadores[2], listas[2], mensajes_listas[2], imagenes_listas[2]))
]

# Iniciar los hilos de envío
for hilo in hilos_envio:
    hilo.start()

# Esperar a que todos los hilos de envío terminen
for hilo in hilos_envio:
    hilo.join()

# Cerrar los navegadores
for navegador in navegadores:
    navegador.quit()
