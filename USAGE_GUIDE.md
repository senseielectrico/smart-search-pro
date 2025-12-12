# Smart Search - Guía de Uso

## Inicio Rápido

### Opción 1: Script BAT
```bash
start.bat
```

### Opción 2: Python directo
```bash
python main.py
```

## Características Principales

### 1. Búsqueda Integrada

La aplicación integra **Windows Search API** para búsquedas ultra-rápidas:

- **Búsqueda por nombre**: Busca en nombres de archivos
- **Búsqueda por contenido**: Busca dentro del contenido de archivos indexados
- **Múltiples palabras**: Usa `*` como separador (ej: `python * script * test`)
- **Ambas opciones**: Puedes buscar en nombre Y contenido simultáneamente

#### Ejemplos de Búsqueda:

```
# Buscar archivos que contengan "python" en el nombre
python

# Buscar archivos que contengan "python" Y "script"
python * script

# Buscar archivos PDF que contengan "invoice"
*.pdf * invoice

# Buscar código Python con "class" en el contenido
*.py (con Content checkbox activado)
```

### 2. Selección de Directorios

El panel izquierdo muestra un árbol de directorios indexados:

- **Checkboxes tristate**:
  - ☐ Sin seleccionar
  - ☑ Completamente seleccionado (incluye subdirectorios)
  - ⊡ Parcialmente seleccionado (algunos subdirectorios)

- **Persistencia**: Las selecciones se guardan automáticamente en:
  ```
  C:\Users\<usuario>\.smart_search\directory_tree.json
  ```

- **Directorios indexados**: Se detectan automáticamente los directorios
  indexados por Windows Search

### 3. Resultados Clasificados

Los resultados se organizan automáticamente en pestañas por categoría:

- **Documentos**: PDF, DOC, DOCX, XLS, TXT, etc.
- **Imágenes**: JPG, PNG, GIF, BMP, SVG, etc.
- **Videos**: MP4, AVI, MKV, MOV, etc.
- **Audio**: MP3, WAV, FLAC, AAC, etc.
- **Código**: PY, JS, TS, JAVA, CPP, etc.
- **Archivos**: ZIP, RAR, 7Z, TAR, etc.
- **Ejecutables**: EXE, MSI, BAT, etc.
- **Datos**: JSON, XML, YAML, DB, etc.
- **Otros**: Archivos no clasificados

Cada pestaña muestra:
- Nombre del archivo
- Ruta completa
- Tamaño (formateado)
- Fecha de modificación
- Categoría

### 4. Operaciones de Archivos

#### Abrir Archivo
- **Botón**: "Open"
- **Atajo**: `Ctrl+O`
- **Límite**: Máximo 10 archivos a la vez

#### Abrir Ubicación
- **Botón**: "Open Location"
- Abre el explorador de Windows en la ubicación del archivo
- Resalta el archivo seleccionado

#### Copiar Archivos
- **Botón**: "Copy To..."
- Selecciona directorio de destino
- Copia múltiples archivos simultáneamente

#### Mover Archivos
- **Botón**: "Move To..."
- Requiere confirmación
- Mueve archivos al directorio seleccionado

#### Copiar Ruta
- **Menú contextual** (click derecho)
- Copia rutas completas al portapapeles

### 5. Tema Visual

- **Botón**: "Dark Mode" / "Light Mode"
- **Preferencia guardada**: Se mantiene entre sesiones
- **Temas disponibles**:
  - **Light**: Tema claro estándar
  - **Dark**: Tema oscuro estilo VS Code

### 6. Atajos de Teclado

| Atajo | Acción |
|-------|--------|
| `Ctrl+F` | Enfocar barra de búsqueda |
| `Ctrl+O` | Abrir archivos seleccionados |
| `Ctrl+L` | Limpiar resultados |
| `Enter` | Ejecutar búsqueda (desde input) |

## Arquitectura de la Integración

### Backend (backend.py)
- `SearchService`: Servicio principal de búsqueda
- `SearchQuery`: Construcción de consultas SQL
- `WindowsSearchEngine`: Motor Windows Search API
- `FallbackSearchEngine`: Motor alternativo sin API
- `FileOperations`: Operaciones de archivos

### File Manager (file_manager.py)
- `DirectoryTree`: Modelo de árbol de directorios
- `DirectoryNode`: Nodos con estados tristate
- `WindowsSearchIndexManager`: Detección de índices
- `FileOperations`: Copiar/mover con progreso

### Classifier (classifier.py)
- `classify_file()`: Clasificación por extensión
- `format_file_size()`: Formateo legible
- `format_date()`: Formateo de fechas
- `group_results_by_type()`: Agrupación

### UI (ui.py + main.py)
- `SmartSearchApp`: Ventana principal integrada
- `IntegratedDirectoryTreeWidget`: Árbol conectado al modelo
- `ClassifiedResultsTableWidget`: Tablas por categoría
- `IntegratedSearchWorker`: Thread de búsqueda

## Configuración

### Archivos de Configuración

```
C:\Users\<usuario>\.smart_search\
├── config.json              # Configuración general
└── directory_tree.json      # Árbol de directorios
```

### config.json
```json
{
  "version": "1.0.0",
  "dark_mode": false
}
```

### directory_tree.json
```json
{
  "version": "1.0",
  "roots": {
    "C:\\": {
      "path": "C:\\",
      "name": "C:\\",
      "state": 0,
      "children": { ... }
    }
  }
}
```

## Solución de Problemas

### Error: "pywin32 not installed"
```bash
pip install pywin32
```

### Error: "No se pudo conectar con Windows Search"
1. Verificar que el servicio Windows Search esté activo:
   - `services.msc` → "Windows Search" → Iniciar
2. Verificar indexación en Configuración de Windows:
   - Configuración → Buscar → Buscar en Windows

### Búsqueda lenta o sin resultados
- **Solución 1**: Verificar que los directorios estén indexados
- **Solución 2**: Reconstruir índice de Windows Search
- **Solución 3**: La aplicación usará motor alternativo automáticamente

### No aparecen directorios en el árbol
- **Solución**: Ejecutar como administrador la primera vez
- **Alternativa**: Añadir manualmente directorios comunes

## Rendimiento

### Búsqueda con Windows Search API
- **Velocidad**: ~10,000 archivos/segundo
- **Indexación**: Solo busca en archivos indexados
- **Ventaja**: Resultados instantáneos

### Búsqueda con Motor Alternativo
- **Velocidad**: ~100-500 archivos/segundo
- **Cobertura**: Busca en todos los archivos
- **Limitación**: Más lento pero completo

## Próximas Características

- [ ] Filtros avanzados por fecha
- [ ] Búsqueda por tamaño
- [ ] Expresiones regulares
- [ ] Exportar resultados (CSV, JSON)
- [ ] Historial de búsquedas
- [ ] Búsquedas guardadas
- [ ] Previsualización de archivos
- [ ] Integración con Everything Search

## Contacto y Soporte

Para reportar bugs o solicitar características:
- Revisar archivo `PROJECT_SUMMARY.md` para arquitectura
- Revisar `ARCHITECTURE.md` para detalles técnicos
- Ejecutar `validate.py` para diagnóstico

---

**Smart Search v1.0.0**
Desarrollado con Python, PyQt6 y Windows Search API
