import itertools
import os
import asyncio
import re
from playwright.async_api import async_playwright

# --- CONFIGURAÇÃO DOS JOGOS ---
jogos_config = [
    {"nome": "Vitória BA", "opcoes": ["1", "X", "2"]}, 
    {"nome": "Chapecoense", "opcoes": ["1", "X"]},
    {"nome": "Atlético MG", "opcoes": ["1", "X", "2"]},
    {"nome": "São Paulo", "opcoes": ["1", "X", "2"]}
]

listas_de_opcoes = [j["opcoes"] for j in jogos_config]
nomes_dos_jogos = [j["nome"] for j in jogos_config]
combinacoes = list(itertools.product(*listas_de_opcoes))

async def destacar_elemento(element):
    """Aplica destaque visual para debug."""
    try:
        await element.evaluate("el => { el.style.border = '4px solid red'; el.style.backgroundColor = 'yellow'; }")
        await asyncio.sleep(0.5)
    except:
        pass

async def limpar_bilhete(page):
    """Localiza a seção do cabeçalho do cupom e clica no botão da lixeira com logs de debug."""
    try:
        print("🔍 [DEBUG] Iniciando tentativa de limpeza do bilhete...")
        
        # 1. Tenta localizar a seção pai que contém os botões e o contador numérico
        secao_topo_cupom = page.locator("section").filter(has=page.get_by_role("button")).filter(has_text=re.compile(r"^[0-9]+$")).first
        
        # Verificamos se a seção existe e o que ela contém
        if await secao_topo_cupom.count() > 0:
            texto_detectado = await secao_topo_cupom.inner_text()
            print(f"   📂 [DEBUG] Seção do cupom encontrada. Conteúdo detectado: '{texto_detectado.strip()}'")
            
            # 2. Localiza o último botão dentro desta seção (Lixeira)
            btn_lixeira = secao_topo_cupom.get_by_role("button").last
            
            if await btn_lixeira.is_visible():
                print("   🧹 [DEBUG] Botão lixeira visível. Executando clique...")
                await btn_lixeira.click()
                print("   ✅ [DEBUG] Clique enviado. Aguardando 1.5s para processamento da UI...")
                await asyncio.sleep(1.5)
            else:
                print("   ⚠️ [DEBUG] Seção encontrada, mas o botão da lixeira não está visível.")
        else:
            # Caso comum: o cupom já está vazio, então a section com número não existe
            print("   ℹ️ [DEBUG] Nenhuma seção com contador numérico encontrada. O cupom deve estar vazio.")
            
    except Exception as e:
        print(f"   ❌ [DEBUG] Erro inesperado na função limpar_bilhete: {str(e)}")

async def run():
    print("\n" + "="*30)
    print("🚀 PLAYWRIGHT: MODO PERSISTENTE")
    print("="*30)

    perfil_bot = os.path.join(os.getcwd(), "perfil_novo_bot")

    async with async_playwright() as p:
        try:
            context = await p.chromium.launch_persistent_context(
                perfil_bot,
                headless=False,
                viewport={'width': 1280, 'height': 800},
                args=["--no-sandbox", "--disable-dev-shm-usage"]
            )
        except Exception as e:
            print(f"❌ ERRO CRÍTICO AO INICIAR: {e}")
            return

        page = context.pages[0] if context.pages else await context.new_page()

        print("🔗 Acessando Superbet...")
        try:
            await page.goto("https://superbet.bet.br/apostas/futebol/brasil/brasileiro-serie-a", wait_until="load")
        except:
            print("⚠️ Timeout na navegação, tentando prosseguir...")

        # Aguarda estabilização inicial
        await asyncio.sleep(10)

        # --- LOOP DE TESTE ---
        for i, bilhete in enumerate(combinacoes[:1], 1):
            print(f"\n--- 🎫 BILHETE DE TESTE #{i} ---")
            
            # Limpeza inicial obrigatória
            await limpar_bilhete(page)

            # Log de preview
            mapa_resultado = {"1": "Vitória", "X": "Empate", "2": "Derrota"}
            for idx, palpite in enumerate(bilhete):
                tipo_aposta = mapa_resultado.get(palpite, palpite)
                print(f"📋 Jogo {idx + 1}: {nomes_dos_jogos[idx]} -> {tipo_aposta}")
            print("-" * 30)

            # Execução das seleções
            for j, palpite in enumerate(bilhete):
                nome_time = nomes_dos_jogos[j]
                posicao = 1 if palpite == "1" else (2 if palpite == "X" else 3)
                
                try:
                    print(f"   🔍 Buscando jogo: {nome_time}...")
                    regex_jogo = re.compile(f"Open.*{nome_time}", re.IGNORECASE)
                    botao_linha = page.get_by_role("button", name=regex_jogo)
                    
                    container = page.locator("div").filter(has=botao_linha).last
                    odds = container.locator("button").filter(has_text=re.compile(r"^\d+\.\d+$"))
                    
                    alvo = odds.nth(posicao - 1)

                    await alvo.scroll_into_view_if_needed()
                    await destacar_elemento(alvo)
                    await alvo.click(force=True)
                    
                    print(f"   ✅ Selecionado: {nome_time} -> {palpite}")
                    await asyncio.sleep(1.5)

                except Exception as e:
                    print(f"   ❌ Erro em {nome_time}: {e}")

            # Validação Final
            print("\n🔍 Verificando Cupom...")
            try:
                btn_aposta = page.get_by_role("button").filter(has_text="Fazer aposta").first
                if await btn_aposta.is_visible():
                    await destacar_elemento(btn_aposta)
                    print("   ✅ [OK] Botão 'Fazer aposta' detectado!")
            except:
                print("   ⚠️ Cupom não identificado.")

            # Limpeza pós-teste para o próximo ciclo
            await limpar_bilhete(page)

        print("\n🏁 Processo finalizado.")
        await asyncio.sleep(10)
        await context.close()

if __name__ == "__main__":
    asyncio.run(run())