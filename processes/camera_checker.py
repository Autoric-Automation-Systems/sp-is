"""Verificação de câmera CSI via libcamera/raspistill (exclusiva do Raspberry Pi).

Em Windows/macOS nada é executado: `supported()` retorna False e a tela de
diagnóstico mostra a câmera em uso a partir das Configurações.
"""
import subprocess

import platform_support


class CameraChecker:
    @staticmethod
    def supported():
        """True apenas quando libcamera/raspistill existem (Raspberry Pi)."""
        return platform_support.csi_camera_supported()

    @staticmethod
    def check():
        """Verifica câmera por libcamera e raspistill apenas"""
        resultados = {}

        if not CameraChecker.supported():
            return resultados

        # libcamera (Bullseye+)
        try:
            result = subprocess.run(["libcamera-hello", "--list"], capture_output=True, text=True, timeout=3)
            if result.stdout.strip():
                resultados["libcamera"] = "Disponivel"
                resultados["libcamera_detalhe"] = result.stdout.strip()[:100]
            else:
                resultados["libcamera"] = "Nenhuma camera"
        except (FileNotFoundError, subprocess.TimeoutExpired):
            resultados["libcamera"] = "Nao disponivel"

        # raspistill (Legacy)
        try:
            result = subprocess.run(["raspistill", "-o", "/dev/null", "-t", "1"],
                                    capture_output=True, text=True, timeout=3)
            if result.returncode == 0:
                resultados["raspistill"] = "Disponivel"
            else:
                resultados["raspistill"] = f"Erro: {result.stderr.strip()[:60]}"
        except (FileNotFoundError, subprocess.TimeoutExpired):
            resultados["raspistill"] = "Nao disponivel"

        resultados["opencv"] = "Nao usado (evita travar camera)"
        return resultados

