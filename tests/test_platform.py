"""Testes da camada de plataforma (Windows/Linux/Raspberry Pi)."""
import os
import sys
import unittest

import platform_support
from processes.camera_checker import CameraChecker
from processes.gpio_checker import GpioChecker
from styles import fonts


class PlatformFlagsTests(unittest.TestCase):
    def test_flags_match_python_platform(self):
        self.assertEqual(platform_support.LINUX, sys.platform.startswith("linux"))
        self.assertEqual(platform_support.WINDOWS, sys.platform.startswith("win"))
        self.assertEqual(platform_support.MACOS, sys.platform == "darwin")

    def test_system_label_reports_the_running_system(self):
        label = platform_support.system_label()
        self.assertIn(platform_support.SYSTEM_NAME, label)
        if platform_support.is_raspberry_pi():
            self.assertIn("Raspberry Pi", label)

    def test_gpio_support_follows_linux(self):
        self.assertEqual(platform_support.io_hardware_supported(), platform_support.LINUX)

    def test_csi_camera_support_follows_linux(self):
        self.assertEqual(
            platform_support.csi_camera_supported(),
            platform_support.LINUX,
        )
        if not platform_support.LINUX:
            self.assertFalse(platform_support.csi_camera_supported())

    def test_font_family_resolves_to_a_non_empty_name(self):
        family = fonts.family()
        self.assertIsInstance(family, str)
        self.assertTrue(family.strip())

    def test_font_family_can_be_overridden(self):
        os.environ["SPIS_FONT"] = "Courier New"
        try:
            self.assertEqual(fonts.family(), "Courier New")
        finally:
            os.environ.pop("SPIS_FONT", None)
        self.assertNotEqual(fonts.family(), "Courier New")


class UnsupportedPlatformDiagnosticsTests(unittest.TestCase):
    @unittest.skipIf(platform_support.LINUX, "Linux expõe pinos via pinctrl/sysfs")
    def test_gpio_probes_return_empty_results(self):
        self.assertEqual(GpioChecker.pinctrl_status(), {})
        self.assertEqual(GpioChecker.gpio_read_all(), {})
        self.assertEqual(GpioChecker.i2c_detected(), [])
        self.assertEqual(GpioChecker.spi_detected(), [])
        self.assertEqual(GpioChecker.onewire_detected(), [])
        self.assertIsNone(GpioChecker.voltagem_cpu())
        self.assertIsNone(GpioChecker.throttled_status())

    @unittest.skipIf(platform_support.LINUX, "libcamera/raspistill só existem no Raspberry Pi")
    def test_camera_checker_reports_no_sources(self):
        self.assertFalse(CameraChecker.supported())
        self.assertEqual(CameraChecker.check(), {})

    @unittest.skipIf(platform_support.LINUX, "Linux tenta gpiozero/RPi.GPIO antes do simulador")
    def test_io_service_falls_back_to_simulation(self):
        from services.io_service import IOService

        service = IOService()
        try:
            self.assertTrue(service.simulated)
            self.assertEqual(service.backend_name, "simulado")

            service.set_simulated_input("presence", True)
            self.assertTrue(service.read_input("presence"))

            service.write_output("ejector", True)
            self.assertTrue(service.read_output("ejector"))
        finally:
            service.close()


class CameraSourceTests(unittest.TestCase):
    def test_parse_source_variants(self):
        from components.camera_view import _parse_source

        self.assertEqual(_parse_source("auto"), ("auto", None))
        self.assertEqual(_parse_source("opencv:2"), ("opencv", 2))
        self.assertEqual(_parse_source("picamera"), ("picamera", 0))
        self.assertEqual(_parse_source("synthetic"), ("synthetic", None))


if __name__ == "__main__":
    unittest.main()
