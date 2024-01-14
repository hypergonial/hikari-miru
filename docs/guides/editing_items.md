---
title: Editing Items
description: Learn how to edit view items in miru.
hide:
  - toc
search:
  exclude: true
---

# Editing Items

A commonly asked question when it comes to handling view items is how to edit them.
View items are exposed through the [`View.children`][miru.view.View.children] property, which contains a list of all added view items.
Additionally, view items can be queried using [`View.get_item_by`][miru.abc.item_handler.ItemHandler.get_item_by] and
[`View.get_item_by_id`][miru.abc.item_handler.ItemHandler.get_item_by_id]. Editing a specific item is as simple as changing the desired properties,
then editing the message with the updated view.

## Example

```py
import hikari
import miru

class EditView(miru.View):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.counter = 0

    @miru.button(label="Counter: 0", style=hikari.ButtonStyle.PRIMARY)
    async def counter_button(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        self.counter += 1
        # Change the property we want to edit
        button.label = f"Counter: {self.counter}"
        # Re-send the view components
        await ctx.edit_response(components=self)

    @miru.button(label="Disable Menu", style=hikari.ButtonStyle.DANGER)
    async def disable_button(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        # Disable all items attached to the view
        for item in self.children:
            item.disabled = True
        await ctx.edit_response(components=self)
        self.stop()
```

Using the above view code should generate a button, that when clicked, increments it's counter shown on the label.
The second button iterates through all items attached to the view and disables them, then stops the view.
