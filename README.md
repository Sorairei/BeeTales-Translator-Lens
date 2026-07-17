# BeeTales Translator Lens

BeeTales Translator Lens es una aplicación de escritorio para Windows que delimita un área de la pantalla mediante una lupa flotante y, en fases posteriores, reconocerá y traducirá localmente el texto que aparezca debajo. El objetivo principal es traducir conversaciones de aplicaciones como Discord sin copiar y pegar y sin enviar capturas o texto a servicios externos.

## Estado del proyecto

La **Fase 1 (estructura e interfaz flotante)** está implementada. Incluye:

- Ventana transparente, sin marco y siempre visible.
- Marco rectangular movible y redimensionable.
- Panel flotante asociado con tema oscuro y acento verde.
- Idiomas de origen: Automático, Español, Inglés, Polaco, Japonés y Portugués.
- Idiomas de destino: Español, Inglés, Polaco, Japonés y Portugués.
- Acciones simuladas de iniciar, pausar/reanudar, copiar, bloquear/desbloquear y cerrar.
- Persistencia JSON de geometrías, idiomas y bloqueo.
- Recuperación segura y respaldo de una configuración dañada.
- Compatibilidad inicial con DPI por monitor y coordenadas negativas.
- Texto de demostración en polaco y español.

Esta fase **no captura la pantalla, no ejecuta OCR y no traduce realmente**. PaddleOCR, PaddlePaddle, MSS, Argos Translate y la descarga de modelos pertenecen a fases posteriores y todavía no son dependencias.

## Requisitos

- Windows 10 u 11 de 64 bits.
- Python 3.11 recomendado.
- Una cuenta de Windows sin privilegios de administrador es suficiente.

## Instalación y ejecución

PowerShell:

```powershell
cd "C:\Users\TU_USUARIO\GitHub\BeeTales Translator Lens"

python -m venv .venv

.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt

python main.py
```

La ruta del proyecto puede contener espacios. Los scripts usan rutas literales o resueltas desde su propia ubicación y no dependen de una carpeta de trabajo sin espacios.

Como alternativa, desde la raíz del repositorio:

```powershell
.\scripts\create_venv.ps1
.\.venv\Scripts\python.exe main.py
```

Si PowerShell bloquea la activación del entorno, no hace falta cambiar permanentemente la política: se puede ejecutar directamente `.\.venv\Scripts\python.exe main.py`.

## Uso de la demostración

1. Arrastra la barra superior pequeña de la lupa para colocarla encima del contenido deseado.
2. Arrastra el control verde de la esquina inferior derecha para cambiar el tamaño.
3. Elige el idioma de origen y el idioma de destino en el panel.
4. Pulsa **Iniciar** para mostrar el resultado simulado:

   - Texto detectado: `Czy ktoś chce zagrać dzisiaj?`
   - Traducción: `¿Alguien quiere jugar hoy?`

5. Pulsa **Pausar** y **Reanudar** para cambiar el estado visual.
6. Pulsa **Copiar** para copiar la traducción simulada al portapapeles.
7. Pulsa **Bloquear lupa** para impedir su movimiento y redimensionamiento; el panel permanece disponible para desbloquearla.
8. Cierra con el botón `×`. Las geometrías y los idiomas se restaurarán en el siguiente inicio.

## Configuración local y privacidad

Los ajustes se guardan mediante `platformdirs` en una ubicación local equivalente a:

```text
%LOCALAPPDATA%\BeeTales\BeeTales Translator Lens\config\settings.json
```

También se preparan carpetas separadas para modelos, caché, registros, historial y depuración. La ubicación exacta depende de Windows y puede consultarse ejecutando:

```powershell
python -c "from beetales_translator_lens.storage.paths import data_directory; print(data_directory())"
```

La aplicación no tiene telemetría, no realiza solicitudes de red y no guarda capturas. El historial estará desactivado por defecto cuando se implemente. Si `settings.json` está dañado, se renombra como `settings.corrupt-FECHA.json` y la aplicación continúa con valores predeterminados.

## Pruebas automatizadas

Con el entorno activado:

```powershell
python -m pytest
```

Las pruebas actuales cubren valores predeterminados, validación, idiomas, geometría con coordenadas negativas, rutas con espacios, escritura/lectura y recuperación de archivos dañados.

## Prueba manual de la Fase 1

Realiza esta comprobación en Windows 10 u 11:

1. Inicia con `python main.py` desde la ruta con espacios.
2. Confirma que aparecen la lupa transparente y el panel **BeeTales Translator Lens**.
3. Mueve y redimensiona la lupa; prueba, si es posible, entre dos monitores.
4. Comprueba escalados de Windows al 100 %, 125 %, 150 % o 200 %.
5. Selecciona `Japonés → Portugués`, pulsa **Iniciar**, pausa, reanuda y copia.
6. Bloquea la lupa y verifica que no se puede mover ni redimensionar; después desbloquéala desde el panel.
7. Mueve ambas ventanas, ciérralas y vuelve a iniciar. Confirma que posición, tamaño e idiomas se conservan.
8. Opcionalmente, daña manualmente el JSON de configuración y confirma que la aplicación recupera los valores predeterminados sin cerrarse.

## Estructura actual

```text
BeeTales Translator Lens/
├── main.py
├── README.md
├── LICENSE
├── requirements.txt
├── pyproject.toml
├── beetales_translator_lens/
│   ├── application.py
│   ├── constants.py
│   ├── exceptions.py
│   ├── platform/
│   │   └── windows_dpi.py
│   ├── storage/
│   │   ├── paths.py
│   │   └── settings_store.py
│   └── ui/
│       ├── capture_overlay.py
│       ├── main_controller.py
│       ├── theme.py
│       └── translation_panel.py
├── tests/
│   └── test_settings_store.py
├── scripts/
│   ├── create_venv.ps1
│   └── build_windows.ps1
└── packaging/
    ├── beetales_translator_lens.spec
    └── version_info.txt
```

El paquete importable se llama `beetales_translator_lens`; el nombre visible conserva siempre **BeeTales Translator Lens**.

## Hoja de ruta

1. **Fase 1 — interfaz flotante:** implementada.
2. **Fase 2 — captura regional:** MSS, varios monitores, exclusión de ventanas y detección de cambios.
3. **Fase 3 — OCR:** PaddleOCR, perfiles de imagen, confianza y métricas.
4. **Fase 4 — traducción:** Argos Translate, modelos, rutas, caché y detección de idioma.
5. **Fase 5 — ciclo continuo:** trabajos en segundo plano, pausa, rendimiento e historial opcional.
6. **Fase 6 — experiencia:** asistente, atajos globales, bandeja, clic a través y gestión de modelos.
7. **Fase 7 — distribución:** PyInstaller `onedir`, metadatos, icono y ZIP.

El archivo `.spec` incluido es una base para la Fase 7; el empaquetado final y PyInstaller todavía no forman parte de los criterios de aceptación de la Fase 1.

## Licencia

MIT. Consulta [LICENSE](LICENSE).
