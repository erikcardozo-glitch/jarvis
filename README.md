# 👏 Jarvis - Double Clap Home Automation

Aplaude 2 veces y Jarvis te da la bienvenida con voz AI, te dice el clima, pone música y organiza tus apps.

## ¿Qué hace?
1. Detecta **2 aplausos** por el micrófono
2. Reproduce música de fondo
3. Una voz AI (ElevenLabs) dice la fecha, el clima y una frase motivacional
4. Abre **Slack** y **Claude** lado a lado

## Instalación

```bash
pip install sounddevice numpy requests
```

## Configuración

Copia el archivo de ejemplo y completá con tus claves:

```bash
cp .env.example .env
```

Variables de entorno:
- `ELEVENLABS_KEY` — Tu API key de [ElevenLabs](https://elevenlabs.io)
- `ELEVENLABS_VOICE` — ID de la voz (default: George)
- `JARVIS_CIUDAD` — Tu ciudad para el clima (default: Buenos Aires)

## Uso

```bash
python bienvenido_jarvis.py
```

> Si no detecta los aplausos, ajustá `THRESHOLD` en el script (subí el valor si hay ruido, bajalo si no detecta).

## Requisitos
- macOS
- Python 3.9+
- Micrófono
- Cuenta en ElevenLabs (tiene plan gratuito)

## Personalización
- Editá la lista `FRASES` para cambiar las frases motivacionales
- Cambiá las apps en `abrir_apps_lado_a_lado()` por las que uses
- Agregá tu propio `musica.mp3` en la carpeta del proyecto
