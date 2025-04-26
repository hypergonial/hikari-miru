import hikari
import pytest

import miru


def test_placeholder_length() -> None:
    """Test that the select handles placeholders that are too long."""
    with pytest.raises(ValueError):
        miru.TextSelect(options=[miru.SelectOption(label="amongus")], placeholder="a" * 151)


def test_select_option_length() -> None:
    """Test that the select handles having too many options."""
    with pytest.raises(ValueError):
        miru.TextSelect(options=[miru.SelectOption(label="amongus")] * 26)


def test_select_from_hikari() -> None:
    """Test that the select is built correctly from a hikari component."""
    select: miru.TextSelect = miru.TextSelect._from_component(
        hikari.TextSelectMenuComponent(
            id=0,
            type=hikari.ComponentType.TEXT_SELECT_MENU,
            custom_id="test",
            placeholder="test",
            min_values=1,
            max_values=1,
            is_disabled=True,
            options=[
                hikari.SelectMenuOption(
                    label="amongus", value="amongus", description=None, emoji=None, is_default=False
                )
            ],
        )
    )
    assert select.custom_id == "test"
    assert select.placeholder == "test"
    assert select.min_values == 1
    assert select.max_values == 1
    assert select.disabled is True
    assert select.options == [
        hikari.SelectMenuOption(label="amongus", value="amongus", description=None, emoji=None, is_default=False)
    ]
