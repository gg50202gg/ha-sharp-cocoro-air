"""Async client for the Taiwan SHARP COCORO AIR cloud API."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from aiohttp import ClientError, ClientSession

from .const import CODE_TO_PRESET


class CocoroAirError(Exception):
    """Base COCORO AIR API error."""


class CocoroAirAuthError(CocoroAirError):
    """Authentication failed."""


class CocoroAirConnectionError(CocoroAirError):
    """The cloud service could not be reached."""


@dataclass(frozen=True, slots=True)
class CocoroAirConfig:
    """Connection details captured from the official application."""

    base_url: str
    app_secret: str
    terminal_app_id: str
    box_id: str
    device_id: str
    echonet_node: str
    echonet_object: str
    user_agent: str


@dataclass(frozen=True, slots=True)
class CocoroAirStatus:
    """Normalized air purifier state."""

    raw: Mapping[str, str]
    is_on: bool
    preset_mode: str | None
    temperature: int | None
    humidity: int | None
    power_w: int | None
    energy_kwh: float | None


def _property_value(item: Mapping[str, Any]) -> str | None:
    """Extract a value from any COCORO AIR value container."""
    for key in ("valueSingle", "valueRange", "valueBinary"):
        value = item.get(key)
        if isinstance(value, Mapping) and value.get("code") is not None:
            return str(value["code"])
    return None


def _hex_int(value: str | None) -> int | None:
    if not value:
        return None
    try:
        return int(value, 16)
    except ValueError:
        return None


def _decode_f1(value: str | None) -> tuple[int | None, int | None]:
    """Decode temperature and humidity from SHARP proprietary EPC F1."""
    if not value or len(value) < 10:
        return None, None
    try:
        temperature = int(value[6:8], 16)
        if temperature > 127:
            temperature -= 256
        humidity = int(value[8:10], 16)
    except ValueError:
        return None, None
    if not -1 < temperature < 51:
        temperature = None
    if not 6 < humidity < 100:
        humidity = None
    return temperature, humidity


def _decode_mode(f3: str | None) -> str | None:
    if not f3 or len(f3) < 10:
        return None
    return CODE_TO_PRESET.get(f3[8:10].upper())


def decode_status(payload: Mapping[str, Any]) -> CocoroAirStatus:
    """Convert a deviceStatus response into stable entity values."""
    device = payload.get("deviceStatus")
    if not isinstance(device, Mapping):
        raise CocoroAirError("deviceStatus is missing from the cloud response")
    properties = device.get("status")
    if not isinstance(properties, list):
        raise CocoroAirError("status is missing from the cloud response")

    values: dict[str, str] = {}
    for item in properties:
        if not isinstance(item, Mapping) or not item.get("statusCode"):
            continue
        value = _property_value(item)
        if value is not None:
            values[str(item["statusCode"]).upper()] = value

    temperature, humidity = _decode_f1(values.get("F1"))
    power = _hex_int(values.get("84"))
    energy_raw = _hex_int(values.get("85"))
    return CocoroAirStatus(
        raw=values,
        is_on=values.get("80", "").upper() == "30",
        preset_mode=_decode_mode(values.get("F3")),
        temperature=temperature,
        humidity=humidity,
        power_w=power,
        energy_kwh=None if energy_raw is None else round(energy_raw * 0.001, 2),
    )


class CocoroAirApi:
    """Small API client that keeps SHARP load-balancer cookies private."""

    def __init__(self, session: ClientSession, config: CocoroAirConfig) -> None:
        self._session = session
        self.config = config
        self._cookies: dict[str, str] = {}

    @property
    def _headers(self) -> dict[str, str]:
        return {"Accept": "application/json", "User-Agent": self.config.user_agent}

    def _remember_cookies(self, response: Any) -> None:
        for name, morsel in response.cookies.items():
            self._cookies[name] = morsel.value

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, str] | None = None,
        json: Mapping[str, Any] | None = None,
        retry_auth: bool = True,
        error_class: type[CocoroAirError] = CocoroAirError,
    ) -> Mapping[str, Any]:
        try:
            async with self._session.request(
                method,
                f"{self.config.base_url.rstrip('/')}/{path.lstrip('/')}",
                params=params,
                json=json,
                headers=self._headers,
                cookies=self._cookies,
                timeout=30,
            ) as response:
                self._remember_cookies(response)
                if response.status in (401, 403) and retry_auth:
                    self._cookies.clear()
                    await self.async_login()
                    return await self._request(
                        method,
                        path,
                        params=params,
                        json=json,
                        retry_auth=False,
                        error_class=error_class,
                    )
                if response.status in (401, 403):
                    raise CocoroAirAuthError("COCORO AIR rejected the credentials")
                response.raise_for_status()
                try:
                    data = await response.json(content_type=None)
                except ValueError:
                    raise CocoroAirError(
                        "COCORO AIR returned invalid JSON"
                    ) from None
        except CocoroAirAuthError:
            raise
        except (ClientError, TimeoutError):
            # Transport exceptions can contain the URL and credential parameters.
            raise CocoroAirConnectionError(
                "Could not communicate with COCORO AIR"
            ) from None

        if not isinstance(data, Mapping):
            raise CocoroAirError("COCORO AIR returned an unexpected response")
        if data.get("errorCode"):
            raise error_class("COCORO AIR rejected the request")
        return data

    async def async_login(self) -> None:
        """Create a cloud session using the application's terminal identifier."""
        await self._request(
            "POST",
            "setting/login/",
            params={"appSecret": self.config.app_secret, "serviceName": "sharp-tw2"},
            json={"terminalAppId": self.config.terminal_app_id},
            retry_auth=False,
            error_class=CocoroAirAuthError,
        )

    async def async_get_status(self) -> CocoroAirStatus:
        """Fetch and decode current purifier state."""
        if not self._cookies:
            await self.async_login()
        data = await self._request(
            "GET",
            "control/deviceStatus",
            params={
                "appSecret": self.config.app_secret,
                "boxId": self.config.box_id,
                "echonetNode": self.config.echonet_node,
                "echonetObject": self.config.echonet_object,
            },
        )
        return decode_status(data)

    async def _async_control(self, status: list[Mapping[str, Any]]) -> None:
        if not self._cookies:
            await self.async_login()
        await self._request(
            "POST",
            "control/deviceControl",
            params={
                "appSecret": self.config.app_secret,
                "terminalAppId": self.config.terminal_app_id,
                "boxId": self.config.box_id,
            },
            json={
                "controlList": [
                    {
                        "deviceId": self.config.device_id,
                        "echonetNode": self.config.echonet_node,
                        "echonetObject": self.config.echonet_object,
                        "status": status,
                    }
                ]
            },
        )

    async def async_set_power(self, turn_on: bool) -> None:
        """Set ECHONET Lite operation status EPC 80."""
        await self._async_control(
            [
                {
                    "statusCode": "80",
                    "valueType": "valueSingle",
                    "valueSingle": {"code": "30" if turn_on else "31"},
                }
            ]
        )

    async def async_set_preset(self, mode_code: str) -> None:
        """Set FP-S90T proprietary airflow mode via EPC F3."""
        f3_value = f"01000000{mode_code.upper()}{'0' * 46}"
        await self._async_control(
            [
                {
                    "statusCode": "f3",
                    "valueType": "valueBinary",
                    "valueBinary": {"code": f3_value},
                },
                {
                    "statusCode": "f1",
                    "valueType": "valueBinary",
                    "valueBinary": {"code": "0" * 80},
                },
                {
                    "statusCode": "f2",
                    "valueType": "valueBinary",
                    "valueBinary": {"code": "0" * 80},
                },
            ]
        )
