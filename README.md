# Smart Search

**Herramienta avanzada de búsqueda de archivos para Windows con interfaz gráfica PyQt6**

Busca archivos rápidamente por nombre o contenido. Organiza resultados automáticamente por tipo. Copia, mueve u abre archivos con un solo clic.

---

## Tabla de Contenidos

1. [Inicio Rápido](#inicio-rápido)
2. [Características](#características)
3. [Requisitos](#requisitos-del-sistema)
4. [Instalación](#instalación)
5. [Uso](#uso-básico)
6. [Atajos de Teclado](#atajos-de-teclado)
7. [Estructura de Archivos](#estructura-de-archivos)
8. [Troubleshooting](#troubleshooting)
9. [Licencia](#licencia)

---

## Inicio Rápido

```bash
# Opción 1: Ejecución directa (recomendado)
python main.py

# Opción 2: Usar script BAT (Windows)
start.bat

# Opción 3: Script de instalación (primera vez)
python install.py
```

La aplicación abrirá una ventana con selector de directorios y campo de búsqueda.

---

## Descripción

Herramienta profesional de búsqueda de archivos para Windows con integración completa de:
- **Windows Search API** (búsqueda ultra-rápida, 10,000 archivos/seg)
- **Interfaz PyQt6** (moderna, responsive, tema claro/oscuro)
- **Gestión inteligente de directorios** (con estados persistentes)
- **Clasificación automática** (9 categorías de archivo)

## Características Principales

### Búsqueda Avanzada
- **Windows Search API**: Motor principal ultra-rápido (10,000 archivos/seg)
- **Motor fallback**: Alternativa automática si Windows Search no disponible
- **Múltiples palabras clave**: Usa `*` como separador (AND logic)
  - Ejemplo: `python * script * test`
- **Búsqueda dual**: Por nombre Y/O contenido de archivos
- **Directorios múltiples**: Selección jerárquica con checkboxes tristate
- **Resultados en tiempo real**: Threading no bloqueante, UI responsivo
- **Hasta 10,000 resultados**: Escalable y potente

### Clasificación Inteligente (9 Categorías)
```
Documentos (PDF, DOC, TXT, XLS)
Imágenes (JPG, PNG, GIF, SVG)
Videos (MP4, AVI, MKV, MOV)
Audio (MP3, WAV, FLAC, AAC)
Código (PY, JS, HTML, JSON, XML)
Comprimidos (ZIP, RAR, 7Z, TAR)
Ejecutables (EXE, MSI, DLL, JAR)
Datos (DB, SQLITE, CSV, CFG)
Otros (Extensiones no clasificadas)
```

### Gestión de Directorios Inteligente
- **Árbol auto-indexado**: Detección automática de directorios de Windows
- **Estados tristate**: Unchecked / Partial / Checked
- **Propagación inteligente**: Marcar carpeta padre marca automáticamente hijos
- **Persistencia de estado**: Se recuerdan selecciones entre sesiones
- **Tooltips informativos**: Muestra ruta completa al pasar el mouse

### Operaciones de Archivos
- **Abrir**: Con aplicación predeterminada (Ctrl+O)
- **Abrir ubicación**: En Windows Explorer con archivo seleccionado
- **Copiar**: Múltiples archivos a carpeta destino
- **Mover**: Con confirmación y validación de conflictos
- **Copiar ruta**: Al portapapeles con clic derecho
- **Menú contextual**: Clic derecho para opciones adicionales

### Interfaz Visual
- **Tema claro/oscuro**: Toggle en la barra superior
  - Modo oscuro: Inspirado en Visual Studio Code
  - Modo claro: Interfaz estándar Windows
- **Atajos de teclado**: Ctrl+F, Ctrl+O, Ctrl+L, Enter
- **Ordenamiento por columna**: Haz clic en encabezados
- **Selección múltiple**: Ctrl+Click, Shift+Click
- **Menú contextual**: Clic derecho en resultados
- **Barra de progreso**: Indicador visual durante búsqueda
- **Contador de archivos**: Muestra total de resultados encontrados

### Rendimiento y Optimización
- Caché de resultados (5 minutos)
- Búsqueda multihilo sin bloquear UI
- Limitación automática a 10,000 resultados
- Soporte para búsqueda en unidades de red (UNC paths)
- Fallback eficiente sin dependencias externas

---

## Layout de Interfaz

```
╔════════════════════════════════════════════════════════════════════════╗
║ Smart Search v1.0.0                                          [☀ Dark] ║
╠═══════════════════════╦═══════════════════════════════════════════════╣
║ DIRECTORIOS           ║ RESULTADOS (Por Categoría)                    ║
║                       ║                                               ║
║ ☑ C:\Users\Juan\      ║ Documentos (15)                              ║
║   ☑ Desktop           ║ ├─ proyecto.pdf        C:\...\  150KB  2024  ║
║   ☑ Documents         ║ ├─ informe.docx        C:\...\  250KB  2024  ║
║   ☑ Downloads         ║ └─ resumen.txt         C:\...\   45KB  2024  ║
║   ☑ Pictures          ║                                               ║
║   ☑ Videos            ║ Imágenes (8)                                  ║
║   ☑ Music             ║ ├─ foto.jpg            C:\...\  2.5MB  2024  ║
║                       ║ ├─ captura.png         C:\...\  850KB  2024  ║
║ Búsqueda:            ║                                               ║
║ ☑ Filename            ║ Código (3)                                    ║
║ ☐ Content            ║ ├─ script.py           C:\...\   5KB  2024   ║
║                       ║ └─ config.json         C:\...\   3KB  2024   ║
╠═══════════════════════╩═══════════════════════════════════════════════╣
║ [Buscar: python * test_____] [Search] [Stop]                         ║
╠════════════════════════════════════════════════════════════════════════╣
║ [Open] [Open Location] [Copy To...] [Move To...] [Clear]             ║
║ Status: Ready | Files: 26                                             ║
╚════════════════════════════════════════════════════════════════════════╝
```

## Requisitos del Sistema

### Mínimos Recomendados
- **Windows 10/11** (64-bit)
- **Python 3.8+**
- **4 GB RAM**
- **200 MB espacio en disco**
- **Permisos de lectura** en directorios a buscar

### Dependencias de Software
```
PyQt6 >= 6.0
pywin32 >= 300
comtypes >= 1.1
```

### Opcional
- **Windows Search** debe estar habilitado (recomendado pero funciona sin)

---

## Instalación

### Método 1: Instalación Automática (Recomendado)

```bash
# En Windows Command Prompt o PowerShell:
python install.py
```

Este script automáticamente:
- Detecta Python
- Instala dependencias
- Crea acceso directo en Inicio
- Configura Windows Search si es posible
- Valida la instalación

### Método 2: Instalación Manual

**Paso 1**: Clonar o descargar el repositorio
```bash
git clone https://github.com/usuario/smart-search.git
cd smart_search
```

**Paso 2**: Crear ambiente virtual (recomendado)
```bash
# Windows Command Prompt
python -m venv venv
venv\Scripts\activate

# Windows PowerShell
python -m venv venv
venv\Scripts\Activate.ps1
```

**Paso 3**: Instalar dependencias
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Paso 4**: Ejecutar la aplicación
```bash
python main.py
```

### Método 3: Sin ambiente virtual (Rápido)

```bash
pip install -r requirements.txt
python main.py
```

### Verificación de Instalación

```bash
# Validar que todo funciona correctamente
python validate_integration.py
```

Deberías ver mensajes de confirmación de todos los módulos.

## Uso Básico

### Búsqueda Paso a Paso

**Paso 1: Seleccionar directorios**
1. En el panel izquierdo, marca las carpetas donde buscar
2. Puedes marcar carpetas específicas (Desktop, Documents, etc.)
3. Las subcarpetas se seleccionan automáticamente

**Paso 2: Ingresar términos**
1. Escribe en el campo "Buscar:"
2. Para múltiples palabras, sepáralas con `*` (AND logic)
3. Ejemplo: `python * test * 2024`

**Paso 3: Configurar opciones**
1. **Filename**: Busca en nombres de archivos (recomendado)
2. **Content**: Busca dentro del contenido (más lento)

**Paso 4: Ejecutar**
1. Haz clic en "Search" o presiona Enter
2. Los resultados aparecen en pestañas por categoría
3. Haz clic en "Stop" si deseas detener la búsqueda

**Paso 5: Actuar sobre resultados**
1. Selecciona uno o varios archivos (Ctrl+Click)
2. Haz clic en acción: Open, Copy To, Move To, etc.
3. Sigue las instrucciones en pantalla

### Ejemplos de Búsqueda

| Búsqueda | Resultado |
|----------|-----------|
| `python` | Todos los archivos con "python" en el nombre |
| `python * test` | Archivos con "python" AND "test" |
| `*.pdf * invoice` | Archivos PDF con "invoice" en el nombre |
| (marcar Content) `function * class` | Archivos que contienen ambas palabras |

### Búsqueda Avanzada

**Buscar solo por nombre** (recomendado):
- Desactiva "Content"
- Activa "Filename"
- Resultados en < 1 segundo

**Buscar en contenido** (más lento):
- Activa "Content"
- Desactiva "Filename" si solo necesitas contenido
- Espera más tiempo (10-30 segundos según volumen)

**Limitar a directorios específicos**:
- Solo marca las carpetas donde deseas buscar
- Las desmarcadas serán ignoradas
- Acelera significativamente la búsqueda

### Menú Contextual (Click Derecho)

En cualquier archivo en los resultados:
- **Open**: Abre con aplicación predeterminada
- **Open Location**: Navega a la carpeta en Explorer
- **Copy Path**: Copia la ruta al portapapeles

---

## Atajos de Teclado

| Atajo | Acción | Descripción |
|-------|--------|-------------|
| **Ctrl+F** | Enfocar búsqueda | Enfoca el campo de búsqueda |
| **Enter** | Ejecutar búsqueda | Inicia la búsqueda (cuando está en el campo) |
| **Ctrl+O** | Abrir archivos | Abre los seleccionados |
| **Ctrl+L** | Limpiar | Limpia todos los resultados |
| **Escape** | Detener | Cancela búsqueda en curso |
| **Ctrl+C** | Copiar rutas | Copia paths al portapapeles |
| **Clic derecho** | Menú contextual | Muestra opciones adicionales |
| **Doble clic** | Abrir archivo | Abre el archivo (en tabla) |
| **Ctrl+Click** | Selección múltiple | Selecciona/deselecciona |
| **Shift+Click** | Rango de selección | Selecciona desde última a actual |

## Estructura de Archivos

### Directorios y Archivos Principales

```
smart_search/
├── main.py                          # Punto de entrada y UI principal
├── backend.py                       # Motor de búsqueda (Windows API + fallback)
├── categories.py                    # Sistema unificado de categorías
├── classifier.py                    # Clasificación y formateo de resultados
├── config.py                        # Configuración centralizada
├── file_manager.py                  # Gestión de árbol de directorios
├── utils.py                         # Funciones auxiliares
├── install.py                       # Script de instalación automática
├── validate_integration.py          # Validador de módulos
├── start.bat                        # Acceso directo para Windows
├── requirements.txt                 # Dependencias pip
├── README.md                        # Este archivo
├── LICENSE                          # Licencia MIT
│
├── tests/                           # Suite de pruebas
│   ├── test_backend.py              # Tests del motor
│   ├── test_security.py             # Tests de seguridad
│   ├── test_utils.py                # Tests de utilidades
│   ├── conftest.py                  # Configuración pytest
│   └── __init__.py
│
├── docs/                            # Documentación adicional
│   ├── ARCHITECTURE.md              # Diseño técnico detallado
│   ├── DEVELOPMENT.md               # Guía para desarrolladores
│   └── TROUBLESHOOTING.md           # Solución de problemas
│
└── .smart_search/                   # Directorio de usuario (se crea al ejecutar)
    ├── config.json                  # Configuración persistente
    └── directory_tree.json          # Estado del árbol guardado
```

### Archivos Clave

| Archivo | Propósito | Líneas |
|---------|-----------|--------|
| **main.py** | Interfaz gráfica PyQt6, coordinación de eventos | ~1000 |
| **backend.py** | Motor de búsqueda con Windows Search API + fallback | ~800 |
| **categories.py** | Definición única de categorías (fuente de verdad) | ~120 |
| **classifier.py** | Clasificación, formateo de resultados y estadísticas | ~200 |
| **config.py** | Configuración centralizada de parámetros globales | ~170 |
| **file_manager.py** | Gestión del árbol jerárquico de directorios | ~500 |
| **utils.py** | Funciones utilitarias compartidas | ~150 |

### Configuración de Usuario

Se guarda automáticamente en:
```
C:\Users\[TuUsuario]\.smart_search\
```

Archivos generados:
- `config.json`: Tema (claro/oscuro), preferencias
- `directory_tree.json`: Estados de selección de carpetas

---

## Arquitectura de Módulos

```
main.py (Punto de entrada)
├── SmartSearchApp (QMainWindow)
│   ├── IntegratedDirectoryTreeWidget
│   │   └── DirectoryTree (backend)
│   │       └── WindowsSearchIndexManager
│   ├── ClassifiedResultsTableWidget (x9)
│   │   └── SearchResult (dataclass)
│   └── IntegratedSearchWorker (QThread)
│       └── SearchService
│           ├── WindowsSearchEngine (COM/WMI)
│           └── FallbackSearchEngine (recursivo)
│
├── backend.py
│   ├── SearchService (orquestador)
│   ├── SearchQuery (constructor)
│   ├── SearchResult (modelo)
│   ├── WindowsSearchEngine (Windows Search API)
│   ├── FallbackSearchEngine (alternativa)
│   └── FileOperations (copiar, mover, abrir)
│
├── categories.py
│   ├── FileCategory (Enum x9)
│   ├── CATEGORY_EXTENSIONS (mapeo)
│   └── classify_by_extension() (función)
│
└── classifier.py
    ├── classify_file() (por extensión)
    ├── format_file_size() (formateo)
    ├── format_date() (formateo)
    └── group_results_by_type() (agrupación)
```

## Troubleshooting

### Problema: "No results found" (Sin resultados)

**Causas posibles**:
- No hay directorios seleccionados
- Términos de búsqueda muy específicos
- Los archivos no existen o están en carpetas no seleccionadas

**Soluciones**:
```
1. Marca al menos una carpeta en el árbol izquierdo
2. Intenta términos más generales
3. Verifica que el archivo existe manualmente en Explorer
4. Intenta buscar solo por nombre (desactiva "Content")
5. Expande el árbol para ver subcarpetas
```

### Problema: "La búsqueda es lenta"

**Causas**:
- Búsqueda por contenido activada
- Demasiados directorios seleccionados
- Windows Search no indexada

**Soluciones**:
```
Opción 1: Desactiva búsqueda por contenido
- Desactiva el checkbox "Content"

Opción 2: Limita directorios
- Selecciona solo carpetas específicas
- Acelera significativamente

Opción 3: Reindexación Windows
- Configuración → Búsqueda → Indexación
- Click en "Advanced"
- Reconstruye el índice

Opción 4: Reinicia la aplicación
python main.py
```

### Problema: "ERROR: pywin32 not found"

**Solución**:
```bash
pip install pywin32
pywin32_postinstall.py -install
```

Si aún tiene error:
```bash
# Desinstala y reinstala
pip uninstall pywin32
pip install --upgrade pywin32
```

### Problema: "Windows Search not available"

**Nota normal**: Smart Search usará automáticamente el motor fallback.

**Para habilitar Windows Search**:
```
1. Configuración → Privacidad y seguridad
2. Búsqueda de Windows → Activa "Búsqueda en Windows"
3. Espera a reindexación (~30 minutos)
```

**Motor fallback funciona bien**:
- Búsqueda por nombre: Muy rápido
- Búsqueda por contenido: Un poco más lento
- No requiere Windows Search

### Problema: "Permission Denied" (Acceso denegado)

**Causa**: Intenta acceder a carpetas protegidas sin permisos

**Soluciones**:
```
1. Ejecuta como administrador:
   - PowerShell: Start-Process python main.py -Verb RunAs
   - O: Click derecho → Ejecutar como administrador

2. Desselecciona carpetas protegidas:
   - C:\Windows
   - C:\Program Files
   - C:\Program Files (x86)
   - C:\ProgramData

3. Verifica permisos NTFS del archivo
```

### Problema: "PyQt6 import error"

**Solución**:
```bash
pip install --upgrade PyQt6
pip install PyQt6-sip

# Si aún no funciona:
pip uninstall PyQt6
pip install PyQt6==6.5.0
```

### Problema: "La aplicación se congela"

**Soluciones inmediatas**:
```
1. Haz clic en "Stop" para cancelar búsqueda
2. Cierra la aplicación (Alt+F4)
3. Abre nuevamente

Si persiste:
- Intenta con directorios más pequeños
- Desactiva búsqueda por contenido
- Reinicia tu computadora
```

### Problema: "Config file corrupted" (Configuración dañada)

**Solución**:
```bash
# Opción 1: Desde PowerShell
rmdir "$env:USERPROFILE\.smart_search" -Force

# Opción 2: Manualmente
1. Abre: C:\Users\[TuUsuario]\.smart_search\
2. Elimina los archivos JSON
3. Reinicia la aplicación

# Opción 3: Desde Python
import shutil
import os
path = os.path.expanduser('~/.smart_search')
shutil.rmtree(path, ignore_errors=True)
```

### Problema: "No funciona búsqueda por contenido"

**Limitaciones**:
- Solo funciona en archivos de texto
- No funciona en binarios (.jpg, .exe, .zip)
- Puede ser lenta en archivos >10 MB

**Soluciones**:
```
1. Verifica que el archivo es texto puro:
   - .txt, .py, .json, .xml, .html, .csv, etc.

2. Intenta limitar directorios

3. Intenta con términos más generales

4. Revisa logs si está activado:
   - Abre terminal y ejecuta:
   - python -c "import logging; logging.basicConfig(level=logging.DEBUG)"
```

### Problema: "Las selecciones de carpetas no se guardan"

**Solución**:
```bash
# Verifica permisos en carpeta de usuario
# La app necesita escribir en: C:\Users\[TuUsuario]\.smart_search\

# Si no puedes crear archivos allí:
1. Abre: C:\Users\[TuUsuario]
2. Click derecho → Propiedades
3. Pestaña Seguridad
4. Editar → Permisos completos para tu usuario

# O reinicia como administrador
python main.py
```

---

## Preguntas Frecuentes (FAQ)

### P: ¿Es seguro buscar en todo el disco?
**R**: Sí, Smart Search solo **lee** archivos. Nunca modifica sin tu confirmación.

### P: ¿Puedo buscar en unidades de red?
**R**: Sí, soporta rutas UNC (\\servidor\carpeta), pero será más lento.

### P: ¿Funciona sin Windows Search?
**R**: Sí, tiene un motor fallback integrado. Funciona en cualquier Windows.

### P: ¿Qué tan seguro es mover archivos?
**R**: Muy seguro. Pide confirmación antes de mover y valida destinos.

### P: ¿Puedo guardar búsquedas?
**R**: No en v1.0, pero está planeado para v1.1.

### P: ¿Soporta expresiones regulares?
**R**: No en v1.0, está planeado para v2.0.

### P: ¿Cuántos archivos puede encontrar?
**R**: Hasta 10,000 resultados por búsqueda.

### P: ¿Funciona en Windows 7?
**R**: Smart Search está optimizado para Windows 10/11. Windows 7 no soportado.

---

## Rendimiento

### Velocidades Típicas

| Operación | Tiempo |
|-----------|--------|
| Búsqueda por nombre (1 palabra, 1 carpeta) | < 1 segundo |
| Búsqueda por nombre (3 palabras, 5 carpetas) | 2-5 segundos |
| Búsqueda por contenido (100 MB) | 10-30 segundos |
| Indexación Windows (SSD) | 15-30 minutos |
| Indexación Windows (HDD) | 30-60 minutos |

### Optimizaciones Implementadas

- Caché de resultados (5 minutos TTL)
- Threading multihilo sin bloquear UI
- Limitación automática a 10,000 resultados
- Fallback eficiente sin dependencias
- Selección jerárquica de directorios

---

## Desarrollo y Contribuciones

### Ejecutar Tests

```bash
# Todos los tests
pytest

# Con cobertura
pytest --cov=smart_search

# Test específico
pytest tests/test_backend.py -v
```

### Estructura de Código

```python
# main.py - Capa de Presentación
SmartSearchApp (QMainWindow)
├─ IntegratedDirectoryTreeWidget  # Árbol de directorios
├─ ClassifiedResultsTableWidget   # Tabla de resultados (x9)
└─ IntegratedSearchWorker         # Thread de búsqueda

# backend.py - Capa de Lógica
SearchService                     # Orquestador
├─ WindowsSearchEngine            # Con Windows Search API
├─ FallbackSearchEngine           # Sin dependencias
└─ FileOperations                 # Copiar, mover, abrir

# categories.py - Sistema de Categorización
FileCategory                      # Enum (9 categorías)
CATEGORY_EXTENSIONS              # Mapeo extensión → categoría
classify_by_extension()           # Función de clasificación
```

### Contribuir

Las contribuciones son bienvenidas:

1. Haz fork del repositorio
2. Crea una rama: `git checkout -b feature/mejora`
3. Commit cambios: `git commit -m "Agrega mejora"`
4. Push: `git push origin feature/mejora`
5. Abre un Pull Request

**Directrices**:
- Sigue PEP 8
- Añade docstrings en español
- Incluye tests para nuevas características
- Actualiza README si añades funcionalidades

---

## Historial de Versiones

### v1.0.0 (Diciembre 2025) - Actual
- Lanzamiento inicial
- Interfaz PyQt6 completa
- Windows Search API + fallback
- 9 categorías de archivos
- Tema claro/oscuro
- Operaciones de archivo
- Persistencia de configuración

### Próximas Versiones

**v1.1.0** (Q1 2026):
- [ ] Búsquedas guardadas
- [ ] Historial de búsqueda
- [ ] Filtro por tamaño/fecha

**v1.2.0** (Q2 2026):
- [ ] Expresiones regulares
- [ ] Exportar a CSV
- [ ] Integración Everything SDK

**v2.0.0** (Q3 2026):
- [ ] Sincronización en nube
- [ ] Plugin system
- [ ] Indexador local personalizado

---

## Licencia

**MIT License** - Libre para uso personal y comercial

```
Copyright (c) 2025 Smart Search Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```

Ver archivo completo: `LICENSE`

---

## Soporte y Contacto

### Reportar Bugs
- GitHub Issues: [github.com/usuario/smart-search/issues](https://github.com/usuario/smart-search/issues)
- Describe el problema, pasos para reproducir, versión de Windows

### Solicitar Funcionalidades
- GitHub Discussions: [Propuestas de mejoras](https://github.com/usuario/smart-search/discussions)
- Explica el caso de uso y beneficios

### Diagnóstico
Ejecuta para recopilar información del sistema:
```bash
python validate_integration.py
```

---

## Documentación Adicional

- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)**: Diseño técnico detallado
- **[DEVELOPMENT.md](docs/DEVELOPMENT.md)**: Guía para desarrolladores
- **[TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)**: Solución avanzada de problemas

---

## Notas Importantes

1. **Windows Only**: Smart Search está optimizado solo para Windows 10/11
2. **Python 3.8+**: Versiones anteriores no soportadas
3. **Administrador recomendado**: Para acceso completo al sistema de archivos
4. **Antivirus compatible**: Algunos antivirus pueden ralentizar búsquedas
5. **SSD recomendado**: Para mejor rendimiento de indexación

---

## Créditos

- **Smart Search Team**: Desarrollo principal
- **Comunidad**: Reportes de bugs y sugerencias
- **PyQt6**: Interfaz gráfica multiplataforma
- **Windows Search API**: Búsqueda nativa de Windows

---

## Cambios Recientes

**Última actualización**: 11 de Diciembre de 2025
**Versión actual**: v1.0.0
**Estado**: Estable y listo para producción

---

**Tabla de Referencia Rápida**

| Acción | Atajo | Ruta |
|--------|-------|------|
| Buscar | Ctrl+F | Campo de búsqueda |
| Ejecutar | Enter | Cuando está en campo |
| Abrir | Ctrl+O | Botón o clic derecho |
| Limpiar | Ctrl+L | Botón Clear |
| Copiar ruta | Ctrl+C | Clic derecho |

---

**¡Gracias por usar Smart Search!**

Si encuentras útil esta herramienta, considera dejar una estrella en GitHub.
Para sugerencias y mejoras, abre un issue o discussion.

