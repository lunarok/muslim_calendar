"""
Configuration de l'integration Muslim Calendar via l'interface Home Assistant.
"""

import logging
import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, OptionsFlow
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN, CALC_METHODS

_LOGGER = logging.getLogger(__name__)

DEFAULT_LAT = 47.4
DEFAULT_LON = -0.64


async def get_location_options(hass) -> dict:
    """Recupere les localisations disponibles dans Home Assistant."""
    options = {}

    try:
        home_state = hass.states.get("zone.home")
        if home_state:
            lat = home_state.attributes.get("latitude")
            lon = home_state.attributes.get("longitude")
            if lat is not None and lon is not None:
                options["zone.home"] = {"name": "Maison (zone.home)", "lat": lat, "lon": lon}
    except Exception as e:
        _LOGGER.warning(f"Could not get zone.home: {e}")

    try:
        entity_registry = er.async_get(hass)
        for entity_id, entry in entity_registry.entities.items():
            if entry.domain not in ("device_tracker", "zone"):
                continue
            state = hass.states.get(entity_id)
            if not state or not state.attributes:
                continue
            source_type = str(state.attributes.get("source_type", "")).lower()
            if "mobile_app" not in source_type:
                continue
            lat = state.attributes.get("latitude")
            lon = state.attributes.get("longitude")
            if lat is None or lon is None:
                continue
            device_name = state.name or entity_id.split(".")[-1]
            options[entity_id] = {"name": device_name, "lat": lat, "lon": lon}
    except Exception as e:
        _LOGGER.warning(f"Could not get device trackers: {e}")

    if not options:
        options["custom"] = {"name": "Personnalisee (coordonnees)", "lat": DEFAULT_LAT, "lon": DEFAULT_LON}

    return options


class MuslimCalendarConfigFlow(ConfigFlow, domain=DOMAIN):
    """Configuration du plugin Muslim Calendar."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Configure l'integration."""
        errors = {}
        locations = await get_location_options(self.hass)

        if user_input is not None:
            location = user_input.get("location", "custom")
            method = user_input.get("method", "isna")

            if location == "custom":
                try:
                    lat = float(user_input.get("lat", DEFAULT_LAT))
                    lon = float(user_input.get("lon", DEFAULT_LON))
                    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                        errors["base"] = "invalid_location"
                except (TypeError, ValueError):
                    errors["base"] = "invalid_location"
            else:
                loc = locations.get(location)
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
                loc_name = locations.get(location, {}).get("name", location)
                return self.async_create_entry(title=f"Muslim Calendar ({loc_name})", data=data)

        loc_choices = {k: v["name"] for k, v in locations.items()}

        schema = vol.Schema({
            vol.Required("location", default="custom"): vol.In(loc_choices),
            vol.Required("method", default="isna"): vol.In(list(CALC_METHODS.keys())),
            vol.Optional("lat", default=str(DEFAULT_LAT)): str,
            vol.Optional("lon", default=str(DEFAULT_LON)): str,
            vol.Optional("adjust_fajr", default=0): int,
            vol.Optional("adjust_dhuhr", default=0): int,
            vol.Optional("adjust_asr", default=0): int,
            vol.Optional("adjust_maghrib", default=0): int,
            vol.Optional("adjust_isha", default=0): int,
            vol.Optional("iqamah_fajr", default=20): int,
            vol.Optional("iqamah_dhuhr", default=15): int,
            vol.Optional("iqamah_asr", default=15): int,
            vol.Optional("iqamah_maghrib", default=10): int,
            vol.Optional("iqamah_isha", default=15): int,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    @staticmethod
    async def async_get_options_flow(config_entry):
        return MuslimCalendarOptionsFlow(config_entry)


class MuslimCalendarOptionsFlow(OptionsFlow):

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        errors = {}
        config = self.config_entry.data
        current_loc = config.get("location", "custom")

        if user_input is not None:
            method = user_input.get("method", config.get("method", "isna"))
            location = user_input.get("location", current_loc)
            iqamah_fajr = int(user_input.get("iqamah_fajr", 20))
            iqamah_dhuhr = int(user_input.get("iqamah_dhuhr", 15))
            iqamah_asr = int(user_input.get("iqamah_asr", 15))
            iqamah_maghrib = int(user_input.get("iqamah_maghrib", 10))
            iqamah_isha = int(user_input.get("iqamah_isha", 15))
            adjust_fajr = int(user_input.get("adjust_fajr", 0))
            adjust_dhuhr = int(user_input.get("adjust_dhuhr", 0))
            adjust_asr = int(user_input.get("adjust_asr", 0))
            adjust_maghrib = int(user_input.get("adjust_maghrib", 0))
            adjust_isha = int(user_input.get("adjust_isha", 0))

            if location == "custom":
                try:
                    lat = float(user_input.get("lat", config.get("lat", DEFAULT_LAT)))
                    lon = float(user_input.get("lon", config.get("lon", DEFAULT_LON)))
                except (TypeError, ValueError):
                    lat = config.get("lat", DEFAULT_LAT)
                    lon = config.get("lon", DEFAULT_LON)
            else:
                locations = await get_location_options(self.hass)
                loc = locations.get(location)
                if loc:
                    lat = loc["lat"]
                    lon = loc["lon"]
                else:
                    lat = config.get("lat", DEFAULT_LAT)
                    lon = config.get("lon", DEFAULT_LON)

            data = {
                "location": location,
                "lat": lat,
                "lon": lon,
                "method": method,
                "adjust_fajr": adjust_fajr,
                "adjust_dhuhr": adjust_dhuhr,
                "adjust_asr": adjust_asr,
                "adjust_maghrib": adjust_maghrib,
                "adjust_isha": adjust_isha,
                "iqamah_fajr": iqamah_fajr,
                "iqamah_dhuhr": iqamah_dhuhr,
                "iqamah_asr": iqamah_asr,
                "iqamah_maghrib": iqamah_maghrib,
                "iqamah_isha": iqamah_isha,
            }
            return self.async_create_entry(title="", data=data)

        locations = await get_location_options(self.hass)
        loc_choices = {k: v["name"] for k, v in locations.items()}

        # Ensure current location is in choices (fallback to custom if not)
        if current_loc not in loc_choices:
            loc_choices["custom"] = "Personnalisee (coordonnees)"

        schema = vol.Schema({
            vol.Required("location", default=current_loc): vol.In(loc_choices),
            vol.Required("method", default=config.get("method", "isna")): vol.In(list(CALC_METHODS.keys())),
            vol.Optional("lat", default=str(config.get("lat", DEFAULT_LAT))): str,
            vol.Optional("lon", default=str(config.get("lon", DEFAULT_LON))): str,
            vol.Optional("adjust_fajr", default=config.get("adjust_fajr", 0)): int,
            vol.Optional("adjust_dhuhr", default=config.get("adjust_dhuhr", 0)): int,
            vol.Optional("adjust_asr", default=config.get("adjust_asr", 0)): int,
            vol.Optional("adjust_maghrib", default=config.get("adjust_maghrib", 0)): int,
            vol.Optional("adjust_isha", default=config.get("adjust_isha", 0)): int,
            vol.Optional("iqamah_fajr", default=config.get("iqamah_fajr", 20)): int,
            vol.Optional("iqamah_dhuhr", default=config.get("iqamah_dhuhr", 15)): int,
            vol.Optional("iqamah_asr", default=config.get("iqamah_asr", 15)): int,
            vol.Optional("iqamah_maghrib", default=config.get("iqamah_maghrib", 10)): int,
            vol.Optional("iqamah_isha", default=config.get("iqamah_isha", 15)): int,
        })

        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)