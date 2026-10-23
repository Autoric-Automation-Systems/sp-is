#!/usr/bin/env python3
"""Test script to check GPIO status display"""
from processes.gpio_checker import GpioChecker

print("=== Testando GPIO Status ===\n")

print("1. GPIO Info:")
gi = GpioChecker.gpio_info()
print(f"   Bibliotecas: {gi.get('bibliotecas', [])}")
print(f"   /dev/gpiomem existe: {gi.get('dev_gpiomem', False)}\n")

print("2. GPIO Read All (from /sys/class/gpio):")
gpios = GpioChecker.gpio_read_all()
if gpios:
    for num, info in sorted(gpios.items()):
        print(f"   GPIO {num}: direction={info['direction']}, value={info['value']}")
else:
    print("   Nenhum GPIO exportado em /sys/class/gpio")
    print("   (Isso é normal se nenhuma aplicação exportou GPIO)\n")

print("3. Barramentos I2C:")
i2c = GpioChecker.i2c_detected()
print(f"   Dispositivos I2C: {len(i2c)} encontrados")
if i2c:
    print(f"   Endereços: {i2c}\n")
else:
    print("   Nenhum dispositivo I2C encontrado\n")

print("4. Barramentos SPI:")
spi = GpioChecker.spi_detected()
print(f"   Dispositivos SPI: {len(spi)} encontrados")
if spi:
    print(f"   Dispositivos: {spi}\n")
else:
    print("   Nenhum dispositivo SPI encontrado\n")

print("5. Barramentos 1-Wire:")
ow = GpioChecker.onewire_detected()
print(f"   Dispositivos 1-Wire: {len(ow)} encontrados")
if ow:
    print(f"   Dispositivos: {ow}\n")
else:
    print("   Nenhum dispositivo 1-Wire encontrado\n")

print("\n=== Diagnóstico ===")
if not gpios:
    print("⚠ PROBLEMA: Nenhum GPIO está exportado em /sys/class/gpio")
    print("  - Isso faz com que os pinos não mostrem status 'HIGH/LOW'")
    print("  - Os pinos aparecerão em cinza (#555) indicando 'Não exportado'")
    print("  - Para exportar um pino manualmente:")
    print("    echo <BCM_NUMBER> > /sys/class/gpio/export")
    print("    echo in > /sys/class/gpio/gpio<BCM_NUMBER>/direction")
else:
    print("✓ GPIOs estão sendo monitorados corretamente")
