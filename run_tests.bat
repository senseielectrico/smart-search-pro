@echo off
REM Smart Search - Test Runner Batch Script
REM ========================================
REM
REM Ejecuta la suite de tests con diferentes opciones
REM
REM Uso:
REM   run_tests.bat          - Ejecutar todos los tests
REM   run_tests.bat unit     - Solo tests unitarios
REM   run_tests.bat coverage - Con reporte de cobertura
REM   run_tests.bat quick    - Test rápido
REM

setlocal

REM Configurar colores (requiere Windows 10+)
set ESC=
set BLUE=%ESC%[94m
set GREEN=%ESC%[92m
set RED=%ESC%[91m
set YELLOW=%ESC%[93m
set RESET=%ESC%[0m

echo.
echo ============================================================
echo Smart Search - Test Suite
echo ============================================================
echo.

REM Verificar que Python esté instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo %RED%ERROR: Python no encontrado%RESET%
    echo Por favor instale Python 3.8 o superior
    exit /b 1
)

REM Verificar que pytest esté instalado
python -m pytest --version >nul 2>&1
if errorlevel 1 (
    echo %YELLOW%pytest no encontrado. Instalando dependencias...%RESET%
    python -m pip install pytest pytest-cov pytest-html psutil
    if errorlevel 1 (
        echo %RED%ERROR: No se pudieron instalar las dependencias%RESET%
        exit /b 1
    )
)

REM Determinar qué tests ejecutar según argumento
set TEST_TYPE=%1

if "%TEST_TYPE%"=="" (
    echo %BLUE%Ejecutando todos los tests...%RESET%
    python tests\run_tests.py
    goto :end
)

if /i "%TEST_TYPE%"=="unit" (
    echo %BLUE%Ejecutando tests unitarios...%RESET%
    python tests\run_tests.py --unit
    goto :end
)

if /i "%TEST_TYPE%"=="integration" (
    echo %BLUE%Ejecutando tests de integración...%RESET%
    python tests\run_tests.py --integration
    goto :end
)

if /i "%TEST_TYPE%"=="performance" (
    echo %BLUE%Ejecutando tests de rendimiento...%RESET%
    python tests\run_tests.py --performance
    goto :end
)

if /i "%TEST_TYPE%"=="ui" (
    echo %BLUE%Ejecutando tests de UI...%RESET%
    python tests\run_tests.py --ui
    goto :end
)

if /i "%TEST_TYPE%"=="coverage" (
    echo %BLUE%Ejecutando tests con cobertura...%RESET%
    python tests\run_tests.py --coverage
    echo.
    echo %GREEN%Reporte de cobertura generado en: coverage_html\index.html%RESET%
    goto :end
)

if /i "%TEST_TYPE%"=="html" (
    echo %BLUE%Ejecutando tests con reporte HTML...%RESET%
    python tests\run_tests.py --html
    goto :end
)

if /i "%TEST_TYPE%"=="quick" (
    echo %BLUE%Ejecutando test rápido...%RESET%
    python tests\run_tests.py --quick
    goto :end
)

if /i "%TEST_TYPE%"=="check" (
    echo %BLUE%Verificando dependencias...%RESET%
    python tests\run_tests.py --check-deps
    goto :end
)

if /i "%TEST_TYPE%"=="all" (
    echo %BLUE%Ejecutando suite completa con reportes...%RESET%
    python tests\run_tests.py --coverage --html
    echo.
    echo %GREEN%Reportes generados:%RESET%
    echo   - Cobertura: coverage_html\index.html
    echo   - HTML: test_report_*.html
    goto :end
)

if /i "%TEST_TYPE%"=="help" (
    goto :help
)

REM Opción desconocida
echo %RED%ERROR: Opción desconocida: %TEST_TYPE%%RESET%
echo.
goto :help

:help
echo Uso: run_tests.bat [OPCION]
echo.
echo Opciones:
echo   (ninguna)     - Ejecutar todos los tests
echo   unit          - Solo tests unitarios
echo   integration   - Solo tests de integración
echo   performance   - Solo tests de rendimiento
echo   ui            - Solo tests de UI
echo   coverage      - Ejecutar con reporte de cobertura
echo   html          - Generar reporte HTML
echo   quick         - Test rápido de verificación
echo   check         - Verificar dependencias
echo   all           - Suite completa con todos los reportes
echo   help          - Mostrar esta ayuda
echo.
echo Ejemplos:
echo   run_tests.bat
echo   run_tests.bat unit
echo   run_tests.bat coverage
echo   run_tests.bat all
echo.
goto :end

:end
echo.
echo ============================================================
endlocal
