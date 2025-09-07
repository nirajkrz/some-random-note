#!/usr/bin/env python3
"""
Zephyr CLI Tool - Command line interface for Zephyr Test Management
"""

import click
import asyncio
import json
import aiohttp
import os
import sys
from datetime import datetime
from tabulate import tabulate
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.text import Text

console = Console()

class ZephyrMCPClient:
    """CLI Client for Zephyr MCP Server"""
    
    def __init__(self, mcp_server_url="http://localhost:8000"):
        self.mcp_server_url = mcp_server_url
        
    async def call_tool(self, tool_name, arguments):
        """Call MCP tool"""
        async with aiohttp.ClientSession() as session:
            payload = {
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            try:
                async with session.post(f"{self.mcp_server_url}/mcp", json=payload) as response:
                    result = await response.json()
                    if 'result' in result:
                        content = result['result']['content'][0]['text']
                        return json.loads(content)
                    else:
                        return {"error": "No result from MCP server"}
            except Exception as e:
                return {"error": str(e)}

@click.group()
@click.option('--server-url', default='http://localhost:8000', help='MCP Server URL')
@click.pass_context
def cli(ctx, server_url):
    """Zephyr Test Management CLI Tool"""
    ctx.ensure_object(dict)
    ctx.obj['client'] = ZephyrMCPClient(server_url)

@cli.command()
@click.pass_context
def projects(ctx):
    """List all projects"""
    async def _get_projects():
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Loading projects...", total=None)
            
            client = ctx.obj['client']
            result = await client.call_tool("get_projects", {})
            
            if "error" in result:
                console.print(f"[red]Error: {result['error']}[/red]")
                return
            
            progress.remove_task(task)
            
            # Create table
            table = Table(title="Zephyr Projects", show_header=True, header_style="bold blue")
            table.add_column("ID", style="cyan")
            table.add_column("Key", style="yellow")
            table.add_column("Name", style="green")
            table.add_column("Description")
            
            for project in result.get("projects", []):
                table.add_row(
                    project.get("id", ""),
                    project.get("key", ""),
                    project.get("name", ""),
                    project.get("description", "")[:50] + "..." if len(project.get("description", "")) > 50 else project.get("description", "")
                )
            
            console.print(table)
            console.print(f"\n[green]Total projects: {result.get('total_count', 0)}[/green]")
    
    asyncio.run(_get_projects())

@cli.command()
@click.argument('project_id')
@click.option('--version-id', help='Specific version ID')
@click.pass_context
def release_status(ctx, project_id, version_id):
    """Get release status for a project"""
    async def _get_status():
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Loading release status...", total=None)
            
            client = ctx.obj['client']
            args = {"project_id": project_id}
            if version_id:
                args["version_id"] = version_id
                
            result = await client.call_tool("get_release_status", args)
            
            if "error" in result:
                console.print(f"[red]Error: {result['error']}[/red]")
                return
            
            progress.remove_task(task)
            
            for release in result.get("releases", []):
                version = release.get("version", {})
                summary = release.get("execution_summary", {})
                cycles = release.get("cycles", [])
                
                # Release header
                panel_content = f"""
[bold]Version:[/bold] {version.get('name', 'N/A')}
[bold]Description:[/bold] {version.get('description', 'N/A')}
[bold]Cycles:[/bold] {len(cycles)}

[bold cyan]Execution Summary:[/bold cyan]
• Total Tests: {summary.get('totalTestsCount', 0)}
• Executed: {summary.get('totalExecuted', 0)}
• Passed: [green]{summary.get('totalPassed', 0)}[/green]
• Failed: [red]{summary.get('totalFailed', 0)}[/red]
• Blocked: [yellow]{summary.get('totalBlocked', 0)}[/yellow]
"""
                
                console.print(Panel(panel_content, title=f"Release: {version.get('name', 'Unknown')}", expand=False))
                
                if cycles:
                    table = Table(title="Test Cycles", show_header=True, header_style="bold magenta")
                    table.add_column("Cycle Name")
                    table.add_column("Description")
                    
                    for cycle in cycles:
                        table.add_row(
                            cycle.get("name", ""),
                            cycle.get("description", "")[:40] + "..." if len(cycle.get("description", "")) > 40 else cycle.get("description", "")
                        )
                    
                    console.print(table)
    
    asyncio.run(_get_status())

@cli.command()
@click.argument('project_id')
@click.argument('version_id')
@click.option('--cycle-id', help='Specific cycle ID')
@click.pass_context
def progress(ctx, project_id, version_id, cycle_id):
    """Get execution progress"""
    async def _get_progress():
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress_bar:
            task = progress_bar.add_task("Loading execution progress...", total=None)
            
            client = ctx.obj['client']
            args = {"project_id": project_id, "version_id": version_id}
            if cycle_id:
                args["cycle_id"] = cycle_id
                
            result = await client.call_tool("get_execution_progress", args)
            
            if "error" in result:
                console.print(f"[red]Error: {result['error']}[/red]")
                return
            
            progress_bar.remove_task(task)
            
            # Create progress table
            table = Table(title="Test Execution Progress", show_header=True, header_style="bold blue")
            table.add_column("Cycle", style="cyan")
            table.add_column("Total", justify="right")
            table.add_column("Passed", justify="right", style="green")
            table.add_column("Failed", justify="right", style="red")
            table.add_column("Blocked", justify="right", style="yellow")
            table.add_column("Pending", justify="right", style="dim")
            table.add_column("Execution %", justify="right")
            table.add_column("Pass %", justify="right")
            
            for prog in result.get("progress", []):
                cycle = prog.get("cycle", {})
                table.add_row(
                    cycle.get("name", ""),
                    str(prog.get("total_tests", 0)),
                    str(prog.get("passed", 0)),
                    str(prog.get("failed", 0)),
                    str(prog.get("blocked", 0)),
                    str(prog.get("unexecuted", 0)),
                    f"{prog.get('execution_rate', 0):.1f}%",
                    f"{prog.get('pass_rate', 0):.1f}%"
                )
            
            console.print(table)
    
    asyncio.run(_get_progress())

@cli.command()
@click.argument('project_id')
@click.argument('version_id')
@click.option('--include-details', is_flag=True, help='Include detailed execution info')
@click.option('--output', '-o', help='Output to JSON file')
@click.pass_context
def report(ctx, project_id, version_id, include_details, output):
    """Generate comprehensive test report"""
    async def _generate_report():
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Generating test report...", total=None)
            
            client = ctx.obj['client']
            args = {
                "project_id": project_id,
                "version_id": version_id,
                "include_details": include_details
            }
            
            result = await client.call_tool("generate_test_report", args)
            
            if "error" in result:
                console.print(f"[red]Error: {result['error']}[/red]")
                return
            
            progress.remove_task(task)
            
            # Save to file if requested
            if output:
                with open(output, 'w') as f:
                    json.dump(result, f, indent=2, default=str)
                console.print(f"[green]Report saved to {output}[/green]")
            
            # Display summary
            metrics = result.get("overall_metrics", {})
            defects = result.get("defect_summary", {})
            
            summary_content = f"""
[bold yellow]Overall Test Metrics[/bold yellow]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Total Tests: {metrics.get('total_tests', 0)}
• Executed: {metrics.get('total_