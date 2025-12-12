# ARQUITECTO DATA EVALUACIÓN
## Smart Search Pro v3.0

**Evaluación: 7.5/10**

---

## RESUMEN EJECUTIVO

| Aspecto | Calificación | Estado |
|---------|--------------|--------|
| **Schema Design** | 7/10 | NORMALIZADO CON MEJORAS PENDIENTES |
| **Query Optimization** | 6/10 | LENTAS - Falta indexación estratégica |
| **Cache Strategies** | 8/10 | EFECTIVO - LRU bien implementado |
| **Data Persistence** | 8/10 | ROBUSTO - Migraciones y WAL activos |
| **Thread Safety** | 8/10 | SEGURO - Locks adecuados |
| **Escalabilidad** | 6/10 | LIMITADA - SQLite puede ser cuello de botella |

---

## 1. ANALISIS SCHEMA DESIGN

### 1.1 Arquitectura General

```
Core Database (core/database.py)
├── search_history (1000+ registros esperados)
├── saved_searches (bajo volumen)
├── hash_cache (100k+ registros potenciales)
├── file_tags (many-to-many)
├── preview_cache (caché de vistas previas)
├── operation_history (auditoría)
└── settings (configuración)

Sistemas Paralelos
├── SearchHistory (search/history.py) - JSON file-based
└── HashCache (duplicates/cache.py) - SQLite separado
```

### 1.2 PROBLEMAS IDENTIFICADOS

#### PROBLEMA 1: Duplicidad de Almacenamiento
```
search_history.json (SearchHistory class)
└── Almacena: query, timestamp, result_count, execution_time_ms, filters_used

search_history TABLE (core/database.py)
└── Almacena: query, query_type, result_count, execution_time, timestamp, filters, metadata
```

**IMPACTO**: Datos desincronizados. Búsquedas recientes no se persisten en DB centralizada.

---

#### PROBLEMA 2: Schema de hash_cache Sin Integridad

**En core/database.py:**
```sql
CREATE TABLE hash_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL UNIQUE,
    file_hash TEXT NOT NULL,          -- Solo 1 hash!
    file_size INTEGER NOT NULL,
    modified_time REAL NOT NULL,
    created_at REAL NOT NULL,
    accessed_count INTEGER DEFAULT 0,
    last_accessed REAL
);
```

**En duplicates/cache.py:**
```python
# Soporta quick_hash Y full_hash por separado
hash_cache TABLE:
    - quick_hash TEXT
    - full_hash TEXT
    - algorithm TEXT
    - access_count INTEGER
```

**DIFERENCIA CRÍTICA**: core/database.py solo usa 1 hash genérico, pero duplicates/cache.py necesita 2 tipos.

---

#### PROBLEMA 3: Falta de Normalización - file_tags

```sql
CREATE TABLE file_tags (
    id INTEGER PRIMARY KEY,
    file_path TEXT NOT NULL,
    tag TEXT NOT NULL,
    created_at REAL NOT NULL,
    UNIQUE(file_path, tag)
);
```

**FALTA**:
- Foreign key a tabla de archivos (inexistente)
- Tabla separada de tags para normalización
- Índice en (file_path, tag) debería ser PRIMARY KEY

**MEJOR SCHEMA**:
```sql
-- Tabla de tags centralizada
CREATE TABLE tags (
    id INTEGER PRIMARY KEY,
    tag TEXT NOT NULL UNIQUE
);

-- Tabla de enlace normalizada
CREATE TABLE file_tags (
    file_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    created_at REAL NOT NULL,
    PRIMARY KEY (file_id, tag_id),
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);
```

---

#### PROBLEMA 4: Indexación Insuficiente

**Índices Actuales:**
- `idx_search_history_timestamp` - OK
- `idx_search_history_query` - Débil (no UNIQUE)
- `idx_saved_searches_name` - OK
- `idx_hash_cache_path` - OK pero PRIMARY KEY mejor
- `idx_hash_cache_hash` - MISSING para lookups frecuentes
- `idx_file_tags_path` - Débil (no COMPOSITE)
- `idx_file_tags_tag` - Débil (no COMPOSITE)
- `idx_operation_history_type` - OK
- `idx_operation_history_timestamp` - OK
- `idx_preview_cache_path` - OK pero PRIMARY KEY mejor

**FALTA**: Índices COMPOSITE para búsquedas por múltiples columnas.

---

### 1.3 SCORE SCHEMA: 7/10

**Positivos:**
- WAL habilitado (√)
- Foreign keys ON (√)
- Migraciones versionadas (√)
- Connection pooling (√)

**Negativos:**
- Duplicidad search_history.json vs TABLE (-1.5)
- Schema hash_cache inconsistente (-1)
- file_tags no normalizado (-0.5)

---

## 2. ANÁLISIS QUERY OPTIMIZATION

### 2.1 Queries Actuales Identificadas

#### Query 1: SearchHistory.get_suggestions()
```python
# PROBLEMA: O(n) en memoria
for query, freq in sorted(self.query_frequency.items(),
                          key=lambda x: x[1], reverse=True):
    if query.lower().startswith(partial_lower):
        suggestions.append(query)
```

**LÍNEA 173-181**: Itera TODA la tabla frequency ordenada 3 veces.

**COSTO**: O(n log n) * 3 iteraciones = O(3n log n)

**MEJOR**:
```sql
-- Single query con índice BITMAP
SELECT DISTINCT query FROM search_history
WHERE query LIKE ?||'%'
ORDER BY result_count DESC
LIMIT ?;
```

---

#### Query 2: HashCache.get_duplicates_by_hash()
```python
cursor = conn.execute(
    f"SELECT file_path FROM hash_cache WHERE {column} = ?",
    (hash_value,)
)
```

**LÍNEA 424-428**: SQL Injection vulnerable (column interpolation)

**PROBLEMA**: `column` es concatenado directamente en f-string
```python
column = 'quick_hash' if hash_type == 'quick' else 'full_hash'
# ✗ BAD: f"SELECT file_path FROM hash_cache WHERE {column} = ?"
```

**RIESGO**: Si hash_type viene de usuario, es SQL Injection.

**MEJOR**:
```python
columns = {'quick': 'quick_hash', 'full': 'full_hash'}
if hash_type not in columns:
    raise ValueError("Invalid hash_type")

sql = f"SELECT file_path FROM hash_cache WHERE {columns[hash_type]} = ?"
cursor = conn.execute(sql, (hash_value,))
```

---

#### Query 3: Database.get_stats()
```python
# LÍNEA 635: Query sin índice por tabla
for table in tables:
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    stats["tables"][table] = cursor.fetchone()[0]
```

**PROBLEMA**: COUNT(*) sin índice hace FULL TABLE SCAN

**COSTO**: O(n) por tabla * número de tablas

**MEJOR**: Mantener metadata table con row counts actualizados
```sql
CREATE TABLE table_stats (
    table_name TEXT PRIMARY KEY,
    row_count INTEGER,
    updated_at REAL
);

-- Actualizar con triggers
CREATE TRIGGER search_history_insert AFTER INSERT ON search_history
BEGIN
    UPDATE table_stats SET row_count = row_count + 1
    WHERE table_name = 'search_history';
END;
```

---

### 2.2 ANÁLISIS DE PLAN DE EJECUCIÓN

#### Búsqueda de sugerencias (actual)
```
EXPLAIN QUERY PLAN
SELECT * FROM hash_cache WHERE quick_hash = ?
```

**Resultado Esperado (sin índice)**:
```
SCAN TABLE hash_cache
```

**Resultado Esperado (con índice)**:
```
SEARCH TABLE hash_cache USING INDEX idx_quick_hash
```

**MEJORA**: 10-100x más rápido con índice BITMAP en hash_cache

---

#### Historial de búsquedas por fecha
```sql
-- Consulta típica
SELECT * FROM search_history
WHERE timestamp > ?
ORDER BY timestamp DESC
LIMIT 100;
```

**ESTADO**: ✓ Índice exists (idx_search_history_timestamp)

**POTENCIAL MEJORA**: Agregar índice DESCENDING
```sql
CREATE INDEX idx_search_history_timestamp_desc
ON search_history(timestamp DESC);
```

---

### 2.3 SCORE QUERIES: 6/10

**Problemas Críticos:**
- SearchHistory.get_suggestions() - O(3n log n) en cada llamada (-2)
- SQL Injection en hash_type parameter (-1.5)
- COUNT(*) sin tracking (-0.5)

**Positivos:**
- WHERE clauses con parámetros ✓
- Índices básicos ✓

---

## 3. ANÁLISIS CACHE STRATEGIES

### 3.1 HashCache (duplicates/cache.py) - EXCELENTE

**Características Implementadas:**
```python
✓ LRU Eviction Policy
✓ Timestamp-based last_accessed
✓ SQLite persistence
✓ Thread-safe with Lock
✓ Automatic validation (mtime checking)
✓ Access count tracking
✓ VACUUM optimization
```

**Estrategia**:
```python
class HashCache:
    DEFAULT_MAX_SIZE = 100000      # Entries before eviction
    DEFAULT_EVICTION_SIZE = 10000  # Remove oldest 10k when full
```

**COSTO**: Mantener 100k hashes en SQLite ~50-100MB

**MÉTODO LRU**:
```sql
DELETE FROM hash_cache
WHERE file_path IN (
    SELECT file_path FROM hash_cache
    ORDER BY last_accessed ASC
    LIMIT ?
)
```

**PROBLEMA**: Evict es BLOCKING operation (FULL TABLE SCAN)

**MEJORA**: Usar BATCH DELETE con OFFSET
```sql
-- Mejor para grandes datasets
WITH to_delete AS (
    SELECT file_path FROM hash_cache
    ORDER BY last_accessed ASC
    LIMIT 10000
)
DELETE FROM hash_cache WHERE file_path IN (SELECT file_path FROM to_delete);
```

---

### 3.2 SearchHistory Cache (search/history.py) - BUENO PERO MEJORABLE

**Actual**: JSON file-based
```python
self.query_frequency: Dict[str, int] = defaultdict(int)
self.filter_frequency: Dict[str, int] = defaultdict(int)
```

**CARACTERÍSTICAS**:
```python
✓ Frecuencia de queries (en memoria)
✓ Frecuencia de filters (en memoria)
✓ Persistencia a JSON
✓ Atomic file writes (temp file + replace)
✓ Automatic trimming (max_entries=1000)
```

**PROBLEMAS**:

1. **Full file rewrite en cada add()**
   ```python
   # LÍNEA 118-119
   self.entries.insert(0, entry)  # O(n) en lista
   self._save()                   # Reescribe TODO el JSON
   ```

   **COSTO**: O(n) per búsqueda = lento si max_entries=1000

2. **Carga completa en memoria**
   ```python
   # LÍNEA 71: _load() lee TODOS los 1000 registros
   self.entries: List[SearchHistoryEntry] = []
   ```

   **MEJOR**: Lazy loading o SQL queries

---

### 3.3 Preview Cache (core/database.py)

```sql
CREATE TABLE preview_cache (
    id INTEGER PRIMARY KEY,
    file_path TEXT NOT NULL UNIQUE,
    preview_data TEXT NOT NULL,
    preview_type TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    modified_time REAL NOT NULL,
    created_at REAL NOT NULL,
    accessed_count INTEGER DEFAULT 0,
    last_accessed REAL
);
```

**BUENO**: Schema similar a hash_cache

**PROBLEMA**: No hay eviction policy en core/database.py

**FALTA**:
- No se implementa LRU manual
- No hay VACUUM automático
- TABLE podría crecer indefinidamente

---

### 3.4 SCORE CACHE: 8/10

**Positivos:**
- HashCache LRU bien hecho (√)
- SearchHistory frequency tracking (√)
- Atomic writes (√)
- Thread-safe operations (√)

**Mejoras necesarias:**
- Batch eviction en HashCache (-0.5)
- SearchHistory reescribe TODO el JSON (-1)
- Preview cache sin eviction (-0.5)

---

## 4. ANÁLISIS DATA PERSISTENCE

### 4.1 WAL (Write-Ahead Logging) - ACTIVADO

```python
# LÍNEA 325, 339
journal_mode: str = "WAL"
cursor.execute(f"PRAGMA journal_mode = {self._journal_mode}")
```

**VENTAJAS**:
- Lecturas paralelas con escrituras ✓
- Recuperación rápida de crashes ✓
- Mejor rendimiento en writes ✓

**DESVENTAJA**: WAL files pueden crecer (cleanup requerido)

---

### 4.2 Synchronous Mode - NORMAL (Bueno)

```python
synchronous: str = "NORMAL"  # LIGNE 296
```

**TRADE-OFF**:
- `NORMAL` = Seguro contra crashes del OS
- `FULL` = Más seguro pero 2x más lento
- `OFF` = Fastest pero unsafe

**ESTADO**: Apropiado para aplicación de búsqueda

---

### 4.3 Migraciones Versionadas

```python
MIGRATIONS: list[Migration] = [
    Migration(
        version=1,
        description="Initial schema",
        sql="...",
        rollback_sql="..."  # Buena práctica
    ),
]
```

**ESTADO**: ✓ Rollback soportado

**PROBLEMA**: Solo 1 migración, no hay histórico de cambios

---

### 4.4 Connection Pooling

```python
class ConnectionPool:
    def __init__(self, pool_size: int = 5, timeout: float = 30.0):
        self._pool: Queue[sqlite3.Connection] = Queue(maxsize=pool_size)
```

**ESTADO**: ✓ Bien implementado
- Tamaño ajustable
- Timeout configurable
- Cleanup automático

**LÍMITE SQLite**: Max 5 conexiones simultáneas es conservador pero seguro

---

### 4.5 SCORE PERSISTENCE: 8/10

**Positivos:**
- WAL activado (✓)
- Migraciones versionadas (✓)
- Connection pooling (✓)
- Synchronous=NORMAL (✓)

**Mejoras:**
- PRAGMA synchronous podría usar EXTRA para más seguridad (-0.5)
- WAL cleanup strategy no documentado (-0.5)
- Backup strategy no presente (-1)

---

## 5. ANÁLISIS THREAD SAFETY

### 5.1 ConnectionPool - THREAD SAFE

```python
self._lock = threading.Lock()
self._pool: Queue[sqlite3.Connection] = Queue()

# LÍNEA 116-122
with self._lock:
    if self._connection_count < self._pool_size:
        conn = self._create_connection()
```

**ESTADO**: ✓ Uso correcto de Lock + Queue

---

### 5.2 HashCache - THREAD SAFE

```python
self._lock = threading.Lock()

def get_hash(self, ...):
    with self._lock:
        # Operations...
```

**ESTADO**: ✓ Todos los métodos públicos están bloqueados

---

### 5.3 SearchHistory - NO THREAD SAFE

```python
class SearchHistory:
    def add(self, query: str, ...):
        self.entries.insert(0, entry)  # ✗ NO LOCK!
        self.query_frequency[normalized_query] += 1  # ✗ RACE CONDITION!
        self._save()
```

**PROBLEMA CRÍTICO**: Sin Lock en SearchHistory.add()

**ESCENARIO DE RACE**:
```
Thread 1: self.entries.insert(0, entry1)
Thread 2: self.entries.insert(0, entry2)
Result: Índices inconsistentes, posible crash
```

**RECOMENDACIÓN**: Agregar Lock
```python
class SearchHistory:
    def __init__(self, ...):
        self._lock = threading.Lock()

    def add(self, query: str, ...):
        with self._lock:
            self.entries.insert(0, entry)
            self.query_frequency[normalized_query] += 1
            self._save()
```

---

### 5.4 SCORE THREAD SAFETY: 8/10 (con error crítico)

**Positivos:**
- ConnectionPool threadsafe (✓)
- HashCache threadsafe (✓)

**Problemas:**
- SearchHistory.add() SIN LOCK (-2 por criticidad)

---

## 6. ESCALABILIDAD Y LIMITACIONES

### 6.1 Limitación: SQLite Single Writer

```
SQLite Architecture:
├─ Multiple Readers (WAL enabled)
└─ Single Writer (QUEUE model)
```

**PROBLEMA**: Con 5 conexiones pool_size, si >1 thread intenta escribir:
```
Thread A writes query -> locks DB for ~50ms
Thread B waits...
Thread C waits...
Thread D waits...
Thread E waits...

All writes are SERIALIZED
```

**PROYECCIÓN**:
- 100 búsquedas/segundo = 100ms búsqueda = BOTTLENECK
- hash_cache 100k entries = ~500MB eventual

---

### 6.2 Migración a PostgreSQL

**Cuando considerar:**
- >1000 búsquedas/día
- >500k hashes en caché
- Necesidad de concurrent writes
- Múltiples instancias/procesos

**IMPACTO ACTUAL**: SQLite es ADECUADO para versión 3.0

---

### 6.3 Particionamiento Futuro

```
Opción 1: Temporal (año/mes)
search_history_2024_12
search_history_2024_11

Opción 2: Hash (por rango)
hash_cache_0_25k
hash_cache_25k_50k
hash_cache_50k_75k
hash_cache_75k_100k
```

**NO RECOMENDADO para SQLite** (mejor en PostgreSQL)

---

## 7. RECOMENDACIONES PRIORIZADAS

### CRÍTICAS (Hacer ASAP)

1. **Agregar Lock a SearchHistory.add()**
   ```python
   # duplicates/search/history.py
   self._lock = threading.Lock()  # en __init__

   def add(self, query, ...):
       with self._lock:
           # Proteger todas las operaciones
   ```
   **Esfuerzo**: 5 minutos | **Impacto**: Evita crashes concurrentes

---

2. **Validar Parameter en get_duplicates_by_hash()**
   ```python
   # duplicates/cache.py línea 421
   hash_type_map = {'quick': 'quick_hash', 'full': 'full_hash'}
   if hash_type not in hash_type_map:
       raise ValueError("Invalid hash_type")
   column = hash_type_map[hash_type]
   ```
   **Esfuerzo**: 3 minutos | **Impacto**: Elimina SQL Injection

---

### ALTOS IMPACTO (Próximas 2 sprints)

3. **Consolidar search_history: JSON → SQL**
   - Reemplazar SearchHistory.json con queries SQL
   - Mantener in-memory cache solo de últimas 100 búsquedas
   - Sincronizar automáticamente a core/database.py

   **Esfuerzo**: 2-3 horas | **Impacto**: Single source of truth

---

4. **Normalizar file_tags schema**
   ```sql
   -- Nueva tabla
   CREATE TABLE tags (
       id INTEGER PRIMARY KEY,
       tag TEXT NOT NULL UNIQUE
   );

   -- Reemplazar file_tags
   CREATE TABLE file_tags (
       file_id INTEGER NOT NULL,
       tag_id INTEGER NOT NULL,
       created_at REAL NOT NULL,
       PRIMARY KEY (file_id, tag_id),
       FOREIGN KEY (tag_id) REFERENCES tags(id)
   );
   ```
   **Esfuerzo**: 1.5 horas | **Impacto**: -50% disk space, queries más rápidas

---

5. **Agregar índices COMPOSITE**
   ```sql
   CREATE INDEX idx_file_tags_composite
   ON file_tags(file_path, tag);

   CREATE INDEX idx_search_history_query_timestamp
   ON search_history(query, timestamp DESC);
   ```
   **Esfuerzo**: 20 minutos | **Impacto**: 5-10x más rápido en lookups frecuentes

---

### MEDIANO IMPACTO (Nice to have)

6. **Implementar eviction policy en preview_cache**
   - Similar a HashCache.DEFAULT_MAX_SIZE
   - Auto-evict cuando >50MB

7. **Batch eviction en HashCache**
   - Cambiar LRU delete a batch operation
   - Reduce lock contention

8. **Query optimization SearchHistory.get_suggestions()**
   - Mover a SQL con LIKE '%'
   - Cache top 100 suggestions in-memory

---

## 8. SCRIPTS OPTIMIZACIÓN

### Script 1: Agregar índices faltantes

```sql
-- Ejecutar en core database
CREATE INDEX IF NOT EXISTS idx_hash_cache_hash
ON hash_cache(file_hash);

CREATE INDEX IF NOT EXISTS idx_search_history_query_timestamp
ON search_history(query, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_file_tags_composite
ON file_tags(file_path, tag);

CREATE INDEX IF NOT EXISTS idx_preview_cache_accessed
ON preview_cache(last_accessed);

-- Verificar
PRAGMA index_list(hash_cache);
```

---

### Script 2: Auditoría de tamaño BD

```python
import sqlite3
from pathlib import Path

def audit_database(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Tamaño por tabla
    cursor.execute("""
        SELECT
            name,
            (SELECT page_count FROM pragma_page_count) *
            (SELECT page_size FROM pragma_page_size) as size_bytes
        FROM sqlite_master
        WHERE type='table'
    """)

    print("Database Audit:")
    for table, size in cursor.fetchall():
        print(f"  {table}: {size / 1024 / 1024:.2f} MB")

    conn.close()

# Uso
audit_database("~/.smart_search/data.db")
```

---

### Script 3: Monitoreo de performance

```python
def monitor_queries(db_path, timeout=5.0):
    import sqlite3

    conn = sqlite3.connect(db_path, timeout=timeout)
    cursor = conn.cursor()

    # Habilitar query profiling
    cursor.execute("PRAGMA query_only = OFF")

    # Analizar queries lentas (>100ms)
    slow_queries = []

    for query in logged_queries:
        start = time.time()
        cursor.execute(f"EXPLAIN ANALYZE {query}")
        duration = (time.time() - start) * 1000

        if duration > 100:
            slow_queries.append((query, duration))

    return sorted(slow_queries, key=lambda x: x[1], reverse=True)
```

---

## 9. CONCLUSIONES

| Aspecto | Puntuación | Recomendación |
|---------|-----------|---------------|
| **Schema Design** | 7/10 | Normalizar file_tags, consolidar search_history |
| **Query Performance** | 6/10 | Agregar índices composite, optimizar suggestions |
| **Cache Strategy** | 8/10 | Excelente LRU, mejorar batch eviction |
| **Persistence** | 8/10 | WAL y migraciones bien. Agregar backup strategy |
| **Thread Safety** | 8/10 | CRÍTICO: Agregar lock a SearchHistory |
| **Escalabilidad** | 6/10 | SQLite OK, pero considerar PostgreSQL >500k registros |

---

## ARQUITECTO DATA - VEREDICTO FINAL

**PUNTUACIÓN GLOBAL: 7.5/10**

### Fortalezas
- WAL activado y connection pooling bien implementado
- LRU cache elegante en HashCache
- Migraciones versionadas con rollback
- Thread safety en componentes críticos

### Debilidades Críticas
- SearchHistory sin thread safety (RACE CONDITIONS posible)
- SQL Injection en get_duplicates_by_hash() parameter
- Duplicidad JSON vs SQL en search history
- file_tags no normalizado

### Próximos Pasos
1. **INMEDIATO**: Agregar lock a SearchHistory.add() y validar hash_type
2. **1 SEMANA**: Consolidar search_history en SQL, normalizar file_tags
3. **1 MES**: Agregar índices composite, implementar eviction policy en preview_cache

**Código está PRODUCCIÓN-LISTO pero requiere 2-3 horas de hardening crítico.**

---

## AUTOR: Arquitecto de Datos
**Fecha**: 2025-12-12
**Versión de Análisis**: v1.0
