"""
Configuration de l'integration Muslim Calendar via l'interface Home Assistant.
"""

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from .const import DOMAIN, DEVICE_NAME, CALC_METHODS


async def get_location_options(hass: HomeAssistant) -> dict:
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
    except Exception:
        pass

    # 2. Device trackers depuis les apps mobiles
    try:
        entity_registry = er.async_get(hass)
        for entry_id, entry in entity_registry.entities.items():
            if entry.domain == "device_tracker":
                entity_id = f"device_tracker.{entry_id}"
                state = hass.states.get(entity_id)
                if state and state.attributes:
                    source_type = state.attributes.get("source_type", "")
                    if "mobile_app" in str(source_type) or entry.domain == "device_tracker":
                        lat = state.attributes.get("latitude")
                        lon = state.attributes.get("longitude")
                        if lat is not None and lon is not None:
                            device_name = state.name or entry_id.split(".")[-1]
                            options[entity_id] = {
                                "name": f"{device_name} (app mobile)",
                                "lat": lat,
                                "lon": lon,
                            }
    except Exception:
        pass

    if not options:
        options["custom"] = {"name": "Personnalisee (coordonnees)", "lat": 47.4, "lon": -0.64}

    return options


class MuslimCalendarConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configuration du plugin Muslim Calendar."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            location = user_input.get("location", "custom")
            lat = user_input.get("lat")
            lon = user_input.get("lon")
            method = user_input.get("method", "isna")

            if location == "custom":
                if not lat or not lon:
                    errors["base"] = "location_required"
                elif not (-90 <= float(lat) <= 90) or not (-180 <= float(lon) <= 180):
                    errors["base"] = "invalid_location"
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
                title = f"Muslim Calendar ({self._location_options.get(location, {}).get('name', location)})"
                return self.async_create_entry(title=title, data=data)

        # Charger les localisations
        self._location_options = await get_location_options(self.hass)

        schema_dict = {
            vol.Required("location", default="custom"): vol.In(
                {k: v["name"] for k, v in self._location_options.items()}
            ),
            vol.Required("method", default="isna"): vol.In(list(CALC_METHODS.keys())),
        }

        # Champs coordonnees caches ou conditionnels
        schema_dict[vol.Optional("lat")] = vol.Coerce(float)
        schema_dict[vol.Optional("lon")] = vol.Coerce(float)

        # Ajustements
        for prayer in ["fajr", "dhuhr", "asr", "maghrib", "isha"]:
            schema_dict[vol.Optional(f"adjust_{prayer}", default=0)] = vol.Coerce(int)
        for prayer in ["fajr", "dhuhr", "asr", "maghrib", "isha"]:
            if prayer == "fajr":
                default_iq = 20
            elif prayer == "dhuhr":
                default_iq = 15
            elif prayer == "asr":
                default_iq = 15
            elif prayer == "maghrib":
                default_iq = 10
            else:
                default_iq = 15
            schema_dict[vol.Optional(f"iqamah_{prayer}", default=default_iq)] = vol.Coerce(int)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(schema_dict),
            errors=errors,
            description_placeholders={
                "location_count": str(len(self._location_options)),
            }
        )
