import datetime

from discord import Embed


class Colors:
    NORMAL = 0x5EA33E

    ERROR = 0xFF0000
    WARNING = 0xFFA500
    SUCCESS = NORMAL


class ThemedEmbed(Embed):
    Normal: Embed
    Error: Embed
    Warning: Embed
    Success: Embed

    def __init__(self, *args, **kwargs):
        kwargs_default = {
            "color": Colors.NORMAL,
            "timestamp": datetime.datetime.now(),
        }

        kwargs_default.update(kwargs)

        super().__init__(*args, **kwargs_default)


class Normal(ThemedEmbed):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, color=Colors.NORMAL, **kwargs)


class Error(ThemedEmbed):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, color=Colors.ERROR, **kwargs)


class Warning(ThemedEmbed):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, color=Colors.WARNING, **kwargs)


class Success(ThemedEmbed):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, color=Colors.SUCCESS, **kwargs)


ThemedEmbed.Normal = Normal
ThemedEmbed.Error = Error
ThemedEmbed.Warning = Warning
ThemedEmbed.Success = Success
