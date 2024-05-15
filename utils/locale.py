from enum import Enum
from models.constants import files_cache


with open("locales/en_US.mloc", "w+") as f:
    f.write(f"")


class Locale(Enum):
    """Supported locales."""

    en_US = "American English"
    pt_PT = "Portuguese"
    de_DE = "German"
    fr_FR = "French"
    ru_RU = "Russian"
    zh_CN = "Chinese(Simplified)"


class LocaleEngine:
    _translations: dict

    def __init__(self, debug=False):
        self._translations = {}
        self._locale = Locale.en_US
        self.debug_mode = debug

    @property
    def translations(self):
        return self._translations

    @property
    def available_translations(self):
        return list(self.translations.keys())

    def add_translation(self, locale, translation):
        self._translations[locale] = translation

    def get_translation(self, locale):
        return self._translations[locale]

    def translate(self, text: str):
        text_lines = text.splitlines()
        translated = []
        for l in text_lines:
            if not l:
                # Make sure double new lines don't trigger bad translations
                translated.append("")
                continue
            # Auto log into a file missing translations (it has to be triggered in app to translate)
            # This means it's not totally automatic, it must spawn the string in the app in order to trigger this
            # logging, nonetheless better than 1 by 1
            if self.debug_mode:
                if l and l not in self.translations[self.locale].keys():
                    with open("locales/en_US.mloc", "a", encoding="utf-8") as f:
                        f.write(f"{l}»»{l}\n")
            loc_text = self.translations[self.locale].get(l, f"Loc Error: {l}")
            loc_text = (
                l if "❓" in l and loc_text.startswith("Loc Error: ") else loc_text
            )
            translated.append(loc_text)
        return "\n".join(translated)

    def array_translate(self, text_lines: list):
        translated = []
        for l in text_lines:
            translated.append(self.translate(l))
        return translated

    def load_locale_translations(self):
        for loc in Locale:
            data = files_cache.get(f"{loc.name}.loc")
            if data is None:
                continue
            formatted_data = {}
            for line in data.splitlines():
                if len(line.split("»»", 2)) == 2:
                    key, value = line.split("»»", 1)
                    formatted_data[key] = ("»" if self.debug_mode else "") + value
            if loc.name != Locale.en_US.name:
                # Make it so it dynamically adds translations to fix missing ones in loc files
                for k, v in self.translations[Locale.en_US].items():
                    if not formatted_data.get(k):
                        formatted_data[k] = v
            text = ""
            for k, v in sorted(formatted_data.items(), key=lambda x: x[0]):
                text += f"{k}»»{v}\n"
            # In dev, we can use this to output latest loc files from server
            try:
                with open(f"locales/{loc.name}.loc", "w+", encoding="utf-8") as f:
                    f.write(text)
            except PermissionError:
                # This might fail in production due to privileged directories
                # Better to handle it now
                ...
            self.add_translation(loc, formatted_data)

    @property
    def locale(self):
        return self._locale

    @locale.setter
    def locale(self, locale: Locale):
        self._locale = locale


ENGINE = LocaleEngine(debug=False)
loc = ENGINE.translate
aloc = ENGINE.array_translate
