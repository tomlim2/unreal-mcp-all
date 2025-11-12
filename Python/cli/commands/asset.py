"""Asset management commands"""
import click
import sys
from ..app import cli
from ..utils import APIClient, ASSET_PREFIXES, apply_naming_convention
from ..formatters import format_preview_table, format_as_json


@cli.group()
def asset():
    """Asset management commands for Unreal Engine"""
    pass


@asset.command('rename-by-type')
@click.option('--host', default=None, help='Override HTTP bridge host')
@click.option('--port', default=None, type=int, help='Override HTTP bridge port')
@click.option('--dry-run', is_flag=True, help='Preview changes without applying')
@click.pass_context
def rename_by_type(ctx, host, port, dry_run):
    """Rename selected assets by applying type-based prefixes.

    This command:
    1. Gets selected assets from Unreal Engine
    2. Applies naming conventions (T_ for Texture2D, M_ for Material, etc.)
    3. Shows preview of changes
    4. Asks for confirmation
    5. Executes rename operations
    6. Shows results
    """
    # Get configuration from context
    api_host = host or ctx.obj.get('host', 'localhost')
    api_port = port or ctx.obj.get('port', 8080)

    # Create API client
    client = APIClient(host=api_host, port=api_port)

    try:
        # Step 1: Get selected assets from Unreal Engine
        click.echo("Getting selected assets from Unreal Engine...")
        result = client.get_selected_assets()

        if not result.get("success"):
            error = result.get("error", "Unknown error")
            click.echo(click.style(f"Error: {error}", fg='red'))
            sys.exit(1)

        # Extract assets from result
        result_data = result.get("result", {})
        if result_data.get("success") == False:
            error = result_data.get("error", "Unknown error")
            click.echo(click.style(f"Error: {error}", fg='red'))
            sys.exit(1)

        result_result = result_data.get("result", {})
        assets = result_result.get("assets", [])
        asset_count = result_result.get("count", 0)

        if asset_count == 0:
            click.echo(click.style("No assets selected in Content Browser.", fg='yellow'))
            click.echo("Please select assets in Unreal Engine and try again.")
            sys.exit(0)

        click.echo(click.style(f"Found {asset_count} selected asset(s).\n", fg='green'))

        # Step 2-4: Apply naming conventions and build preview
        click.echo("Analyzing naming conventions...")
        preview = []
        operations = []

        for asset in assets:
            asset_type = asset.get("type", "")
            old_name = asset.get("name", "")
            path = asset.get("path", "")

            # Apply naming convention
            new_name, needs_rename = apply_naming_convention(old_name, asset_type, ASSET_PREFIXES)

            preview_item = {
                "path": path,
                "old_name": old_name,
                "new_name": new_name,
                "needs_rename": needs_rename,
                "asset_type": asset_type
            }
            preview.append(preview_item)

            if needs_rename:
                operations.append({
                    "old_path": path,
                    "new_name": new_name
                })

        # Step 5: Build array of assets that need renaming
        to_rename = [p for p in preview if p["needs_rename"]]
        already_correct = [p for p in preview if not p["needs_rename"]]

        # Step 6: Show expected display names (preview)
        click.echo("\n" + "=" * 60)
        click.echo(format_preview_table(preview))
        click.echo("=" * 60 + "\n")

        if not to_rename:
            click.echo(click.style("All assets already have correct naming conventions!", fg='green'))
            sys.exit(0)

        # If dry-run, stop here
        if dry_run:
            click.echo(click.style("Dry run complete. No changes were made.", fg='yellow'))
            sys.exit(0)

        # Step 7: Confirm with user
        if not click.confirm(f"\nProceed with renaming {len(to_rename)} asset(s)?"):
            click.echo("Rename cancelled.")
            sys.exit(0)

        # Step 8: Send to Unreal Engine and rename assets
        click.echo("\nRenaming assets...")
        rename_result = client.rename_assets(operations)

        if not rename_result.get("success"):
            error = rename_result.get("error", "Unknown error")
            click.echo(click.style(f"Error: {error}", fg='red'))
            sys.exit(1)

        # Extract rename results
        rename_data = rename_result.get("result", {})
        if rename_data.get("success") == False:
            error = rename_data.get("error", "Unknown error")
            click.echo(click.style(f"Error: {error}", fg='red'))
            sys.exit(1)

        rename_result_data = rename_data.get("result", {})
        success_list = rename_result_data.get("success", [])
        failed_list = rename_result_data.get("failed", [])
        success_count = rename_result_data.get("success_count", 0)
        failed_count = rename_result_data.get("failed_count", 0)

        # Step 9: Show results to user
        click.echo("\n" + "=" * 60)
        if success_count > 0:
            click.echo(click.style(f"✓ Rename Complete!", fg='green', bold=True))
            click.echo(f"\nSuccessfully Renamed ({success_count}):")
            for item in success_list:
                new_name = item.get("new_name")
                click.echo(click.style(f"  ✓ {new_name}", fg='green'))

        if failed_count > 0:
            click.echo(click.style(f"\n✗ Failed ({failed_count}):", fg='red', bold=True))
            for item in failed_list:
                path = item.get("path", "unknown")
                error = item.get("error", "Unknown error")
                click.echo(click.style(f"  ✗ {path}: {error}", fg='red'))

        click.echo("=" * 60)

        if failed_count == 0:
            click.echo(click.style(f"\nAll {success_count} asset(s) renamed successfully!", fg='green', bold=True))
        else:
            click.echo(click.style(f"\n{success_count} succeeded, {failed_count} failed.", fg='yellow'))
            sys.exit(1)

    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg='red'))
        import traceback
        traceback.print_exc()
        sys.exit(1)


@asset.command('list-selected')
@click.option('--host', default=None, help='Override HTTP bridge host')
@click.option('--port', default=None, type=int, help='Override HTTP bridge port')
@click.option('--format', type=click.Choice(['table', 'json']), default='table', help='Output format')
@click.pass_context
def list_selected(ctx, host, port, format):
    """List currently selected assets in Unreal Engine"""
    # Get configuration from context
    api_host = host or ctx.obj.get('host', 'localhost')
    api_port = port or ctx.obj.get('port', 8080)

    # Create API client
    client = APIClient(host=api_host, port=api_port)

    try:
        click.echo("Getting selected assets from Unreal Engine...")
        result = client.get_selected_assets()

        if not result.get("success"):
            error = result.get("error", "Unknown error")
            click.echo(click.style(f"Error: {error}", fg='red'))
            sys.exit(1)

        # Extract assets
        result_data = result.get("result", {})
        result_result = result_data.get("result", {})
        assets = result_result.get("assets", [])
        count = result_result.get("count", 0)

        if count == 0:
            click.echo(click.style("No assets selected.", fg='yellow'))
            sys.exit(0)

        if format == 'json':
            click.echo(format_as_json(assets))
        else:
            from ..formatters.table_formatter import format_as_table
            click.echo(f"\nSelected Assets ({count}):")
            headers = ["Name", "Type", "Path"]
            table_data = [
                {
                    "Name": a.get("name", ""),
                    "Type": a.get("type", ""),
                    "Path": a.get("package_path", "")
                }
                for a in assets
            ]
            click.echo(format_as_table(table_data, headers))

    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg='red'))
        sys.exit(1)
