# GPIO, sensores e saídas

## Leitura da pinagem (aba GPIO / Portas)

A aba **GPIO / Portas** do Diagnóstico lê o estado real dos 40 pinos com
`pinctrl get` (Raspberry Pi OS). Não é necessário exportar pinos em
`/sys/class/gpio` para visualizar modo, pull e nível lógico.

Se `pinctrl` não estiver disponível (por exemplo, em um PC), a tabela mostra
`--` e a lista de GPIOs exportados via sysfs continua sendo exibida quando
existir.

## Sensores e saídas da inspeção (aba Sensores / Saídas)

A aba **Sensores / Saídas** usa o `IOService`:

- `presence_pin` — sensor de presença de peça
- `ejection_pin` — sensor de peça na expulsão
- `trigger.pin` — entrada de trigger (quando a fonte é PIN)
- `ejector_pin` — saída do expulsor
- `led_pin` — saída do LED de trigger

Os pinos são configuráveis em **Configurações → Entradas e saídas (I/O)**.
O backend é escolhido automaticamente:

1. `gpiozero` (preferencial no Raspberry Pi OS);
2. `RPi.GPIO`;
3. simulado (PC sem GPIO) — nesse modo, a aba permite simular os sensores.

## Comportamento no ciclo de inspeção

- Cada ciclo pulsa o LED de trigger por 120 ms.
- Quando o resultado é `ERRO: SEM TAMPA`, o expulsor é acionado pelo tempo
  configurado em **Expulsador** (padrão 100 ms).
- `SEM GARRAFA`, `ROI INVÁLIDO` e `CÂMERA INDISPONÍVEL` não acionam o expulsor.

## Diagnóstico de problemas

- **Sensores sempre inativos:** verifique o pino BCM configurado, o nível
  elétrico (entradas ativas em nível alto) e o `GND` comum.
- **`gpiozero` não disponível:** instale com
  `sudo apt install python3-gpiozero` ou use `RPi.GPIO`.
- **Saídas não acionam:** confirme o mapeamento de pinos em Configurações e
  use o botão **Testar** na aba Sensores / Saídas.
