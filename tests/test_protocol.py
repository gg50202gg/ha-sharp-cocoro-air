"""Pure protocol tests; Home Assistant is not required."""

from importlib.util import module_from_spec, spec_from_file_location
import ast
from pathlib import Path
from http.cookies import SimpleCookie
import sys
import types
import unittest
from unittest.mock import AsyncMock, Mock


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


class FakeResponse:
    """Exercise request handling without cloud access or real credentials."""

    def __init__(self, data=None, *, status=200, cookies="", error=None):
        self.data = {} if data is None else data
        self.status = status
        self.cookies = SimpleCookie(cookies)
        self.error = error

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    def raise_for_status(self):
        if self.status >= 400:
            raise api.ClientError("URL contains private-app-secret")

    async def json(self, **kwargs):
        if self.error:
            raise self.error
        return self.data


class ApiRequestTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.session = Mock()
        self.client = api.CocoroAirApi(
            self.session,
            api.CocoroAirConfig(
                base_url="https://example.invalid/",
                app_secret="private-app-secret",
                terminal_app_id="test-terminal",
                box_id="test-box",
                device_id="test-device",
                echonet_node="test-node",
                echonet_object="test-object",
                user_agent="test-agent",
            ),
        )

    async def test_login_api_error_is_auth_error(self):
        self.session.request.return_value = FakeResponse({"errorCode": "denied"})
        with self.assertRaises(api.CocoroAirAuthError):
            await self.client.async_login()
        self.assertEqual(self.session.request.call_count, 1)

    async def test_other_api_error_is_not_auth_error(self):
        self.session.request.return_value = FakeResponse({"errorCode": "private-data"})
        with self.assertRaises(api.CocoroAirError) as result:
            await self.client._request("GET", "control/deviceStatus")
        self.assertNotIsInstance(result.exception, api.CocoroAirAuthError)
        self.assertNotIn("private-data", str(result.exception))

    async def test_invalid_json_becomes_api_error(self):
        self.session.request.return_value = FakeResponse(error=ValueError("bad JSON"))
        with self.assertRaisesRegex(api.CocoroAirError, "invalid JSON"):
            await self.client._request("GET", "control/deviceStatus")

    async def test_non_object_json_becomes_api_error(self):
        self.session.request.return_value = FakeResponse([])
        with self.assertRaisesRegex(api.CocoroAirError, "unexpected response"):
            await self.client._request("GET", "control/deviceStatus")

    async def test_transport_error_hides_credential_url(self):
        self.session.request.return_value = FakeResponse(status=503)
        with self.assertRaises(api.CocoroAirConnectionError) as result:
            await self.client._request("GET", "control/deviceStatus")
        self.assertNotIn("private-app-secret", str(result.exception))
        self.assertTrue(result.exception.__suppress_context__)

    async def test_timeout_becomes_connection_error(self):
        self.session.request.side_effect = TimeoutError()
        with self.assertRaises(api.CocoroAirConnectionError):
            await self.client._request("GET", "control/deviceStatus")

    async def test_expired_session_logs_in_and_retries_once(self):
        self.client._cookies["session"] = "expired"
        self.session.request.side_effect = [
            FakeResponse(status=401),
            FakeResponse(cookies="session=renewed"),
            FakeResponse({"deviceStatus": {"status": []}}),
        ]
        state = await self.client.async_get_status()
        self.assertFalse(state.is_on)
        self.assertEqual(self.session.request.call_count, 3)
        self.assertEqual(self.client._cookies, {"session": "renewed"})
        calls = self.session.request.call_args_list
        self.assertTrue(calls[1].args[1].endswith("setting/login/"))
        self.assertEqual(calls[0].kwargs["params"], calls[2].kwargs["params"])

    async def test_repeated_unauthorized_does_not_loop(self):
        self.client._cookies["session"] = "expired"
        self.session.request.side_effect = [
            FakeResponse(status=403),
            FakeResponse(cookies="session=renewed"),
            FakeResponse(status=403),
        ]
        with self.assertRaises(api.CocoroAirAuthError):
            await self.client.async_get_status()
        self.assertEqual(self.session.request.call_count, 3)

    async def test_login_unauthorized_does_not_retry(self):
        self.session.request.return_value = FakeResponse(status=401)
        with self.assertRaises(api.CocoroAirAuthError):
            await self.client.async_login()
        self.assertEqual(self.session.request.call_count, 1)

    async def test_login_connection_failure_is_not_auth_failure(self):
        self.session.request.return_value = FakeResponse(status=503)
        with self.assertRaises(api.CocoroAirConnectionError):
            await self.client.async_login()


class FanTurnOnContractTests(unittest.IsolatedAsyncioTestCase):
    """Run the actual method in isolation without replacing HA's installed modules."""

    def setUp(self):
        tree = ast.parse((API_PATH.parent / "fan.py").read_text(encoding="utf-8"))
        fan_class = next(node for node in tree.body if isinstance(node, ast.ClassDef))
        method = next(
            node for node in fan_class.body
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "async_turn_on"
        )
        module = ast.Module(body=[method], type_ignores=[])
        self.sleep = AsyncMock()
        namespace = {"Any": object, "asyncio": types.SimpleNamespace(sleep=self.sleep)}
        exec(compile(module, str(API_PATH.parent / "fan.py"), "exec"), namespace)
        self.turn_on = namespace["async_turn_on"]
        self.power = AsyncMock()
        self.refresh = AsyncMock()
        self.preset = AsyncMock()
        self.operations = Mock()
        self.operations.attach_mock(self.power, "power")
        self.operations.attach_mock(self.sleep, "sleep")
        self.operations.attach_mock(self.preset, "preset")
        self.operations.attach_mock(self.refresh, "refresh")
        self.fan = types.SimpleNamespace(
            is_on=False,
            coordinator=types.SimpleNamespace(
                api=types.SimpleNamespace(async_set_power=self.power),
                async_request_refresh=self.refresh,
            ),
            async_set_preset_mode=self.preset,
        )

    async def test_home_assistant_positional_turn_on(self):
        await self.turn_on(self.fan, None, None)
        self.power.assert_awaited_once_with(True)
        self.sleep.assert_awaited_once_with(5)
        self.refresh.assert_awaited_once()

    async def test_home_assistant_positional_preset(self):
        await self.turn_on(self.fan, None, "pollen")
        self.power.assert_awaited_once_with(True)
        self.preset.assert_awaited_once_with("pollen")
        self.refresh.assert_not_awaited()

    async def test_already_on_does_not_repeat_power_command(self):
        self.fan.is_on = True
        await self.turn_on(self.fan, percentage=None, preset_mode=None)
        self.power.assert_not_awaited()
        self.sleep.assert_not_awaited()
        self.refresh.assert_awaited_once()

    async def test_waits_after_power_before_setting_preset(self):
        from unittest.mock import call

        await self.turn_on(self.fan, None, "pollen")
        self.assertEqual(
            self.operations.mock_calls,
            [call.power(True), call.sleep(5), call.preset("pollen")],
        )

    async def test_already_on_sets_preset_without_waiting(self):
        self.fan.is_on = True
        await self.turn_on(self.fan, None, "pollen")
        self.sleep.assert_not_awaited()
        self.power.assert_not_awaited()
        self.preset.assert_awaited_once_with("pollen")

    async def test_failed_power_does_not_wait_or_change_mode(self):
        self.power.side_effect = api.CocoroAirConnectionError("unreachable")
        with self.assertRaises(api.CocoroAirConnectionError):
            await self.turn_on(self.fan, None, "pollen")
        self.sleep.assert_not_awaited()
        self.preset.assert_not_awaited()
        self.refresh.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
