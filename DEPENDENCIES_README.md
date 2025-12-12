# Smart Search - Dependencies Management

Este documento describe cómo gestionar las dependencias del proyecto Smart Search.

## Archivos de Dependencias

### 1. **requirements.txt**
Archivo estándar de Python que lista todas las dependencias necesarias con sus versiones mínimas.

**Contenido:**
```
PyQt6>=6.6.0              # GUI framework - interfaz gráfica
PyQt6-Qt6>=6.6.0          # Qt6 bindings para PyQt6
PyQt6-sip>=13.6.0         # SIP bindings para PyQt6
pywin32>=305              # Windows API - acceso a funcionalidades de Windows
comtypes>=1.1.14          # COM interface support - soporte para interfaces COM
send2trash>=1.8.2         # Safe file deletion - eliminar archivos de forma segura a la papelera
```

## Métodos de Instalación

### Método 1: Usar el Script Batch (Recomendado para Windows)

```bash
install_dependencies.bat
```

**Ventajas:**
- Interfaz amigable
- Verifica que Python esté instalado
- Upgrade automático de pip
- Verificación post-instalación
- Manejo de errores mejorado

**Qué hace:**
1. Verifica que Python esté instalado
2. Verifica que pip esté disponible
3. Actualiza pip a la última versión
4. Instala todas las dependencias desde requirements.txt
5. Verifica que las librerías se importan correctamente

### Método 2: Usar pip directamente

```bash
python -m pip install -r requirements.txt
```

**Rápido y directo:**
- Instala todas las dependencias de requirements.txt
- Requiere que requirements.txt esté en el mismo directorio

### Método 3: Instalación Individual

```bash
python -m pip install PyQt6>=6.6.0 PyQt6-sip>=13.6.0 pywin32>=305 comtypes>=1.1.14 send2trash>=1.8.2
```

## Verificación de Dependencias

### Usar el Verificador de Dependencias

```bash
python check_dependencies.py
```

**Salida esperada:**
```
============================================================
Smart Search - Dependency Verification
============================================================

[OK] PyQt6                v6.6.0          GUI framework
[OK] PyQt6_sip            v13.6.0         PyQt6 SIP bindings
[OK] pywin32              v305            Windows API access
[OK] comtypes             v1.4.13         COM interface support
[OK] send2trash           v1.8.2          Safe file deletion to recycle bin

============================================================

Summary: 5/5 packages installed
Status: ALL DEPENDENCIES OK

You can now run Smart Search!
```

### Interpretación de Resultados

- **[OK]**: Dependencia instalada y versión compatible
- **[X] (version unknown)**: Instalada pero no se pudo detectar versión
- **[X] OUTDATED**: Instalada pero versión es anterior a la requerida
- **[X] NOT INSTALLED**: Falta instalar

## Requisitos Previos

1. **Python 3.8+** instalado
2. **pip** (gestor de paquetes de Python)
3. **Acceso a internet** para descargar los paquetes

### Verificar Python

```bash
python --version
python -m pip --version
```

## Solucionar Problemas

### Problema: "Python no está instalado o no está en PATH"

**Solución:**
1. Descargar Python desde https://www.python.org/
2. En el instalador, marcar: "Add Python to PATH"
3. Reiniciar la terminal/cmd
4. Verificar con: `python --version`

### Problema: Error de permisos al instalar

**Solución:**
```bash
python -m pip install --user -r requirements.txt
```

O ejecutar la terminal como Administrador.

### Problema: Versión de pip desactualizada

**Solución:**
```bash
python -m pip install --upgrade pip
```

### Problema: Módulo no encontrado al ejecutar Smart Search

1. Verificar: `python check_dependencies.py`
2. Si hay paquetes faltantes, ejecutar:
   ```bash
   python -m pip install -r requirements.txt
   ```
3. Verificar nuevamente con `python check_dependencies.py`

## Descripción de Dependencias

### PyQt6 (Requerido)
- **Versión mínima:** 6.6.0
- **Propósito:** Framework para crear la interfaz gráfica de usuario (GUI)
- **Componentes:** PyQt6, PyQt6-Qt6, PyQt6-sip
- **Uso:** Ventanas, botones, campos de entrada, tablas, diálogos

### pywin32 (Requerido)
- **Versión mínima:** 305
- **Propósito:** Acceso a APIs de Windows para interactuar con el sistema
- **Uso:** Búsqueda de archivos, acceso al registro, manejo de procesos

### comtypes (Requerido)
- **Versión mínima:** 1.1.14
- **Propósito:** Soporte para interfaces COM (Component Object Model)
- **Uso:** Interacción con componentes COM del sistema Windows

### send2trash (Opcional pero Recomendado)
- **Versión mínima:** 1.8.2
- **Propósito:** Eliminar archivos de forma segura a la papelera en lugar de borrarlos permanentemente
- **Uso:** Operaciones de eliminación de archivos

## Estructura de Directorios

```
smart_search/
├── requirements.txt                 # Dependencias del proyecto
├── install_dependencies.bat         # Script de instalación (Windows)
├── check_dependencies.py            # Script de verificación
├── DEPENDENCIES_README.md           # Este archivo
├── main.py                          # Punto de entrada principal
├── ui.py                            # Interfaz gráfica
├── backend.py                       # Lógica del backend
└── ... (otros archivos)
```

## Comandos Rápidos

| Tarea | Comando |
|-------|---------|
| Instalar todo | `install_dependencies.bat` |
| Verificar estado | `python check_dependencies.py` |
| Instalar manualmente | `python -m pip install -r requirements.txt` |
| Actualizar todas | `python -m pip install --upgrade -r requirements.txt` |
| Listar paquetes | `python -m pip list` |
| Ver detalles de un paquete | `python -m pip show PyQt6` |

## Actualizar Dependencias

### Actualizar un paquete específico
```bash
python -m pip install --upgrade PyQt6
```

### Actualizar todos los paquetes
```bash
python -m pip install --upgrade -r requirements.txt
```

## Entorno Virtual (Recomendado para Desarrollo)

Se recomienda usar un entorno virtual para evitar conflictos:

```bash
# Crear entorno virtual
python -m venv venv

# Activar (Windows)
venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Desactivar
deactivate
```

## Notas de Compatibilidad

- **Windows 10/11:** Totalmente compatible
- **Python 3.8-3.13:** Verificado y funcional
- **pip 21.0+:** Requerido para instalación adecuada

## Soporte y Ayuda

Para problemas con dependencias:

1. Ejecutar: `python check_dependencies.py`
2. Revisar el mensaje de error
3. Consultar la sección "Solucionar Problemas"
4. Si persiste, contactar al administrador del proyecto

---

**Última actualización:** Diciembre 2025
**Versión:** 1.0
