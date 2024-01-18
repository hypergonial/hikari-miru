from __future__ import annotations

import typing as t

if t.TYPE_CHECKING:
    import hikari

    from miru.abc.context import Context
    from miru.abc.item import InteractiveViewItem, Item
    from miru.abc.item_handler import ItemHandler
    from miru.view import View

# Type variables
AppT = t.TypeVar("AppT", bound="hikari.RESTAware")
BuilderT = t.TypeVar("BuilderT", bound="hikari.api.ComponentBuilder")
ViewT = t.TypeVar("ViewT", bound="View")
ViewItemT = t.TypeVar("ViewItemT", bound="InteractiveViewItem")
HandlerT = t.TypeVar("HandlerT", bound="ItemHandler[t.Any, t.Any, t.Any, t.Any, t.Any]")
ContextT = t.TypeVar("ContextT", bound="Context[t.Any]")
ItemT = t.TypeVar("ItemT", bound="Item[t.Any, t.Any, t.Any]")
InteractionT = t.TypeVar("InteractionT", bound="hikari.ComponentInteraction | hikari.ModalInteraction")
RespBuilderT = t.TypeVar("RespBuilderT", bound="hikari.api.InteractionResponseBuilder")

# Aliases
ResponseBuildersT: t.TypeAlias = (
    "hikari.api.InteractionMessageBuilder | hikari.api.InteractionDeferredBuilder | hikari.api.InteractionModalBuilder"
)
ModalResponseBuildersT: t.TypeAlias = "hikari.api.InteractionMessageBuilder | hikari.api.InteractionDeferredBuilder"
UnhandledModalInterHookT: t.TypeAlias = "t.Callable[[hikari.ModalInteraction], t.Coroutine[t.Any, t.Any, None]]"
UnhandledCompInterHookT: t.TypeAlias = "t.Callable[[hikari.ComponentInteraction], t.Coroutine[t.Any, t.Any, None]]"
InteractiveButtonStylesT: t.TypeAlias = "t.Literal[hikari.ButtonStyle.PRIMARY, hikari.ButtonStyle.SECONDARY, hikari.ButtonStyle.SUCCESS, hikari.ButtonStyle.DANGER]"
