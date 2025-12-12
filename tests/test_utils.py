"""
Tests para Utilidades - Smart Search
====================================

Tests para funciones de utilidades:
- format_file_size
- format_date
- Funciones auxiliares

Ejecutar con: python -m pytest tests/test_utils.py -v
"""

import os
import sys
import pytest
from datetime import datetime
from pathlib import Path

# Añadir el directorio padre al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from classifier import format_file_size, format_date


# ============================================================================
# TESTS PARA format_file_size
# ============================================================================

class TestFormatFileSize:
    """Tests para la función format_file_size"""

    def test_bytes_formatting(self):
        """Test: Formateo de bytes"""
        assert format_file_size(0) == "0 B"
        assert format_file_size(1) == "1 B"
        assert format_file_size(512) == "512 B"
        assert format_file_size(1023) == "1023 B"

    def test_kilobytes_formatting(self):
        """Test: Formateo de kilobytes"""
        assert format_file_size(1024) == "1.00 KB"
        assert format_file_size(1536) == "1.50 KB"
        assert format_file_size(2048) == "2.00 KB"
        assert format_file_size(1024 * 10) == "10.00 KB"

    def test_megabytes_formatting(self):
        """Test: Formateo de megabytes"""
        assert format_file_size(1024 * 1024) == "1.00 MB"
        assert format_file_size(1024 * 1024 * 2.5) == "2.50 MB"
        assert format_file_size(1024 * 1024 * 100) == "100.00 MB"

    def test_gigabytes_formatting(self):
        """Test: Formateo de gigabytes"""
        assert format_file_size(1024 * 1024 * 1024) == "1.00 GB"
        assert format_file_size(1024 * 1024 * 1024 * 5) == "5.00 GB"
        assert format_file_size(1024 * 1024 * 1024 * 100) == "100.00 GB"

    def test_terabytes_formatting(self):
        """Test: Formateo de terabytes"""
        assert format_file_size(1024 ** 4) == "1.00 TB"
        assert format_file_size(1024 ** 4 * 2) == "2.00 TB"

    def test_petabytes_formatting(self):
        """Test: Formateo de petabytes"""
        assert format_file_size(1024 ** 5) == "1.00 PB"

    def test_negative_size(self):
        """Test: Tamaños negativos son manejados"""
        # Puede lanzar error o retornar 0 B
        try:
            result = format_file_size(-100)
            assert result in ["0 B", "-100 B"]
        except ValueError:
            pass

    def test_float_size(self):
        """Test: Tamaños flotantes son manejados"""
        result = format_file_size(1536.5)
        assert "1.50 KB" in result or "1.5 KB" in result

    def test_very_large_size(self):
        """Test: Tamaños muy grandes"""
        # 1 Exabyte
        huge_size = 1024 ** 6
        result = format_file_size(huge_size)
        assert result is not None
        assert len(result) > 0


# ============================================================================
# TESTS PARA format_date
# ============================================================================

class TestFormatDate:
    """Tests para la función format_date"""

    def test_valid_timestamp(self):
        """Test: Timestamp válido"""
        # 2024-01-15 10:30:45
        timestamp = datetime(2024, 1, 15, 10, 30, 45).timestamp()
        result = format_date(timestamp)

        assert "2024" in result
        assert "01" in result or "1" in result
        assert "15" in result
        assert "10" in result or "30" in result

    def test_epoch_time(self):
        """Test: Timestamp en epoch (1970)"""
        timestamp = 0
        result = format_date(timestamp)
        assert "1970" in result or "1969" in result  # Depende de timezone

    def test_recent_date(self):
        """Test: Fecha reciente"""
        # Fecha de hace 1 día
        recent = (datetime.now() - __import__('datetime').timedelta(days=1)).timestamp()
        result = format_date(recent)

        assert result != "Fecha inválida"
        assert "202" in result  # Año 202X

    def test_future_date(self):
        """Test: Fecha futura"""
        # Fecha dentro de 1 año
        future = (datetime.now() + __import__('datetime').timedelta(days=365)).timestamp()
        result = format_date(future)

        assert result != "Fecha inválida"

    def test_invalid_timestamp(self):
        """Test: Timestamp inválido"""
        # Timestamp negativo extremo
        invalid = -999999999999
        result = format_date(invalid)
        assert result == "Fecha inválida" or "1" in result

    def test_string_timestamp(self):
        """Test: String como timestamp (debe fallar o convertir)"""
        try:
            # Intentar con string numérico
            result = format_date("1704974445")
            # Si convierte, debe retornar fecha válida
            assert "Fecha" in result or "20" in result
        except (TypeError, ValueError, AttributeError):
            # Rechazar es válido
            pass

    def test_none_timestamp(self):
        """Test: None como timestamp"""
        try:
            result = format_date(None)
            assert result == "Fecha inválida"
        except (TypeError, AttributeError):
            # Lanzar error también es válido
            pass

    def test_datetime_object(self):
        """Test: Objeto datetime en lugar de timestamp"""
        # format_date espera timestamp, no datetime
        dt = datetime(2024, 1, 15, 10, 30, 45)

        try:
            result = format_date(dt)
            # Si maneja datetime objects, ok
            assert "2024" in result
        except (TypeError, AttributeError):
            # Si requiere timestamp, usar .timestamp()
            result = format_date(dt.timestamp())
            assert "2024" in result


# ============================================================================
# TESTS DE RENDIMIENTO
# ============================================================================

class TestUtilsPerformance:
    """Tests de rendimiento de utilidades"""

    def test_format_file_size_performance(self):
        """Test: format_file_size es rápido"""
        import time

        start = time.time()
        for i in range(10000):
            format_file_size(i * 1024)
        duration = time.time() - start

        # Debe formatear 10k tamaños en menos de 0.1s
        assert duration < 0.1

    def test_format_date_performance(self):
        """Test: format_date es rápido"""
        import time

        timestamp = datetime.now().timestamp()
        start = time.time()
        for _ in range(10000):
            format_date(timestamp)
        duration = time.time() - start

        # Debe formatear 10k fechas en menos de 0.5s
        assert duration < 0.5


# ============================================================================
# TESTS DE EDGE CASES
# ============================================================================

class TestUtilsEdgeCases:
    """Tests de casos límite"""

    def test_format_size_boundary_values(self):
        """Test: Valores límite en format_file_size"""
        boundaries = [
            0,
            1,
            1023,
            1024,
            1024**2 - 1,
            1024**2,
            1024**3 - 1,
            1024**3,
        ]

        for size in boundaries:
            result = format_file_size(size)
            assert result is not None
            assert len(result) > 0
            assert " " in result  # Debe tener espacio entre número y unidad

    def test_format_date_boundary_timestamps(self):
        """Test: Timestamps límite"""
        # Timestamp mínimo seguro (1970-01-01)
        min_timestamp = 0
        result_min = format_date(min_timestamp)
        assert result_min is not None

        # Timestamp actual
        now_timestamp = datetime.now().timestamp()
        result_now = format_date(now_timestamp)
        assert "202" in result_now

        # Timestamp futuro razonable (2030)
        future_timestamp = datetime(2030, 1, 1).timestamp()
        result_future = format_date(future_timestamp)
        assert "2030" in result_future

    def test_format_size_precision(self):
        """Test: Precisión del formateo de tamaño"""
        # 1.5 KB
        size = 1536
        result = format_file_size(size)
        assert "1.50 KB" in result or "1.5 KB" in result

        # 2.75 MB
        size = int(1024 * 1024 * 2.75)
        result = format_file_size(size)
        assert "2.7" in result or "2.8" in result  # Puede redondear


# ============================================================================
# TESTS DE CONSISTENCIA
# ============================================================================

class TestUtilsConsistency:
    """Tests de consistencia de funciones"""

    def test_format_size_consistency(self):
        """Test: format_file_size retorna resultados consistentes"""
        size = 1024 * 1024 * 5  # 5 MB

        # Llamar múltiples veces debe retornar lo mismo
        results = [format_file_size(size) for _ in range(100)]
        assert all(r == results[0] for r in results)

    def test_format_date_consistency(self):
        """Test: format_date retorna resultados consistentes"""
        timestamp = datetime(2024, 1, 15, 10, 30, 45).timestamp()

        # Llamar múltiples veces debe retornar lo mismo
        results = [format_date(timestamp) for _ in range(100)]
        assert all(r == results[0] for r in results)

    def test_format_size_unit_progression(self):
        """Test: Unidades progresan correctamente"""
        # Verificar que las unidades cambian apropiadamente
        sizes_and_units = [
            (512, "B"),
            (1024, "KB"),
            (1024**2, "MB"),
            (1024**3, "GB"),
            (1024**4, "TB"),
        ]

        for size, expected_unit in sizes_and_units:
            result = format_file_size(size)
            assert expected_unit in result


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
