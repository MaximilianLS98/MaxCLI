"""
Developer tools commands for MaxCLI.

This module provides various utilities for developers including JWT decoding,
base64 operations, and other common development tasks.
"""

import argparse
import base64
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional


def decode_jwt_token(token: str) -> tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]], Optional[str], Optional[str]]:
    """Decode a JWT token into its components.

    Args:
        token: The JWT token string to decode.

    Returns:
        Tuple of (header, payload, signature, error_message).
        If successful, error_message is None.
    """
    try:
        # Split the token into its three parts
        parts = token.strip().split('.')

        if len(parts) != 3:
            return None, None, None, "Invalid JWT format. JWT should have 3 parts separated by dots."

        header_encoded, payload_encoded, signature = parts

        # Decode header
        try:
            # Add padding if necessary
            header_padded = header_encoded + '=' * (4 - len(header_encoded) % 4)
            header_bytes = base64.urlsafe_b64decode(header_padded)
            header = json.loads(header_bytes)
        except Exception as e:
            return None, None, None, f"Failed to decode header: {e}"

        # Decode payload
        try:
            # Add padding if necessary
            payload_padded = payload_encoded + '=' * (4 - len(payload_encoded) % 4)
            payload_bytes = base64.urlsafe_b64decode(payload_padded)
            payload = json.loads(payload_bytes)
        except Exception as e:
            return None, None, None, f"Failed to decode payload: {e}"

        return header, payload, signature, None

    except Exception as e:
        return None, None, None, f"Unexpected error: {e}"


def format_timestamp(timestamp: int) -> str:
    """Format a Unix timestamp into a human-readable string.

    Args:
        timestamp: Unix timestamp (seconds since epoch).

    Returns:
        Formatted string with both absolute and relative time.
    """
    try:
        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        now = datetime.now(timezone.utc)

        # Calculate time difference
        diff = now - dt

        # Format the absolute time
        absolute = dt.strftime('%Y-%m-%d %H:%M:%S UTC')

        # Format the relative time
        if diff.total_seconds() < 0:
            # Future time
            diff = dt - now
            if diff.days > 0:
                relative = f"in {diff.days} day{'s' if diff.days != 1 else ''}"
            elif diff.seconds >= 3600:
                hours = diff.seconds // 3600
                relative = f"in {hours} hour{'s' if hours != 1 else ''}"
            elif diff.seconds >= 60:
                minutes = diff.seconds // 60
                relative = f"in {minutes} minute{'s' if minutes != 1 else ''}"
            else:
                relative = f"in {diff.seconds} second{'s' if diff.seconds != 1 else ''}"
        else:
            # Past time
            if diff.days > 0:
                relative = f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
            elif diff.seconds >= 3600:
                hours = diff.seconds // 3600
                relative = f"{hours} hour{'s' if hours != 1 else ''} ago"
            elif diff.seconds >= 60:
                minutes = diff.seconds // 60
                relative = f"{minutes} minute{'s' if minutes != 1 else ''} ago"
            else:
                relative = f"{diff.seconds} second{'s' if diff.seconds != 1 else ''} ago"

        return f"{absolute} ({relative})"

    except Exception as e:
        return f"<invalid timestamp: {e}>"


def format_jwt_value(key: str, value: Any) -> str:
    """Format a JWT claim value for display.

    Args:
        key: The claim key name.
        value: The claim value.

    Returns:
        Formatted string representation.
    """
    # Special handling for timestamp fields
    timestamp_fields = ['exp', 'iat', 'nbf', 'auth_time']

    if key in timestamp_fields and isinstance(value, (int, float)):
        return format_timestamp(int(value))

    # Format other types
    if isinstance(value, dict):
        return json.dumps(value, indent=2)
    elif isinstance(value, list):
        if len(value) == 0:
            return "[]"
        elif len(value) == 1:
            return str(value[0])
        else:
            return "\n    " + "\n    ".join(f"• {item}" for item in value)
    else:
        return str(value)


def decode_jwt_command(args: argparse.Namespace) -> None:
    """Decode and display JWT token information.

    Args:
        args: Parsed command-line arguments containing the JWT token.
    """
    token = args.token

    # Decode the token
    header, payload, signature, error = decode_jwt_token(token)

    if error:
        print(f"\n❌ Error: {error}\n")
        return

    # Display header
    print("\n" + "━" * 60)
    print("🔐 JWT Token Information")
    print("━" * 60)

    print("\n📋 Header:")
    if header:
        for key, value in header.items():
            print(f"  {key}: {value}")

    # Display payload/claims
    print("\n📦 Claims:")
    if payload:
        # Standard claims to show first (if present)
        standard_claims = ['iss', 'sub', 'aud', 'exp', 'nbf', 'iat', 'jti']

        # Show standard claims first
        for claim in standard_claims:
            if claim in payload:
                value_str = format_jwt_value(claim, payload[claim])
                print(f"  {claim}: {value_str}")

        # Show remaining custom claims
        for key, value in payload.items():
            if key not in standard_claims:
                value_str = format_jwt_value(key, value)
                # Handle multi-line values with proper indentation
                if '\n' in value_str:
                    print(f"  {key}:{value_str}")
                else:
                    print(f"  {key}: {value_str}")

    # Check token validity based on timestamps
    print("\n⏱️  Status:")
    now = datetime.now(timezone.utc).timestamp()

    is_valid = True
    status_messages = []

    # Check expiration
    if payload and 'exp' in payload:
        exp = payload['exp']
        if now > exp:
            is_valid = False
            exp_dt = datetime.fromtimestamp(exp, tz=timezone.utc)
            diff = now - exp
            if diff < 3600:
                time_str = f"{int(diff // 60)} minutes ago"
            elif diff < 86400:
                time_str = f"{int(diff // 3600)} hours ago"
            else:
                time_str = f"{int(diff // 86400)} days ago"
            status_messages.append(f"❌ Token expired {time_str}")
        else:
            exp_dt = datetime.fromtimestamp(exp, tz=timezone.utc)
            diff = exp - now
            if diff < 3600:
                time_str = f"{int(diff // 60)} minutes"
            elif diff < 86400:
                time_str = f"{int(diff // 3600)} hours"
            else:
                time_str = f"{int(diff // 86400)} days"
            status_messages.append(f"✓ Expires in {time_str}")

    # Check not-before
    if payload and 'nbf' in payload:
        nbf = payload['nbf']
        if now < nbf:
            is_valid = False
            nbf_dt = datetime.fromtimestamp(nbf, tz=timezone.utc)
            diff = nbf - now
            if diff < 3600:
                time_str = f"{int(diff // 60)} minutes"
            else:
                time_str = f"{int(diff // 3600)} hours"
            status_messages.append(f"⚠️  Not valid for another {time_str}")

    # Display overall status
    if is_valid:
        print("  ✓ Token is currently valid")
    else:
        print("  ✗ Token is NOT valid")

    # Display specific status messages
    for msg in status_messages:
        print(f"  {msg}")

    # Display signature info
    if signature:
        print(f"\n🔏 Signature:")
        print(f"  Present: Yes ({len(signature)} characters)")
        print(f"  Note: Signature verification requires the secret key")

    print("\n" + "━" * 60 + "\n")


def register_commands(subparsers) -> None:
    """Register decode commands with subparsers.

    This function is called from the devtools_manager to register
    the decode command and its subcommands.

    Args:
        subparsers: The subparsers object from argparse to add commands to.
    """
    # Main decode command with subcommands
    decode_parser = subparsers.add_parser(
        'decode',
        help='Decode and inspect various encoded formats',
        description="""
Decode Command - Developer Tools for Decoding

Decode and inspect various encoded formats commonly used in development:
• JWT tokens - View claims, expiry, and token status
• Base64 strings (coming soon)
• URL encoded strings (coming soon)

All commands provide human-readable output with helpful formatting.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max decode jwt <token>              # Decode and display JWT information
  max decode jwt $(pbpaste)           # Decode JWT from clipboard (macOS)
        """
    )

    # Create subparsers for decode subcommands
    decode_subparsers = decode_parser.add_subparsers(
        title="Decode Commands",
        dest="decode_command",
        description="Available decoding operations",
        metavar="<format>"
    )

    # JWT decode command
    jwt_parser = decode_subparsers.add_parser(
        'jwt',
        help='Decode and display JWT token information',
        description="""
Decode JWT Token

Decodes a JWT (JSON Web Token) and displays its contents in a human-readable format.

The command shows:
• Header information (algorithm, token type)
• All claims/payload data with proper formatting
• Expiry and validity status with relative times
• Whether the token is currently valid, expired, or not yet valid

Note: This command only decodes the token. It does NOT verify the signature.
For signature verification, you would need the secret key or public key.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max decode jwt eyJhbGc...            # Decode a JWT token
  max decode jwt $(pbpaste)            # Decode from clipboard (macOS)

Common JWT Claims:
  iss - Issuer (who created the token)
  sub - Subject (user identifier)
  aud - Audience (intended recipient)
  exp - Expiration time
  nbf - Not before (token not valid before this time)
  iat - Issued at (when token was created)
  jti - JWT ID (unique identifier)
        """
    )
    jwt_parser.add_argument(
        'token',
        help='The JWT token to decode'
    )
    jwt_parser.set_defaults(func=decode_jwt_command)
