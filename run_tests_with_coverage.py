"""
Script para ejecutar tests con cobertura
========================================

Ejecuta todos los tests y genera reporte de cobertura.
"""

import sys
import subprocess
import os

def main():
    """Ejecuta tests con cobertura"""

    print("="*70)
    print("EJECUTANDO TESTS CON COBERTURA")
    print("="*70)
    print()

    # Cambiar al directorio del proyecto
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Ejecutar pytest con cobertura
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/",
        "--cov=.",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "--cov-config=.coveragerc",
        "-v",
        "--tb=short"
    ]

    try:
        result = subprocess.run(cmd, check=False)

        print()
        print("="*70)
        print("REPORTE GENERADO")
        print("="*70)
        print("Reporte HTML: htmlcov/index.html")
        print("="*70)

        return result.returncode

    except FileNotFoundError:
        print("ERROR: pytest o pytest-cov no instalado")
        print("Instalar con: pip install pytest pytest-cov")
        return 1

if __name__ == "__main__":
    sys.exit(main())
