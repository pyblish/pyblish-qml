from vendor import click
from app import run


@click.command()
@click.option("--host", type=str, required=True)
@click.option("--port", type=int, required=True)
def main(host, port):
    run(host, port)
