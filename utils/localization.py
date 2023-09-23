import json
from copy import deepcopy
from pathlib import Path

from i18n import load_path, get, config, set

from models.config import Locale
from utils.logger import Logger
from utils.path import BasePath

LocalizationLogger = Logger("Localization Manager")


class LocalizationManager:
    def __init__(self, page):
        # Point localization locations
        load_path.append(str(BasePath.joinpath("locales")))
        # Set localization filename format
        set("filename_format", "{locale}.{format}")
        # Set localization file format
        set("file_format", "json")
        # Remove the root key for locales
        set("skip_locale_root_data", True)
        # Add available languages into the list of locales
        set("available_locales", [l.value for l in Locale])
        # Set American English as the default fallback language
        set("fallback", Locale.American_English.value)
        # Set the locale based on the settings
        # page.app_config.locale = Locale.Portuguese
        set("locale", page.preferences.locale.value)
        LocalizationLogger.debug(
            f"Loaded localization settings -> {json.dumps(config.settings, separators=(',', ':'))}"
        )

    def get_all_translations(self):
        for translation in Path(get("load_path")[0]).glob("*.json"):
            yield translation

    def update_all_translations(self):
        english = json.load(
            Path(get("load_path")[0] + "/en_US.json").open(encoding="utf")
        )
        for translation in self.get_all_translations():
            if translation.name == "en_US.json":
                continue
            try:
                translation_data = json.load(translation.open(encoding="utf-8"))
            except json.decoder.JSONDecodeError:
                translation_data = {}
            if not translation_data:
                translation_data = {}
            before = deepcopy(translation_data)
            self.ensure_keys(english, translation_data)
            if before != translation_data:
                LocalizationLogger.debug(
                    f"Updated translation file: {translation.stem}"
                )
                json.dump(translation_data, translation.open(mode="w+"), indent=4)

    def ensure_keys(self, original, new):
        for key, value in original.items():
            if key not in new.keys():
                if isinstance(value, str):
                    new[key] = f"# TRANSLATION ERROR: {value}"
                elif isinstance(value, dict):
                    new[key] = {}
                    self.ensure_keys(original[key], new[key])
            else:
                if isinstance(value, dict):
                    self.ensure_keys(original[key], new[key])
                elif isinstance(value, str) and new[key].startswith(
                    f"# TRANSLATION ERROR: "
                ):
                    new[key] = f"# TRANSLATION ERROR: {value}"
        for key, value in deepcopy(new).items():
            if key not in original.keys():
                del new[key]
            else:
                if isinstance(value, dict):
                    self.ensure_keys(original[key], new[key])
