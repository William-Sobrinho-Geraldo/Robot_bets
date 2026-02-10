import itertools
import os
import asyncio
import re
from playwright.async_api import async_playwright

# --- CONFIGURAÇÃO DOS JOGOS ---
jogos_config = [
    {"nome": "Vitória BA", "opcoes": ["1", "X", "2"]}, 
    {"nome": "Mirassol", "opcoes": ["1", "X", "2"]}, 
    {"nome": "Chapecoense", "opcoes": ["1", "X", "2"]},
    {"nome": "Atlético MG", "opcoes": ["1", "X", "2"]},
    {"nome": "São Paulo", "opcoes": ["1", "X", "2"]},
    {"nome": "Vasco da Gama", "opcoes": ["1", "X"]},
]

listas_de_opcoes = [j["opcoes"] for j in jogos_config]
nomes_dos_jogos = [j["nome"] for j in jogos_config]
combinacoes = list(itertools.product(*listas_de_opcoes))
quantidade_total = len(combinacoes)
print(f"\n Quantidade de apostas totais: {quantidade_total}")

async def limpar_bilhete(page):
    """Localiza a seção do cabeçalho do cupom e clica na lixeira."""
    try:
        print("🔍 [DEBUG] Verificando bilhete ativo...")
        secao_topo = page.locator("section").filter(has=page.get_by_role("button")).filter(has_text=re.compile(r"^[0-9]+$")).first
        
        if await secao_topo.count() > 0:
            qtd = await secao_topo.inner_text()
            print(f"   📂 [DEBUG] Cupom com {qtd.strip()} itens detectado.")
            
            btn_lixeira = secao_topo.get_by_role("button").last
            if await btn_lixeira.is_visible():
                await btn_lixeira.click()
                print("   ✨ [DEBUG] Bilhete esvaziado.")
                await asyncio.sleep(2) 
        else:
            print("   ℹ️ [DEBUG] Bilhete já está limpo.")
    except Exception as e:
        print(f"   ❌ [DEBUG] Erro na limpeza: {str(e)[:50]}")

async def run():
    print("\n" + "="*30)
    print("🚀 PLAYWRIGHT: MODO PERSISTENTE ROBUSTO")
    print("="*30)

    perfil_bot = os.path.join(os.getcwd(), "perfil_novo_bot")

    async with async_playwright() as p:
        try:
            context = await p.chromium.launch_persistent_context(
                perfil_bot,
                headless=False,
                viewport={'width': 1366, 'height': 768},
                args=["--no-sandbox", "--disable-dev-shm-usage"]
            )
        except Exception as e:
            print(f"❌ ERRO CRÍTICO AO INICIAR: {e}")
            return

        page = context.pages[0] if context.pages else await context.new_page()

        print("🔗 Acessando Superbet 3s ...")
        try:
            await page.goto("https://superbet.bet.br/apostas/futebol/brasil/brasileiro-serie-a", wait_until="load")
            await asyncio.sleep(3)
        except:
            print("⚠️ Timeout na navegação, tentando prosseguir...")

        # --- LOOP DE TESTE ---
        # for i, bilhete in enumerate(combinacoes[:9], 1):
        for i, bilhete in enumerate(combinacoes, 1):
            print(f"\n--- 🎫 BILHETE DE TESTE #{i} ---")
            
            await limpar_bilhete(page)

            # Primeiro FOR: Apenas exibição (Log)
            mapa_resultado = {"1": "Vitória", "X": "Empate", "2": "Derrota"}
            for idx, palpite in enumerate(bilhete):
                print(f"  📋 {nomes_dos_jogos[idx]} -> {mapa_resultado.get(palpite)}")
            print("-" * 30)

            # Segundo FOR: Execução do clique
            for j, palpite in enumerate(bilhete):
                nome_time = nomes_dos_jogos[j]
                
                try:
                    print(f"   🔍 Buscando: {nome_time} (Alvo: {mapa_resultado[palpite]})...")
                    regex_jogo = re.compile(f"Open.*{nome_time}", re.IGNORECASE)
                    botao_linha = page.get_by_role("button", name=regex_jogo)
                    
                    container = page.locator("div").filter(has=botao_linha).last
                    await container.wait_for(state="visible", timeout=10000)
                    
                    # Identifica botões de odds reais (regex para números e opcionalmente o 'X ' que vimos antes)
                    # odds = container.locator("button").filter(has_text=re.compile(r"^(X\s)?\d+\.\d+$"))
                    odds = container.locator("button").filter(has_text=re.compile(r"\d+\.\d+"))
                    count_odds = await odds.count()

                    # Lógica de indexação baseada no seu modelo preferido
                    # Lógica de indexação corrigida para o comportamento da Superbet
                    if palpite == "1":
                        alvo = odds.first
                    elif palpite == "X":
                        # Se houver 3 colunas, o índice 1 é o Empate.
                        # Se houver apenas 2, o sistema decide se o X está disponível.
                        alvo = odds.nth(1) if count_odds > 1 else None
                        if alvo:
                            txt = await alvo.inner_text()
                            print(f"   🔍 [DEBUG] Alvo Empate detectado como: {txt.strip()}")
                    else: # Palpite "2" (Derrota)
                        # Se count_odds for 3, a derrota é o índice 2 (last).
                        # Se for 2, e não for empate, pode ser um mercado sem empate.
                        alvo = odds.last if count_odds >= 2 else None
                        if alvo:
                            txt = await alvo.inner_text()
                            print(f"   🔍 [DEBUG] Alvo Derrota detectado como: {txt.strip()}")
                    # if palpite == "1":
                    #     alvo = odds.first
                    # elif palpite == "2":
                    #     # Se houver apenas 2 opções (1 e X), clica no last se quiser o segundo mercado, 
                    #     # ou retorna None se a vitória do visitante não existir no grid.
                    #     alvo = odds.last if count_odds > 2 else None
                    #     print(f"   \n\n Caí na DERROTA, count_odds: {count_odds} \n\n alvo: {await alvo.inner_text() if alvo else 'None'} \n\n")

                    # else: # Palpite "X" (Empate)
                    #     # Se houver 3 colunas, o índice 1 é o meio. Se houver 2 colunas, o 'X' é o índice 1 (last).
                    #     alvo = odds.nth(1) if count_odds > 1 else None
                    #     print(f"   \n\n Caí no empate, count_odds: {count_odds} \n\n alvo: {await alvo.inner_text() if alvo else 'None'} \n\n")

                    if alvo:
                        # Scroll nativo para visibilidade
                        await alvo.scroll_into_view_if_needed()
                        await asyncio.sleep(0.5)

                        # Clique forçado com timeout de segurança
                        await alvo.click(force=True, timeout=5000)
                        print(f"   ✅ Selecionado: {nome_time}")
                    else:
                        print(f"   ⚠️ Opção {palpite} indisponível para {nome_time}")

                    await asyncio.sleep(1)

                except Exception as e:
                    print(f"   ❌ Erro em {nome_time}: {str(e)[:50]}...")

            print("\n🔍 Validando Cupom...")
            try:
                btn_aposta = page.get_by_role("button").filter(has_text="Fazer aposta").first
                await btn_aposta.wait_for(state="visible", timeout=5000)
                print("   ✅ [OK] Bilhete pronto.")
            except:
                print("   ⚠️ Cupom incompleto.")

        print("\n🏁 Processo finalizado com sucesso.")
        await asyncio.sleep(5)
        await context.close()

if __name__ == "__main__":
    asyncio.run(run())