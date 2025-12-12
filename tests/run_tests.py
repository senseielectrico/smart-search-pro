"""
Smart Search - Test Runner
===========================

Script para ejecutar la suite completa de tests con diferentes configuraciones.

Uso:
    python tests/run_tests.py                 # Ejecutar todos los tests
    python tests/run_tests.py --unit          # Solo tests unitarios
    python tests/run_tests.py --integration   # Solo tests de integración
    python tests/run_tests.py --performance   # Solo tests de rendimiento
    python tests/run_tests.py --coverage      # Con reporte de cobertura
    python tests/run_tests.py --html          # Generar reporte HTML
"""

import sys
import os
import subprocess
import argparse
import time
from pathlib import Path
from datetime import datetime


class Colors:
    """Códigos de color para output en consola"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class TestRunner:
    """Ejecutor de tests con múltiples opciones"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.absolute()
        self.tests_dir = self.project_root / "tests"
        self.results = {
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'errors': 0
        }

    def print_header(self, text):
        """Imprime encabezado destacado"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{text.center(70)}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")

    def print_section(self, text):
        """Imprime sección"""
        print(f"\n{Colors.CYAN}{Colors.BOLD}{text}{Colors.ENDC}")
        print(f"{Colors.CYAN}{'-'*len(text)}{Colors.ENDC}")

    def print_success(self, text):
        """Imprime mensaje de éxito"""
        print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")

    def print_error(self, text):
        """Imprime mensaje de error"""
        print(f"{Colors.RED}✗ {text}{Colors.ENDC}")

    def print_warning(self, text):
        """Imprime advertencia"""
        print(f"{Colors.YELLOW}⚠ {text}{Colors.ENDC}")

    def check_dependencies(self):
        """Verifica que las dependencias necesarias estén instaladas"""
        self.print_section("Verificando dependencias...")

        dependencies = {
            'pytest': 'pytest',
            'pytest-cov': 'pytest-cov',
            'pytest-html': 'pytest-html',
            'psutil': 'psutil'
        }

        missing = []
        for package, import_name in dependencies.items():
            try:
                __import__(import_name.replace('-', '_'))
                self.print_success(f"{package} instalado")
            except ImportError:
                missing.append(package)
                self.print_error(f"{package} NO instalado")

        if missing:
            self.print_warning(f"\nPaquetes faltantes: {', '.join(missing)}")
            print(f"Instalar con: pip install {' '.join(missing)}")
            return False

        return True

    def run_pytest(self, args):
        """Ejecuta pytest con los argumentos especificados"""
        cmd = ['pytest'] + args
        print(f"\n{Colors.BLUE}Ejecutando: {' '.join(cmd)}{Colors.ENDC}\n")

        start_time = time.time()
        result = subprocess.run(cmd, cwd=str(self.project_root))
        duration = time.time() - start_time

        print(f"\n{Colors.CYAN}Duración: {duration:.2f} segundos{Colors.ENDC}")

        return result.returncode == 0

    def run_all_tests(self, verbose=True, coverage=False, html_report=False):
        """Ejecuta todos los tests"""
        self.print_section("Ejecutando suite completa de tests")

        args = [
            'tests/test_suite.py',
            '-v' if verbose else '-q',
            '--tb=short',
            '--color=yes'
        ]

        if coverage:
            args.extend([
                '--cov=.',
                '--cov-report=term-missing',
                '--cov-report=html:coverage_html'
            ])

        if html_report:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            args.append(f'--html=test_report_{timestamp}.html')
            args.append('--self-contained-html')

        return self.run_pytest(args)

    def run_unit_tests(self, verbose=True):
        """Ejecuta solo tests unitarios"""
        self.print_section("Ejecutando tests unitarios")

        args = [
            'tests/test_suite.py',
            '-v' if verbose else '-q',
            '-k', 'Test and not Integration and not Performance and not UI',
            '--tb=short'
        ]

        return self.run_pytest(args)

    def run_integration_tests(self, verbose=True):
        """Ejecuta solo tests de integración"""
        self.print_section("Ejecutando tests de integración")

        args = [
            'tests/test_suite.py',
            '-v' if verbose else '-q',
            '-k', 'Integration',
            '--tb=short'
        ]

        return self.run_pytest(args)

    def run_performance_tests(self, verbose=True):
        """Ejecuta solo tests de rendimiento"""
        self.print_section("Ejecutando tests de rendimiento")

        args = [
            'tests/test_suite.py',
            '-v' if verbose else '-q',
            '-k', 'Performance',
            '--tb=short'
        ]

        return self.run_pytest(args)

    def run_ui_tests(self, verbose=True):
        """Ejecuta solo tests de UI"""
        self.print_section("Ejecutando tests de UI")

        args = [
            'tests/test_suite.py',
            '-v' if verbose else '-q',
            '-k', 'UI',
            '--tb=short'
        ]

        return self.run_pytest(args)

    def generate_coverage_report(self):
        """Genera reporte de cobertura detallado"""
        self.print_section("Generando reporte de cobertura")

        args = [
            'tests/test_suite.py',
            '--cov=.',
            '--cov-report=term-missing',
            '--cov-report=html:coverage_html',
            '--cov-report=json:coverage.json',
            '-v'
        ]

        success = self.run_pytest(args)

        if success:
            self.print_success("Reporte de cobertura generado en: coverage_html/index.html")

        return success

    def run_quick_test(self):
        """Ejecuta un test rápido para verificación"""
        self.print_section("Ejecutando test rápido")

        args = [
            'tests/test_suite.py::TestSearchResult::test_creation_basic',
            '-v'
        ]

        return self.run_pytest(args)

    def print_summary(self, success, duration):
        """Imprime resumen final"""
        self.print_header("RESUMEN FINAL")

        if success:
            self.print_success("Todos los tests pasaron exitosamente")
        else:
            self.print_error("Algunos tests fallaron")

        print(f"\n{Colors.CYAN}Tiempo total: {duration:.2f} segundos{Colors.ENDC}")


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description='Ejecutar tests de Smart Search',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--unit',
        action='store_true',
        help='Ejecutar solo tests unitarios'
    )

    parser.add_argument(
        '--integration',
        action='store_true',
        help='Ejecutar solo tests de integración'
    )

    parser.add_argument(
        '--performance',
        action='store_true',
        help='Ejecutar solo tests de rendimiento'
    )

    parser.add_argument(
        '--ui',
        action='store_true',
        help='Ejecutar solo tests de UI'
    )

    parser.add_argument(
        '--coverage',
        action='store_true',
        help='Generar reporte de cobertura'
    )

    parser.add_argument(
        '--html',
        action='store_true',
        help='Generar reporte HTML'
    )

    parser.add_argument(
        '--quick',
        action='store_true',
        help='Ejecutar test rápido de verificación'
    )

    parser.add_argument(
        '--check-deps',
        action='store_true',
        help='Solo verificar dependencias'
    )

    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Modo silencioso'
    )

    args = parser.parse_args()

    runner = TestRunner()

    # Banner
    runner.print_header("SMART SEARCH - TEST SUITE")
    print(f"{Colors.CYAN}Directorio del proyecto: {runner.project_root}{Colors.ENDC}")
    print(f"{Colors.CYAN}Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}")

    # Verificar dependencias
    if args.check_deps:
        return 0 if runner.check_dependencies() else 1

    if not runner.check_dependencies():
        return 1

    # Ejecutar tests según argumentos
    start_time = time.time()
    verbose = not args.quiet

    try:
        if args.quick:
            success = runner.run_quick_test()
        elif args.unit:
            success = runner.run_unit_tests(verbose)
        elif args.integration:
            success = runner.run_integration_tests(verbose)
        elif args.performance:
            success = runner.run_performance_tests(verbose)
        elif args.ui:
            success = runner.run_ui_tests(verbose)
        elif args.coverage:
            success = runner.generate_coverage_report()
        else:
            # Por defecto, ejecutar todos los tests
            success = runner.run_all_tests(
                verbose=verbose,
                coverage=args.coverage,
                html_report=args.html
            )

        duration = time.time() - start_time
        runner.print_summary(success, duration)

        return 0 if success else 1

    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Tests interrumpidos por el usuario{Colors.ENDC}")
        return 130
    except Exception as e:
        runner.print_error(f"Error inesperado: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
