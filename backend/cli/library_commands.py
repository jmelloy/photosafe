"""Library management CLI commands"""

import click
from sqlalchemy.orm import Session
from sqlmodel import select
import app.database
from app.models import User, Library


@click.group()
def library():
    """Library management commands"""
    pass


@library.command()
@click.option("--username", required=True, help="Username of the library owner")
@click.option("--name", prompt=True, help="Library name")
@click.option("--path", help="Path to the library (optional)")
@click.option("--description", help="Library description (optional)")
def create(username: str, name: str, path: str, description: str):
    """Create a new library for a user"""
    db: Session = app.database.SessionLocal()
    try:
        # Check if user exists
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            click.echo(f"Error: User '{username}' not found", err=True)
            return

        # Create library
        new_library = Library(
            name=name,
            path=path,
            description=description,
            owner_id=user.id,
        )
        db.add(new_library)
        db.commit()
        db.refresh(new_library)

        click.echo(f"✓ Library created successfully: {name} (ID: {new_library.id})")
        click.echo(f"  → Owner: {username}")
        if path:
            click.echo(f"  → Path: {path}")
    except Exception as e:
        db.rollback()
        click.echo(f"Error creating library: {str(e)}", err=True)
    finally:
        db.close()


@library.command()
@click.option("--username", help="Filter by username (optional)")
def list(username: str):
    """List all libraries"""
    db: Session = app.database.SessionLocal()
    try:
        query = select(Library)
        if username:
            user = db.exec(select(User).where(User.username == username)).first()
            if not user:
                click.echo(f"Error: User '{username}' not found", err=True)
                return
            query = query.where(Library.owner_id == user.id)

        libraries = db.exec(query).all()
        if not libraries:
            click.echo("No libraries found")
            return

        click.echo(f"\n{'ID':<6} {'Name':<30} {'Owner':<20} {'Photos':<10} {'Path'}")
        click.echo("-" * 100)
        for lib in libraries:
            owner_name = lib.owner.username if lib.owner else "N/A"
            photo_count = len(lib.photos)
            path_display = lib.path or ""
            click.echo(
                f"{lib.id:<6} {lib.name:<30} {owner_name:<20} {photo_count:<10} {path_display}"
            )
        click.echo()
    finally:
        db.close()


@library.command()
@click.argument("library_id", type=int)
def info(library_id: int):
    """Show detailed library information"""
    db: Session = app.database.SessionLocal()
    try:
        library = db.exec(select(Library).where(Library.id == library_id)).first()
        if not library:
            click.echo(f"Error: Library {library_id} not found", err=True)
            return

        click.echo("\nLibrary Information:")
        click.echo(f"  ID:          {library.id}")
        click.echo(f"  Name:        {library.name}")
        click.echo(
            f"  Owner:       {library.owner.username if library.owner else 'N/A'}"
        )
        click.echo(f"  Path:        {library.path or 'N/A'}")
        click.echo(f"  Description: {library.description or 'N/A'}")
        click.echo(f"  Created:     {library.created_at}")
        click.echo(f"  Updated:     {library.updated_at}")
        click.echo(f"  Photos:      {len(library.photos)}")
        click.echo()
    finally:
        db.close()


@library.command()
@click.argument("library_id", type=int)
@click.option("--name", help="New library name")
@click.option("--path", help="New library path")
@click.option("--description", help="New library description")
def update(library_id: int, name: str, path: str, description: str):
    """Update a library"""
    db: Session = app.database.SessionLocal()
    try:
        library = db.exec(select(Library).where(Library.id == library_id)).first()
        if not library:
            click.echo(f"Error: Library {library_id} not found", err=True)
            return

        updated = False
        if name:
            library.name = name
            updated = True
        if path is not None:
            library.path = path
            updated = True
        if description is not None:
            library.description = description
            updated = True

        if updated:
            db.commit()
            click.echo(f"✓ Library {library_id} updated successfully")
        else:
            click.echo("No changes specified")
    except Exception as e:
        db.rollback()
        click.echo(f"Error updating library: {str(e)}", err=True)
    finally:
        db.close()
