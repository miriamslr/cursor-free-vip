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
            # Caminho padrão CORRETO para ser usado se config.ini não existir
            "base": "C:\\Program Files\\cursor\\resources\\app", 
            "main": "out\\vs\\workbench\\workbench.desktop.main.js"
        },
        "Linux": {
            "bases": ["/opt/Cursor/resources/app", "/usr/share/cursor/resources/app", "/usr/lib/cursor/app/"],
            "main": "out/vs/workbench/workbench.desktop.main.js"
        }
    }

    if system == "Linux":
        extracted_usr_paths = glob.glob(os.path.expanduser("~/squashfs-root/usr/share/cursor/resources/app"))
        paths_map["Linux"]["bases"].extend(extracted_usr_paths)

    if system not in paths_map:
        raise OSError(translator.get('reset.unsupported_os', system=system) if translator else f"Unsupported OS: {system}")

    base_path = ""
    # A lógica agora prioriza o config, mas o fallback é o caminho correto.
    if system == "Windows":
        base_path = config.get('WindowsPaths', 'cursor_path', fallback=paths_map["Windows"]["base"])
    elif system == "Darwin":
        base_path = config.get('MacPaths', 'cursor_path', fallback=paths_map["Darwin"]["base"])
    elif system == "Linux":
        if config.has_option('LinuxPaths', 'cursor_path'):
            base_path = config.get('LinuxPaths', 'cursor_path')
        else:
            for base in paths_map["Linux"]["bases"]:
                if os.path.exists(base):
                    base_path = base
                    break
    
    if not base_path or not os.path.exists(base_path):
         raise OSError(translator.get('reset.path_not_found', path=base_path) if translator else f"Cursor path not found: {base_path}")

    main_path = os.path.join(base_path, paths_map[system]["main"])

    if not os.path.exists(main_path):
        raise OSError(translator.get('reset.file_not_found', path=main_path) if translator else f"Cursor main.js file not found: {main_path}")

    return main_path


def modify_workbench_js(file_path: str, translator=None) -> bool:
    """
    Modify file content
    """
    try:
        print(f"{Fore.CYAN}{EMOJI['INFO']} Iniciando modificação do arquivo: {file_path}{Style.RESET_ALL}")
        
        original_stat = os.stat(file_path)
        original_mode = original_stat.st_mode
        original_uid = original_stat.st_uid
        original_gid = original_stat.st_gid
        print(f"{Fore.CYAN}{EMOJI['INFO']} Permissões originais - Modo: {oct(original_mode)}, UID: {original_uid}, GID: {original_gid}{Style.RESET_ALL}")

        with open(file_path, "r", encoding="utf-8", errors="ignore") as main_file:
            content = main_file.read()

        print(f"{Fore.CYAN}{EMOJI['INFO']} Aplicando padrões de substituição...{Style.RESET_ALL}")
        
        patterns = {
            # MODIFICAÇÃO PRINCIPAL: Usa a assinatura exata que encontramos.
            'async getEffectiveTokenLimit(e){const n=e.modelName;if(!n)return 2e5;const r=this.lb.get(n);if(r){const[a,l]=r;if(l>new Date)return a}const o=await this.aiClient();try{const l=(await o.getEffectiveTokenLimit(new hOt({modelDetails:e}))).tokenLimit;return this.lb.set(n,[l,new Date(Date.now()+864e5)]),l}catch(a){return console.error(a),2e5}}':
            'async getEffectiveTokenLimit(e){return 9000000}',

            'async getEffectiveTokenLimit(e){return 9000000}':
            'async getEffectiveTokenLimit(e){return 9000000;const n=e.modelName;if(!n)return 9e5;}',
            
            't.isTrial||t.isEnterpriseTrial?"Pro Trial":"Pro"':
            '"Pro"',
            
            'title:"Upgrade",size:"small",get codicon(){return o.rocket},get onClick(){return e.pay}':
            'title:"Patched by VIP",size:"small",get codicon(){return o.github},get onClick(){return()=>this.openUrl("https://github.com/yeongpin/cursor-free-vip")}',

            'notifications-toasts':
            'notifications-toasts hidden'
        }

        found_any = False
        content_modified = content
        for old, new in patterns.items():
            if old in content_modified:
                print(f"{Fore.GREEN}{EMOJI['SUCCESS']} Padrão encontrado e será substituído ({content_modified.count(old)} ocorrências):")
                print(f"  Antigo: {old[:70]}...")
                print(f"  Novo: {new[:70]}...")
                content_modified = content_modified.replace(old, new)
                found_any = True
            else:
                print(f"{Fore.YELLOW}{EMOJI['WARNING']} Padrão não encontrado no arquivo:")
                print(f"  {old[:70]}...")

        if not found_any:
            print(f"{Fore.RED}{EMOJI['ERROR']} Nenhum dos padrões foi encontrado. A modificação falhou. Sua versão do Cursor pode ser incompatível.{Style.RESET_ALL}")
            return False

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{file_path}.backup.{timestamp}"
        shutil.copy2(file_path, backup_path)
        print(f"{Fore.GREEN}{EMOJI['SUCCESS']} Backup criado em: {backup_path}{Style.RESET_ALL}")

        print(f"{Fore.CYAN}{EMOJI['INFO']} Substituindo arquivo original pelo modificado...{Style.RESET_ALL}")
        with open(file_path, "w", encoding="utf-8", errors="ignore") as main_file:
            main_file.write(content_modified)

        print(f"{Fore.GREEN}{EMOJI['SUCCESS']} Arquivo modificado com sucesso{Style.RESET_ALL}")
        
        print(f"{Fore.CYAN}{EMOJI['INFO']} Restaurando permissões originais...{Style.RESET_ALL}")
        os.chmod(file_path, original_mode)
        if platform.system() != "Windows":
            os.chown(file_path, original_uid, original_gid)

        return True

    except Exception as e:
        print(f"{Fore.RED}{EMOJI['ERROR']} Falha ao modificar o arquivo: {str(e)}{Style.RESET_ALL}")
        return False

def run(translator=None):
    try:
        config, config_dir = get_config(translator)
        if not config:
            return False
            
        print(f"\n{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{EMOJI['RESET']} Ferramenta para Burlar o Limite de Tokens{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*50}{Style.RESET_ALL}")

        workbench_path = get_workbench_cursor_path(config, translator)
        modify_workbench_js(workbench_path, translator)

    except Exception as e:
        print(f"{Fore.RED}{EMOJI['ERROR']} Um erro inesperado ocorreu: {e}{Style.RESET_ALL}")

    print(f"\n{Fore.CYAN}{'='*50}{Style.RESET_ALL}")
    input(f"{EMOJI['INFO']} Pressione Enter para sair...")

if __name__ == "__main__":
    class SimpleTranslator:
        def get(self, key, **kwargs):
            parts = key.split('.')
            text = parts[-1].replace('_', ' ').title()
            return text

    run(translator=SimpleTranslator())