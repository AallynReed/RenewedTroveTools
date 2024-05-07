from enum import Enum
from models.constants import files_cache

class Locale(Enum):
    """Supported locales."""
    en_US = "American English"
    pt_PT = "Portuguese"
    de_DE = "German"
    fr_FR = "French"
    ru_RU = "Russian"


class LocaleEngine:
    _translations: dict
    def __init__(self):
        self._translations = {}
        self._locale = Locale.en_US

    @property
    def translations(self):
        return self._translations

    def add_translation(self, locale, translation):
        self._translations[locale] = translation

    def get_translation(self, locale):
        return self._translations[locale]

    def translate(self, text: str):
        return self.translations[self.locale].get(text, "Loc Error!")

    def load_locale_translations(self):
        for file, data in files_cache.items():
            loc, ext = file.split(".")
            if loc in [l.name for l in Locale] and ext == "loc":
                formatted_data = {}
                for line in data.splitlines():
                    if len(line.split("»»", 2)) == 2:
                        key, value = line.split("»»", 1)
                        formatted_data[key] = value
                self.add_translation(Locale[loc], formatted_data)

    @property
    def locale(self):
        return self._locale

    @locale.setter
    def locale(self, locale: Locale):
        self._locale = locale


ENGINE = LocaleEngine()
loc = ENGINE.translate