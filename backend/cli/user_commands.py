"""User management CLI commands"""

import click
from datetime import datetime
from sqlalchemy.orm import Session
from sqlmodel import select
import app.database
from app.models import User, PersonalAccessToken
from app.auth import get_password_hash, create_personal_access_token, revoke_personal_access_token


@click.group()
def user():
    """User management commands"""
    pass


@user.command()
@click.option("--username", prompt=True, help="Username for the new user")
@click.option("--email", prompt=True, help="Email address")
@click.option(
    "--password",
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
    help="Password",
)
@click.option("--name", help="Full name (optional)")
@click.option("--superuser", is_flag=True, help="Create as superuser")
def create(username: str, email: str, password: str, name: str, superuser: bool):
    """Create a new user"""
    db: Session = app.database.SessionLocal()
    try:
        # Check if user exists
        existing_user = db.exec(select(User).where(User.username == username)).first()
        if existing_user:
            click.echo(f"Error: User '{username}' already exists", err=True)
            return

        existing_email = db.exec(select(User).where(User.email == email)).first()
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
    db: Session = app.database.SessionLocal()
    try:
        users = db.exec(select(User)).all()
        if not users:
            click.echo("No users found")
            return

        click.echo(
            f"\n{'ID':<6} {'Username':<20} {'Email':<30} {'Name':<25} {'Superuser'}"
        )
        click.echo("-" * 95)
        for u in users:
            superuser_mark = "✓" if u.is_superuser else ""
            click.echo(
                f"{u.id:<6} {u.username:<20} {u.email:<30} {(u.name or ''):<25} {superuser_mark}"
            )
        click.echo()
    finally:
        db.close()


@user.command()
@click.argument("username")
def info(username: str):
    """Show detailed user information"""
    db: Session = app.database.SessionLocal()
    try:
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            click.echo(f"Error: User '{username}' not found", err=True)
            return

        click.echo("\nUser Information:")
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


@user.command()
@click.argument("username")
@click.option("--name", prompt=True, help="Name/description for this token")
@click.option("--expires-in-days", type=int, help="Number of days until token expires (optional)")
def create_token(username: str, name: str, expires_in_days: int):
    """Create a Personal Access Token for a user"""
    db: Session = app.database.SessionLocal()
    try:
        # Find user
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            click.echo(f"Error: User '{username}' not found", err=True)
            return
        
        # Create token
        pat, token = create_personal_access_token(db, user, name, expires_in_days)
        
        click.echo("\n✓ Personal Access Token created successfully!")
        click.echo(f"  Token ID:    {pat.id}")
        click.echo(f"  Name:        {pat.name}")
        click.echo(f"  Created:     {pat.created_at}")
        if pat.expires_at:
            click.echo(f"  Expires:     {pat.expires_at}")
        else:
            click.echo("  Expires:     Never")
        click.echo(f"\n  Token:       {token}")
        click.echo("\n⚠ WARNING: Store this token securely!")
        click.echo("  This is the only time it will be shown.\n")
    except Exception as e:
        db.rollback()
        click.echo(f"Error creating token: {str(e)}", err=True)
    finally:
        db.close()


@user.command()
@click.argument("username")
def list_tokens(username: str):
    """List all Personal Access Tokens for a user"""
    db: Session = app.database.SessionLocal()
    try:
        # Find user
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            click.echo(f"Error: User '{username}' not found", err=True)
            return
        
        # Get tokens
        tokens = db.exec(
            select(PersonalAccessToken).where(PersonalAccessToken.user_id == user.id)
        ).all()
        
        if not tokens:
            click.echo(f"\nNo tokens found for user '{username}'\n")
            return
        
        click.echo(f"\nPersonal Access Tokens for '{username}':")
        click.echo(f"\n{'ID':<6} {'Name':<30} {'Created':<20} {'Last Used':<20} {'Expires':<20}")
        click.echo("-" * 100)
        
        for token in tokens:
            last_used = token.last_used_at.strftime("%Y-%m-%d %H:%M") if token.last_used_at else "Never"
            expires = token.expires_at.strftime("%Y-%m-%d %H:%M") if token.expires_at else "Never"
            created = token.created_at.strftime("%Y-%m-%d %H:%M")
            
            # Check if expired
            if token.expires_at and datetime.now(token.expires_at.tzinfo or None) > token.expires_at:
                expires = f"{expires} (EXPIRED)"
            
            click.echo(f"{token.id:<6} {token.name:<30} {created:<20} {last_used:<20} {expires:<20}")
        click.echo()
    finally:
        db.close()


@user.command()
@click.argument("username")
@click.argument("token_id", type=int)
@click.confirmation_option(prompt="Are you sure you want to revoke this token?")
def revoke_token(username: str, token_id: int):
    """Revoke (delete) a Personal Access Token"""
    db: Session = app.database.SessionLocal()
    try:
        # Find user
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            click.echo(f"Error: User '{username}' not found", err=True)
            return
        
        # Revoke token
        success = revoke_personal_access_token(db, user, token_id)
        
        if success:
            click.echo(f"✓ Token {token_id} revoked successfully")
        else:
            click.echo(f"Error: Token {token_id} not found or not owned by user", err=True)
    except Exception as e:
        db.rollback()
        click.echo(f"Error revoking token: {str(e)}", err=True)
    finally:
        db.close()
