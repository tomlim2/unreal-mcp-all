"""Main CLI application using Click"""
import click
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@click.group()
@click.version_option(version="2.0.0")
@click.option('--config', type=click.Path(), help='Config file path')
@click.option('--format', type=click.Choice(['json', 'table', 'pretty']),
              default='pretty', help='Output format')
@click.option('--host', default='localhost', help='HTTP bridge host')
@click.option('--port', default=8080, help='HTTP bridge port')
@click.pass_context
def cli(ctx, config, format, host, port):
    """MegaMelange CLI - AI-Powered Creative Hub

    Command line interface for controlling Unreal Engine and other creative tools.
    """
    ctx.ensure_object(dict)
    ctx.obj['config'] = config
    ctx.obj['format'] = format
    ctx.obj['host'] = host
    ctx.obj['port'] = port


# Import command groups (will be registered via decorators)
from .commands import asset


if __name__ == '__main__':
    cli()
