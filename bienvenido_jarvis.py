#!/usr/bin/env python3
"""
Double-clap welcome script for Señor Erik.

Detects 2 claps → voz AI dice bienvenido → abre YouTube → Claude + Cursor lado a lado.

Dependencias:
    pip install sounddevice numpy pyttsx3

Uso:
    python bienvenido_tatay.py
"""

import os
import sys
import time
import threading
import subprocess

import locale
import random
import tempfile

import numpy as np
import requests
import sounddevice as sd

# ──────────────────────────────────────────────────────────────────────────────
#  Configuración
# ──────────────────────────────────────────────────────────────────────────────
SAMPLE_RATE    = 44100
BLOCK_SIZE     = int(SAMPLE_RATE * 0.05)   # 50 ms por bloque
THRESHOLD      = 0.20     # RMS mínimo para contar como aplauso  ← ajusta si falla
COOLDOWN       = 0.1    # segundos de pausa mínima entre aplausos
DOUBLE_WINDOW  = 2.0     # ventana de tiempo para el segundo aplauso

MUSICA_FILE    = os.path.join(os.path.dirname(os.path.abspath(__file__)), "musica.mp3")

ELEVENLABS_KEY   = os.environ.get("ELEVENLABS_KEY", "")
ELEVENLABS_VOICE = os.environ.get("ELEVENLABS_VOICE", "JBFqnCBsd6RMkjVDRZzb")  # George
CIUDAD           = os.environ.get("JARVIS_CIUDAD", "Buenos Aires")

FRASES = [
    "Recuerde, el éxito es la suma de pequeños esfuerzos repetidos día tras día.",
    "Hoy es un gran día para construir algo increíble.",
    "La disciplina supera al talento cuando el talento no se disciplina.",
    "Cada línea de código te acerca más a tu objetivo.",
    "Los grandes logros empiezan con la decisión de intentarlo.",
    "No espere el momento perfecto, tome el momento y hágalo perfecto.",
    "El único límite es el que usted se pone a sí mismo.",
    "Trabaje en silencio y deje que el éxito haga el ruido.",
]

# ──────────────────────────────────────────────────────────────────────────────
#  Estado global
# ──────────────────────────────────────────────────────────────────────────────
clap_times: list[float] = []
triggered = False
lock = threading.Lock()


# ──────────────────────────────────────────────────────────────────────────────
#  Detección de aplausos
# ──────────────────────────────────────────────────────────────────────────────
def audio_callback(indata, frames, time_info, status):
    global triggered, clap_times

    if triggered:
        return

    rms = float(np.sqrt(np.mean(indata ** 2)))
    now = time.time()

    if rms > THRESHOLD:
        with lock:
            # Ignora si estamos en el cooldown del aplauso anterior
            if clap_times and (now - clap_times[-1]) < COOLDOWN:
                return

            clap_times.append(now)
            # Limpia aplausos fuera de la ventana
            clap_times = [t for t in clap_times if now - t <= DOUBLE_WINDOW]

            count = len(clap_times)
            print(f"  👏  Aplauso {count}/2  (RMS={rms:.3f})")

            if count >= 2:
                triggered = True
                clap_times = []
                threading.Thread(target=secuencia_bienvenida, daemon=True).start()


# ──────────────────────────────────────────────────────────────────────────────
#  Secuencia de bienvenida
# ──────────────────────────────────────────────────────────────────────────────
def secuencia_bienvenida():
    print("\n🚀  Iniciando secuencia de bienvenida…\n")

    # Arranca la música en paralelo a volumen bajo (0.15 = 15%)
    musica_proc = subprocess.Popen(["afplay", "-v", "0.15", MUSICA_FILE])

    fecha = obtener_fecha()
    clima = obtener_clima()
    frase = random.choice(FRASES)
    mensaje = f"Bienvenido a casa, señor Erik. {fecha}. {clima} Espero que tenga una excelente jornada. {frase}"
    hablar(mensaje)
    abrir_apps_lado_a_lado()

    print("\n✅  Secuencia completada.\n")


def obtener_fecha() -> str:
    """Devuelve la fecha actual en español."""
    dias = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
    meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
             "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    now = time.localtime()
    dia_nombre = dias[now.tm_wday]
    mes_nombre = meses[now.tm_mon - 1]
    return f"Hoy es {dia_nombre} {now.tm_mday} de {mes_nombre}"


def obtener_clima() -> str:
    """Consulta el clima actual usando wttr.in."""
    try:
        resp = requests.get(f"https://wttr.in/{CIUDAD}?format=j1&lang=es", timeout=5)
        data = resp.json()
        current = data["current_condition"][0]
        temp = current["temp_C"]
        desc_es = current.get("lang_es", [{}])[0].get("value", current["weatherDesc"][0]["value"])
        sensacion = current["FeelsLikeC"]
        return f"El clima en este momento es de {temp} grados, sensación térmica de {sensacion}, con cielo {desc_es.lower()}."
    except Exception:
        return ""


def hablar(texto: str):
    """Genera y reproduce audio con ElevenLabs."""
    print(f"  🔊  Diciendo: «{texto}»")
    try:
        resp = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE}",
            headers={"xi-api-key": ELEVENLABS_KEY, "Content-Type": "application/json"},
            json={
                "text": texto,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {"stability": 0.6, "similarity_boost": 0.85},
            },
            timeout=15,
        )
        if resp.status_code == 200:
            tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            tmp.write(resp.content)
            tmp.close()
            subprocess.run(["afplay", tmp.name])
            os.unlink(tmp.name)
            return
    except Exception as e:
        print(f"     Error ElevenLabs: {e}")

    # Fallback: voz del sistema
    subprocess.run(["say", texto])


def abrir_apps_lado_a_lado():
    sw, sh = obtener_resolucion_pantalla()
    mitad = sw // 2

# ── Abre Slack ────────────────────────────────────────────────────────────
    print("  💬  Abriendo Slack…")
    subprocess.Popen(["open", "-a", "Slack"])
    time.sleep(1.8)

    # ── Abre Claude ──────────────────────────────────────────────────────────
    print("  🤖  Abriendo Claude…")
    subprocess.Popen(["open", "-a", "Claude"])
    time.sleep(1.8)

    # ── Coloca ventanas lado a lado con AppleScript ──────────────────────────
    print("  🪟  Organizando ventanas…")
    applescript = f"""
    tell application "System Events"
        try
            tell process "Slack"
                set frontmost to true
                set position of window 1 to {{0, 0}}
                set size of window 1 to {{{mitad}, {sh}}}
            end tell
        end try
        try
            tell process "Claude"
                set frontmost to true
                set position of window 1 to {{{mitad}, 0}}
                set size of window 1 to {{{mitad}, {sh}}}
            end tell
        end try
    end tell
    """
    subprocess.run(["osascript", "-e", applescript], capture_output=True)


# ──────────────────────────────────────────────────────────────────────────────
#  Utilidades
# ──────────────────────────────────────────────────────────────────────────────
def obtener_resolucion_pantalla() -> tuple[int, int]:
    try:
        out = subprocess.run(
            ["osascript", "-e",
             "tell application \"Finder\" to get bounds of window of desktop"],
            capture_output=True, text=True
        ).stdout.strip()
        parts = [int(x.strip()) for x in out.split(",")]
        return parts[2], parts[3]
    except Exception:
        return 1920, 1080


# ──────────────────────────────────────────────────────────────────────────────
#  Main
# ──────────────────────────────────────────────────────────────────────────────
def main():
    global triggered

    print("=" * 55)
    print("  🎤  Escuchando aplausos… (Ctrl+C para salir)")
    print(f"  Umbral actual: {THRESHOLD}  (ajusta THRESHOLD si falla)")
    print("=" * 55)

    try:
        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            blocksize=BLOCK_SIZE,
            channels=1,
            dtype="float32",
            callback=audio_callback,
        ):
            while True:
                time.sleep(0.1)
                if triggered:
                    # Espera a que la secuencia acabe y vuelve a escuchar
                    time.sleep(8)
                    triggered = False
                    print("\n👂  Escuchando de nuevo…\n")
    except KeyboardInterrupt:
        print("\n\nHasta luego! 👋")
        sys.exit(0)


if __name__ == "__main__":
    main()
