"""
Módulo de gestión del árbol de directorios indexados de Windows.

Proporciona funcionalidades para:
- Obtener árbol de directorios indexados por Windows Search
- Gestión de estados de checkboxes (checked, unchecked, partial)
- Propagación automática de estados en jerarquía
- Guardar/cargar configuración de directorios seleccionados
- Operaciones de archivos con progreso (copiar, mover)
- Abrir archivos y ubicaciones en explorador
"""

import os
import json
import shutil
import subprocess
import threading
import logging
from pathlib import Path
from typing import Dict, List, Set, Optional, Callable, Tuple
from enum import Enum
from dataclasses import dataclass, field, asdict
import winreg

# Configurar logging para seguridad
logger = logging.getLogger(__name__)

# Importar funciones de seguridad centralizadas
from core.security import (
    validate_path_safety,
    validate_subprocess_path,
    log_security_event,
    SecurityEvent,
    PROTECTED_PATHS
)


class CheckState(Enum):
    """Estados posibles de un checkbox en el árbol de directorios."""
    UNCHECKED = 0
    PARTIAL = 1
    CHECKED = 2


@dataclass
class DirectoryNode:
    """Representa un nodo en el árbol de directorios."""
    path: str
    name: str
    state: CheckState = CheckState.UNCHECKED
    children: Dict[str, 'DirectoryNode'] = field(default_factory=dict)
    parent: Optional['DirectoryNode'] = field(default=None, repr=False)

    def to_dict(self) -> dict:
        """Convierte el nodo a diccionario para serialización."""
        return {
            'path': self.path,
            'name': self.name,
            'state': self.state.value,
            'children': {k: v.to_dict() for k, v in self.children.items()}
        }

    @classmethod
    def from_dict(cls, data: dict, parent: Optional['DirectoryNode'] = None) -> 'DirectoryNode':
        """Crea un nodo desde un diccionario."""
        node = cls(
            path=data['path'],
            name=data['name'],
            state=CheckState(data.get('state', 0)),
            parent=parent
        )
        for child_name, child_data in data.get('children', {}).items():
            node.children[child_name] = cls.from_dict(child_data, parent=node)
        return node


class DirectoryTree:
    """
    Gestiona el árbol de directorios con estados de selección.

    Implementa propagación automática de estados:
    - Marcar padre -> marca todos los hijos
    - Desmarcar padre -> desmarca todos los hijos
    - Marcar todos los hijos -> marca el padre
    - Desmarcar algún hijo -> padre queda en estado partial
    """

    def __init__(self):
        self.root_nodes: Dict[str, DirectoryNode] = {}
        self._lock = threading.Lock()

    def add_directory(self, path: str) -> DirectoryNode:
        """
        Añade un directorio al árbol, creando la estructura jerárquica necesaria.

        Args:
            path: Ruta del directorio a añadir

        Returns:
            Nodo creado o existente
        """
        path = os.path.normpath(path)
        parts = Path(path).parts

        with self._lock:
            current_path = parts[0]

            # Crear o obtener nodo raíz
            if current_path not in self.root_nodes:
                self.root_nodes[current_path] = DirectoryNode(
                    path=current_path,
                    name=current_path
                )

            current_node = self.root_nodes[current_path]

            # Construir la jerarquía
            for part in parts[1:]:
                current_path = os.path.join(current_path, part)

                if part not in current_node.children:
                    new_node = DirectoryNode(
                        path=current_path,
                        name=part,
                        parent=current_node
                    )
                    current_node.children[part] = new_node

                current_node = current_node.children[part]

            return current_node

    def set_state(self, path: str, state: CheckState, propagate: bool = True):
        """
        Establece el estado de un nodo y propaga según las reglas.

        Args:
            path: Ruta del directorio
            state: Nuevo estado
            propagate: Si True, propaga a hijos y actualiza padres
        """
        node = self._find_node(path)
        if not node:
            return

        with self._lock:
            node.state = state

            if propagate:
                # Propagar hacia abajo (hijos)
                if state in (CheckState.CHECKED, CheckState.UNCHECKED):
                    self._propagate_to_children(node, state)

                # Actualizar hacia arriba (padres)
                self._update_parent_states(node)

    def _propagate_to_children(self, node: DirectoryNode, state: CheckState):
        """Propaga el estado a todos los hijos recursivamente."""
        for child in node.children.values():
            child.state = state
            self._propagate_to_children(child, state)

    def _update_parent_states(self, node: DirectoryNode):
        """Actualiza los estados de los padres basándose en los hijos."""
        if not node.parent:
            return

        parent = node.parent

        # Contar estados de los hijos
        checked_count = sum(1 for c in parent.children.values()
                          if c.state == CheckState.CHECKED)
        unchecked_count = sum(1 for c in parent.children.values()
                            if c.state == CheckState.UNCHECKED)
        total_children = len(parent.children)

        # Determinar estado del padre
        if checked_count == total_children:
            parent.state = CheckState.CHECKED
        elif unchecked_count == total_children:
            parent.state = CheckState.UNCHECKED
        else:
            parent.state = CheckState.PARTIAL

        # Continuar hacia arriba
        self._update_parent_states(parent)

    def _find_node(self, path: str) -> Optional[DirectoryNode]:
        """Busca un nodo por su ruta."""
        path = os.path.normpath(path)
        parts = Path(path).parts

        if parts[0] not in self.root_nodes:
            return None

        current_node = self.root_nodes[parts[0]]

        for part in parts[1:]:
            if part not in current_node.children:
                return None
            current_node = current_node.children[part]

        return current_node

    def get_selected_directories(self, include_partial: bool = False) -> List[str]:
        """
        Obtiene lista plana de directorios seleccionados.

        Args:
            include_partial: Si True, incluye directorios en estado partial

        Returns:
            Lista de rutas seleccionadas
        """
        selected = []

        def collect_selected(node: DirectoryNode):
            if node.state == CheckState.CHECKED:
                selected.append(node.path)
            elif node.state == CheckState.PARTIAL and include_partial:
                selected.append(node.path)

            for child in node.children.values():
                collect_selected(child)

        with self._lock:
            for root in self.root_nodes.values():
                collect_selected(root)

        return selected

    def get_checked_leaf_directories(self) -> List[str]:
        """
        Obtiene solo los directorios hoja (sin hijos) que están marcados.
        Optimización: evita incluir padres si todos sus hijos están marcados.

        Returns:
            Lista de rutas de directorios hoja seleccionados
        """
        selected = []

        def collect_leaves(node: DirectoryNode):
            if node.state == CheckState.CHECKED:
                if not node.children:
                    # Es hoja y está marcado
                    selected.append(node.path)
                else:
                    # Tiene hijos, buscar en ellos
                    for child in node.children.values():
                        collect_leaves(child)
            elif node.state == CheckState.PARTIAL:
                # Estado partial, explorar hijos
                for child in node.children.values():
                    collect_leaves(child)

        with self._lock:
            for root in self.root_nodes.values():
                collect_leaves(root)

        return selected

    def save_config(self, filepath: str):
        """
        Guarda la configuración del árbol a un archivo JSON.

        Args:
            filepath: Ruta del archivo de configuración
        """
        config = {
            'version': '1.0',
            'roots': {k: v.to_dict() for k, v in self.root_nodes.items()}
        }

        with self._lock:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

    def load_config(self, filepath: str) -> bool:
        """
        Carga la configuración del árbol desde un archivo JSON.

        Args:
            filepath: Ruta del archivo de configuración

        Returns:
            True si se cargó correctamente, False en caso contrario
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                config = json.load(f)

            with self._lock:
                self.root_nodes.clear()
                for root_name, root_data in config.get('roots', {}).items():
                    self.root_nodes[root_name] = DirectoryNode.from_dict(root_data)

            return True
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            print(f"Error loading config: {e}")
            return False

    def clear(self):
        """Limpia el árbol completamente."""
        with self._lock:
            self.root_nodes.clear()


class WindowsSearchIndexManager:
    """
    Gestiona la interacción con el índice de Windows Search.
    Obtiene información sobre unidades indexadas y directorios.
    """

    @staticmethod
    def get_indexed_drives() -> List[Tuple[str, bool]]:
        """
        Obtiene las unidades disponibles y su estado de indexación.

        Returns:
            Lista de tuplas (letra_unidad, está_indexada)
        """
        drives = []

        try:
            # Obtener unidades disponibles
            import string
            from ctypes import windll

            bitmask = windll.kernel32.GetLogicalDrives()
            for letter in string.ascii_uppercase:
                if bitmask & 1:
                    drive = f"{letter}:\\"
                    is_indexed = WindowsSearchIndexManager._is_drive_indexed(drive)
                    drives.append((drive, is_indexed))
                bitmask >>= 1
        except Exception as e:
            print(f"Error getting drives: {e}")

        return drives

    @staticmethod
    def _is_drive_indexed(drive: str) -> bool:
        """
        Verifica si una unidad está indexada por Windows Search.

        Args:
            drive: Ruta de la unidad (ej: "C:\\")

        Returns:
            True si está indexada, False en caso contrario
        """
        try:
            # Intentar acceder al registro de Windows Search
            key_path = r"SOFTWARE\Microsoft\Windows Search\CrawlScopeManager\Windows\SystemIndex\WorkingSetRules"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ) as key:
                i = 0
                while True:
                    try:
                        value_name = winreg.EnumValue(key, i)[0]
                        if value_name.upper().startswith(drive.upper()):
                            return True
                        i += 1
                    except OSError:
                        break
        except Exception:
            pass

        # Método alternativo: verificar si la unidad es del sistema
        import platform
        system_drive = os.environ.get('SystemDrive', 'C:')
        return drive.rstrip('\\').upper() == system_drive.upper()

    @staticmethod
    def get_indexed_directories(drive: str = None) -> List[str]:
        """
        Obtiene directorios indexados por Windows Search.

        Args:
            drive: Unidad específica a consultar (ej: "C:\\"). Si es None, obtiene todas.

        Returns:
            Lista de rutas de directorios indexados
        """
        directories = set()

        try:
            # Directorios comunes que Windows suele indexar
            user_profile = os.environ.get('USERPROFILE', '')
            if user_profile:
                common_indexed = [
                    os.path.join(user_profile, 'Desktop'),
                    os.path.join(user_profile, 'Documents'),
                    os.path.join(user_profile, 'Downloads'),
                    os.path.join(user_profile, 'Pictures'),
                    os.path.join(user_profile, 'Music'),
                    os.path.join(user_profile, 'Videos'),
                ]

                for directory in common_indexed:
                    if os.path.exists(directory):
                        if drive is None or directory.startswith(drive):
                            directories.add(directory)

            # Intentar obtener desde el registro
            directories.update(WindowsSearchIndexManager._get_indexed_from_registry(drive))

        except Exception as e:
            print(f"Error getting indexed directories: {e}")

        return sorted(list(directories))

    @staticmethod
    def _get_indexed_from_registry(drive: str = None) -> Set[str]:
        """Obtiene directorios indexados desde el registro de Windows."""
        indexed = set()

        try:
            key_path = r"SOFTWARE\Microsoft\Windows Search\CrawlScopeManager\Windows\SystemIndex\WorkingSetRules"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ) as key:
                i = 0
                while True:
                    try:
                        value_name, value_data, _ = winreg.EnumValue(key, i)
                        # value_name contiene la ruta
                        if value_name.startswith('file:///'):
                            path = value_name.replace('file:///', '').replace('/', '\\')
                            if drive is None or path.startswith(drive):
                                if os.path.exists(path):
                                    indexed.add(path)
                        i += 1
                    except OSError:
                        break
        except Exception:
            pass

        return indexed


# NOTE: validate_path_safety moved to core.security module


class FileOperations:
    """
    Operaciones de archivos con soporte para progreso y cancelación.
    """

    @staticmethod
    def copy_file(src: str, dst: str,
                  progress_callback: Optional[Callable[[int, int], None]] = None,
                  cancel_event: Optional[threading.Event] = None) -> bool:
        """
        Copia un archivo con reporte de progreso.

        Args:
            src: Ruta del archivo origen
            dst: Ruta del archivo destino
            progress_callback: Función callback(bytes_copied, total_bytes)
            cancel_event: Evento para cancelar la operación

        Returns:
            True si se copió correctamente, False en caso contrario
        """
        try:
            # Validar seguridad del path antes de operar
            validate_path_safety(src, dst)

            if not os.path.exists(src):
                raise FileNotFoundError(f"Source file not found: {src}")

            # Crear directorio destino si no existe
            os.makedirs(os.path.dirname(dst), exist_ok=True)

            file_size = os.path.getsize(src)
            bytes_copied = 0
            buffer_size = 1024 * 1024  # 1 MB

            with open(src, 'rb') as fsrc:
                with open(dst, 'wb') as fdst:
                    while True:
                        # Verificar cancelación
                        if cancel_event and cancel_event.is_set():
                            fdst.close()
                            os.remove(dst)
                            return False

                        buffer = fsrc.read(buffer_size)
                        if not buffer:
                            break

                        fdst.write(buffer)
                        bytes_copied += len(buffer)

                        # Reportar progreso
                        if progress_callback:
                            progress_callback(bytes_copied, file_size)

            # Copiar metadatos
            shutil.copystat(src, dst)
            return True

        except Exception as e:
            print(f"Error copying file: {e}")
            return False

    @staticmethod
    def copy_directory(src: str, dst: str,
                      progress_callback: Optional[Callable[[str, int, int], None]] = None,
                      cancel_event: Optional[threading.Event] = None) -> bool:
        """
        Copia un directorio completo con reporte de progreso.

        Args:
            src: Ruta del directorio origen
            dst: Ruta del directorio destino
            progress_callback: Función callback(current_file, files_done, total_files)
            cancel_event: Evento para cancelar la operación

        Returns:
            True si se copió correctamente, False en caso contrario
        """
        try:
            # Validar seguridad del path antes de operar
            validate_path_safety(src, dst)

            if not os.path.exists(src):
                raise FileNotFoundError(f"Source directory not found: {src}")

            # Contar archivos totales
            total_files = sum(1 for _, _, files in os.walk(src) for _ in files)
            files_done = 0

            # Crear directorio destino
            os.makedirs(dst, exist_ok=True)

            for root, dirs, files in os.walk(src):
                # Verificar cancelación
                if cancel_event and cancel_event.is_set():
                    return False

                # Crear subdirectorios
                for directory in dirs:
                    src_dir = os.path.join(root, directory)
                    dst_dir = os.path.join(dst, os.path.relpath(src_dir, src))
                    os.makedirs(dst_dir, exist_ok=True)

                # Copiar archivos
                for file in files:
                    if cancel_event and cancel_event.is_set():
                        return False

                    src_file = os.path.join(root, file)
                    dst_file = os.path.join(dst, os.path.relpath(src_file, src))

                    # Copiar archivo
                    shutil.copy2(src_file, dst_file)
                    files_done += 1

                    # Reportar progreso
                    if progress_callback:
                        progress_callback(src_file, files_done, total_files)

            return True

        except Exception as e:
            print(f"Error copying directory: {e}")
            return False

    @staticmethod
    def move_file(src: str, dst: str,
                  progress_callback: Optional[Callable[[int, int], None]] = None,
                  cancel_event: Optional[threading.Event] = None) -> bool:
        """
        Mueve un archivo con reporte de progreso.

        Args:
            src: Ruta del archivo origen
            dst: Ruta del archivo destino
            progress_callback: Función callback(bytes_moved, total_bytes)
            cancel_event: Evento para cancelar la operación

        Returns:
            True si se movió correctamente, False en caso contrario
        """
        try:
            # Validar seguridad del path antes de operar
            validate_path_safety(src, dst)

            # Intentar mover directamente (rápido si está en la misma unidad)
            try:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.move(src, dst)
                return True
            except (OSError, shutil.Error):
                # Si falla, copiar y luego eliminar
                if FileOperations.copy_file(src, dst, progress_callback, cancel_event):
                    os.remove(src)
                    return True
                return False

        except Exception as e:
            print(f"Error moving file: {e}")
            return False

    @staticmethod
    def move_directory(src: str, dst: str,
                      progress_callback: Optional[Callable[[str, int, int], None]] = None,
                      cancel_event: Optional[threading.Event] = None) -> bool:
        """
        Mueve un directorio completo con reporte de progreso.

        Args:
            src: Ruta del directorio origen
            dst: Ruta del directorio destino
            progress_callback: Función callback(current_file, files_done, total_files)
            cancel_event: Evento para cancelar la operación

        Returns:
            True si se movió correctamente, False en caso contrario
        """
        try:
            # Validar seguridad del path antes de operar
            validate_path_safety(src, dst)

            # Intentar mover directamente
            try:
                shutil.move(src, dst)
                return True
            except (OSError, shutil.Error):
                # Si falla, copiar y luego eliminar
                if FileOperations.copy_directory(src, dst, progress_callback, cancel_event):
                    shutil.rmtree(src)
                    return True
                return False

        except Exception as e:
            print(f"Error moving directory: {e}")
            return False

    @staticmethod
    def open_file(filepath: str) -> bool:
        """
        Abre un archivo con su aplicación predeterminada.

        Args:
            filepath: Ruta del archivo a abrir

        Returns:
            True si se abrió correctamente, False en caso contrario
        """
        try:
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"File not found: {filepath}")

            os.startfile(filepath)
            return True

        except Exception as e:
            print(f"Error opening file: {e}")
            return False

    @staticmethod
    def open_location(filepath: str) -> bool:
        """
        Abre la ubicación del archivo en el explorador de Windows.

        Args:
            filepath: Ruta del archivo cuya ubicación se quiere abrir

        Returns:
            True si se abrió correctamente, False en caso contrario
        """
        try:
            # Validar y sanitizar el path
            validated_path = validate_subprocess_path(filepath)

            # Usar explorer con /select para resaltar el archivo
            # Usar lista de argumentos (NO string) para prevenir command injection
            subprocess.run(
                ['explorer', '/select,', str(validated_path)],
                check=True,
                timeout=5,
                shell=False  # CRITICAL: Never use shell=True
            )
            return True

        except subprocess.TimeoutExpired:
            logger.error(f"Timeout opening location: {filepath}")
            return False
        except Exception as e:
            logger.error(f"Error opening location: {e}")
            return False


# Funciones de utilidad para facilitar el uso del módulo

def create_tree_from_indexed_directories(drives: Optional[List[str]] = None) -> DirectoryTree:
    """
    Crea un árbol de directorios a partir de los directorios indexados.

    Args:
        drives: Lista de unidades a incluir (ej: ["C:\\", "D:\\"]). Si es None, incluye todas.

    Returns:
        DirectoryTree poblado con los directorios indexados
    """
    tree = DirectoryTree()

    if drives is None:
        # Obtener todas las unidades indexadas
        indexed_drives = WindowsSearchIndexManager.get_indexed_drives()
        drives = [drive for drive, is_indexed in indexed_drives if is_indexed]

    for drive in drives:
        directories = WindowsSearchIndexManager.get_indexed_directories(drive)
        for directory in directories:
            tree.add_directory(directory)

    return tree


def get_search_scope_from_config(config_path: str) -> List[str]:
    """
    Obtiene el ámbito de búsqueda desde un archivo de configuración.

    Args:
        config_path: Ruta al archivo de configuración del árbol

    Returns:
        Lista de directorios seleccionados para búsqueda
    """
    tree = DirectoryTree()
    if tree.load_config(config_path):
        return tree.get_checked_leaf_directories()
    return []


if __name__ == "__main__":
    # Ejemplo de uso
    print("=== Windows Search Index Manager ===\n")

    # Obtener unidades indexadas
    print("Unidades disponibles:")
    drives = WindowsSearchIndexManager.get_indexed_drives()
    for drive, is_indexed in drives:
        status = "Indexada" if is_indexed else "No indexada"
        print(f"  {drive} - {status}")

    print("\n=== DirectoryTree Example ===\n")

    # Crear árbol desde directorios indexados
    tree = create_tree_from_indexed_directories()

    # Ejemplo: marcar algunos directorios
    user_profile = os.environ.get('USERPROFILE', '')
    if user_profile:
        documents = os.path.join(user_profile, 'Documents')
        if os.path.exists(documents):
            print(f"Marcando: {documents}")
            tree.set_state(documents, CheckState.CHECKED)

    # Obtener directorios seleccionados
    selected = tree.get_checked_leaf_directories()
    print(f"\nDirectorios seleccionados: {len(selected)}")
    for directory in selected[:5]:  # Mostrar solo los primeros 5
        print(f"  {directory}")

    # Guardar configuración
    config_path = os.path.join(os.path.dirname(__file__), 'directory_config.json')
    tree.save_config(config_path)
    print(f"\nConfiguración guardada en: {config_path}")

    print("\n=== FileOperations Example ===\n")

    # Ejemplo de callback de progreso
    def progress_callback(current, total):
        percent = (current / total * 100) if total > 0 else 0
        print(f"\rProgreso: {percent:.1f}% ({current}/{total} bytes)", end='')

    print("Módulo listo para usar.")
