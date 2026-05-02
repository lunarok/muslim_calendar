"""
Configuration de l'integration Muslim Calendar via l'interface Home Assistant.
"""

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN, DEVICE_NAME, CALC_METHODS, LOCATIONS


class MuslimCalendarConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configuration du plugin Muslim Calendar."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return MuslimCalendarOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            location = user_input.get("location", "custom")
            lat = user_input.get("lat")
            lon = user_input.get("lon")

            if location == "custom":
                if not lat or not lon:
                    errors["base"] = "location_required"
                elif not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                    errors["base"] = "invalid_location"
            else:
                # Use preset location coordinates
                loc = LOCATIONS.get(location, LOCATIONS["custom"])
                lat = loc["lat"]
                lon = loc["lon"]

            if not errors:
                data = {
                    "location": location,
                    "lat": lat,
                    "lon": lon,
                    "method": user_input.get("method", "isna"),
                    "adjust_fajr": user_input.get("adjust_fajr", 0),
                    "adjust_dhuhr": user_input.get("adjust_dhuhr", 0),
                    "adjust_asr": user_input.get("adjust_asr", 0),
                    "adjust_maghrib": user_input.get("adjust_maghrib", 0),
                    "adjust_isha": user_input.get("adjust_isha", 0),
                    "iqamah_fajr": user_input.get("iqamah_fajr", 20),
                    "iqamah_dhuhr": user_input.get("iqamah_dhuhr", 15),
                    "iqamah_asr": user_input.get("iqamah_asr", 15),
                    "iqamah_maghrib": user_input.get("iqamah_maghrib", 10),
                    "iqamah_isha": user_input.get("iqamah_isha", 15),
                }
                return self.async_create_entry(title=DEVICE_NAME, data=data)

        locations_schema = {vol.Required("location", default="angers"): vol.In(
            {k: v["name"] for k, v in LOCATIONS.items()}
        )}

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                **locations_schema,
                vol.Required("method", default="isna"): vol.In(list(CALC_METHODS.keys())),
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
            }),
            errors=errors,
            description_placeholders={
                "location": "Localisation (ville ou Masjid Al-Haram)",
            }
        )


class MuslimCalendarOptionsFlowHandler(config_entries.OptionsFlowWithConfig):
    """Gestion des options (reconfiguration)."""

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            location = user_input.get("location", self.config_entry.data.get("location", "custom"))

            if location == "custom":
                lat = user_input.get("lat", self.config_entry.data.get("lat", 47.4))
                lon = user_input.get("lon", self.config_entry.data.get("lon", -0.64))
            else:
                loc = LOCATIONS.get(location, LOCATIONS["custom"])
                lat = loc["lat"]
                lon = loc["lon"]

            data = {
                "location": location,
                "lat": lat,
                "lon": lon,
                "method": user_input.get("method", self.config_entry.data.get("method", "isna")),
                "adjust_fajr": user_input.get("adjust_fajr", self.config_entry.data.get("adjust_fajr", 0)),
                "adjust_dhuhr": user_input.get("adjust_dhuhr", self.config_entry.data.get("adjust_dhuhr", 0)),
                "adjust_asr": user_input.get("adjust_asr", self.config_entry.data.get("adjust_asr", 0)),
                "adjust_maghrib": user_input.get("adjust_maghrib", self.config_entry.data.get("adjust_maghrib", 0)),
                "adjust_isha": user_input.get("adjust_isha", self.config_entry.data.get("adjust_isha", 0)),
                "iqamah_fajr": user_input.get("iqamah_fajr", self.config_entry.data.get("iqamah_fajr", 20)),
                "iqamah_dhuhr": user_input.get("iqamah_dhuhr", self.config_entry.data.get("iqamah_dhuhr", 15)),
                "iqamah_asr": user_input.get("iqamah_asr", self.config_entry.data.get("iqamah_asr", 15)),
                "iqamah_maghrib": user_input.get("iqamah_maghrib", self.config_entry.data.get("iqamah_maghrib", 10)),
                "iqamah_isha": user_input.get("iqamah_isha", self.config_entry.data.get("iqamah_isha", 15)),
            }
            return self.async_create_entry(title="", data=data)

        current_location = self.config_entry.data.get("location", "custom")
        locations_schema = {vol.Required("location", default=current_location): vol.In(
            {k: v["name"] for k, v in LOCATIONS.items()}
        )}

        extra_fields = {}
        if current_location == "custom":
            extra_fields[vol.Required("lat", default=self.config_entry.data.get("lat", 47.4))] = vol.Coerce(float)
            extra_fields[vol.Required("lon", default=self.config_entry.data.get("lon", -0.64))] = vol.Coerce(float)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                **locations_schema,
                vol.Required("method", default=self.config_entry.data.get("method", "isna")): vol.In(list(CALC_METHODS.keys())),
                vol.Optional("adjust_fajr", default=self.config_entry.data.get("adjust_fajr", 0)): vol.Coerce(int),
                vol.Optional("adjust_dhuhr", default=self.config_entry.data.get("adjust_dhuhr", 0)): vol.Coerce(int),
                vol.Optional("adjust_asr", default=self.config_entry.data.get("adjust_asr", 0)): vol.Coerce(int),
                vol.Optional("adjust_maghrib", default=self.config_entry.data.get("adjust_maghrib", 0)): vol.Coerce(int),
                vol.Optional("adjust_isha", default=self.config_entry.data.get("adjust_isha", 0)): vol.Coerce(int),
                vol.Optional("iqamah_fajr", default=self.config_entry.data.get("iqamah_fajr", 20)): vol.Coerce(int),
                vol.Optional("iqamah_dhuhr", default=self.config_entry.data.get("iqamah_dhuhr", 15)): vol.Coerce(int),
                vol.Optional("iqamah_asr", default=self.config_entry.data.get("iqamah_asr", 15)): vol.Coerce(int),
                vol.Optional("iqamah_maghrib", default=self.config_entry.data.get("iqamah_maghrib", 10)): vol.Coerce(int),
                vol.Optional("iqamah_isha", default=self.config_entry.data.get("iqamah_isha", 15)): vol.Coerce(int),
            }),
            description_placeholders={"description": "Modifiez les parametres de Muslim Calendar."}
        )
