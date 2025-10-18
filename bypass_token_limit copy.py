import os
import shutil
import platform
import tempfile
import glob
from colorama import Fore, Style, init
import configparser
import sys
from config import get_config
from datetime import datetime

# Initialize colorama
init()

# Define emoji constants
EMOJI = {
    "FILE": "📄",
    "BACKUP": "💾",
    "SUCCESS": "✅",
    "ERROR": "❌",
    "INFO": "ℹ️",
    "RESET": "🔄",
    "WARNING": "⚠️",
}


def get_workbench_cursor_path(config, translator=None) -> str:
    """Get Cursor workbench.desktop.main.js path"""
    system = platform.system()

    paths_map = {
        "Darwin": {  # macOS
            "base": "/Applications/Cursor.app/Contents/Resources/app",
            "main": "out/vs/workbench/workbench.desktop.main.js"
        },
        "Windows": {
            "base": os.path.expandvars("%LOCALAPPDATA%\\Programs\\Cursor\\resources\\app"),
            "main": "out\\vs\\workbench\\workbench.desktop.main.js"
        },
        "Linux": {
            "bases": ["/opt/Cursor/resources/app", "/usr/share/cursor/resources/app", "/usr/lib/cursor/app/"],
            "main": "out/vs/workbench/workbench.desktop.main.js"
        }
    }

    if system == "Linux":
        # Add extracted AppImage with correct usr structure
        extracted_usr_paths = glob.glob(os.path.expanduser("~/squashfs-root/usr/share/cursor/resources/app"))

        paths_map["Linux"]["bases"].extend(extracted_usr_paths)

    if system not in paths_map:
        raise OSError(translator.get('reset.unsupported_os', system=system) if translator else f"不支持的操作系统: {system}")

    if system == "Linux":
        for base in paths_map["Linux"]["bases"]:
            main_path = os.path.join(base, paths_map["Linux"]["main"])
            print(f"{Fore.CYAN}{EMOJI['INFO']} Checking path: {main_path}{Style.RESET_ALL}")
            if os.path.exists(main_path):
                return main_path

    if system == "Windows":
        base_path = config.get('WindowsPaths', 'cursor_path')
    elif system == "Darwin":
        base_path = paths_map[system]["base"]
        if config.has_section('MacPaths') and config.has_option('MacPaths', 'cursor_path'):
            base_path = config.get('MacPaths', 'cursor_path')
    else:  # Linux
        # For Linux, we've already checked all bases in the loop above
        # If we're here, it means none of the bases worked, so we'll use the first one
        base_path = paths_map[system]["bases"][0]
        if config.has_section('LinuxPaths') and config.has_option('LinuxPaths', 'cursor_path'):
            base_path = config.get('LinuxPaths', 'cursor_path')

    main_path = os.path.join(base_path, paths_map[system]["main"])

    if not os.path.exists(main_path):
        raise OSError(translator.get('reset.file_not_found', path=main_path) if translator else f"未找到 Cursor main.js 文件: {main_path}")

    return main_path


def modify_workbench_js(file_path: str, translator=None) -> bool:
    """
    Modify file content
    """
    print(f"{Fore.CYAN}{EMOJI['INFO']} Iniciando modificação do arquivo: {file_path}{Style.RESET_ALL}")
    try:
        # Save original file permissions
        print(f"{Fore.CYAN}{EMOJI['INFO']} Obtendo permissões originais do arquivo...{Style.RESET_ALL}")
        original_stat = os.stat(file_path)
        original_mode = original_stat.st_mode
        original_uid = original_stat.st_uid
        original_gid = original_stat.st_gid
        print(f"{Fore.CYAN}{EMOJI['INFO']} Permissões obtidas - Modo: {oct(original_mode)}, UID: {original_uid}, GID: {original_gid}{Style.RESET_ALL}")

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", errors="ignore", delete=False) as tmp_file:
            # Read original content
            with open(file_path, "r", encoding="utf-8", errors="ignore") as main_file:
                content = main_file.read()

            # Padrões de substituição com descrições
            patterns = {
                # Padrões para o botão "Upgrade to Pro"
                'Botão Upgrade to Pro (1)': (
                    r'Upgrade to Pro',
                    'Pro'
                ),
                
                # Padrões para o limite de tokens
                'Limite de tokens (1)': (
                    r'(getEffectiveTokenLimit\s*\([^)]*\)\s*{[^}]*?return\s*)[\d.]+e?\+?\d*',
                    r'\1 9000000'
                ),
                
                'Limite de tokens (2)': (
                    r'(getEffectiveTokenLimit\s*=\s*function\s*\([^)]*\)\s*{[^}]*?return\s*)[\d.]+e?\+?\d*',
                    r'\1 9000000'
                ),
                
                'Limite de tokens (3)': (
                    r'(getEffectiveTokenLimit\s*\([^)]*\)\s*{[^}]*?return\s*Math\.min\()([^,)]+',
                    r'\19000000'
                ),
                
                # Padrão para mensagem de usuário Pro
                'Mensagem de status Pro': (
                    r'(You are currently signed in with)([^<]*)',
                    r'\1 <strong>Pro</strong>\2'
                ),
                
                # Padrão para notificações
                'Ocultar notificações': (
                    r'(notifications-toasts)',
                    r'\1 hidden'
                ),
                
                # Padrão para mensagem de trial
                'Remover "Trial"': (
                    r'(Pro|Free)\s*Trial',
                    'Pro'
                ),
                
                # Padrão para auto-select
                'Modificar Auto-select': (
                    r'Auto-select',
                    'Bypass-Version-Pin'
                )
            }

            # Aplicar padrões de substituição
            print(f"{Fore.CYAN}{EMOJI['INFO']} Aplicando padrões de substituição...{Style.RESET_ALL}")
            total_substituicoes = 0
            
            for pattern_name, (old_pattern, new_pattern) in patterns.items():
                print(f"\n{Fore.CYAN}{EMOJI['INFO']} Verificando padrão: {pattern_name}{Style.RESET_ALL}")
                
                # Usar expressão regular para encontrar correspondências
                import re
                matches = list(re.finditer(old_pattern, content, re.DOTALL))
                
                if matches:
                    print(f"{Fore.GREEN}{EMOJI['SUCCESS']} Padrão encontrado ({len(matches)} ocorrências):{Style.RESET_ALL}")
                    for i, match in enumerate(matches[:3]):  # Mostrar apenas as 3 primeiras ocorrências
                        match_text = match.group(0)
                        start_line = content[:match.start()].count('\n') + 1
                        print(f"  Ocorrência {i+1} (linha ~{start_line}):")
                        print(f"  {Fore.CYAN}Antigo:{Style.RESET_ALL} {match_text[:150]}...")
                        
                        # Fazer a substituição
                        content = content[:match.start()] + new_pattern + content[match.end():]
                        total_substituições += 1
                        
                        # Ajustar os índices após a substituição
                        offset = len(new_pattern) - len(match_text)
                        if i < len(matches) - 1:
                            for j in range(i + 1, len(matches)):
                                matches[j] = type('', (), {'start': lambda m=matches[j], o=offset: m.start() + o,
                                                         'end': lambda m=matches[j], o=offset: m.end() + o})()
                        
                        print(f"  {Fore.GREEN}Novo:{Style.RESET_ALL} {new_pattern[:150]}...")
                        print("  ---")
                else:
                    print(f"{Fore.YELLOW}{EMOJI['WARNING']} Padrão não encontrado no arquivo.{Style.RESET_ALL}")
            
            print(f"\n{Fore.CYAN}{EMOJI['INFO']} Total de substituições realizadas: {total_substituições}{Style.RESET_ALL}")
            
            # Verificar se o conteúdo foi modificado
            if total_substituições == 0:
                print(f"{Fore.YELLOW}{EMOJI['WARNING']} Nenhuma substituição foi realizada. Verifique os padrões de busca.{Style.RESET_ALL}")
            else:
                print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {total_substituições} substituições realizadas com sucesso!{Style.RESET_ALL}")
                
                # Verificar se a função getEffectiveTokenLimit foi modificada
                if 'getEffectiveTokenLimit' in content and 'return 9000000' in content:
                    print(f"{Fore.GREEN}{EMOJI['SUCCESS']} O limite de tokens foi definido para 9.000.000 com sucesso!{Style.RESET_ALL}")
                else:
                    print(f"{Fore.YELLOW}{EMOJI['WARNING']} Não foi possível confirmar a modificação do limite de tokens.{Style.RESET_ALL}")

            # Write to temporary file
            tmp_file.write(content)
            tmp_path = tmp_file.name

        # Backup original file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{file_path}.backup.{timestamp}"
        print(f"{Fore.CYAN}{EMOJI['INFO']} Criando backup do arquivo original em: {backup_path}{Style.RESET_ALL}")
        shutil.copy2(file_path, backup_path)
        print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {translator.get('reset.backup_created', path=backup_path)}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{EMOJI['INFO']} Tamanho do backup: {os.path.getsize(backup_path)} bytes{Style.RESET_ALL}")

        # Move temporary file to original position
        print(f"{Fore.CYAN}{EMOJI['INFO']} Substituindo arquivo original pelo modificado...{Style.RESET_ALL}")
        if os.path.exists(file_path):
            os.remove(file_path)
        shutil.move(tmp_path, file_path)
        print(f"{Fore.GREEN}{EMOJI['SUCCESS']} Arquivo modificado com sucesso{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{EMOJI['INFO']} Tamanho do novo arquivo: {os.path.getsize(file_path)} bytes{Style.RESET_ALL}")

        # Restore original permissions
        print(f"{Fore.CYAN}{EMOJI['INFO']} Restaurando permissões originais...{Style.RESET_ALL}")
        os.chmod(file_path, original_mode)
        if os.name != "nt":  # Not Windows
            os.chown(file_path, original_uid, original_gid)
            print(f"{Fore.CYAN}{EMOJI['INFO']} Permissões restauradas - Modo: {oct(original_mode)}, UID: {original_uid}, GID: {original_gid}{Style.RESET_ALL}")
        else:
            print(f"{Fore.CYAN}{EMOJI['INFO']} Permissões restauradas - Modo: {oct(original_mode)}{Style.RESET_ALL}")

        print(f"{Fore.GREEN}{EMOJI['SUCCESS']} {translator.get('reset.file_modified')}{Style.RESET_ALL}")
        return True

    except Exception as e:
        import traceback
        print(f"{Fore.RED}{EMOJI['ERROR']} {translator.get('reset.modify_file_failed', error=str(e))}{Style.RESET_ALL}")
        print(f"{Fore.RED}{EMOJI['ERROR']} Detalhes do erro: {traceback.format_exc()}{Style.RESET_ALL}")
        if "tmp_path" in locals() and os.path.exists(tmp_path):
            try:
                print(f"{Fore.YELLOW}{EMOJI['WARNING']} Removendo arquivo temporário: {tmp_path}{Style.RESET_ALL}")
                os.unlink(tmp_path)
            except Exception as cleanup_error:
                print(f"{Fore.RED}{EMOJI['ERROR']} Falha ao remover arquivo temporário: {cleanup_error}{Style.RESET_ALL}")
        return False


def run(translator=None):
    config, config_dir = get_config(translator)
    if not config:
        return False
    print(f"\n{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{EMOJI['RESET']} {translator.get('bypass_token_limit.title')}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}")

    workbench_path = get_workbench_cursor_path(config, translator)
    modify_workbench_js(workbench_path, translator)

    print(f"\n{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
    input(f"{EMOJI['INFO']} {translator.get('bypass_token_limit.press_enter')}...")

if __name__ == "__main__":
    from main import translator as main_translator
    run(main_translator)