# cli.py
import click


@click.command()
@click.argument("name")
def greet(name):
    """A simple greeting command."""
    click.echo(f"Hello, {name}!")


# if __name__ == "__main__":
#     greet()
