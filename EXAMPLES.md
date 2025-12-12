# Smart Search - Ejemplos de Uso

## Casos de Uso Prácticos

### 1. Buscar archivos Python con "test" en el nombre

**Pasos**:
1. Abrir Smart Search
2. En el árbol izquierdo, marcar `C:\Users\<tu usuario>\Documents`
3. En la barra de búsqueda: `python * test`
4. Marcar checkbox "Filename"
5. Click "Search"

**Resultado**: Todos los archivos .py que contengan "python" Y "test" en el nombre

**Ejemplo de resultados**:
```
test_backend.py
python_test_suite.py
my_python_test.py
```

---

### 2. Buscar documentos PDF que contengan "invoice"

**Pasos**:
1. Marcar directorios relevantes (Documents, Downloads)
2. Búsqueda: `*.pdf * invoice`
3. Marcar "Filename" y "Content"
4. Click "Search"

**Resultado**: PDFs con "invoice" en nombre o contenido

**Pestañas**:
- Documentos (15) ← Aquí aparecerán los PDFs

---

### 3. Buscar imágenes PNG en Downloads

**Pasos**:
1. Marcar solo `Downloads`
2. Búsqueda: `*.png`
3. Solo "Filename"
4. Search

**Resultado**: Todas las imágenes PNG en Downloads

**Pestañas**:
- Imágenes (47) ← Aquí aparecerán

---

### 4. Buscar código JavaScript con "react" en el contenido

**Pasos**:
1. Marcar proyecto: `C:\projects\my-app`
2. Búsqueda: `*.js * *.jsx`
3. Marcar "Content"
4. Search

**Resultado**: Archivos JS/JSX que contengan "react" en el código

**Pestañas**:
- Código (123) ← Aquí aparecerán

---

### 5. Buscar archivos modificados recientemente (con "2024")

**Pasos**:
1. Marcar directorios
2. Búsqueda: `2024`
3. "Filename"
4. Search
5. Click en columna "Modified" para ordenar

**Resultado**: Archivos con "2024" en nombre, ordenados por fecha

---

## Operaciones sobre Resultados

### Abrir Archivo

**Método 1**: Botón
1. Seleccionar archivo(s) en tabla
2. Click "Open"
3. Se abre con aplicación predeterminada

**Método 2**: Atajo
1. Seleccionar archivo(s)
2. `Ctrl+O`

**Método 3**: Doble click
1. Doble click en archivo

**Límite**: Máximo 10 archivos a la vez

---

### Abrir Ubicación en Explorador

**Uso**:
1. Seleccionar archivo
2. Click "Open Location"
3. Se abre Explorer con archivo resaltado

**Útil para**:
- Ver archivos relacionados
- Verificar contexto del archivo
- Operaciones manuales adicionales

---

### Copiar Archivos

**Ejemplo**: Copiar todos los PDFs encontrados a USB

**Pasos**:
1. Buscar: `*.pdf`
2. Ir a pestaña "Documentos"
3. `Ctrl+A` (seleccionar todo)
4. Click "Copy To..."
5. Seleccionar `E:\backup\` (USB)
6. Confirmar

**Resultado**: Todos los PDFs copiados a USB

---

### Mover Archivos

**Ejemplo**: Mover screenshots a carpeta organizada

**Pasos**:
1. Buscar: `screenshot * *.png`
2. Seleccionar archivos deseados
3. Click "Move To..."
4. Seleccionar `C:\Users\<user>\Pictures\Screenshots`
5. Confirmar diálogo
6. Archivos movidos

**Advertencia**: Requiere confirmación (es destructivo)

---

### Copiar Rutas al Portapapeles

**Uso**:
1. Seleccionar archivo(s)
2. Click derecho → "Copy Path"
3. Pegar en otro programa

**Resultado en portapapeles**:
```
C:\Users\<user>\Documents\file1.pdf
C:\Users\<user>\Downloads\file2.pdf
C:\Users\<user>\Desktop\file3.pdf
```

**Útil para**:
- Scripts
- Documentación
- Compartir rutas

---

## Gestión de Directorios

### Seleccionar Directorio Completo

**Uso**:
1. Click en checkbox del directorio padre
2. Todos los subdirectorios se marcan automáticamente

**Ejemplo**:
```
☑ Documents
  ☑ Projects
  ☑ Personal
  ☑ Work
```

---

### Selección Parcial

**Uso**:
1. Expandir directorio
2. Marcar solo algunos subdirectorios

**Resultado**:
```
⊡ Documents          ← Parcial (algunos hijos marcados)
  ☑ Projects        ← Marcado
  ☐ Personal        ← No marcado
  ☑ Work            ← Marcado
```

---

### Guardar Selección

**Automático**: La selección se guarda al cerrar la aplicación

**Manual**:
- La configuración se guarda en: `~/.smart_search/directory_tree.json`

**Restauración**: Al abrir la app, se restaura la última selección

---

## Uso de Tema

### Activar Tema Oscuro

**Pasos**:
1. Click "Dark Mode"
2. Tema cambia inmediatamente
3. Preferencia se guarda

**Ventajas**:
- Menos fatiga visual
- Mejor para trabajo nocturno
- Estilo moderno

---

### Volver a Tema Claro

**Pasos**:
1. Click "Light Mode"
2. Vuelve a tema estándar

---

## Búsquedas Avanzadas

### Combinaciones de Palabras

**Ejemplo 1**: Buscar archivos de factura de 2024
```
invoice * 2024
```

**Ejemplo 2**: Buscar notas de reunión
```
meeting * notes * *.txt
```

**Ejemplo 3**: Buscar código Python de tests
```
*.py * test * unit
```

---

### Búsqueda por Extensión

**Documentos Office**:
```
*.docx * *.xlsx * *.pptx
```

**Imágenes**:
```
*.jpg * *.png * *.gif
```

**Código**:
```
*.py * *.js * *.ts
```

**Archivos comprimidos**:
```
*.zip * *.rar * *.7z
```

---

### Búsqueda en Contenido

**Buscar código con palabra clave**:
1. Búsqueda: `function * async`
2. Marcar "Content"
3. Buscar en directorio de proyecto

**Buscar documentos con frase**:
1. Búsqueda: `quarterly report`
2. Marcar "Content"
3. Buscar en Documents

---

## Workflow Típicos

### 1. Organizar Screenshots

```
Búsqueda: screenshot * *.png
Directorio: Desktop
Operación: Move To → Pictures\Screenshots
```

---

### 2. Backup de Proyectos

```
Búsqueda: *.py * *.js * *.json
Directorio: C:\projects
Operación: Copy To → E:\backup\projects
```

---

### 3. Limpiar Descargas

```
Búsqueda: *.exe * *.msi
Directorio: Downloads
Revisión: Abrir ubicación de cada uno
Decisión: Mover a carpeta instaladores o eliminar
```

---

### 4. Encontrar Documentación

```
Búsqueda: readme * *.md * *.txt
Directorio: Proyectos
Operación: Abrir archivos relevantes
```

---

### 5. Recopilar Imágenes de Proyecto

```
Búsqueda: *.png * *.jpg * *.svg
Directorio: C:\projects\my-app
Operación: Copy To → Carpeta de recursos
```

---

## Atajos de Productividad

### Teclado

| Acción | Atajo |
|--------|-------|
| Enfocar búsqueda | `Ctrl+F` |
| Ejecutar búsqueda | `Enter` |
| Abrir seleccionados | `Ctrl+O` |
| Limpiar resultados | `Ctrl+L` |
| Seleccionar todo | `Ctrl+A` |

---

### Mouse

| Acción | Método |
|--------|--------|
| Ordenar resultados | Click en encabezado de columna |
| Menú contextual | Click derecho en archivo |
| Selección múltiple | `Ctrl+Click` |
| Rango de selección | `Shift+Click` |

---

## Tips y Trucos

### 1. Refinar Búsquedas

Si hay demasiados resultados:
- Añadir más palabras clave con `*`
- Reducir directorios seleccionados
- Usar extensión específica

---

### 2. Búsqueda Rápida

Para búsquedas frecuentes:
1. Seleccionar directorios comunes
2. La selección se guarda
3. Solo cambiar términos de búsqueda

---

### 3. Organización por Pestañas

Usar las pestañas para:
- Ver solo un tipo de archivo
- Comparar cantidades (ej: "Documentos (150)")
- Exportar por tipo

---

### 4. Verificar Antes de Mover

Antes de mover archivos:
1. Usar "Open Location" para verificar
2. Comprobar que no están en uso
3. Verificar destino correcto

---

### 5. Limpiar Resultados Frecuentemente

Para mantener rendimiento:
- Click "Clear Results" entre búsquedas
- `Ctrl+L` es más rápido

---

## Solución de Problemas Comunes

### No encuentra archivos que sé que existen

**Solución 1**: Verificar que el directorio esté marcado

**Solución 2**: Verificar que Windows Search esté indexando ese directorio
- Configuración → Buscar → Opciones de búsqueda

**Solución 3**: Esperar a que termine la indexación

---

### Búsqueda muy lenta

**Causa**: Búsqueda en contenido en directorios grandes

**Solución**:
- Desmarcar "Content" si no es necesario
- Reducir directorios seleccionados
- Solo "Filename" es mucho más rápido

---

### Archivo no se abre

**Causa**: No hay aplicación asociada

**Solución**:
- Click derecho → "Open Location"
- Abrir manualmente desde Explorer

---

## Casos de Uso Avanzados

### Buscar Duplicados (manual)

1. Buscar por nombre común: `report`
2. Ordenar por tamaño
3. Identificar archivos idénticos
4. Usar "Open Location" para comparar

---

### Migrar Archivos de Proyecto

1. Buscar todos los archivos: `*`
2. Ir a pestaña "Código"
3. Seleccionar todos
4. Copy To → Nuevo directorio

---

### Auditoría de Archivos

1. Buscar por extensión: `*.exe`
2. Ordenar por fecha
3. Revisar ejecutables recientes
4. Verificar seguridad

---

## Conclusión

Smart Search es una herramienta potente para:
- Encontrar archivos rápidamente
- Organizar archivos por tipo
- Realizar operaciones masivas
- Mantener directorios limpios

**Recuerda**:
- Usar `*` para múltiples palabras
- Marcar directorios relevantes
- Aprovechar las pestañas de clasificación
- Guardar tiempo con atajos

---

**Smart Search v1.0.0**
Para más información, ver `USAGE_GUIDE.md`
