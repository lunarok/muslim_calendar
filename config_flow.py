"""
Configuration de l'integration Muslim Calendar via l'interface Home Assistant.
"""

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN, DEVICE_NAME, CALC_METHODS, HIJRI_MONTHS_FR


class Muslim CalendarConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configuration du plugin Muslim Calendar."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return SalatOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            lat = user_input.get("lat")
            lon = user_input.get("lon")
            if not lat or not lon:
                errors["base"] = "location_required"
            elif not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                errors["base"] = "invalid_location"
            else:
                return self.async_create_entry(title=DEVICE_NAME, data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("lat", default=47.4): vol.Coerce(float),
                vol.Required("lon", default=-0.64): vol.Coerce(float),
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
                "lat": "Latitude du lieu",
                "lon": "Longitude du lieu",
                "method": "Methode de calcul des heures de priere",
            }
        )


class SalatOptionsFlowHandler(config_entries.OptionsFlowWithConfig):
    """Gestion des options (reconfiguration)."""

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required("lat", default=self.config_entry.data.get("lat", 47.4)): vol.Coerce(float),
                vol.Required("lon", default=self.config_entry.data.get("lon", -0.64)): vol.Coerce(float),
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
            description_placeholders={
                "description": "Modifiez les parametres de l'integration Muslim Calendar.",
                "lat": "Latitude du lieu",
                "lon": "Longitude du lieu",
                "method": "Methode de calcul",
                "adjust": "Ajustement en minutes (+ ou -) pour chaque priere",
                "iqamah": "Decalage en minutes apres l'heure de la priere",
            }
        )
