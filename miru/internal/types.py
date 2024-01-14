from __future__ import annotations

import typing as t

if t.TYPE_CHECKING:
    import hikari

    from miru.abc.item import Item, ViewItem
    from miru.abc.item_handler import ItemHandler
    from miru.context import Context, ViewContext
    from miru.view import View

AppT = t.TypeVar("AppT", bound="hikari.RESTAware")
BuilderT = t.TypeVar("BuilderT", bound="hikari.api.ComponentBuilder")
ViewT = t.TypeVar("ViewT", bound="View")
ViewItemT = t.TypeVar("ViewItemT", bound="ViewItem")
ViewContextT = t.TypeVar("ViewContextT", bound="ViewContext")
HandlerT = t.TypeVar("HandlerT", bound="ItemHandler[t.Any, t.Any, t.Any, t.Any, t.Any]")
ContextT = t.TypeVar("ContextT", bound="Context[t.Any]")
ItemT = t.TypeVar("ItemT", bound="Item[t.Any, t.Any, t.Any]")
InteractionT = t.TypeVar("InteractionT", bound="hikari.ComponentInteraction | hikari.ModalInteraction")
RespBuilderT = t.TypeVar("RespBuilderT", bound="hikari.api.InteractionResponseBuilder")
ViewResponseBuildersT: t.TypeAlias = (
    "hikari.api.InteractionMessageBuilder | hikari.api.InteractionDeferredBuilder | hikari.api.InteractionModalBuilder"
)

ModalResponseBuildersT: t.TypeAlias = "hikari.api.InteractionMessageBuilder | hikari.api.InteractionDeferredBuilder"
