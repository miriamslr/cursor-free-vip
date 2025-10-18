# Arquivo: patch_real.py (versão final para estudo)

file_to_modify = "workbench.desktop.main.js"

# --- Padrões ATUALIZADOS com a sua assinatura ---
# Esta é a assinatura exata que você encontrou no seu arquivo.
original_pattern = 'async getEffectiveTokenLimit(e){const n=e.modelName;if(!n)return 2e5;const t=this.modelConfigService.getModelConfig(e);return t?.contextTokenLimit??2e5}'

# A substituição agora substitui a função inteira por uma que só retorna 9 milhões.
new_pattern = 'async getEffectiveTokenLimit(e){return 9000000}'
# ------------------------------------------------

print(f"--- Iniciando a simulação de patch para: {file_to_modify} ---")

try:
    with open(file_to_modify, "r", encoding="utf-8") as f:
        content = f.read()

    print("\n[ORIGINAL]\n" + content)

    if original_pattern in content:
        print("\n[STATUS] ✅ Padrão original encontrado no arquivo.")
        
        modified_content = content.replace(original_pattern, new_pattern)
        
        with open(file_to_modify, "w", encoding="utf-8") as f:
            f.write(modified_content)
        
        print("\n[MODIFICADO]\n" + modified_content)
        print("\n[STATUS] ✅ Arquivo modificado com sucesso!")

    else:
        print("\n[ERRO] ❌ Padrão original NÃO encontrado.")

except Exception as e:
    print(f"\n[ERRO] ❌ Ocorreu um erro durante o processo: {e}")