"""Muslim Calendar config flow."""
import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, OptionsFlow
from .const import DOMAIN, CALC_METHODS


class MuslimCalendarConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("method", default="isna"): vol.In(list(CALC_METHODS.keys())),
            }),
        )

    @staticmethod
    async def async_get_options_flow(config_entry):
        return MuslimCalendarOptionsFlow(config_entry)


class MuslimCalendarOptionsFlow(OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        return self.async_show_form(step_id="init", data_schema=vol.Schema({}))
