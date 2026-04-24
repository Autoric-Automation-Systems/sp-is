"""Módulo de verificação de GPIO, portas físicas e periféricos do Raspberry Pi"""
import os
import subprocess
import glob


class GpioChecker:
    """Verifica status de GPIO, HDMI, USB, Ethernet e câmera no Raspberry Pi"""

    @staticmethod
    def gpio_info():
        """Retorna dicionário com status completo do GPIO"""
        info = {
            "bibliotecas": [],
            "modos": {},
            "pinos_ocupados": [],
            "pinos_disponiveis": [],
        }

        # Verifica RPi.GPIO
        try:
            import RPi.GPIO as GPIO
            info["bibliotecas"].append("RPi.GPIO")
            info["modos"]["RPi.GPIO"] = {
                "BOARD": hasattr(GPIO, "BOARD"),
                "BCM": hasattr(GPIO, "BCM"),
                "versao": getattr(GPIO, "VERSION", "desconhecida"),
            }
            # Tenta ler o modo atual
            try:
                info["modos"]["RPi.GPIO"]["modo_atual"] = GPIO.getmode()
            except:
                info["modos"]["RPi.GPIO"]["modo_atual"] = "Não configurado"
        except ImportError:
            pass

        # Verifica gpiozero
        try:
            import gpiozero
            info["bibliotecas"].append("gpiozero")
            info["modos"]["gpiozero"] = {
                "versao": getattr(gpiozero, "__version__", "desconhecida"),
            }
        except ImportError:
            pass

        # Verifica /dev/gpiomem
        info["dev_gpiomem"] = os.path.exists("/dev/gpiomem")

        # Verifica /sys/class/gpio
        gpio_sys = "/sys/class/gpio"
        if os.path.isdir(gpio_sys):
            try:
                exported = [d for d in os.listdir(gpio_sys) if d.startswith("gpio") and d[4:].isdigit()]
                info["pinos_ocupados"] = sorted(exported)
            except:
                pass

        # Verifica wiringpi se existir
        try:
            result = subprocess.run(["gpio", "-v"], capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                info["bibliotecas"].append("wiringPi")
        except:
            pass

        # Verifica pigpio
        try:
            import pigpio  # type: ignore
            info["bibliotecas"].append("pigpio")
        except ImportError:
            pass

        return info

    @staticmethod
    def gpio_read_all():
        """Tenta ler valores de todos os GPIOs via /sys/class/gpio"""
        resultados = {}
        gpio_base = "/sys/class/gpio"
        if not os.path.isdir(gpio_base):
            return resultados
        try:
            for d in os.listdir(gpio_base):
                if d.startswith("gpio") and d[4:].isdigit():
                    num = d[4:]
                    value_path = os.path.join(gpio_base, d, "value")
                    direction_path = os.path.join(gpio_base, d, "direction")
                    if os.path.exists(value_path) and os.path.exists(direction_path):
                        with open(direction_path) as f:
                            direction = f.read().strip()
                        with open(value_path) as f:
                            value = f.read().strip()
                        resultados[int(num)] = {"direction": direction, "value": value}
        except:
            pass
        return resultados

    @staticmethod
    def usb_ports():
        """Lista dispositivos USB conectados"""
        count = 0
        try:
            result = subprocess.run(["lsusb"], capture_output=True, text=True, timeout=3)
            lines = [l for l in result.stdout.strip().split("\n") if l.strip()]
            # Filtra hubs raiz Linux Foundation
            reais = [l for l in lines if "Linux Foundation" not in l and "0000:0000" not in l]
            count = len(reais)
        except:
            pass
        return count

    @staticmethod
    def hdmi_status():
        """Verifica status HDMI via tvservice"""
        try:
            result = subprocess.run(["tvservice", "-s"], capture_output=True, text=True, timeout=3)
            if "PAL" in result.stdout or "NTSC" in result.stdout or "HDMI" in result.stdout or "connected" in result.stdout.lower():
                return True, result.stdout.strip()
            return False, "HDMI inativo"
        except:
            pass
        # Fallback /sys/class/drm
        try:
            for entry in os.listdir("/sys/class/drm"):
                if "HDMI" in entry or "hdmi" in entry:
                    status_path = f"/sys/class/drm/{entry}/status"
                    if os.path.exists(status_path):
                        with open(status_path) as f:
                            status = f.read().strip()
                            if "connected" in status:
                                return True, f"HDMI conectado ({entry})"
        except:
            pass
        return False, "HDMI não detectado"

    @staticmethod
    def ethernet_status():
        """Verifica se interfaces de rede estão ativas"""
        import psutil
        try:
            stats = psutil.net_if_stats()
            for name, s in stats.items():
                if any(x in name for x in ["eth", "enx", "wlan", "Wi-Fi"]):
                    if s.isup:
                        return True, f"{name} ativo"
            return False, "Nenhuma interface ativa"
        except:
            return False, "Erro ao verificar"

    @staticmethod
    def i2c_detected():
        """Verifica dispositivos I2C"""
        try:
            result = subprocess.run(["i2cdetect", "-y", "1"], capture_output=True, text=True, timeout=3)
            lines = result.stdout.strip().split("\n")
            dispositivos = []
            for line in lines[1:]:  # Pula cabeçalho
                parts = line.split()
                for p in parts[1:]:
                    if p not in ["--", "UU"] and len(p) == 2:
                        try:
                            int(p, 16)
                            dispositivos.append(p)
                        except:
                            pass
            return dispositivos
        except:
            return []

    @staticmethod
    def spi_detected():
        """Verifica se SPI está habilitado"""
        try:
            devices = sorted(glob.glob("/dev/spidev*"))
            return devices
        except:
            return []

    @staticmethod
    def pinctrl_status():
        """Lê status REAL dos 40 pinos via pinctrl"""
        pinos = {}
        try:
            result = subprocess.run(["pinctrl", "get"], capture_output=True, text=True, timeout=3)
            for line in result.stdout.strip().split("\n"):
                # Formato: "0: ip    pu | hi // ID_SDA/GPIO0 = input"
                if ":" not in line:
                    continue
                
                try:
                    # Extract GPIO number
                    gpio_num = int(line.split(":")[0].strip())
                    
                    # Remove o número e pega o resto
                    colon_pos = line.index(":")
                    rest = line[colon_pos+1:].lstrip()  # Remove o ':' e espaços
                    
                    # Separa por '//' 
                    if "//" in rest:
                        status_part, func_part = rest.split("//", 1)
                    else:
                        status_part = rest
                        func_part = ""
                    
                    status_part = status_part.strip()  # "ip    pu | hi"
                    func_part = func_part.strip()
                    
                    # Parse status
                    if "|" in status_part:
                        func_info, value = status_part.split("|", 1)
                        value = value.strip()
                    else:
                        func_info = status_part
                        value = "?"
                    
                    # Parse modo e pull
                    tokens = func_info.strip().split()
                    mode = tokens[0] if tokens else "?"
                    pull = tokens[1] if len(tokens) > 1 else "?"
                    
                    # Extrai função
                    if "=" in func_part:
                        func_name = func_part.split("=", 1)[1].strip()
                    else:
                        func_name = func_part
                    
                    pinos[gpio_num] = {
                        "mode": mode,
                        "pull": pull,
                        "value": value,
                        "function": func_name
                    }
                except:
                    pass
        except:
            pass
        return pinos

    @staticmethod
    def onewire_detected():
        """Verifica dispositivos 1-Wire"""
        try:
            if os.path.isdir("/sys/bus/w1/devices"):
                devices = [d for d in os.listdir("/sys/bus/w1/devices") if d.startswith("28-") or d.startswith("10-")]
                return devices
        except:
            pass
        return []

    @staticmethod
    def temperatura_cpu():
        """Lê temperatura da CPU (RPi)"""
        try:
            with open("/sys/class/thermal/thermal_zone0/temp") as f:
                temp = int(f.read().strip()) / 1000.0
                return temp
        except:
            return None

    @staticmethod
    def frequencia_cpu():
        """Lê frequência da CPU (RPi)"""
        try:
            with open("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq") as f:
                freq = int(f.read().strip()) / 1000.0
                return freq
        except:
            return None

    @staticmethod
    def voltagem_cpu():
        """Lê voltagem da CPU via vcgencmd"""
        try:
            result = subprocess.run(["vcgencmd", "measure_volts", "core"], capture_output=True, text=True, timeout=2)
            return result.stdout.strip()
        except:
            return None

    @staticmethod
    def throttled_status():
        """Verifica status de throttling (vcgencmd get_throttled)"""
        try:
            result = subprocess.run(["vcgencmd", "get_throttled"], capture_output=True, text=True, timeout=2)
            return result.stdout.strip()
        except:
            return None
