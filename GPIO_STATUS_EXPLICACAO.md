# GPIO Status - Explicação e Soluções

## O Problema

O status dos pinos GPIO não aparecia na aba "GPIO / Portas" do diagnóstico.

## Causas Identificadas

### 1. **Layout incorreto do RPi 4** ❌
- O arquivo original tinha pinos duplicados e em ordem errada
- Exemplo: GPIO27 aparecia duas vezes na mesma linha `(13, "GPIO27", 27, 27, "GPIO27", 14)`

### 2. **SPI detection com bug** ❌
- A função `spi_detected()` estava usando `subprocess.run()` com `shell=True` 
- Isso listava arquivos do diretório em vez de dispositivos em `/dev/spidev*`

### 3. **Nenhum GPIO exportado** ⚠️
- Para ver o status (HIGH/LOW) dos pinos, eles precisam estar **exportados em `/sys/class/gpio`**
- Por padrão, nenhum GPIO está exportado se a aplicação não os usa

## Soluções Implementadas

### 1. **Layout Correto para RPi 4** ✓
```python
LAYOUT = [
    (1,  "3.3V",    None,  None, "5V",      2),
    (3,  "GPIO2",   2,     3,    "GPIO3",   5),
    (7,  "GPIO4",   4,     14,   "GPIO14",  8),
    ...
]
```

### 2. **SPI Detection Corrigido** ✓
```python
def spi_detected():
    """Verifica se SPI está habilitado"""
    try:
        devices = sorted(glob.glob("/dev/spidev*"))
        return devices
    except:
        return []
```

### 3. **Exportação Automática de GPIOs** ✓
Adicionadas duas novas funções em `GpioChecker`:

```python
def export_gpio(gpio_num):
    """Exporta um GPIO para /sys/class/gpio"""
    
def set_gpio_direction(gpio_num, direction="in"):
    """Define a direção de um GPIO (in/out)"""

def export_common_gpios():
    """Exporta GPIOs comuns: [17, 27, 22, 23, 24, 25, 26, 20, 21]"""
```

### 4. **Botão na Interface** ✓
Adicionado botão **"Exportar GPIOs Comuns"** na seção "Bibliotecas GPIO"

## Como Usar

### Opção 1: Usar o Botão (Recomendado)
1. Abra a aba "GPIO / Portas"
2. Clique em "Exportar GPIOs Comuns"
3. Os pinos GPIO 17, 27, 22, 23, 24, 25, 26, 20, 21 aparecerão com status

### Opção 2: Exportar Manualmente via Terminal
```bash
# Exportar um pino específico
echo 17 > /sys/class/gpio/export
echo in > /sys/class/gpio/gpio17/direction

# Para desexportar
echo 17 > /sys/class/gpio/unexport
```

## Entendendo o Status dos Pinos

| Cor | Significado |
|-----|------------|
| 🔴 Vermelho | 3.3V (alimentação) |
| 🟠 Laranja | 5V (alimentação) |
| ⚫ Cinza | GND (terra) |
| 🟢 Verde | HIGH (1 - lógico alto) |
| 🟩 Verde Escuro | LOW (0 - lógico baixo) |
| ⬜ Cinza Claro | Não exportado (sem status) |

## Nota Importante

- Os pinos aparecem em **cinza claro** se não estão exportados
- Isso é **normal e esperado** se sua aplicação não usa GPIO
- Quando exportados, mudam para **verde/verde escuro** conforme o valor (1/0)
- A atualização acontece a cada 2 segundos automaticamente

## Arquivos Modificados

- ✅ `views/diagnosis/tab_gpio.py` - Layout corrigido + botão adicionado
- ✅ `processes/gpio_checker.py` - Funções de export + SPI fix
- ✅ `views/diagnosis_view.py` - Logging de erros adicionado
