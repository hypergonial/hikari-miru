# miru navigators

## Installation

`miru.ext.nav` is already included with your miru installation, if you installed `hikari-miru`, simply import it to get started.

## Usage

```py
@bot.listen()
async def navigator(event: hikari.GuildMessageCreateEvent) -> None:

    # Do not process messages from bots or webhooks
    if not event.is_human:
        return

    me = bot.get_me()

    # If the bot is mentioned
    if me.id in event.message.user_mentions_ids:
        embed = hikari.Embed(title="I'm the second page!", description="Also an embed!")
        pages = ["I'm the first page!", embed, "I'm the last page!"]
        # Define our navigator and pass in our list of pages
        navigator = nav.NavigatorView(pages=pages)
        # You may also pass an interaction object to this function
        await navigator.send(event.channel_id)
```

For more examples see the [detailed example](https://github.com/HyperGH/hikari-miru/tree/main/examples/navigator.py), or refer to the [documentation](https://hikari-miru.readthedocs.io/en/latest/guides/navigators.html).
