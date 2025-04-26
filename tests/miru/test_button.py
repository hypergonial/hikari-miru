import hikari
import pytest

import miru

bot = hikari.GatewayBot("amongus")
client = miru.Client(bot)


def test_label_and_emoji() -> None:
    """Test that both label and emoji cannot be empty."""
    row = hikari.impl.MessageActionRowBuilder()
    with pytest.raises(TypeError):
        miru.Button(label=None, emoji=None)._build(row)


def test_url_style_override() -> None:
    """Test that url style is overridden."""
    button = miru.LinkButton("https://google.com")
    assert button.style == hikari.ButtonStyle.LINK


def test_emoji_parse() -> None:
    """Test that emoji is parsed correctly."""
    button = miru.Button(emoji="<:FoxPray:1005399743314272286>")
    assert button.emoji == hikari.Emoji.parse("<:FoxPray:1005399743314272286>")


def test_from_hikari() -> None:
    """Test that the button is built correctly from a hikari component."""
    button = miru.Button._from_component(
        hikari.ButtonComponent(
            id=0,
            type=hikari.ComponentType.BUTTON,
            style=hikari.ButtonStyle.PRIMARY,
            is_disabled=True,
            label="test",
            emoji=hikari.Emoji.parse("<:FoxPray:1005399743314272286>"),
            custom_id="test",
            url=None,
        )
    )
    assert button.label == "test"
    assert button.emoji == hikari.Emoji.parse("<:FoxPray:1005399743314272286>")
    assert button.custom_id == "test"
    assert button.style == hikari.ButtonStyle.PRIMARY
    assert button.disabled is True


def test_url_from_hikari() -> None:
    """Test that the button is built correctly from a hikari component."""
    button = miru.LinkButton._from_component(
        hikari.ButtonComponent(
            id=0,
            type=hikari.ComponentType.BUTTON,
            style=hikari.ButtonStyle.LINK,
            is_disabled=True,
            label="test",
            url="https://google.com",
            emoji=None,
            custom_id=None,
        )
    )

    assert button.label == "test"
    assert button.url == "https://google.com"
    assert button.style == hikari.ButtonStyle.LINK
    assert button.disabled is True
    assert button.emoji is None


def test_button_label_length() -> None:
    """Test that the button handles labels that are too long."""
    with pytest.raises(ValueError):
        miru.Button(label="a" * 81)


def test_button_custom_id_length() -> None:
    """Test that the button handles custom_ids that are too long."""
    with pytest.raises(ValueError):
        miru.Button(custom_id="a" * 101)
