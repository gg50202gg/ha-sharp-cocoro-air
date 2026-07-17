"""Pure protocol tests; Home Assistant is not required."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
import types
import unittest


API_PATH = (
    Path(__file__).parents[1]
    / "custom_components"
    / "sharp_cocoro_air"
    / "api.py"
)


class _ClientError(Exception):
    pass


aiohttp_stub = types.ModuleType("aiohttp")
aiohttp_stub.ClientError = _ClientError
aiohttp_stub.ClientSession = object
sys.modules.setdefault("aiohttp", aiohttp_stub)
package_stub = types.ModuleType("sharp_cocoro_air")
package_stub.__path__ = [str(API_PATH.parent)]
sys.modules.setdefault("sharp_cocoro_air", package_stub)
spec = spec_from_file_location("sharp_cocoro_air.api", API_PATH)
api = module_from_spec(spec)
sys.modules[spec.name] = api
spec.loader.exec_module(api)


def item(code, value_type, value):
    return {
        "statusCode": code,
        "valueType": value_type,
        "valueSingle": {"code": value} if value_type == "valueSingle" else None,
        "valueRange": {"code": value} if value_type == "valueRange" else None,
        "valueBinary": {"code": value} if value_type == "valueBinary" else None,
    }


class DecodeStatusTests(unittest.TestCase):
    def test_decodes_fp_s90t_status(self):
        payload = {
            "deviceStatus": {
                "status": [
                    item("80", "valueSingle", "30"),
                    item("84", "valueRange", "0006"),
                    item("85", "valueRange", "000000F9"),
                    item("F1", "valueBinary", "64009D1B3903" + "00" * 37),
                    item("F3", "valueBinary", "110000002000" + "00" * 22),
                ]
            }
        }
        state = api.decode_status(payload)
        self.assertTrue(state.is_on)
        self.assertEqual(state.preset_mode, "auto")
        self.assertEqual(state.temperature, 27)
        self.assertEqual(state.humidity, 57)
        self.assertEqual(state.power_w, 6)
        self.assertEqual(state.energy_kwh, 0.25)

    def test_rejects_missing_device_status(self):
        with self.assertRaises(api.CocoroAirError):
            api.decode_status({})

    def test_decodes_comfort_mode(self):
        payload = {
            "deviceStatus": {
                "status": [item("F3", "valueBinary", "110000004000" + "00" * 22)]
            }
        }
        self.assertEqual(api.decode_status(payload).preset_mode, "feel")

    def test_filters_sensor_sentinel_values(self):
        payload = {
            "deviceStatus": {
                "status": [item("F1", "valueBinary", "000000FF0600")]
            }
        }
        state = api.decode_status(payload)
        self.assertIsNone(state.temperature)
        self.assertIsNone(state.humidity)


if __name__ == "__main__":
    unittest.main()
