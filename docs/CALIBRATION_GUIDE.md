# Guia de Calibração do ARK Reroll

## Por que calibrar é necessário?
Diferente de bots baseados em injeção de memória (que podem resultar em banimentos), o **ARK Reroll Automator** funciona lendo a tela exatamente como um ser humano faria. Como cada jogador possui um monitor de tamanho diferente, joga em resoluções distintas e utiliza configurações de escala de interface (UI Scale) próprias, o aplicativo não tem como "adivinhar" onde os botões estão. 

Você precisa calibrar as coordenadas uma única vez para ensinar ao bot onde ele deve clicar e onde ele deve ler.

## Tabela de Hotkeys

| Tecla | Função | O que faz |
|-------|---------|-----------|
| **F10** | Posição do Item | Salva a coordenada (X,Y) do item que você quer rolar. |
| **F8**  | Botão REROLL | Salva a coordenada (X,Y) do botão de Imbue/Upgrade. |
| **F11** | Sup. Esq. Área OCR | Define o ponto de Início (Canto Superior Esquerdo) do recorte de leitura. |
| **F12** | Inf. Dir. Área OCR | Define o ponto Final (Canto Inferior Direito) do recorte de leitura. |
| **F6**  | Iniciar Reroll | Inicia o loop de automação imediatamente. |
| **HOME**| Parar Emergência | Interrompe o bot na hora. |

---

## Passo a Passo Ilustrado

### 1. Preparação da Mesa
Sempre coloque o item que você quer rolar no **PRIMEIRO SLOT** da Imbue Station. Isso garante que o item não vai "pular" para outro slot quando os seus recursos acabarem.
Faça um Reroll manual clicando no botão uma vez para gerar os primeiros atributos.

### 2. Configurando o Clique
- Mova o mouse para cima do item no inventário da mesa e aperte **F10**.
- Mova o mouse para cima do botão verde de Imbue/Reroll e aperte **F8**.

### 3. A Grande Sacada: A Área de Leitura (OCR)
O balão preto de atributos (Tooltip) só aparece quando o mouse está em cima do item. Se você tentar marcar o F12 exatamente na bordinha do tooltip, você fatalmente vai arrastar o mouse para fora do item, o tooltip vai sumir e você vai se perder.

**A regra de ouro é: Capture toda a área vazia!**
1. Coloque o mouse lá no topo superior esquerdo da seção de inventário e aperte **F11**.
2. Arraste o mouse livremente para o fundo à direita, cobrindo todo o espaço vazio onde a caixa de atributos costuma aparecer, e aperte **F12**. 
*(Não tem problema nenhum o tooltip desaparecer da tela na hora de apertar o F12! O programa vai salvar a tela corretamente).*

> **ATENÇÃO:** O botão de Reroll **NÃO** deve ficar dentro dessa área virtual que você marcou com F11 e F12.

---

## Troubleshooting (Problemas Comuns)

**Problema:** O bot inicia, a tela pisca e ele diz "Stat não apareceu", mesmo eu vendo o stat na tela.
**Solução:** 
1. Verifique se o seu jogo está em modo *Windowed Fullscreen* ou *Borderless*.
2. A sua área de OCR pode estar muito pequena. Refaça o F11 e F12 abrangendo um espaço muito maior para a direita e para baixo.
3. Se você estiver jogando em outra língua que não seja o Inglês, os nomes dos atributos mudam e o bot não vai achá-los.

**Problema:** O bot travou em um número que não faz sentido (ex: leu 20% ao invés de 50%).
**Solução:** A área do seu OCR (F11/F12) englobou o botão de Reroll ou a quantidade de recursos necessários. Refaça a calibração do F11/F12 focando **apenas** na área onde o tooltip surge, deixando os recursos de fora.

**Problema:** O overlay sumiu!
**Solução:** Jogos em "Exclusive Fullscreen" bloqueiam janelas sobrepostas do Windows. Troque as configurações de vídeo do ARK para "Windowed Fullscreen".

## Dicas para melhorar a precisão
- Aumente o *Delay do Bot (segundos)* para `1.0` ou `1.2` se você joga em servidores com ping alto. O servidor demora um pouco para atualizar o item após o clique do Reroll.
- Evite deixar chats globais abertos atrás da área do Tooltip. O texto verde do chat se mistura com o preto transparente do Tooltip e confunde a leitura do Windows.
