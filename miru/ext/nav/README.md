# miru navigators

## Installation

`miru.ext.nav` is already included with your miru installation, if you installed `hikari-miru`, simply import it to get started.

## Usage

```py
@bot.listen()
async def navigator(event: hikari.GuildMessageCreateEvent) -> None:
    if not event.is_human:
        return

    me = bot.get_me()

    if me.id in event.message.user_mentions_ids:
        embed = hikari.Embed(title="I'm the second page!", description="Also an embed!")
        pages = ["I'm the first page!", embed, "I'm the last page!"]
        navigator = nav.NavigatorView(pages=pages)
        await navigator.send(event.channel_id)
```

For more examples see the [detailed example](https://github.com/hypergonial/hikari-miru/tree/main/examples/navigator.py), or refer to the [documentation](https://hikari-miru.readthedocs.io/en/latest/guides/navigators.html).
