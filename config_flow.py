"""
Configuration de l'integration Muslim Calendar via l'interface Home Assistant.
"""

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_registry import Entry
from .const import DOMAIN, DEVICE_NAME, CALC_METHODS


async def get_location_options(hass: HomeAssistant) -> dict:
    """Recupere les localisations disponibles dans Home Assistant."""
    options = {}
    entity_registry = er.async_get(hass)

    # 1. Zone Home
    home_state = hass.states.get("zone.home")
    if home_state:
        lat = home_state.attributes.get("latitude")
        lon = home_state.attributes.get("longitude")
        if lat and lon:
            options["zone.home"] = {"name": "Maison (zone.home)", "lat": lat, "lon": lon}

    # 2. Device trackers depuis les apps mobiles (companion app)
    for entry_id, entry in entity_registry.entities.items():
        if entry.domain == "device_tracker":
            # Verifier que c'est une app mobile
            entity_id = f"device_tracker.{entry_id.replace('.', '_').replace(':', '_')}"
            state = hass.states.get(entity_id)
            if not state:
                # Essayer avec l'entity_id original
                state = hass.states.get(f"device_tracker.{entry_id}")

            if state and state.attributes:
                source_type = state.attributes.get("source_type", "")
                gps_coords = state.attributes.get("latitude") and state.attributes.get("longitude")

                # Accepter mobile_app (companion app) ou gps
                if "mobile_app" in source_type or (
                    gps_coords and state.state not in ("not_home", "unavailable")
                ):
                    lat = state.attributes.get("latitude")
                    lon = state.attributes.get("longitude")
                    if lat and lon:
                        # Utiliser le nom de l'appareil plutot que l'entity_id
                        device_name = state.name or entry_id.split(".")[-1]
                        options[entity_id] = {
                            "name": f"{device_name} (app mobile)",
                            "lat": lat,
                            "lon": lon,
                        }

    return options


def build_location_schema(options: dict, current_value: str = None) -> dict:
    """Construit le schema voluptuous pour le menu localisations."""
    choices = {k: v["name"] for k, v in options.items()}
    if not choices:
        choices["custom"] = "Personnalisee (lat/lon)"

    return {vol.Required("location", default=current_value or list(choices.keys())[0] if choices else "custom"): vol.In(choices)}


class MuslimCalendarConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configuration du plugin Muslim Calendar."""

    VERSION = 1
    _location_options = {}

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return MuslimCalendarOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        errors = {}

        # Charger les options de localisation depuis HA
        if not self._location_options:
            self._location_options = await get_location_options(self.hass)

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
                # Utiliser les coordonnes de l'entite selectionnee
                loc = self._location_options.get(location)
                if loc:
                    lat = loc["lat"]
                    lon = loc["lon"]
                else:
                    errors["base"] = "location_not_available"

            if not errors:
                data = {
                    "location": location,
                    "location_name": self._location_options.get(location, {}).get("name", location) if location != "custom" else "Personnalisee",
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

        schema_dict = build_location_schema(self._location_options)
        schema_dict[vol.Required("method", default="isna")] = vol.In(list(CALC_METHODS.keys()))
        schema_dict[vol.Optional("adjust_fajr", default=0)] = vol.Coerce(int)
        schema_dict[vol.Optional("adjust_dhuhr", default=0)] = vol.Coerce(int)
        schema_dict[vol.Optional("adjust_asr", default=0)] = vol.Coerce(int)
        schema_dict[vol.Optional("adjust_maghrib", default=0)] = vol.Coerce(int)
        schema_dict[vol.Optional("adjust_isha", default=0)] = vol.Coerce(int)
        schema_dict[vol.Optional("iqamah_fajr", default=20)] = vol.Coerce(int)
        schema_dict[vol.Optional("iqamah_dhuhr", default=15)] = vol.Coerce(int)
        schema_dict[vol.Optional("iqamah_asr", default=15)] = vol.Coerce(int)
        schema_dict[vol.Optional("iqamah_maghrib", default=10)] = vol.Coerce(int)
        schema_dict[vol.Optional("iqamah_isha", default=15)] = vol.Coerce(int)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(schema_dict),
            errors=errors,
            description_placeholders={
                "location_desc": f"{len(self._location_options)} localisation(s) disponible(s)",
            }
        )


class MuslimCalendarOptionsFlowHandler(config_entries.OptionsFlowWithConfig):
    """Gestion des options (reconfiguration)."""

    _location_options = {}

    async def async_step_init(self, user_input=None):
        if not self._location_options:
            self._location_options = await get_location_options(self.hass)

        if user_input is not None:
            location = user_input.get("location", self.config_entry.data.get("location", "custom"))
            lat = user_input.get("lat")
            lon = user_input.get("lon")

            if location == "custom":
                if not lat or not lon:
                    lat = self.config_entry.data.get("lat", 47.4)
                    lon = self.config_entry.data.get("lon", -0.64)
            else:
                loc = self._location_options.get(location)
                if loc:
                    lat = loc["lat"]
                    lon = loc["lon"]
                else:
                    lat = self.config_entry.data.get("lat")
                    lon = self.config_entry.data.get("lon")

            data = {
                "location": location,
                "location_name": self._location_options.get(location, {}).get("name", location) if location != "custom" else "Personnalisee",
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

        schema_dict = {}
        if current_location in self._location_options:
            schema_dict[vol.Required("location", default=current_location)] = vol.In(
                {k: v["name"] for k, v in self._location_options.items()}
            )
        else:
            schema_dict[vol.Required("location", default="custom")] = vol.In(
                {**{k: v["name"] for k, v in self._location_options.items()}, "custom": "Personnalisee (lat/lon)"}
            )

        schema_dict[vol.Required("method", default=self.config_entry.data.get("method", "isna"))] = vol.In(list(CALC_METHODS.keys()))
        schema_dict[vol.Optional("adjust_fajr", default=self.config_entry.data.get("adjust_fajr", 0))] = vol.Coerce(int)
        schema_dict[vol.Optional("adjust_dhuhr", default=self.config_entry.data.get("adjust_dhuhr", 0))] = vol.Coerce(int)
        schema_dict[vol.Optional("adjust_asr", default=self.config_entry.data.get("adjust_asr", 0))] = vol.Coerce(int)
        schema_dict[vol.Optional("adjust_maghrib", default=self.config_entry.data.get("adjust_maghrib", 0))] = vol.Coerce(int)
        schema_dict[vol.Optional("adjust_isha", default=self.config_entry.data.get("adjust_isha", 0))] = vol.Coerce(int)
        schema_dict[vol.Optional("iqamah_fajr", default=self.config_entry.data.get("iqamah_fajr", 20))] = vol.Coerce(int)
        schema_dict[vol.Optional("iqamah_dhuhr", default=self.config_entry.data.get("iqamah_dhuhr", 15))] = vol.Coerce(int)
        schema_dict[vol.Optional("iqamah_asr", default=self.config_entry.data.get("iqamah_asr", 15))] = vol.Coerce(int)
        schema_dict[vol.Optional("iqamah_maghrib", default=self.config_entry.data.get("iqamah_maghrib", 10))] = vol.Coerce(int)
        schema_dict[vol.Optional("iqamah_isha", default=self.config_entry.data.get("iqamah_isha", 15))] = vol.Coerce(int)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema_dict),
            description_placeholders={"description": f"{len(self._location_options)} localisation(s) disponible(s). Modifiez les parametres."}
        )
