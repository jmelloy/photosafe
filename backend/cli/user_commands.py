"""User management CLI commands"""

import click
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import User
from app.auth import get_password_hash


@click.group()
def user():
    """User management commands"""
    pass


@user.command()
@click.option("--username", prompt=True, help="Username for the new user")
@click.option("--email", prompt=True, help="Email address")
@click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True, help="Password")
@click.option("--name", help="Full name (optional)")
@click.option("--superuser", is_flag=True, help="Create as superuser")
def create(username: str, email: str, password: str, name: str, superuser: bool):
    """Create a new user"""
    db: Session = SessionLocal()
    try:
        # Check if user exists
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            click.echo(f"Error: User '{username}' already exists", err=True)
            return

        existing_email = db.query(User).filter(User.email == email).first()
        if existing_email:
            click.echo(f"Error: Email '{email}' already exists", err=True)
            return

        # Create new user
        hashed_password = get_password_hash(password)
        new_user = User(
            username=username,
            email=email,
            name=name,
            hashed_password=hashed_password,
            is_superuser=superuser,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        click.echo(f"✓ User created successfully: {username} (ID: {new_user.id})")
        if superuser:
            click.echo("  → Superuser privileges granted")
    except Exception as e:
        db.rollback()
        click.echo(f"Error creating user: {str(e)}", err=True)
    finally:
        db.close()


@user.command()
def list():
    """List all users"""
    db: Session = SessionLocal()
    try:
        users = db.query(User).all()
        if not users:
            click.echo("No users found")
            return

        click.echo(f"\n{'ID':<6} {'Username':<20} {'Email':<30} {'Name':<25} {'Superuser'}")
        click.echo("-" * 95)
        for u in users:
            superuser_mark = "✓" if u.is_superuser else ""
            click.echo(f"{u.id:<6} {u.username:<20} {u.email:<30} {(u.name or ''):<25} {superuser_mark}")
        click.echo()
    finally:
        db.close()


@user.command()
@click.argument("username")
def info(username: str):
    """Show detailed user information"""
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            click.echo(f"Error: User '{username}' not found", err=True)
            return

        click.echo(f"\nUser Information:")
        click.echo(f"  ID:          {user.id}")
        click.echo(f"  Username:    {user.username}")
        click.echo(f"  Email:       {user.email}")
        click.echo(f"  Name:        {user.name or 'N/A'}")
        click.echo(f"  Active:      {'Yes' if user.is_active else 'No'}")
        click.echo(f"  Superuser:   {'Yes' if user.is_superuser else 'No'}")
        click.echo(f"  Date Joined: {user.date_joined}")
        click.echo(f"  Last Login:  {user.last_login or 'Never'}")
        click.echo()

        # Count photos and libraries
        photo_count = len(user.photos)
        library_count = len(user.libraries)
        click.echo(f"  Photos:      {photo_count}")
        click.echo(f"  Libraries:   {library_count}")
        click.echo()
    finally:
        db.close()
