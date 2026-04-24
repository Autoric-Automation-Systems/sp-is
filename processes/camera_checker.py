"""Módulo de verificação de câmera no Raspberry Pi - APENAS subprocessos, sem OpenCV"""
import subprocess


class CameraChecker:
    @staticmethod
    def check():
        """Verifica câmera por libcamera e raspistill apenas"""
        resultados = {}

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

