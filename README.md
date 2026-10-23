# SP-IS — Smart Plant Inspection System

Aplicação desktop (CustomTkinter) para inspeção visual de garrafas/potes em uma
esteira. Inclui cadastro de receitas por ROI, trigger por botão ou pino GPIO,
expulsor, histórico de capturas, estatísticas e diagnóstico do hardware.

## Navegação

Todas as telas usam o mesmo header, footer e biblioteca visual
([components/ui.py](components/ui.py)), construída sobre **CustomTkinter**
(tema escuro, cantos arredondados e widgets nativos modernos). O menu lateral oferece:

| Tela | Conteúdo |
| --- | --- |
| **Principal** | Vídeo **sempre ao vivo**, painel com a última captura analisada e suas métricas, 10 miniaturas (clique carrega no painel, duplo clique amplia), trigger manual e estatísticas completas |
| **Receitas** | Seletor de receita em uso, criação, edição e exclusão |
| **Configurações** | Câmera, fonte de trigger, tempo do expulsador e pinos de I/O |
| **Usuários** | Placeholder (credenciais via variáveis de ambiente) |
| **Diagnósticos** | Sensores/saídas, CPU, memória, disco, GPIO, rede e sistema |
| **Ajuda** | Passo a passo de operação e atalhos |
| **Sobre** | Descrição do aplicativo, recursos e ambiente |

A aplicação inicia em modo **visitante** (sem usuário). Receitas e Configurações
exigem login; o cabeçalho mostra o resumo de estatísticas em todas as telas.

A navegação é feita em um shell persistente: header, footer, menu lateral e
páginas ficam em cache e são apenas alternados (`tkraise`), sem reconstrução —
por isso a troca de tela não pisca e clicar no item já ativo não faz nada.

A janela inicia em modo **windowed**; `SPIS_WINDOW=fullscreen` habilita tela cheia.

## Estrutura

```
app.py                 Janela, rotas e ciclo de vida das views
paths.py               Caminhos absolutos do projeto
components/            Layout, sidebar, header, footer, ROI, câmera e UI padrão
  ui.py                Botões, labels, painéis, badges, cards, formulários e scroll
views/                 Páginas do shell (principal, receitas, configurações, ajuda, sobre)
views/diagnosis/       Abas do diagnóstico (I/O, CPU, memória, disco, GPIO, rede)
services/              Config, receitas, visão, ciclo, banco, histórico, I/O e trigger
processes/             Integração com SO/hardware (psutil, GPIO, câmera)
styles/theme.py        Paleta, tipografia e espaçamentos
data/                  Configuração, receitas (JSON) e imagens de referência
tests/                 Testes de serviços (unittest)
```

## Requisitos

### Raspberry Pi

```bash
sudo apt install python3-picamera2 python3-opencv python3-pil python3-psutil \
                 python3-tk python3-gpiozero
pip install customtkinter
```

### Desenvolvimento (PC)

```bash
python -m venv .venv
. .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

No Linux, instale o Tkinter pelo gerenciador de pacotes (`sudo apt install python3-tk`).

## Execução

```bash
python app.py        # aplicação
python dev.py        # recarrega ao alterar arquivos .py
python -m unittest discover -s tests -v
```

### Variáveis de ambiente

| Variável | Padrão | Descrição |
| --- | --- | --- |
| `SPIS_CAMERA` | — | Sobrescreve a câmera: `auto`, `picamera`, `opencv:<idx>` ou `synthetic` |
| `SPIS_CAMERA_INDEX` | `0` | Índice padrão do backend OpenCV usado em `auto` |
| `SPIS_WINDOW` | `windowed` | `windowed`, `fullscreen` ou `zoomed` |
| `SPIS_ADMIN_USER` / `SPIS_ADMIN_PASSWORD` | `admin` / `admin` | Credenciais de acesso |
| `SPIS_LOG_LEVEL` | `INFO` | Nível de log |

Sem câmera disponível, o backend `synthetic` gera uma cena com e sem tampa
(alternando a cada 4 s), permitindo validar UI, ROI, trigger e estatísticas no PC.

## Configuração (`data/config.json`)

```json
{
  "threshold": 300,
  "min_brightness": 50,
  "active_recipe": "Pote Plastico",
  "camera_source": "auto",
  "trigger": { "mode": "button", "pin": 17 },
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

- `trigger.mode`: `button` (botão na tela Principal) ou `pin` (entrada GPIO).
- `ejector.time_ms`: duração do pulso do expulsor quando o resultado é
  `ERRO: SEM TAMPA`.
- `io`: pinos BCM dos sensores e saídas. Ajuste conforme a fiação real.
- Chaves ausentes são completadas com os padrões e a escrita é atômica.

### Fluxo de inspeção

1. O trigger (botão ou PIN) dispara `RunCycle`.
2. A câmera entrega o frame mais recente (BGR, 640×480) em thread separada.
3. O ROI da receita é recortado/limitado ao frame; Canny mede bordas e brilho.
4. Resultados: `OK`, `ERRO: SEM TAMPA`, `SEM GARRAFA`, `ROI INVÁLIDO` ou
   `CÂMERA INDISPONÍVEL`.
5. Cada ciclo pulsa o LED de trigger; reprovação por tampa dispara o expulsor.
6. O frame é armazenado em JPEG no histórico (SQLite) e o vídeo ao vivo continua rodando.

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
- Calibração de `threshold`/`min_brightness` é global, não por receita.
- O histórico é persistido localmente; a sincronização com banco online ainda não existe.
- A ordem de cor e a rotação de 180° da câmera devem ser validadas no Raspberry Pi.
