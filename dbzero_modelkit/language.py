"""Multi-language string support backed by dbzero."""

from __future__ import annotations

from typing import Optional

import dbzero as db0


@db0.enum(
    values=["LEN", "LPL", "LGER", "LFR", "LESP"],
    type_id="/dbzero/dbzero-modelkit/LanguageCode",
)
class LanguageCode:
    """Common language codes used by multi-language strings."""


@db0.memo(id="/dbzero/dbzero-modelkit/ML_String", no_default_tags=True)
class ML_String:
    """Store textual information in a primary language and optional translations."""

    def __init__(
        self,
        value: str,
        lang_code: LanguageCode,
        ml_versions: Optional[dict[LanguageCode, str]] = None,
        prefix: Optional[str] = None,
    ) -> None:
        db0.set_prefix(self, prefix)
        self.value = value
        self.__lang_code = lang_code
        self.__ml_versions = ml_versions

    def __str__(self) -> str:
        """Return the primary stored value."""
        return self.value

    def get(
        self,
        lang_code: Optional[LanguageCode] = None,
        fallback_codes: Optional[list[LanguageCode]] = None,
        default: Optional[str] = None,
    ) -> Optional[str]:
        """Return a requested translation, fallback translation, or default value."""
        if lang_code is None or lang_code == self.__lang_code:
            return self.value

        if self.__ml_versions is not None:
            if lang_code in self.__ml_versions:
                return self.__ml_versions[lang_code]

            if fallback_codes is not None:
                for code in fallback_codes:
                    if code in self.__ml_versions:
                        return self.__ml_versions[code]

        if fallback_codes is not None and self.__lang_code in fallback_codes:
            return self.value

        return default

    def __load__(self, lang: Optional[LanguageCode] = None) -> Optional[str]:
        """Load the requested language value, defaulting to Polish fallback."""
        return self.get(lang, fallback_codes=[LanguageCode.LPL])
