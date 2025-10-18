# Arquivo: diagnostico.py
import os
import re
from colorama import Fore, Style, init

# Inicializa o colorama
init()

# --- CONFIGURAÇÃO ---
# Coloque aqui o caminho completo para o arquivo do Cursor
# Já deixei o seu caminho preenchido.
file_path = r"C:\Users\Miriam Nova\AppData\Local\Programs\Cursor\resources\app\out\vs\workbench\workbench.desktop.main.js"

# Termos que vamos procurar para encontrar a linha certa
search_terms = ["getEffectiveTokenLimit", "modelConfigService", "contextTokenLimit"]
# --------------------

print(f"{Fore.CYAN}--- Iniciando Diagnóstico ---{Style.RESET_ALL}")
print(f"Procurando no arquivo: {file_path}\n")

try:
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Usamos uma expressão regular para encontrar a função inteira
    # Ela procura por "getEffectiveTokenLimit" seguido por qualquer coisa até encontrar uma chave de fechamento '}'
    pattern = r'(\w+\.prototype\.getEffectiveTokenLimit\s*=\s*async function\s*\([^)]*\)\s*\{[^}]*\})|' \
              r'(getEffectiveTokenLimit\s*:\s*async\s*\([^)]*\)\s*=>\s*\{[^}]*\})|' \
              r'(async getEffectiveTokenLimit\s*\([^)]*\)\s*\{[^}]*\})'

    matches = re.findall(pattern, content)

    found_signature = ""
    if matches:
        # A regex tem 3 grupos, então precisamos pegar o resultado que não está vazio
        for match_tuple in matches:
            for match in match_tuple:
                if match:
                    found_signature = match
                    break
            if found_signature:
                break

    if found_signature:
        print(f"{Fore.GREEN}✅ Assinatura da função encontrada!{Style.RESET_ALL}")
        print("Copie o bloco de texto abaixo, exatamente como ele aparece:")
        print("-" * 50)
        print(f"{Fore.YELLOW}{found_signature}{Style.RESET_ALL}")
        print("-" * 50)
    else:
        print(f"{Fore.RED}❌ Não foi possível encontrar a assinatura da função automaticamente.{Style.RESET_ALL}")
        print("Isso pode significar que a estrutura da função mudou drasticamente.")

except FileNotFoundError:
    print(f"{Fore.RED}ERRO: O arquivo não foi encontrado em:{Style.RESET_ALL}\n{file_path}")
    print("Por favor, verifique se o caminho está correto dentro do script 'diagnostico.py'.")
except Exception as e:
    print(f"{Fore.RED}Ocorreu um erro inesperado: {e}{Style.RESET_ALL}")