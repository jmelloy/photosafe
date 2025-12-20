#!/usr/bin/env python
"""PhotoSafe CLI - Main entry point"""

import click
from . import user_commands
from . import library_commands
from . import import_commands
from . import sync_commands
from . import maintenance_commands
from . import task_commands


@click.group()
def cli():
    """PhotoSafe - Photo library management CLI"""
    pass


# Register command groups
cli.add_command(user_commands.user)
cli.add_command(library_commands.library)
cli.add_command(import_commands.import_photos)
cli.add_command(sync_commands.sync)
cli.add_command(maintenance_commands.maintenance)
cli.add_command(task_commands.task)


if __name__ == "__main__":
    cli()
