class TelegramInitDataInvalidError(Exception):
    """initData failed structural validation, age check, or HMAC verification."""


class TelegramLoginWidgetInvalidError(Exception):
    """Login Widget payload failed structural validation, age check, or HMAC verification."""
