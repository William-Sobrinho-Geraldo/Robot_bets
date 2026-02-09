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

async def run():
    print("\n" + "="*30)
    print("🚀 PLAYWRIGHT: MODO PERSISTENTE (RESETS)")
    print("="*30)

    # Mudamos o nome da pasta para garantir que não haja travas antigas
    perfil_bot = os.path.join(os.getcwd(), "perfil_novo_bot")

    async with async_playwright() as p:
        try:
            # Removido o channel="chrome" para usar o Chromium do Playwright
            # Isso isola o robô do seu navegador de uso diário
            context = await p.chromium.launch_persistent_context(
                perfil_bot,
                headless=False,
                viewport={'width': 1280, 'height': 800},
                args=["--no-sandbox", "--disable-dev-shm-usage"]
            )
        except Exception as e:
            print(f"❌ ERRO CRÍTICO: {e}")
            return

        page = context.pages[0] if context.pages else await context.new_page()

        print("🔗 Acessando Superbet...")
        try:
            await page.goto("https://superbet.bet.br/apostas/futebol/brasil/brasileiro-serie-a", wait_until="load")
        except:
            print("⚠️ Timeout, tentando prosseguir...")

        print("⏳ Aguardando renderização (15s)...")
        await asyncio.sleep(15)

        # --- LOOP DE TESTE ---
        for i, bilhete in enumerate(combinacoes[:1], 1):
            print(f"\n--- 🎫 BILHETE DE TESTE #{i} ---")
            
            for j, palpite in enumerate(bilhete):
                nome_time = nomes_dos_jogos[j]
                posicao = 1 if palpite == "1" else (2 if palpite == "X" else 3)
                
                try:
                    print(f"   🔍 Buscando jogo: {nome_time}...")
                    
                    # Localiza a linha do jogo baseada no seu Codegen
                    regex_jogo = re.compile(f"Open.*{nome_time}", re.IGNORECASE)
                    botao_linha = page.get_by_role("button", name=regex_jogo)
                    
                    # Localiza as odds dentro da linha
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

            # --- VALIDAÇÃO ---
            print("\n🔍 Verificando Cupom...")
            try:
                btn_aposta = page.get_by_role("button").filter(has_text="Fazer aposta").first
                if await btn_aposta.is_visible():
                    await destacar_elemento(btn_aposta)
                    print("   ✅ [OK] Botão detectado!")
            except:
                print("   ⚠️ Cupom não identificado.")

        print("\n🏁 Processo finalizado.")
        await asyncio.sleep(10)
        await context.close()

if __name__ == "__main__":
    asyncio.run(run())