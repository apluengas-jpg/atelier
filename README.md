# ATELIER · beta funcional
**El arte también tiene un mapa.**
Mapa cultural interactivo de Metepec que conecta artistas, espacios y audiencias.

## 1. Instalar y ejecutar en Visual Studio Code

Requisitos: Python 3.9 o superior. Para que carguen las tipografías y los mosaicos del mapa necesitas conexión a internet.

1. Abre la carpeta `atelier` en VS Code (Archivo > Abrir carpeta).
2. Abre la terminal integrada (Ctrl + `).
3. Crea y activa un entorno virtual:

   **Windows (PowerShell)**
   ```
   python -m venv venv
   venv\Scripts\Activate.ps1
   ```
   Si PowerShell bloquea el script: `Set-ExecutionPolicy -Scope Process Bypass` y vuelve a activar.

   **macOS / Linux**
   ```
   python3 -m venv venv
   source venv/bin/activate
   ```
4. Instala dependencias:
   ```
   pip install -r requirements.txt
   ```
5. Inicia la beta:
   ```
   python app.py
   ```
6. Abre http://127.0.0.1:5000 en tu navegador. Para verla como móvil, usa las herramientas de desarrollo (F12) y activa la vista de dispositivo.

Detén el servidor con Ctrl + C. Con `debug=True`, los cambios en Python se recargan solos y los cambios en JSON, HTML, CSS y JS se ven al refrescar.

## 2. Compartir la beta en otros dispositivos

**A) Celular, tablet u otra computadora en tu misma red Wi-Fi (rápido, sin cuentas):**

1. Con el servidor corriendo (`python app.py`), busca la IP local de tu computadora:
   - **Windows:** `ipconfig` en la terminal → busca "Dirección IPv4" (algo como `192.168.1.34`).
   - **macOS:** `ipconfig getifaddr en0` en la terminal, o Preferencias del Sistema → Red.
2. En el otro dispositivo (conectado al mismo Wi-Fi), abre `http://` seguido de esa IP y el puerto, por ejemplo:
   ```
   http://192.168.1.34:5000
   ```
3. Si no carga, revisa que el firewall de tu computadora permita conexiones entrantes a Python, y que ambos dispositivos estén en la misma red (no en "red de invitados").

Esto solo funciona mientras tu computadora esté prendida, el servidor corriendo y el otro dispositivo en la misma red. Para compartir con alguien fuera de tu red, necesitas publicarlo en un servicio de hosting:

**B) Publicarlo en internet (para compartir con cualquier persona, desde cualquier lugar):**

El proyecto ya está listo para esto: incluye `gunicorn` en `requirements.txt`, un `Procfile` con el comando de arranque, `runtime.txt` con la versión de Python, y `render.yaml` con la configuración del servicio. Solo falta subirlo a GitHub y conectarlo a Render.

### Paso 1: sube el proyecto a GitHub

1. Crea una cuenta en [github.com](https://github.com) si no tienes una.
2. Crea un repositorio nuevo (botón verde "New"), por ejemplo llamado `atelier`. Déjalo vacío, sin README ni .gitignore (el proyecto ya trae uno).
3. En la terminal, dentro de la carpeta `atelier` (con el entorno virtual desactivado o no, da igual):
   ```
   git init
   git add .
   git commit -m "Beta de Atelier"
   git branch -M main
   git remote add origin https://github.com/TU-USUARIO/atelier.git
   git push -u origin main
   ```
   Reemplaza `TU-USUARIO` por tu usuario de GitHub. Si te pide iniciar sesión, sigue las instrucciones en pantalla (GitHub ya no acepta contraseña directa: usa un token o el navegador que te abre automáticamente).
4. Verifica en github.com/TU-USUARIO/atelier que los archivos se subieron. `venv/`, `__pycache__/` y `data/atelier.db` NO deben aparecer (el `.gitignore` los excluye a propósito).

### Paso 2: crea el servicio en Render

1. Crea una cuenta gratuita en [render.com](https://render.com) (puedes entrar directo con tu cuenta de GitHub).
2. En el dashboard, botón **New +** → **Web Service**.
3. Conecta tu cuenta de GitHub si te lo pide, y selecciona el repositorio `atelier`.
4. Render suele detectar Python y proponer los comandos solo; confirma o completa así:
   - **Name:** `atelier` (o el nombre que quieras; será parte de la URL).
   - **Region:** la más cercana a ti u Oregon (US West) si no aparece una de México.
   - **Branch:** `main`.
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Instance Type:** **Free**.
5. Botón **Create Web Service**. Render clona el repositorio, instala dependencias y arranca el servidor. Puedes ver el progreso en la pestaña **Logs**; cuando termine verás algo como `Booting worker with pid: ...` y el estado pasará a **Live**.
6. Tu URL pública aparece arriba del panel, con el formato `https://atelier-XXXX.onrender.com`. Ábrela desde cualquier dispositivo, dentro o fuera de tu red.

Si prefieres hacerlo con un clic, Render también puede leer el archivo `render.yaml` incluido: **New +** → **Blueprint** → selecciona el repositorio, y Render arma el servicio con esa configuración automáticamente.

### Cosas a tener en cuenta con el plan gratuito de Render

- **Se "duerme" con inactividad:** si nadie visita el sitio por 15 minutos, Render apaga el servicio. La siguiente visita tarda 30–60 segundos en despertar (verás una pantalla de carga); después responde normal.
- **Los datos no son permanentes entre despliegues:** `data/atelier.db` (donde se guardan `/solicitudes` y `/comentarios`) vive en el disco del servidor, no en GitHub. Cada vez que subas cambios nuevos (`git push`) y Render vuelva a desplegar, esa base de datos se reinicia vacía. Para una beta de presentación o clase esto normalmente no es problema; si necesitas conservar esos datos entre despliegues, se puede migrar a una base de datos externa (por ejemplo Postgres, que Render también ofrece) — puedo ayudarte con eso si llega el momento.
- **Actualizar el sitio:** cualquier `git push` a la rama `main` hace que Render vuelva a desplegar automáticamente en un par de minutos. No necesitas repetir el paso 2.

### Alternativas a Render

- **[Railway](https://railway.app):** proceso casi idéntico (conectar GitHub, detecta Flask, usa el mismo `Procfile`). Su capa gratuita es por crédito de uso en vez de por horas.
- **[PythonAnywhere](https://www.pythonanywhere.com):** pensado para Flask/Django; en vez de Git+build automático, subes el código manualmente o con Git y configuras la app desde su panel web ("Web" → "Add a new web app" → Flask). Es más manual pero muy estable para proyectos pequeños y gratis de forma indefinida (con una URL tipo `tuusuario.pythonanywhere.com`).

## 3. Estructura

```
atelier/
  app.py            Rutas de las páginas y API (JSON) del mapa, búsqueda y formularios
  content.py        Lee /data, fechas en español y búsqueda
  art.py            Genera las ilustraciones demo (SVG) que sustituyen a las fotos
  db.py             SQLite para guardar las solicitudes de colaboración y los comentarios
  requirements.txt
  Procfile          Comando de arranque en producción (gunicorn app:app)
  runtime.txt       Versión de Python para Render
  render.yaml       Configuración opcional de despliegue en Render (Blueprint)
  data/             Contenido editable
    categories.json   Categorías y su color (usado por CSS y por el mapa)
    artists.json      8 artistas demo
    spaces.json       8 espacios demo (con coordenadas)
    events.json       10 eventos demo
    atelier.json      Textos de Atelier, tipos de espacio y de colaboración
  templates/        HTML (Jinja)
    base.html         Cabecera, navegación, diálogos y pie
    home.html  mapa.html  eventos.html  evento.html
    artistas.html  artista.html  espacios.html  espacio.html
    atelier.html  buscar.html  solicitudes.html  comentarios.html  404.html
    partials/_macros.html   Tarjetas de evento, artista y espacio
    partials/_icons.html    Iconos
  static/
    css/style.css     Todo el diseño (tokens al inicio)
    js/app.js         Guardados, modal, búsqueda, filtros, compartir
    js/map.js         Mapa Leaflet, pins, tarjeta y filtros
    vendor/leaflet/   Leaflet incluido localmente
    images/           Aquí van tus fotografías reales
```

Flujo: el navegador pide una página, `app.py` lee los JSON con `content.py` y la plantilla la dibuja. El mapa pide sus puntos a `/api/puntos`.

## 4. Dónde modificar cada cosa

| Qué | Dónde |
|---|---|
| Artistas | `data/artists.json`. Duplica un bloque y cambia `slug`, textos, `portfolio` y `projects` |
| Espacios | `data/spaces.json`. Incluye `lat` y `lng` (clic derecho en un mapa > copiar coordenadas) |
| Eventos | `data/events.json`. `artist` y `space` deben coincidir con el `slug` de esos archivos. Fecha en formato `AAAA-MM-DD` |
| Actualización mensual del mapa | Agrega los eventos del mes en `events.json`. El selector de mes del mapa se genera solo |
| Colores de categoría | `data/categories.json` (campo `color`) |
| Colores base de la interfaz | `static/css/style.css`, bloque `:root` al inicio |
| Tipografías | Enlace de Google Fonts en `templates/base.html` y variables `--f-display` y `--f-text` en `style.css`. Alternativas para los títulos: Instrument Serif, Bodoni Moda, Gloock |
| Botones en mayúsculas | `--btn-transform: uppercase;` en `:root` |
| Imágenes | Copia el archivo a `static/images/` y escribe `"image": "images/nombre.jpg"` en el JSON. Con `null` se usa la ilustración demo. También acepta URLs completas |
| Información de Atelier | `data/atelier.json` (textos, pilares, contacto) |
| Barra "Beta · contenido demo" | `SHOW_DEMO_BAR` en `app.py` |

## 5. Qué es real y qué es simulado en esta beta

Funciona de verdad: navegación, mapa con filtros por categoría y mes, búsqueda, guardar eventos (en el navegador de cada persona), perfiles, formularios de colaboración (se guardan en `data/atelier.db` y se ven en `/solicitudes`), comentarios de retroalimentación (botón flotante "Danos tu opinión", se guardan en `data/atelier.db` y se ven en `/comentarios`), compartir.

Falta para producción:
- Cuentas de usuario para artistas y espacios, con panel para editar su propio perfil.
- Panel de administración para Atelier (hoy se editan los JSON) con subida de imágenes.
- Guardados ligados a una cuenta (hoy viven en el navegador).
- Correo automático al recibir una solicitud, y flujo de aprobación.
- Proveedor de mosaicos de mapa propio si el tráfico crece (los mosaicos gratuitos de CARTO tienen límites de uso).
- Autenticación en `/solicitudes` (hoy es abierta, solo para pruebas locales) y despliegue con un servidor de producción, no `debug=True`.
