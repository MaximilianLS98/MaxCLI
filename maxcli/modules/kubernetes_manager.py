"""
Kubernetes Manager Module for MaxCLI.

This module provides Kubernetes management functionality including:
- Kubernetes context switching
- Cluster management utilities
"""

import argparse
from maxcli.commands.kubernetes import kctx


def register_commands(subparsers) -> None:
    """Register Kubernetes management commands.
    
    Args:
        subparsers: ArgumentParser subparsers object to register commands to.
    """
    # Kubernetes context switching command
    kctx_parser = subparsers.add_parser(
        'kctx', 
        help='Switch Kubernetes context',
        description="""
Switch the current Kubernetes context using kubectl.

This is equivalent to running 'kubectl config use-context <context>' but with a shorter command.
The context must already exist in your kubectl configuration.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  max kctx minikube               # Switch to minikube context
  max kctx production-cluster     # Switch to production cluster context
  
To see available contexts, run: kubectl config get-contexts
        """
    )
    kctx_parser.add_argument('context', help='Kubernetes context name (required)')
    kctx_parser.set_defaults(func=kctx) 