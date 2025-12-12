"""
Smart Search - Test Mocks
==========================

Mocks para simular componentes de Windows Search API y otros servicios externos.
"""

from unittest.mock import Mock, MagicMock
from datetime import datetime


class MockADORecordset:
    """Mock de ADODB.Recordset para tests"""

    def __init__(self, records=None):
        self.records = records or []
        self.current_index = 0
        self._eof = len(self.records) == 0

    @property
    def EOF(self):
        """Simula EOF de ADO Recordset"""
        return self.current_index >= len(self.records)

    def MoveNext(self):
        """Simula MoveNext de ADO Recordset"""
        self.current_index += 1

    def Fields(self, field_name):
        """Simula acceso a campos"""
        if self.current_index < len(self.records):
            record = self.records[self.current_index]
            field = Mock()
            field.Value = record.get(field_name)
            return field
        raise IndexError("No more records")

    def Close(self):
        """Simula cierre del recordset"""
        pass


class MockADOConnection:
    """Mock de ADODB.Connection para tests"""

    def __init__(self):
        self.is_open = False
        self.connection_string = None

    def Open(self, connection_string):
        """Simula apertura de conexión"""
        self.connection_string = connection_string
        self.is_open = True

    def Close(self):
        """Simula cierre de conexión"""
        self.is_open = False


class MockWin32ComClient:
    """Mock de win32com.client para tests"""

    @staticmethod
    def Dispatch(prog_id):
        """Simula Dispatch de COM"""
        if prog_id == "ADODB.Connection":
            return MockADOConnection()
        elif prog_id == "ADODB.Recordset":
            return MockADORecordset()
        else:
            return Mock()


class MockPythonCOM:
    """Mock de pythoncom para tests"""

    @staticmethod
    def CoInitialize():
        """Simula inicialización COM"""
        pass

    @staticmethod
    def CoUninitialize():
        """Simula finalización COM"""
        pass


def create_mock_search_records(count=10):
    """
    Crea registros de búsqueda simulados

    Args:
        count: Número de registros a crear

    Returns:
        Lista de diccionarios simulando registros ADO
    """
    records = []
    for i in range(count):
        records.append({
            'System.ItemPathDisplay': f'C:\\Users\\Test\\Documents\\file{i}.txt',
            'System.FileName': f'file{i}.txt',
            'System.Size': 1024 * (i + 1),
            'System.DateModified': datetime.now(),
            'System.DateCreated': datetime.now(),
            'System.FileExtension': '.txt',
            'System.IsFolder': False
        })
    return records


def create_mock_backend():
    """
    Crea un backend mock completo para tests

    Returns:
        Mock de SearchBackend configurado
    """
    backend = Mock()

    # Configurar métodos
    backend.search = Mock(return_value=[])
    backend._get_connection = Mock(return_value=MockADOConnection())
    backend._parse_record = Mock()

    return backend


def create_mock_directory_tree():
    """
    Crea un DirectoryTree mock para tests

    Returns:
        Mock de DirectoryTree configurado
    """
    tree = Mock()

    # Configurar métodos comunes
    tree.add_directory = Mock()
    tree.set_state = Mock()
    tree.get_checked_paths = Mock(return_value=[])
    tree.propagate_state_up = Mock()
    tree.propagate_state_down = Mock()

    return tree


def create_mock_file_operations():
    """
    Crea FileOperations mock para tests

    Returns:
        Mock de FileOperations configurado
    """
    ops = Mock()

    # Configurar métodos
    ops.copy_file = Mock(return_value=True)
    ops.move_file = Mock(return_value=True)
    ops.delete_file = Mock(return_value=True)
    ops.open_file = Mock(return_value=True)
    ops.open_file_location = Mock(return_value=True)

    return ops


def create_mock_qt_application():
    """
    Crea QApplication mock para tests de UI

    Returns:
        Mock de QApplication
    """
    app = Mock()

    # Configurar métodos básicos
    app.exec = Mock(return_value=0)
    app.quit = Mock()
    app.processEvents = Mock()

    return app


def create_mock_qt_widget():
    """
    Crea QWidget mock para tests de UI

    Returns:
        Mock de QWidget
    """
    widget = Mock()

    # Configurar señales y slots comunes
    widget.show = Mock()
    widget.hide = Mock()
    widget.close = Mock()
    widget.update = Mock()
    widget.repaint = Mock()

    return widget


class MockSearchWorker:
    """Mock de SearchWorker (QThread) para tests"""

    def __init__(self):
        self.is_running = False
        self.progress = Mock()
        self.result = Mock()
        self.finished = Mock()
        self.error = Mock()

    def start(self):
        """Simula inicio del worker"""
        self.is_running = True

    def stop(self):
        """Simula detención del worker"""
        self.is_running = False

    def run(self):
        """Simula ejecución del worker"""
        pass


def setup_win32_mocks():
    """
    Configura todos los mocks necesarios para simular Windows API

    Returns:
        Dict con todos los mocks configurados
    """
    import sys
    from unittest.mock import MagicMock

    # Mock de win32com
    sys.modules['win32com'] = MagicMock()
    sys.modules['win32com.client'] = MagicMock()
    sys.modules['win32com.client'].Dispatch = MockWin32ComClient.Dispatch

    # Mock de pythoncom
    sys.modules['pythoncom'] = MagicMock()
    sys.modules['pythoncom'].CoInitialize = MockPythonCOM.CoInitialize
    sys.modules['pythoncom'].CoUninitialize = MockPythonCOM.CoUninitialize

    # Mock de comtypes
    sys.modules['comtypes'] = MagicMock()
    sys.modules['comtypes.client'] = MagicMock()

    return {
        'win32com': sys.modules['win32com'],
        'pythoncom': sys.modules['pythoncom'],
        'comtypes': sys.modules['comtypes']
    }


def teardown_win32_mocks():
    """Limpia los mocks de Windows API"""
    import sys

    modules_to_remove = [
        'win32com',
        'win32com.client',
        'pythoncom',
        'comtypes',
        'comtypes.client'
    ]

    for module in modules_to_remove:
        if module in sys.modules:
            del sys.modules[module]
