"""
Configuration de l'integration Muslim Calendar via l'interface Home Assistant.
"""

import logging
import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, OptionsFlow
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN, CALC_METHODS

_LOGGER = logging.getLogger(__name__)


async def get_location_options(hass) -> dict:
    """Recupere les localisations disponibles dans Home Assistant."""
    options = {}

    # 1. Zone Home
    try:
        home_state = hass.states.get("zone.home")
        if home_state:
            lat = home_state.attributes.get("latitude")
            lon = home_state.attributes.get("longitude")
            if lat is not None and lon is not None:
                options["zone.home"] = {"name": "Maison (zone.home)", "lat": lat, "lon": lon}
    except Exception as e:
        _LOGGER.warning(f"Could not get zone.home: {e}")

    # 2. Device trackers depuis les apps mobiles
    try:
        entity_registry = er.async_get(hass)
        for entry_id, entry in entity_registry.entities.items():
            if entry.domain == "device_tracker":
                entity_id = f"device_tracker.{entry_id}"
                state = hass.states.get(entity_id)
                if state and state.attributes:
                    source_type = state.attributes.get("source_type", "")
                    if "mobile_app" in str(source_type):
                        lat = state.attributes.get("latitude")
                        lon = state.attributes.get("longitude")
                        if lat is not None and lon is not None:
                            device_name = state.name or entry_id.split(".")[-1]
                            options[entity_id] = {
                                "name": f"{device_name}",
                                "lat": lat,
                                "lon": lon,
                            }
    except Exception as e:
        _LOGGER.warning(f"Could not get device trackers: {e}")

    if not options:
        options["custom"] = {"name": "Personnalisee (coordonnees)", "lat": 47.4, "lon": -0.64}

    return options


class MuslimCalendarConfigFlow(ConfigFlow, domain=DOMAIN):
    """Configuration du plugin Muslim Calendar."""

    VERSION = 1

    @staticmethod
    async def async_get_options_flow(config_entry):
        return MuslimCalendarOptionsFlow(config_entry)

    async def async_step_user(self, user_input=None):
        """Premiere etape: configuration."""
        errors = {}
        self._location_options = await get_location_options(self.hass)

        if user_input is not None:
            location = user_input.get("location", "custom")
            lat = user_input.get("lat")
            lon = user_input.get("lon")
            method = user_input.get("method", "isna")

            if location == "custom":
                if not lat or not lon:
                    errors["base"] = "location_required"
                else:
                    lat = float(lat)
                    lon = float(lon)
            else:
                loc = self._location_options.get(location)
                if loc:
                    lat = loc["lat"]
                    lon = loc["lon"]
                else:
                    errors["base"] = "location_not_available"

            if not errors:
                data = {
                    "location": location,
                    "lat": lat,
                    "lon": lon,
                    "method": method,
                    "adjust_fajr": int(user_input.get("adjust_fajr", 0)),
                    "adjust_dhuhr": int(user_input.get("adjust_dhuhr", 0)),
                    "adjust_asr": int(user_input.get("adjust_asr", 0)),
                    "adjust_maghrib": int(user_input.get("adjust_maghrib", 0)),
                    "adjust_isha": int(user_input.get("adjust_isha", 0)),
                    "iqamah_fajr": int(user_input.get("iqamah_fajr", 20)),
                    "iqamah_dhuhr": int(user_input.get("iqamah_dhuhr", 15)),
                    "iqamah_asr": int(user_input.get("iqamah_asr", 15)),
                    "iqamah_maghrib": int(user_input.get("iqamah_maghrib", 10)),
                    "iqamah_isha": int(user_input.get("iqamah_isha", 15)),
                }
                location_name = self._location_options.get(location, {}).get("name", location)
                return self.async_create_entry(title=f"Muslim Calendar ({location_name})", data=data)

        schema_dict = {
            vol.Required("location", default="custom"): vol.In(
                {k: v["name"] for k, v in self._location_options.items()}
            ),
            vol.Required("method", default="isna"): vol.In(list(CALC_METHODS.keys())),
            vol.Optional("lat"): vol.Coerce(float),
            vol.Optional("lon"): vol.Coerce(float),
            vol.Optional("adjust_fajr", default=0): vol.Coerce(int),
            vol.Optional("adjust_dhuhr", default=0): vol.Coerce(int),
            vol.Optional("adjust_asr", default=0): vol.Coerce(int),
            vol.Optional("adjust_maghrib", default=0): vol.Coerce(int),
            vol.Optional("adjust_isha", default=0): vol.Coerce(int),
            vol.Optional("iqamah_fajr", default=20): vol.Coerce(int),
            vol.Optional("iqamah_dhuhr", default=15): vol.Coerce(int),
            vol.Optional("iqamah_asr", default=15): vol.Coerce(int),
            vol.Optional("iqamah_maghrib", default=10): vol.Coerce(int),
            vol.Optional("iqamah_isha", default=15): vol.Coerce(int),
        }

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(schema_dict),
            errors=errors,
            description_placeholders={"location_count": str(len(self._location_options))},
        )


class MuslimCalendarOptionsFlow(OptionsFlow):
    """Gestion des options (reconfiguration)."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        errors = {}
        config = self.config_entry.data
        self._location_options = await get_location_options(self.hass)

        if user_input is not None:
            location = user_input.get("location", config.get("location", "custom"))
            lat = user_input.get("lat")
            lon = user_input.get("lon")
            method = user_input.get("method", config.get("method", "isna"))

            if location == "custom":
                if lat and lon:
                    lat = float(lat)
                    lon = float(lon)
                else:
                    lat = config.get("lat", 47.4)
                    lon = config.get("lon", -0.64)
            else:
                loc = self._location_options.get(location)
                if loc:
                    lat = loc["lat"]
                    lon = loc["lon"]
                else:
                    lat = config.get("lat")
                    lon = config.get("lon")

            data = {
                "location": location,
                "lat": lat,
                "lon": lon,
                "method": method,
                "adjust_fajr": int(user_input.get("adjust_fajr", config.get("adjust_fajr", 0))),
                "adjust_dhuhr": int(user_input.get("adjust_dhuhr", config.get("adjust_dhuhr", 0))),
                "adjust_asr": int(user_input.get("adjust_asr", config.get("adjust_asr", 0))),
                "adjust_maghrib": int(user_input.get("adjust_maghrib", config.get("adjust_maghrib", 0))),
                "adjust_isha": int(user_input.get("adjust_isha", config.get("adjust_isha", 0))),
                "iqamah_fajr": int(user_input.get("iqamah_fajr", config.get("iqamah_fajr", 20))),
                "iqamah_dhuhr": int(user_input.get("iqamah_dhuhr", config.get("iqamah_dhuhr", 15))),
                "iqamah_asr": int(user_input.get("iqamah_asr", config.get("iqamah_asr", 15))),
                "iqamah_maghrib": int(user_input.get("iqamah_maghrib", config.get("iqamah_maghrib", 10))),
                "iqamah_isha": int(user_input.get("iqamah_isha", config.get("iqamah_isha", 15))),
            }
            return self.async_create_entry(title="", data=data)

        current = self.config_entry.data

        schema_dict = {
            vol.Required("location", default=current.get("location", "custom")): vol.In(
                {k: v["name"] for k, v in self._location_options.items()}
            ),
            vol.Required("method", default=current.get("method", "isna")): vol.In(list(CALC_METHODS.keys())),
            vol.Optional("lat", default=current.get("lat")): vol.Coerce(float),
            vol.Optional("lon", default=current.get("lon")): vol.Coerce(float),
            vol.Optional("adjust_fajr", default=current.get("adjust_fajr", 0)): vol.Coerce(int),
            vol.Optional("adjust_dhuhr", default=current.get("adjust_dhuhr", 0)): vol.Coerce(int),
            vol.Optional("adjust_asr", default=current.get("adjust_asr", 0)): vol.Coerce(int),
            vol.Optional("adjust_maghrib", default=current.get("adjust_maghrib", 0)): vol.Coerce(int),
            vol.Optional("adjust_isha", default=current.get("adjust_isha", 0)): vol.Coerce(int),
            vol.Optional("iqamah_fajr", default=current.get("iqamah_fajr", 20)): vol.Coerce(int),
            vol.Optional("iqamah_dhuhr", default=current.get("iqamah_dhuhr", 15)): vol.Coerce(int),
            vol.Optional("iqamah_asr", default=current.get("iqamah_asr", 15)): vol.Coerce(int),
            vol.Optional("iqamah_maghrib", default=current.get("iqamah_maghrib", 10)): vol.Coerce(int),
            vol.Optional("iqamah_isha", default=current.get("iqamah_isha", 15)): vol.Coerce(int),
        }

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema_dict),
            errors=errors,
        )
