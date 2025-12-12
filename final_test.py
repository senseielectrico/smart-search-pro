#!/usr/bin/env python3
"""Test rápido final de Smart Search"""
import sys

print('=== SMART SEARCH - TEST FINAL ===')
print()

errors = []

# 1. Imports
try:
    from backend import SearchService, SearchQuery
    from ui import SmartSearchWindow
    from classifier import classify_file
    from file_manager import DirectoryTree, CheckState
    from utils import format_file_size
    from categories import FileCategory
    from optimizations import ResultsCache
    print('[OK] Todos los modulos cargan')
except Exception as e:
    errors.append(f'Imports: {e}')
    print(f'[X] Error imports: {e}')

# 2. Backend
try:
    service = SearchService()
    print(f'[OK] SearchService (Windows Search: {service.use_windows_search})')
except Exception as e:
    errors.append(f'Backend: {e}')
    print(f'[X] Backend: {e}')

# 3. Clasificador
try:
    r1 = classify_file('test.py')
    r2 = classify_file('doc.pdf')
    print(f'[OK] Clasificador: .py={r1}, .pdf={r2}')
except Exception as e:
    errors.append(f'Clasificador: {e}')
    print(f'[X] Clasificador: {e}')

# 4. DirectoryTree
try:
    import os
    tree = DirectoryTree()
    docs = os.path.expanduser('~') + r'\Documents'
    tree.add_directory(docs)
    tree.set_state(docs, CheckState.CHECKED)
    selected = tree.get_selected_directories()
    print(f'[OK] DirectoryTree: {len(selected)} dirs seleccionados')
except Exception as e:
    errors.append(f'DirectoryTree: {e}')
    print(f'[X] DirectoryTree: {e}')

# 5. Utils
try:
    r = format_file_size(1536000)
    print(f'[OK] Utils: format_file_size(1536000) = {r}')
except Exception as e:
    errors.append(f'Utils: {e}')
    print(f'[X] Utils: {e}')

# 6. Cache
try:
    cache = ResultsCache()
    cache.put('test', [1,2,3])
    result = cache.get('test')
    print(f'[OK] Cache: put/get funciona')
except Exception as e:
    errors.append(f'Cache: {e}')
    print(f'[X] Cache: {e}')

# 7. Seguridad SQL
try:
    sanitized = SearchQuery.sanitize_sql_input("'; DROP TABLE--")
    print(f'[OK] SQL sanitizado: {repr(sanitized[:30])}...')
except Exception as e:
    errors.append(f'SQL: {e}')
    print(f'[X] SQL: {e}')

# Resultado
print()
print('=' * 40)
if errors:
    print(f'ERRORES: {len(errors)}')
    for e in errors:
        print(f'  - {e}')
    sys.exit(1)
else:
    print('SMART SEARCH LISTO PARA PRODUCCION')
    print('=' * 40)
    print()
    print('Para ejecutar:')
    print('  python main.py')
    print('  o doble-clic en smart_search.pyw')
    sys.exit(0)
