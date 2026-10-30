# SP-IS — Smart Plant Inspection System

Aplicação desktop (CustomTkinter) para inspeção visual de garrafas/potes em uma
esteira. Inclui cadastro de receitas por ROI, trigger por botão ou pino GPIO,
expulsor, histórico de capturas, estatísticas e diagnóstico do hardware.

Roda no **Raspberry Pi** (GPIO + câmera CSI) e também em **Windows, macOS e
Linux de mesa** (webcam + I/O simulado), com o mesmo código e a mesma
configuração — veja [Plataformas suportadas](#plataformas-suportadas).

## Navegação

Todas as telas usam o mesmo header, footer e biblioteca visual
([components/ui.py](components/ui.py)), construída sobre **CustomTkinter**
(tema escuro, cantos arredondados e widgets nativos modernos). O menu lateral
oferece botões altos (pensados para tela touch), distribuídos na altura
disponível:

| Tela | Conteúdo |
| --- | --- |
| **Principal** | Vídeo **sempre ao vivo** ocupando o espaço central (trigger e status flutuam sobre a imagem), miniaturas distribuídas na largura, painel com a última captura analisada e suas métricas, trigger manual e estatísticas completas |
| **Receitas** | Criação, edição e exclusão; cada receita tem três ROIs nomeáveis com janela de % de acerto |
| **Configurações** | Câmera, fonte de trigger, tempo do expulsador e pinos de I/O |
| **Usuários** | Placeholder (credenciais via variáveis de ambiente) |
| **Diagnósticos** | Sensores/saídas, CPU, memória, disco, GPIO, rede e sistema |
| **Ajuda** | Passo a passo de operação e atalhos |
| **Sobre** | Descrição do aplicativo, recursos e ambiente |

A **receita em uso** é escolhida no header e vale para todas as telas; ao lado
ficam o resumo de estatísticas (total, OK, NOK, aprovação e tempo médio).

A aplicação inicia em modo **visitante** (sem usuário). Receitas e Configurações
exigem login.

A navegação é feita em um shell persistente: header, footer, menu lateral e
páginas ficam em cache e são apenas alternados (`tkraise`), sem reconstrução —
por isso a troca de tela não pisca e clicar no item já ativo não faz nada.

A janela inicia em modo **windowed**; `SPIS_WINDOW=fullscreen` habilita tela cheia.

## Estrutura

```
app.py                 Janela, rotas e ciclo de vida das views
run.bat                Atalho de execução no Windows (cria o .venv e abre o app)
paths.py               Caminhos absolutos do projeto
platform_support.py    Detecção de SO e de recursos de hardware (GPIO/CSI)
components/            Layout, sidebar, header, footer, ROI, câmera e UI padrão
  ui.py                Botões, labels, painéis, badges, cards, formulários e scroll
views/                 Páginas do shell (principal, receitas, configurações, ajuda, sobre)
views/diagnosis/       Abas do diagnóstico (I/O, CPU, memória, disco, GPIO, rede)
services/              Config, receitas, visão, ciclo, banco, histórico, I/O e trigger
processes/             Integração com SO/hardware (psutil, GPIO, câmera)
styles/theme.py        Paleta, tipografia e espaçamentos
styles/fonts.py        Família tipográfica por plataforma (SPIS_FONT)
tools/                 Gerador do material promocional (make_promo_pdf.py)
data/                  Configuração, receitas (JSON), imagens de referência e frames da simulação
tests/                 Testes de serviços e da câmera simulada (unittest)
```

## Requisitos

### Raspberry Pi (hardware completo)

```bash
sudo apt install python3-picamera2 python3-opencv python3-pil python3-psutil \
                 python3-tk python3-gpiozero
pip install customtkinter
```

### Windows / macOS / Linux de mesa (webcam)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1      # Linux/macOS: . .venv/bin/activate
pip install -r requirements.txt
python app.py
```

No Prompt de Comando use `.venv\Scripts\activate.bat`; se a política do
PowerShell bloquear o script de ativação, rode
`Set-ExecutionPolicy -Scope Process RemoteSigned`.

No dia a dia no Windows, use **duplo clique em [run.bat](run.bat)**: ele
reaproveita o `.venv` (ou cria e instala as dependências na primeira execução)
e abre o aplicativo. A janela de console mostra os logs — fechá-la encerra o
app.

No Linux de mesa, instale o Tkinter pelo gerenciador de pacotes
(`sudo apt install python3-tk`). No Raspberry Pi, use sempre os pacotes do
sistema para OpenCV/Pillow/psutil/picamera2.

## Plataformas suportadas

A escolha de backend é automática e fica isolada em
[platform_support.py](platform_support.py):

| Recurso | Raspberry Pi (Linux ARM) | Windows / macOS / Linux de mesa |
| --- | --- | --- |
| Interface, receitas, histórico, estatísticas | ✅ | ✅ |
| Câmera | CSI via picamera2 | webcam via OpenCV (DirectShow no Windows) |
| Entradas/saídas, expulsor, LED, trigger por pino | gpiozero / RPi.GPIO | simulado (sem GPIO) |
| Diagnóstico | CPU, memória, disco, rede + GPIO, pinctrl, vcgencmd, HDMI, I2C/SPI/1-Wire | CPU, memória, disco, rede |
| Câmera sintética (`SPIS_CAMERA=synthetic`) | ✅ | ✅ |

Sem GPIO físico, o serviço de I/O cai automaticamente em modo **simulado** — a
tela de Configurações e a aba I/O do diagnóstico indicam isso. O arquivo
`data/config.json` é o mesmo nos dois alvos, então a configuração do Pi pode ser
copiada para o PC (os pinos BCM ficam inertes fora do Raspberry Pi).

## Execução

```bash
python app.py        # aplicação
python dev.py        # recarrega ao alterar arquivos .py
python -m unittest discover -s tests -v
```

No Windows também é possível dar duplo clique em `run.bat`, que usa o `.venv`
do projeto sem precisar abrir o terminal.

O material promocional (A4 retrato, uma página) é gerado a partir dos dados
reais do projeto com `python tools/make_promo_pdf.py` — o PDF fica em
`SP-IS-promocional.pdf`.

### Variáveis de ambiente

| Variável | Padrão | Descrição |
| --- | --- | --- |
| `SPIS_CAMERA` | — | Sobrescreve a câmera: `auto`, `picamera`, `opencv:<idx>` ou `synthetic` |
| `SPIS_CAMERA_INDEX` | `0` | Índice padrão do backend OpenCV usado em `auto` |
| `SPIS_WINDOW` | `windowed` | `windowed`, `fullscreen` ou `zoomed` |
| `SPIS_ADMIN_USER` / `SPIS_ADMIN_PASSWORD` | `admin` / `admin` | Credenciais de acesso |
| `SPIS_FONT` | família padrão do SO | Força a família tipográfica da interface (`Segoe UI`, `DejaVu Sans`...) |
| `SPIS_SIM_DIR` | `data/simulation` | Pasta com as imagens exibidas pela câmera simulada |
| `SPIS_SIM_INTERVAL` | `4` | Segundos que cada imagem da simulação fica no ar |
| `SPIS_LOG_LEVEL` | `INFO` | Nível de log |

### Câmera simulada com imagens próprias

O backend `synthetic` usa as imagens de `data/simulation/` (`.jpg`, `.jpeg`,
`.png`, `.bmp`, `.webp`), exibindo uma por vez na ordem alfabética dos nomes e
alternando a cada `SPIS_SIM_INTERVAL` segundos (padrão `4`). Cada imagem é
recortada para 640×480 sem distorção. A pasta é relida a cada segundo — e a data
de modificação de cada arquivo é comparada —, então adicionar, remover ou
**substituir uma imagem (mesmo nome, conteúdo novo)** aparece em ~1 s, com o
aplicativo aberto.

Sem imagens na pasta, a câmera simulada desenha a cena de teste com e sem tampa
(alternando a cada 4 s), permitindo validar UI, ROI, trigger e estatísticas no PC.

`data/images/` é outra pasta: guarda as **fotos de referência das receitas**,
gerenciadas pelo próprio app (renomear ou excluir uma receita altera esses
arquivos). Não coloque os frames de simulação lá.

## Configuração (`data/config.json`)

```json
{
  "active_recipe": "200ml",
  "camera_source": "auto",
  "rotate_180": true,
  "trigger": { "pin": 17 },
  "ejector": { "time_ms": 100 },
  "io": {
    "presence_pin": 27,
    "ejection_pin": 22,
    "ejector_pin": 23,
    "led_pin": 24,
    "active_high": true
  }
}
```

- `ejector.time_ms`: duração do pulso do expulsor quando um ROI reprova.
- `io`: pinos BCM dos sensores e saídas. Ajuste conforme a fiação real.
- Chaves ausentes são completadas com os padrões e a escrita é atômica.
- Os antigos `threshold`/`min_brightness` (limiar global) foram removidos: o
  critério agora é por ROI, dentro da receita.

## Modelo de avaliação (receitas e ROIs)

Cada receita (`data/recipes/<nome>.json`) tem **três ROIs de inspeção** e a
imagem de referência capturada no cadastro:

```json
{
  "name": "200ml",
  "image": "data/images/200ml.jpg",
  "rois": [
    { "name": "Tampa", "roi": { "x1": 275, "y1": 0, "x2": 365, "y2": 31 },
      "min_match": 85.0, "max_match": 100.0 },
    { "name": "Nível", "roi": { "x1": 275, "y1": 38, "x2": 365, "y2": 69 },
      "min_match": 85.0, "max_match": 100.0 },
    { "name": "ROI 3", "roi": { "x1": 256, "y1": 374, "x2": 384, "y2": 446 },
      "min_match": 0.0, "max_match": 100.0 }
  ]
}
```

- **Nome editável** por ROI (padrões `Tampa`, `Nível` e `ROI 3`); os nomes
  reprovados aparecem no resultado — um só (`ERRO: NÍVEL`) ou **todos** quando
  mais de um ROI falha (`ERRO: NÍVEL + RÓTULO`).
- **Janela de acerto** em % por ROI: a peça é aprovada quando o % de acerto fica
  entre `min_match` e `max_match`.
- O **% de acerto é o SSIM** entre o ROI do frame ao vivo e o mesmo ROI da
  imagem de referência: 100% = região idêntica; valores menores = desvio
  (tampa ausente, nível diferente, peça torta, sujeira, luz fora do padrão).
- No editor, além do mouse, há campos X1/Y1/X2/Y2 (tela touch) com botões
  − / + de 5 px, e o campo **Agora** mostra o % ao vivo para calibrar a janela.
- Cores: cada ROI tem cor própria (azul, âmbar e violeta) usada no overlay, nos
  cards e nos nomes; **verde e vermelho ficam reservados ao resultado**
  (aprovado/reprovado).
- Receitas antigas com um único `roi` são convertidas automaticamente: o ROI
  original vira `Tampa` e as regiões que faltam são criadas logo abaixo, com
  janela **0–100%** (não reprovam nada até serem calibradas no editor). O mesmo
  vale para receitas salvas com menos de três ROIs.

### Fluxo de inspeção

1. O trigger (botão ou PIN) dispara `RunCycle`.
2. A câmera entrega o frame mais recente (BGR, 640×480) em thread separada.
3. Cada ROI é recortado do frame e comparado com o mesmo recorte da referência;
   o % de acerto é comparado com a janela configurada.
4. Resultados: `OK`, `ERRO: <ROI>` (lista todos os ROIs reprovados),
   `SEM REFERÊNCIA`, `ROI INVÁLIDO` ou `CÂMERA INDISPONÍVEL`.
5. Cada ciclo pulsa o LED de trigger; reprovação por qualquer ROI dispara o expulsor.
6. O frame é armazenado em JPEG no histórico (SQLite), junto do % de cada ROI, e
   o vídeo ao vivo continua rodando.

## Estatísticas e banco de dados

O resumo (total, OK, NOK, aprovação e tempo médio) aparece no **header**, em
todas as telas. **Estatísticas completas** detalha por resultado e por receita.

As inspeções são gravadas em SQLite (`data/sp_is.db`) pelo
[services/database.py](services/database.py):

- tabela `inspections` com timestamp, receita, resultado, métricas e o frame JPEG;
- `InspectionRepository` concentra escrita e consultas agregadas;
- a interface já está isolada para trocar SQLite por um banco online
  (PostgreSQL/MySQL) sem alterar as views — basta implementar outro repositório.

O banco é criado automaticamente e não deve ser versionado (veja `.gitignore`).

## Limitações conhecidas

- Autenticação única (`admin`) e tela de usuários ainda é placeholder.
- Cada receita tem exatamente três ROIs (limite atual do modelo).
- O histórico anterior a esta versão não tem % por ROI: as capturas antigas
  aparecem sem métricas (resultado e imagem continuam visíveis).
- O histórico é persistido localmente; a sincronização com banco online ainda não existe.
- A ordem de cor e a rotação de 180° da câmera devem ser validadas no Raspberry Pi.
- Fora do Raspberry Pi não há GPIO: sensores, expulsor, LED e trigger por pino
  funcionam apenas simulados (sem acionar hardware real).
- Temperatura, voltagem, throttling e barramentos (I2C/SPI/1-Wire) só são lidos
  no Linux; em outras plataformas o diagnóstico mostra "não disponível".
