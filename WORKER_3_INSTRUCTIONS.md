# WORKER-3: Archive, Tools, Vault, Operations, Search
## Smart Search Pro v3.0 - Verificación Profunda

**Proyecto:** `C:/Users/ramos/.local/bin/smart_search/`
**Stack:** Python 3.11+, PyQt6, SQLite, 7-Zip SDK, Everything SDK

---

## TU MISIÓN

Eres WORKER-3. Tu responsabilidad es verificar los módulos de funcionalidad avanzada:

### MÓDULOS ASIGNADOS:
1. **archive/** - Gestión de archivos 7-Zip
2. **tools/** - Herramientas (ExifTool, batch rename, etc.)
3. **vault/** - Bóveda segura encriptada
4. **operations/** - Operaciones de archivos estilo TeraCopy
5. **search/** - Motor de búsqueda y Everything SDK
6. **duplicates/** - Detección de duplicados

---

## FASE 1: VERIFICACIÓN DE EXISTENCIA

### Archive:
- [ ] `archive/__init__.py`
- [ ] `archive/manager.py` o equivalente
- [ ] `archive/extractor.py` o equivalente

### Tools:
- [ ] `tools/__init__.py`
- [ ] `tools/exiftool.py` o equivalente
- [ ] `tools/batch_rename.py` o equivalente

### Vault:
- [ ] `vault/__init__.py`
- [ ] `vault/crypto.py` o `vault/encryption.py`
- [ ] `vault/manager.py`
- [ ] `vault/secure_delete.py`

### Operations:
- [ ] `operations/__init__.py`
- [ ] `operations/manager.py`
- [ ] `operations/mover.py`
- [ ] `operations/progress.py`
- [ ] `operations/conflicts.py`

### Search:
- [ ] `search/__init__.py`
- [ ] `search/query_parser.py`
- [ ] `search/filters.py`
- [ ] `search/history.py`

### Duplicates:
- [ ] `duplicates/__init__.py`
- [ ] `duplicates/groups.py`
- [ ] `duplicates/actions.py`
- [ ] `duplicates/cache.py`

---

## FASE 2: VERIFICACIÓN DE INTEGRIDAD

### 2.1 Archive Module
```python
# Verificar integración con 7-Zip
import archive
# Verificar que puede listar contenido de archivos
```

### 2.2 Tools Module
```python
import tools
# Verificar ExifTool integration
# Verificar batch rename
```

### 2.3 Vault Module (CRÍTICO - Seguridad)
```python
from vault import VaultManager
# Verificar que usa encriptación fuerte
# PBKDF2 para derivación de claves
# AES-256 para encriptación
```

### 2.4 Operations Module
```python
from operations import OperationsManager
from operations.mover import FileMover
from operations.progress import ProgressTracker
from operations.conflicts import ConflictResolver
```

### 2.5 Search Module
```python
from search import SearchEngine, QueryParser
from search.filters import SearchFilters
from search.history import SearchHistory
```

### 2.6 Duplicates Module
```python
from duplicates import DuplicateFinder
from duplicates.groups import DuplicateGroup
from duplicates.actions import DuplicateActions
```

---

## FASE 3: VERIFICACIÓN FUNCIONAL

### 3.1 Test Archive (7-Zip)
```python
from archive import ArchiveManager
am = ArchiveManager()
# Verificar que puede detectar tipos de archivo
# .zip, .7z, .rar, .tar.gz
print("ArchiveManager: VERIFICADO")
```

### 3.2 Test Vault (Seguridad Crítica)
```python
from vault import VaultManager
from vault.crypto import derive_key, encrypt, decrypt

# Verificar PBKDF2
from hashlib import pbkdf2_hmac
key = pbkdf2_hmac('sha256', b'password', b'salt', 100000)
assert len(key) == 32  # 256 bits

# Verificar que el vault usa estas primitivas
print("Vault Crypto: VERIFICADO")
```

### 3.3 Test Operations (TeraCopy-style)
```python
from operations.manager import OperationsManager

# Verificar que tiene:
# - Queue de operaciones
# - Pause/Resume
# - Verificación CRC
# - Retry on error
print("OperationsManager: VERIFICADO")
```

### 3.4 Test Search (Everything SDK)
```python
from search import SearchEngine

# Verificar integración con Everything
# Si Everything no está instalado, debe tener fallback
print("SearchEngine: VERIFICADO")
```

### 3.5 Test Duplicates (5 algoritmos hash)
```python
from duplicates import DuplicateFinder

# Verificar que soporta:
# - MD5
# - SHA-1
# - SHA-256
# - xxHash (si disponible)
# - BLAKE3 (si disponible)
print("DuplicateFinder: VERIFICADO")
```

---

## FASE 4: SEGURIDAD CRÍTICA

### 4.1 Vault Security Audit
```python
# Verificar en vault/crypto.py:
# 1. PBKDF2 con mínimo 100,000 iteraciones
# 2. Salt aleatorio de mínimo 16 bytes
# 3. AES-256-GCM o ChaCha20-Poly1305
# 4. No almacenar passwords en texto plano
# 5. Secure delete con overwrite

CHECKLIST_VAULT = [
    "PBKDF2 iterations >= 100000",
    "Salt size >= 16 bytes",
    "AES-256 or ChaCha20",
    "No plaintext passwords",
    "Secure file deletion"
]
```

### 4.2 Operations Security
```python
# Verificar que operations/manager.py:
# 1. Valida rutas antes de operar
# 2. No permite path traversal
# 3. Verifica permisos antes de escribir
# 4. Maneja errores de acceso
```

### 4.3 Search Security
```python
# Verificar que search/query_parser.py:
# 1. Sanitiza input del usuario
# 2. No permite inyección SQL
# 3. Limita tamaño de queries
```

---

## FASE 5: PERFORMANCE

### 5.1 Duplicates Performance
```python
# Verificar que duplicates usa:
# - Comparación por tamaño primero (rápido)
# - Hash parcial después (medio)
# - Hash completo solo si necesario (lento)
```

### 5.2 Search Performance
```python
# Verificar que search tiene:
# - Cache de resultados
# - Índice de archivos
# - Everything SDK para <100ms
```

### 5.3 Operations Performance
```python
# Verificar que operations tiene:
# - Buffer size óptimo (64KB-1MB)
# - Async I/O si es posible
# - Progress updates no bloquean UI
```

---

## REPORTE FINAL

```
=== WORKER-3 REPORTE ===
Fecha: [FECHA]

ARCHIVE MODULE:
- __init__.py: [OK/ERROR]
- manager: [OK/ERROR]
- 7-Zip integration: [FUNCIONAL/ERROR]

TOOLS MODULE:
- __init__.py: [OK/ERROR]
- exiftool: [OK/ERROR]
- batch_rename: [OK/ERROR]

VAULT MODULE (CRÍTICO):
- __init__.py: [OK/ERROR]
- crypto: [OK/ERROR]
- manager: [OK/ERROR]
- PBKDF2: [100000+ iter / INSEGURO]
- AES-256: [SI/NO]
- Secure Delete: [SI/NO]

OPERATIONS MODULE:
- manager.py: [OK/ERROR]
- mover.py: [OK/ERROR]
- progress.py: [OK/ERROR]
- conflicts.py: [OK/ERROR]
- TeraCopy features: [COMPLETO/PARCIAL]

SEARCH MODULE:
- query_parser.py: [OK/ERROR]
- filters.py: [OK/ERROR]
- history.py: [OK/ERROR]
- Everything SDK: [INTEGRADO/FALLBACK]

DUPLICATES MODULE:
- groups.py: [OK/ERROR]
- actions.py: [OK/ERROR]
- cache.py: [OK/ERROR]
- Hash algorithms: [5/5 OK]

SEGURIDAD:
- Vault Encryption: [FUERTE/DÉBIL]
- Path Validation: [OK/VULNERABLE]
- Input Sanitization: [OK/FALTANTE]

PERFORMANCE:
- Duplicates: [OPTIMIZADO/LENTO]
- Search: [<100ms / LENTO]
- Operations: [BUFFER OK / PEQUEÑO]

ERRORES ENCONTRADOS:
1. [error 1]
2. [error 2]

CORRECCIONES APLICADAS:
1. [fix 1]
2. [fix 2]
```

---

## COMANDOS DE INICIO

```bash
cd C:/Users/ramos/.local/bin/smart_search
python -c "from archive import *; print('Archive OK')"
python -c "from vault import *; print('Vault OK')"
python -c "from operations import *; print('Operations OK')"
python -c "from search import *; print('Search OK')"
python -c "from duplicates import *; print('Duplicates OK')"
```

**COMIENZA LA VERIFICACIÓN AHORA.**
