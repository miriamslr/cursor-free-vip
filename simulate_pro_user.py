import os
import json
import re
import shutil
from pathlib import Path
from datetime import datetime, timedelta

# Caminhos importantes
CURSOR_DIR = r"c:\Program Files\cursor"
WORKBENCH_JS = os.path.join(CURSOR_DIR, "resources\app\out\vs\workbench\workbench.desktop.main.js")
BACKUP_EXT = ".bak"

def create_backup(file_path):
    """Cria um backup do arquivo original"""
    backup_path = file_path + BACKUP_EXT
    if not os.path.exists(backup_path):
        shutil.copy2(file_path, backup_path)
        print(f"Backup criado em: {backup_path}")
    return backup_path

def modify_file(file_path, patterns):
    """Modifica o arquivo aplicando os padrões de substituição"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    for pattern, replacement in patterns.items():
        content = re.sub(
            re.escape(pattern),
            replacement,
            content,
            flags=re.DOTALL
        )
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Modificações aplicadas com sucesso!")
        return True
    else:
        print("Nenhuma modificação necessária.")
        return False

def simulate_pro_user():
    print("Iniciando simulação de usuário Pro...")
    
    # Padrões para modificar as verificações de assinatura
    patterns = {
        # Forçar status de assinatura para Pro ativo
        '(isPro:\s*)false': r'\1true',
        '(isPro\(\)\s*{\s*return\s*)(?:false|!1)': r'\1true',
        
        # Remover verificações de trial
        '(isTrial:\s*)true': r'\1false',
        '(isTrial\(\)\s*{\s*return\s*)(?:true|!0)': r'\1false',
        
        # Forçar plano Pro
        '(plan:\s*[\'\"])(?:free|trial)': r'\1pro',
        
        # Remover verificações de limite de uso
        '(hasReachedFreeTierLimit\s*\([^)]*\)\s*{\s*return\s*)(?:true|!0)': r'\1false',
        '(isFreeTier\s*\([^)]*\)\s*{\s*return\s*)(?:true|!0)': r'\1false',
        
        # Forçar limites altos
        '(getEffectiveTokenLimit\s*\([^)]*\)\s*{[^}]*return\s*)\d+': r'\19000000',
        
        # Remover mensagens de upgrade
        '(showUpgradePrompt\s*\([^)]*\)\s*{[^}]*})': r'\1; return true;',
        '(showProUpsell\s*\([^)]*\)\s*{[^}]*})': r'\1; return true;'
    }
    
    # Criar backup se não existir
    backup_path = create_backup(WORKBENCH_JS)
    
    try:
        # Aplicar modificações
        print("Aplicando modificações...")
        modified = modify_file(WORKBENCH_JS, patterns)
        
        if modified:
            print("\n✅ Simulação de usuário Pro ativada com sucesso!")
            print("Reinicie o Cursor para que as alterações tenham efeito.")
        else:
            print("\nℹ️ Nenhuma alteração foi necessária. O Cursor já parece estar configurado como Pro.")
    
    except Exception as e:
        print(f"\n❌ Ocorreu um erro: {str(e)}")
        print(f"Restaurando backup de {backup_path}...")
        shutil.copy2(backup_path, WORKBENCH_JS)
        print("Backup restaurado. Tente novamente com permissões de administrador.")

if __name__ == "__main__":
    print("=" * 60)
    print("Cursor - Simulador de Usuário Pro")
    print("=" * 60)
    print("Este script modificará os arquivos do Cursor para simular uma conta Pro.")
    print("Certifique-se de que o Cursor está fechado antes de continuar.")
    print("-" * 60)
    
    input("Pressione Enter para continuar ou Ctrl+C para cancelar...")
    print()
    
    # Verificar se o script está sendo executado como administrador
    try:
        test_file = os.path.join(os.environ["PROGRAMFILES"], "test_write.tmp")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
    except PermissionError:
        print("ERRO: Este script precisa ser executado como administrador.")
        print("Por favor, feche e execute novamente como administrador.")
        input("Pressione Enter para sair...")
        exit(1)
    
    simulate_pro_user()
    
    print("\n" + "=" * 60)
    print("Atenção: Estas alterações podem ser revertidas a qualquer atualização do Cursor.")
    print("Você precisará executar este script novamente após cada atualização.")
    print("=" * 60)
    input("\nPressione Enter para sair...")
