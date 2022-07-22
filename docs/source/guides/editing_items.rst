Editing Items
=============

A commonly asked question when it comes to handling view items is how to edit them.
View items are exposed through the :obj:`miru.views.View.children` property, which contains a list of all added view items.
Editing a specific item is as simple as changing the desired properties, then editing the message with the updated view.

Example:
--------

::

    import random

    import hikari
    import miru

    class EditView(miru.View):

        @miru.button(label="Random Number", style=hikari.ButtonStyle.PRIMARY)
        async def edit_button(self, button: miru.Button, ctx: miru.ViewContext) -> None:
            button.label = str(random.randint(0, 100)) # Change the property we want to edit
            await ctx.edit_response(components=view) # Re-send the view components
        
        @miru.button(label="Disable Menu", style=hikari.ButtonStyle.DANGER)
        async def disable_button(self, button: miru.Button, ctx: miru.ViewContext) -> None:
            for item in self.children:
                item.disabled = True # Disable all items attached to the view
            await ctx.edit_response(components=view)

    ...

Using the above view code should generate a button, that when clicked, changes it's label to a random number between 0 and 100.
The second button iterates through all items attached to the view and disables them.