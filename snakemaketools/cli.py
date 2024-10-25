# cli.py
import click


# @click.command(context_settings={"show_default": True})
# @click.option("--name", help="Put your name.", default="Stranger")
# @click.option("--something", help="Put your name.", default=None)
def greet(name, something=None):
    """A simple greeting command."""
    click.echo(f"Hello, {name}!")
    if something != None:
        click.echo(f"Hello, {something}!")


# greet_cmd = click.command(context_settings={"show_default": True})(
#     click.option("--name", help="Put your name.", default="Stranger")(
#         click.option("--something", help="Put your name.", default=None)(greet)
#     )
# )


# @click.command(context_settings={"show_default": True})
# def greet_cmd():
#     # Define the options using Click's manual invocation
#     name = click.prompt("Put your name", default="Stranger")
#     something = click.prompt(
#         "Put something (optional)", default=None, show_default=True
#     )

#     # Call the greet function with the gathered inputs
#     greet(name, something)


# @click.command(context_settings={"show_default": True})
# @click.prompt("Put your name", default="Stranger")
# @click.prompt("Put something (optional)", default=None, show_default=True)
# def greet_cmd(name, something):
#     # Call the greet function with the gathered inputs
#     greet(name, something)


greet_cmd = click.Command(
    name="greet",
    context_settings={"show_default": True},
    params=[
        click.Option(["--name"], help="Put your name.", default="Stranger"),
        click.Option(["--something"], help="Put something (optional)", default=None),
    ],
    callback=greet,
)
