"""
Script para encontrar todas las evaluaciones problemáticas de DataFrame.
"""

import os
import re

def find_problematic_patterns():
    """Encuentra patrones que pueden causar el error de DataFrame ambiguity."""
    
    problematic_patterns = [
        r'if\s+\w*data\w*:',
        r'if\s+\w*df\w*:',
        r'if\s+\w*selected\w*:',
        r'if\s+not\s+\w*data\w*:',
        r'if\s+not\s+\w*df\w*:',
        r'if\s+not\s+\w*selected\w*:'
    ]
    
    files_to_check = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.py'):
                files_to_check.append(os.path.join(root, file))
    
    issues_found = []
    
    for file_path in files_to_check:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            for line_num, line in enumerate(lines, 1):
                for pattern in problematic_patterns:
                    if re.search(pattern, line):
                        # Filtrar algunos casos que sabemos que están bien
                        if ('len(' in line or 
                            '.empty' in line or 
                            '.any()' in line or 
                            '.all()' in line or
                            'isinstance(' in line or
                            'hasattr(' in line):
                            continue
                        
                        issues_found.append({
                            'file': file_path,
                            'line': line_num,
                            'content': line.strip(),
                            'pattern': pattern
                        })
        except Exception as e:
            print(f"Error leyendo {file_path}: {e}")
    
    return issues_found

if __name__ == "__main__":
    print("🔍 BUSCANDO EVALUACIONES PROBLEMÁTICAS DE DATAFRAME")
    print("=" * 60)
    
    issues = find_problematic_patterns()
    
    if not issues:
        print("✅ No se encontraron patrones problemáticos")
    else:
        print(f"⚠️ Se encontraron {len(issues)} posibles problemas:")
        print()
        
        for issue in issues:
            print(f"📁 {issue['file']}:{issue['line']}")
            print(f"   {issue['content']}")
            print(f"   Patrón: {issue['pattern']}")
            print()
        
        print("=" * 60)
        print("💡 RECOMENDACIONES:")
        print("- Cambiar 'if data:' por 'if len(data) > 0:'")
        print("- Cambiar 'if df:' por 'if not df.empty:'")
        print("- Cambiar 'if selected:' por 'if len(selected) > 0:'")
