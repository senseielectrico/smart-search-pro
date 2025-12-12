# WORKER-1: Core, System, Database, Security
## Smart Search Pro v3.0 - Verificación Profunda

**Proyecto:** `C:/Users/ramos/.local/bin/smart_search/`
**Stack:** Python 3.11+, PyQt6, SQLite, PyInstaller

---

## TU MISIÓN

Eres WORKER-1. Tu responsabilidad es verificar y optimizar los módulos fundamentales:

### MÓDULOS ASIGNADOS:
1. **core/** - Núcleo del sistema (config, logger, eventbus, exceptions)
2. **system/** - Integración con Windows (tray, autostart, shell, single_instance)
3. **export/** - Exportadores (base, excel, clipboard)
4. **Backend** - backend.py, classifier.py, file_manager.py

---

## FASE 1: VERIFICACIÓN DE EXISTENCIA

Ejecuta estos comandos para verificar que todos los archivos existen:

```python
# Verificar módulos core
from core import Config, Logger, EventBus
from core.exceptions import SmartSearchException

# Verificar módulos system
from system import SystemTray, AutoStart, ShellIntegration, SingleInstance

# Verificar módulos export
from export import BaseExporter, ExcelExporter, ClipboardExporter
```

### Archivos a verificar:
- [ ] `core/__init__.py`
- [ ] `core/config.py`
- [ ] `core/logger.py`
- [ ] `core/eventbus.py`
- [ ] `core/exceptions.py`
- [ ] `system/__init__.py`
- [ ] `system/tray.py`
- [ ] `system/autostart.py`
- [ ] `system/shell_integration.py`
- [ ] `system/single_instance.py`
- [ ] `export/__init__.py`
- [ ] `export/base.py`
- [ ] `export/excel_exporter.py`
- [ ] `export/clipboard.py`
- [ ] `backend.py`
- [ ] `classifier.py`
- [ ] `file_manager.py`

---

## FASE 2: VERIFICACIÓN DE INTEGRIDAD

### 2.1 Verificar imports correctos
```bash
cd C:/Users/ramos/.local/bin/smart_search
python -c "from core import *; print('Core OK')"
python -c "from system import *; print('System OK')"
python -c "from export import *; print('Export OK')"
```

### 2.2 Verificar que no hay imports circulares
- Revisar que `core/__init__.py` no importe de otros módulos
- Verificar que `system/__init__.py` solo importe de core si es necesario

### 2.3 Verificar sintaxis Python
```bash
python -m py_compile core/config.py
python -m py_compile core/logger.py
python -m py_compile system/tray.py
python -m py_compile export/base.py
```

---

## FASE 3: VERIFICACIÓN FUNCIONAL

### 3.1 Test Config
```python
from core.config import Config
cfg = Config()
assert hasattr(cfg, 'get')
assert hasattr(cfg, 'set')
print("Config: FUNCIONAL")
```

### 3.2 Test Logger
```python
from core.logger import Logger
log = Logger(__name__)
log.info("Test message")
print("Logger: FUNCIONAL")
```

### 3.3 Test EventBus
```python
from core.eventbus import EventBus
bus = EventBus()
received = []
bus.subscribe('test', lambda x: received.append(x))
bus.emit('test', 'data')
assert received == ['data']
print("EventBus: FUNCIONAL")
```

### 3.4 Test SystemTray (sin GUI)
```python
from system.tray import SystemTray
# Solo verificar que la clase existe y tiene métodos
assert hasattr(SystemTray, 'show')
print("SystemTray: VERIFICADO")
```

### 3.5 Test Export
```python
from export.base import BaseExporter
assert hasattr(BaseExporter, 'export')
print("BaseExporter: VERIFICADO")
```

---

## FASE 4: SEGURIDAD

### 4.1 SQL Injection Prevention
Verificar que todas las queries usan parámetros:
```python
# CORRECTO:
cursor.execute("SELECT * FROM files WHERE name = ?", (name,))

# INCORRECTO (buscar y reportar):
cursor.execute(f"SELECT * FROM files WHERE name = '{name}'")
```

### 4.2 Path Traversal Prevention
Verificar validación de rutas:
```python
# Buscar en file_manager.py y backend.py
# Debe existir validación como:
if '..' in path or path.startswith('/'):
    raise SecurityError("Path traversal detected")
```

### 4.3 Input Sanitization
Verificar que todos los inputs de usuario se sanitizan antes de usar.

---

## REPORTE FINAL

Al terminar, genera un reporte con formato:

```
=== WORKER-1 REPORTE ===
Fecha: [FECHA]

MÓDULO CORE:
- config.py: [OK/ERROR] - [detalles]
- logger.py: [OK/ERROR] - [detalles]
- eventbus.py: [OK/ERROR] - [detalles]
- exceptions.py: [OK/ERROR] - [detalles]

MÓDULO SYSTEM:
- tray.py: [OK/ERROR] - [detalles]
- autostart.py: [OK/ERROR] - [detalles]
- shell_integration.py: [OK/ERROR] - [detalles]
- single_instance.py: [OK/ERROR] - [detalles]

MÓDULO EXPORT:
- base.py: [OK/ERROR] - [detalles]
- excel_exporter.py: [OK/ERROR] - [detalles]
- clipboard.py: [OK/ERROR] - [detalles]

BACKEND:
- backend.py: [OK/ERROR] - [detalles]
- classifier.py: [OK/ERROR] - [detalles]
- file_manager.py: [OK/ERROR] - [detalles]

SEGURIDAD:
- SQL Injection: [PROTEGIDO/VULNERABLE]
- Path Traversal: [PROTEGIDO/VULNERABLE]
- Input Sanitization: [IMPLEMENTADO/FALTANTE]

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
python -c "import core; import system; import export; print('Todos los módulos cargan correctamente')"
```

**COMIENZA LA VERIFICACIÓN AHORA.**
