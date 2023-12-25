from __future__ import annotations

import typing as t

if t.TYPE_CHECKING:
    import hikari

    from ..abc.item import Item, ViewItem
    from ..abc.item_handler import ItemHandler
    from ..client import Client
    from ..context import Context, ViewContext
    from ..view import View

AppT = t.TypeVar("AppT", bound="hikari.RESTAware")
ClientT = t.TypeVar("ClientT", bound="Client[t.Any]")
BuilderT = t.TypeVar("BuilderT", bound="hikari.api.ComponentBuilder")
ViewT = t.TypeVar("ViewT", bound="View[t.Any]")
ViewItemT = t.TypeVar("ViewItemT", bound="ViewItem[t.Any]")
ViewContextT = t.TypeVar("ViewContextT", bound="ViewContext[t.Any]")
HandlerT = t.TypeVar("HandlerT", bound="ItemHandler[t.Any, t.Any, t.Any, t.Any, t.Any, t.Any]")
ContextT = t.TypeVar("ContextT", bound="Context[t.Any, t.Any]")
ItemT = t.TypeVar("ItemT", bound="Item[t.Any, t.Any, t.Any, t.Any]")
InteractionT = t.TypeVar("InteractionT", bound="hikari.ComponentInteraction | hikari.ModalInteraction")
RespBuilderT = t.TypeVar("RespBuilderT", bound="hikari.api.InteractionResponseBuilder")
ViewResponseBuildersT: t.TypeAlias = (
    "hikari.api.InteractionMessageBuilder | hikari.api.InteractionDeferredBuilder | hikari.api.InteractionModalBuilder"
)

ModalResponseBuildersT: t.TypeAlias = "hikari.api.InteractionMessageBuilder | hikari.api.InteractionDeferredBuilder"
