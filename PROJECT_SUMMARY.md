# Smart Search Backend - Resumen del Proyecto

## Información General

**Ubicación**: `C:\Users\ramos\.local\bin\smart_search\`
**Versión**: 1.0.0
**Fecha**: 2025-12-11
**Autor**: Backend Architect (Claude Opus 4.5)

## Descripción

Sistema completo de búsqueda avanzada para Windows que combina la potencia de Windows Search API (COM/WMI) con un motor de búsqueda alternativo basado en sistema de archivos. Diseñado para ser rápido, confiable y escalable.

## Estructura del Proyecto

```
C:\Users\ramos\.local\bin\smart_search\
│
├── backend.py              # CORE: Motor de búsqueda completo (31 KB)
├── __init__.py             # Módulo Python con exports
├── config.py               # Configuración centralizada
├── requirements.txt        # Dependencias
│
├── example_usage.py        # 9 ejemplos prácticos de uso
├── test_backend.py         # Suite de tests unitarios
├── install.py              # Script de instalación automática
│
├── README.md               # Documentación de usuario
└── ARCHITECTURE.md         # Documentación técnica de arquitectura
```

## Características Principales

### 1. Doble Motor de Búsqueda

**Windows Search API (Principal)**:
- Búsqueda instantánea usando índice de Windows
- Full-text search en contenido de archivos
- Integración COM con ADODB
- SQL queries sobre SystemIndex

**Fallback Engine (Respaldo)**:
- Búsqueda manual por sistema de archivos
- Usa `os.walk()` para directorios
- Siempre disponible (no depende de servicios)
- Pattern matching con wildcards

### 2. Búsqueda Avanzada

```python
# Wildcards múltiples
keywords=['python', '*.py', 'documento*']

# Búsqueda por nombre
search_filename=True

# Búsqueda por contenido (full-text)
search_content=True

# Filtrado por directorios
search_paths=[r'C:\Users\ramos\Documents']

# Filtrado por categoría
file_categories={FileCategory.DOCUMENT, FileCategory.CODE}
```

### 3. Clasificación Automática

9 categorías de archivos:
- DOCUMENT (PDF, DOCX, TXT, etc.)
- IMAGE (JPG, PNG, SVG, etc.)
- VIDEO (MP4, AVI, MKV, etc.)
- AUDIO (MP3, WAV, FLAC, etc.)
- CODE (PY, JS, CPP, etc.)
- ARCHIVE (ZIP, RAR, 7Z, etc.)
- EXECUTABLE (EXE, MSI, APP, etc.)
- DATA (JSON, XML, DB, etc.)
- OTHER

### 4. Threading No Bloqueante

```python
# Búsqueda asíncrona con callbacks
search_id = service.search_async(
    query,
    callback=on_result,              # Por cada resultado
    completion_callback=on_complete,  # Al terminar
    error_callback=on_error           # En caso de error
)

# Verificar estado
if service.is_search_active(search_id):
    print("Búsqueda en progreso...")

# Obtener resultados
results = service.get_results(search_id)
```

### 5. Operaciones de Archivos

```python
ops = FileOperations()

# Copiar
ops.copy(source, destination, overwrite=True)

# Mover
ops.move(source, destination)

# Abrir con app predeterminada
ops.open_file(path)

# Abrir en explorador
ops.open_location(path)

# Eliminar (papelera o permanente)
ops.delete(path, permanent=False)

# Propiedades completas
props = ops.get_properties(path)
```

## Arquitectura

### Diagrama de Componentes

```
┌───────────────────────────────────────────────┐
│          SearchService (Orquestador)          │
│  - Threading y concurrencia                   │
│  - Clasificación de resultados                │
│  - Gestión de búsquedas múltiples             │
└───────────────┬───────────────────────────────┘
                │
        ┌───────┴────────┐
        ▼                ▼
┌──────────────┐  ┌──────────────┐
│ Windows      │  │ Fallback     │
│ Search       │  │ Engine       │
│ Engine       │  │ (os.walk)    │
│ (COM/ADO)    │  │              │
└──────────────┘  └──────────────┘
        │                │
        └────────┬───────┘
                 ▼
        ┌────────────────┐
        │ SearchResult   │
        │ (Clasificado)  │
        └────────────────┘
```

### Clases Principales

1. **SearchService**: Orquestador principal
2. **WindowsSearchEngine**: Integración COM con Windows Search
3. **FallbackSearchEngine**: Motor alternativo de archivos
4. **SearchQuery**: Modelo de consulta
5. **SearchResult**: Resultado enriquecido con clasificación
6. **FileOperations**: Operaciones seguras sobre archivos
7. **FileCategory**: Enum de categorías

## Instalación

### Opción 1: Script Automático

```bash
cd C:\Users\ramos\.local\bin\smart_search
python install.py
```

El script:
1. Verifica Python 3.8+
2. Instala pywin32, comtypes, send2trash
3. Verifica Windows Search API
4. Ejecuta tests básicos
5. Crea script de ejemplo

### Opción 2: Manual

```bash
pip install -r requirements.txt
```

## Uso Rápido

### Ejemplo Básico

```python
from smart_search import SearchService, SearchQuery

# Crear servicio
service = SearchService()

# Búsqueda simple
query = SearchQuery(
    keywords=['documento', 'informe'],
    search_paths=[r'C:\Users\ramos\Documents']
)

results = service.search_sync(query)

for result in results:
    print(f"{result.name} - {result.category.value}")
```

### Ejemplo con Wildcards

```python
query = SearchQuery(
    keywords=['*.py', '*.js'],
    search_paths=[r'C:\Projects']
)

results = service.search_sync(query)
classified = service.classify_results(results)

for category, items in classified.items():
    print(f"{category.value}: {len(items)} archivos")
```

### Ejemplo Asíncrono

```python
def on_result(result):
    print(f"Encontrado: {result.name}")

search_id = service.search_async(
    query,
    callback=on_result,
    completion_callback=lambda r: print(f"Total: {len(r)}")
)
```

## API Reference

### SearchQuery

**Constructor**:
```python
SearchQuery(
    keywords: List[str],                      # Requerido
    search_paths: Optional[List[str]] = None,
    search_content: bool = False,
    search_filename: bool = True,
    file_categories: Optional[Set[FileCategory]] = None,
    max_results: int = 1000,
    recursive: bool = True
)
```

### SearchService

**Métodos principales**:

```python
search_sync(query: SearchQuery) -> List[SearchResult]
```
Búsqueda síncrona (bloquea hasta completar).

```python
search_async(
    query: SearchQuery,
    callback: Optional[Callable] = None,
    completion_callback: Optional[Callable] = None,
    error_callback: Optional[Callable] = None
) -> str
```
Búsqueda asíncrona, retorna search_id.

```python
classify_results(
    results: List[SearchResult]
) -> Dict[FileCategory, List[SearchResult]]
```
Clasifica resultados por categoría.

### FileOperations

**Métodos**:

```python
copy(source: str, destination: str, overwrite: bool = False) -> bool
move(source: str, destination: str, overwrite: bool = False) -> bool
open_file(path: str) -> bool
open_location(path: str) -> bool
delete(path: str, permanent: bool = False) -> bool
get_properties(path: str) -> Dict
```

## Testing

### Ejecutar Tests

```bash
python test_backend.py
```

### Cobertura

- Tests de modelos: SearchQuery, SearchResult, FileCategory
- Tests de búsqueda: WindowsSearch, Fallback, Async
- Tests de operaciones: copy, move, delete, open
- Tests de clasificación

### Resultados Esperados

```
>>> TESTS DE MODELOS: 5/5 PASSED
>>> TESTS DE BÚSQUEDA: 4/4 PASSED
>>> TESTS DE OPERACIONES: 4/4 PASSED
Total: 13 tests
```

## Ejemplos Incluidos

El archivo `example_usage.py` incluye 9 ejemplos completos:

1. Búsqueda básica
2. Búsqueda con wildcards
3. Búsqueda asíncrona
4. Filtrado por categoría
5. Operaciones de archivos
6. Búsqueda por contenido
7. Búsquedas paralelas
8. Filtrado avanzado
9. Exportar resultados

Ejecutar:
```bash
python example_usage.py
```

## Performance

### Benchmarks Estimados

**Windows Search API**:
- 100 resultados: ~50ms
- 1000 resultados: ~200ms
- 10000 resultados: ~1s

**Fallback Engine**:
- 100 resultados: ~500ms
- 1000 resultados: ~5s
- 10000 resultados: ~30s

(Depende de tamaño del directorio y hardware)

### Optimizaciones

1. **Límite de resultados**: `max_results` para evitar sobrecarga
2. **Búsqueda no recursiva**: `recursive=False` para directorios específicos
3. **Threading**: Búsquedas paralelas con `search_async()`
4. **Clasificación O(1)**: Dict lookup por extensión

## Manejo de Errores

### Errores Comunes

**Windows Search no disponible**:
```python
try:
    service = SearchService(use_windows_search=True)
except ConnectionError:
    service = SearchService(use_windows_search=False)
```

**Permisos denegados**:
```python
# Automáticamente skipea directorios sin permisos
# Logs warning y continúa
```

**Archivo no existe**:
```python
try:
    ops.copy(source, dest)
except FileNotFoundError as e:
    print(f"Archivo no encontrado: {e}")
```

## Escalabilidad

### Límites Actuales

- Max resultados por búsqueda: 10,000
- Max búsquedas concurrentes: 5
- Memoria estimada: ~500MB para búsquedas grandes

### Recomendaciones

**Para directorios grandes**:
- Usar Windows Search API (más rápido)
- Limitar `max_results`
- Búsqueda no recursiva si es posible

**Para múltiples búsquedas**:
- Usar `search_async()` para paralelizar
- Limitar a 5 búsquedas simultáneas

**Para mejor performance**:
- Indexar con Windows Search
- Usar paths específicos (no raíz C:\)
- Filtrar por categorías cuando sea posible

## Futuras Mejoras

### v1.1 (Planeado)
- Cache LRU de resultados
- Progress callbacks (porcentaje)
- Cancelación real de threads
- Índice local (Whoosh)

### v2.0 (Futuro)
- REST API con FastAPI
- WebSocket para resultados en tiempo real
- Integración con cloud storage
- Machine Learning para relevancia

## Dependencias

### Requeridas
- Python 3.8+
- pywin32 >= 305
- comtypes >= 1.2.0

### Opcionales
- send2trash >= 1.8.0 (papelera de reciclaje)
- whoosh >= 2.7.4 (índice local - futuro)

## Troubleshooting

### Windows Search no funciona

1. Verificar servicio:
```powershell
Get-Service WSearch
Start-Service WSearch
```

2. Usar fallback:
```python
service = SearchService(use_windows_search=False)
```

### Resultados vacíos

- Verificar que paths existan
- Verificar indexación de Windows Search
- Probar con Fallback Engine

### Performance lenta

- Reducir `max_results`
- Usar paths más específicos
- Activar Windows Search indexing

## Licencia

MIT License

## Contacto y Soporte

Para issues, mejoras o preguntas:
- Revisar `ARCHITECTURE.md` para detalles técnicos
- Ejecutar `test_backend.py` para verificar instalación
- Revisar ejemplos en `example_usage.py`

---

**Archivo principal**: `C:\Users\ramos\.local\bin\smart_search\backend.py` (31 KB)
**Documentación completa**: `README.md` y `ARCHITECTURE.md`
**Tests**: `test_backend.py`
**Instalación**: `install.py`
