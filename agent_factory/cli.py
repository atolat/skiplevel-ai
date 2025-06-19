"""Command-line interface for Agent Factory."""

import os
import sys
from pathlib import Path
from typing import List, Optional

import typer
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.text import Text
from rich.rule import Rule
from rich.columns import Columns

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not available, skip loading
    pass

from .config import load_config, validate_model_availability
from .agent import create_agent
from .traits import get_traits_registry
from .models import get_models_registry

# Initialize CLI app and console
app = typer.Typer(
    name="agent-factory",
    help="🏭 Agent Factory - Build and manage configurable AI agents with Emreq",
    rich_markup_mode="rich"
)
console = Console()

# Available tools
AVAILABLE_TOOLS = {
    "calculator": "Perform mathematical calculations",
    "file_reader": "Read and analyze text files"
}


def get_config_files() -> List[Path]:
    """Get all YAML config files from the configs directory."""
    configs_dir = Path("configs")
    if not configs_dir.exists():
        return []
    
    # Filter out non-agent config files
    excluded_files = {"traits_registry.yaml", "models_registry.yaml"}
    
    config_files = []
    for yaml_file in configs_dir.glob("*.yaml"):
        if yaml_file.name not in excluded_files:
            config_files.append(yaml_file)
    
    return config_files


def load_config_without_validation(config_path: str):
    """Load agent config without API key validation."""
    from .config import AgentConfig, CognitiveCoreConfig, LLMConfig
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        if not isinstance(config_data, dict):
            return None
        
        # Create cognitive core if present
        cognitive_core = None
        if 'cognitive_core' in config_data and config_data['cognitive_core']:
            cognitive_core = CognitiveCoreConfig(**config_data['cognitive_core'])
        
        # Create LLM config
        llm_data = config_data.get('llm', {})
        llm = LLMConfig(**llm_data)
        
        # Create memory config if present
        from .memory_config import MemoryConfig
        memory_data = config_data.get('memory', {})
        memory = MemoryConfig(**memory_data) if memory_data else MemoryConfig()
        
        # Create agent config without API key validation
        config = AgentConfig(
            agent_id=config_data['agent_id'],
            name=config_data['name'],
            description=config_data.get('description'),
            max_tokens=config_data.get('max_tokens', 1000),
            temperature=config_data.get('temperature', 0.7),
            tools=config_data.get('tools', []),
            llm=llm,
            cognitive_core=cognitive_core,
            traits=config_data.get('traits', []),
            memory=memory
        )
        
        return config
        
    except Exception:
        return None


def load_agent_config(agent_identifier: str) -> Optional[tuple]:
    """Load agent config by agent_id or filename.
    
    Returns:
        Tuple of (config, config_file_path) or None if not found
    """
    config_files = get_config_files()
    
    # First try to find by agent_id
    for config_file in config_files:
        try:
            config = load_config_without_validation(str(config_file))
            if config and config.agent_id == agent_identifier:
                return config, config_file
        except Exception:
            continue
    
    # Then try to find by filename (with or without .yaml extension)
    filename = agent_identifier if agent_identifier.endswith('.yaml') else f"{agent_identifier}.yaml"
    config_path = Path("configs") / filename
    
    # Make sure it's not an excluded file
    if config_path.exists() and config_path.name not in {"traits_registry.yaml", "models_registry.yaml"}:
        config = load_config_without_validation(str(config_path))
        if config:
            return config, config_path
    
    return None


@app.command()
def list_agents():
    """📋 List all available agent configurations with their details."""
    
    console.print("\n")
    console.print(Panel(
        "[bold blue]🏭 Available Agent Configurations[/bold blue]",
        border_style="blue"
    ))
    
    config_files = get_config_files()
    
    if not config_files:
        console.print("[yellow]No agent configurations found in configs/ directory.[/yellow]")
        return
    
    # Get models registry to check model availability
    models_registry = get_models_registry()
    
    # Create table for agent list
    agents_table = Table(show_header=True, header_style="bold magenta", box=None, show_lines=True)
    agents_table.add_column("Agent ID", style="cyan", width=18, no_wrap=True)
    agents_table.add_column("Name", style="green", width=12, no_wrap=True)
    agents_table.add_column("Model", style="blue", width=12, no_wrap=True)
    agents_table.add_column("Status", style="yellow", width=12, no_wrap=True)
    agents_table.add_column("Traits", style="magenta", width=12, no_wrap=True)
    agents_table.add_column("Tools", style="red", width=12, no_wrap=True)
    
    loaded_count = 0
    error_count = 0
    unavailable_count = 0
    
    for config_file in sorted(config_files):
        try:
            # Load config directly without API key validation for listing
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            if not isinstance(config_data, dict):
                error_count += 1
                continue
            
            # Extract basic info without full validation
            agent_id = config_data.get('agent_id', 'Unknown')
            name = config_data.get('name', 'Unknown')
            
            # Get model info
            if 'cognitive_core' in config_data and config_data['cognitive_core']:
                model = config_data['cognitive_core'].get('model', 'Unknown')
            elif 'llm' in config_data:
                model = config_data['llm'].get('model_name', 'gpt-3.5-turbo')
            else:
                model = 'gpt-3.5-turbo'
            
            # Check if model is available
            if models_registry.is_model_available(model):
                status = "[green]✓ Available[/green]"
                loaded_count += 1
            else:
                status = "[red]✗ No API Key[/red]"
                unavailable_count += 1
            
            # Get traits info
            traits_list = config_data.get('traits', [])
            if traits_list:
                traits = ", ".join(traits_list[:2])
                if len(traits_list) > 2:
                    traits += "..."
            else:
                traits = "None"
            
            # Get tools info
            tools_list = config_data.get('tools', [])
            if tools_list:
                tools = ", ".join(tools_list[:2])
                if len(tools_list) > 2:
                    tools += "..."
            else:
                tools = "None"
            
            agents_table.add_row(
                agent_id,
                name,
                model,
                status,
                traits,
                tools
            )
            
        except Exception as e:
            error_count += 1
            console.print(f"[dim red]Error loading {config_file.name}: {str(e)[:60]}...[/dim red]")
    
    console.print(agents_table)
    
    # Show summary
    total_agents = loaded_count + unavailable_count
    if unavailable_count > 0 or error_count > 0:
        console.print(f"\n[dim]Total agents: {total_agents} ([green]{loaded_count} available[/green], [red]{unavailable_count} missing API keys[/red])[/dim]")
        if error_count > 0:
            console.print(f"[dim red]{error_count} configurations failed to load[/dim red]")
        
        # Show missing API keys info
        missing_keys = models_registry.get_missing_api_keys()
        if missing_keys:
            console.print("\n[bold yellow]💡 To enable more agents, set these environment variables:[/bold yellow]")
            for api_key, models in missing_keys.items():
                console.print(f"• {api_key} (for {', '.join(models)})")
    else:
        console.print(f"\n[dim]Found {total_agents} available agent configurations[/dim]")


@app.command()
def demo():
    """🎭 Run the Agent Factory demo showcasing different agent personalities."""
    
    console.print("[bold blue]Starting Agent Factory Demo...[/bold blue]")
    
    # Import and run the demo
    try:
        # Add the parent directory to the path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from examples.demo import main as demo_main
        demo_main()
    except ImportError as e:
        console.print(f"[red]Error importing demo: {e}[/red]")
        console.print("[yellow]Make sure the examples/demo.py file exists.[/yellow]")
    except Exception as e:
        console.print(f"[red]Error running demo: {e}[/red]")


@app.command()
def chat(
    agent_name: str = typer.Argument(..., help="Agent ID or config filename to chat with"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed agent information"),
    no_stream: bool = typer.Option(False, "--no-stream", help="Disable streaming responses")
):
    """💬 Start an interactive chat session with a specific agent. Responses stream in real-time by default."""
    
    # Load agent configuration
    result = load_agent_config(agent_name)
    if not result:
        console.print(f"[red]Agent '{agent_name}' not found.[/red]")
        console.print("[yellow]Use 'agent-factory list-agents' to see available agents.[/yellow]")
        raise typer.Exit(1)
    
    config, config_file = result
    
    # Show agent info
    console.print("\n")
    if verbose:
        info_table = Table(show_header=False, box=None, padding=(0, 1))
        info_table.add_row("[bold]Agent ID:[/bold]", config.agent_id)
        info_table.add_row("[bold]Name:[/bold]", config.name)
        info_table.add_row("[bold]Config File:[/bold]", str(config_file))
        
        if hasattr(config, 'cognitive_core') and config.cognitive_core:
            info_table.add_row("[bold]Model:[/bold]", config.cognitive_core.model)
        else:
            info_table.add_row("[bold]Model:[/bold]", config.llm.model_name)
        
        if hasattr(config, 'traits') and config.traits:
            info_table.add_row("[bold]Traits:[/bold]", ", ".join(config.traits))
        
        info_table.add_row("[bold]Temperature:[/bold]", str(config.temperature))
        info_table.add_row("[bold]Max Tokens:[/bold]", str(config.max_tokens))
        
        console.print(Panel(info_table, title=f"📋 {config.name} Info", border_style="blue"))
    
    # Create agent
    try:
        agent = create_agent(config)
    except Exception as e:
        console.print(f"[red]Error creating agent: {e}[/red]")
        raise typer.Exit(1)
    
    # Start chat session
    console.print(f"\n[bold green]💬 Chatting with {config.name}[/bold green]")
    if no_stream:
        console.print("[dim]Type 'quit' or 'exit' to end the conversation[/dim]\n")
    else:
        console.print("[dim]Type 'quit' or 'exit' to end the conversation[/dim]")
        console.print("[dim]🚀 Streaming enabled - responses appear in real-time[/dim]\n")
    
    try:
        while True:
            user_input = Prompt.ask("[bold cyan]You[/bold cyan]")
            
            if user_input.lower() in ["quit", "exit", "q"]:
                console.print("\n[bold green]Chat ended. Goodbye! 👋[/bold green]")
                break
            
            try:
                if no_stream:
                    # Use traditional non-streaming chat
                    response = agent.chat(user_input)
                    
                    # Format response
                    response_text = Text()
                    response_text.append(f"{config.name}: ", style="bold magenta")
                    response_text.append(response)
                    
                    console.print(response_text)
                    console.print()  # Add spacing
                else:
                    # Use streaming chat for real-time responses
                    console.print(f"[bold magenta]{config.name}:[/bold magenta] ", end="")
                    
                    for chunk in agent.chat_stream(user_input):
                        console.print(chunk, end="")
                    
                    console.print("\n")  # Add spacing after streaming
                
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                
                # Provide API key guidance
                if hasattr(config, 'cognitive_core') and config.cognitive_core:
                    model = config.cognitive_core.model.lower()
                    if "claude" in model:
                        console.print("[yellow]Note: Make sure ANTHROPIC_API_KEY is set in your environment[/yellow]")
                    elif "gpt" in model:
                        console.print("[yellow]Note: Make sure OPENAI_API_KEY is set in your environment[/yellow]")
                
    except KeyboardInterrupt:
        console.print("\n\n[bold green]Chat interrupted. Goodbye! 👋[/bold green]")


@app.command()
def create(agent_name: str = typer.Argument(..., help="Name for the new agent configuration")):
    """🛠️ Interactive wizard to create a new agent configuration."""
    
    console.print("\n")
    console.print(Panel(
        "[bold blue]🛠️ Agent Creation Wizard[/bold blue]\n\n"
        "This wizard will help you create a new agent configuration.",
        border_style="blue"
    ))
    
    # Collect agent information
    console.print("\n[bold cyan]Step 1: Basic Information[/bold cyan]")
    
    agent_id = agent_name.lower().replace(" ", "_").replace("-", "_")
    display_name = Prompt.ask("Agent display name", default=agent_name)
    description = Prompt.ask("Agent description", default=f"A custom agent named {display_name}")
    
    # Model selection
    console.print("\n[bold cyan]Step 2: Model Selection[/bold cyan]")
    
    models_registry = get_models_registry()
    available_models = models_registry.get_available_models()
    
    if not available_models:
        console.print("[red]❌ No models available! Please set API keys (OPENAI_API_KEY or ANTHROPIC_API_KEY).[/red]")
        console.print("[dim]Run 'agent-factory models' to see model requirements.[/dim]")
        raise typer.Exit(1)
    
    models_table = Table(show_header=True, header_style="bold magenta")
    models_table.add_column("ID", style="cyan", width=3)
    models_table.add_column("Model", style="green", width=20)
    models_table.add_column("Provider", style="blue", width=12)
    models_table.add_column("Cost", style="yellow", width=8)
    models_table.add_column("Description", style="dim")
    
    model_list = list(available_models.items())
    for i, (model_name, model_data) in enumerate(model_list, 1):
        models_table.add_row(
            str(i), 
            model_name, 
            model_data.get('provider', 'Unknown'),
            model_data.get('cost_tier', 'Unknown'),
            model_data.get('description', 'No description')
        )
    
    console.print(models_table)
    
    model_choice = IntPrompt.ask(
        "Select model",
        choices=[str(i) for i in range(1, len(model_list) + 1)],
        default=1
    )
    selected_model = model_list[model_choice - 1][0]
    
    # System prompt
    console.print("\n[bold cyan]Step 3: System Prompt[/bold cyan]")
    system_prompt = Prompt.ask(
        "System prompt (core instructions for the agent)",
        default=f"You are {display_name}, a helpful AI assistant."
    )
    
    # Trait selection
    console.print("\n[bold cyan]Step 4: Personality Traits[/bold cyan]")
    
    try:
        traits_registry = get_traits_registry()
        available_traits = traits_registry.list_available_traits()
        
        if available_traits:
            console.print("Available traits:")
            traits_table = Table(show_header=True, header_style="bold magenta")
            traits_table.add_column("Trait", style="green", width=15)
            traits_table.add_column("Description", style="dim")
            
            for trait, desc in sorted(available_traits.items()):
                traits_table.add_row(trait, desc)
            
            console.print(traits_table)
            
            selected_traits = []
            while True:
                trait_input = Prompt.ask(
                    "Add trait (or 'done' to finish)",
                    default="done"
                )
                
                if trait_input.lower() == "done":
                    break
                
                if trait_input in available_traits:
                    if trait_input not in selected_traits:
                        selected_traits.append(trait_input)
                        console.print(f"[green]Added trait: {trait_input}[/green]")
                    else:
                        console.print(f"[yellow]Trait {trait_input} already added[/yellow]")
                else:
                    console.print(f"[red]Unknown trait: {trait_input}[/red]")
        else:
            selected_traits = []
            console.print("[yellow]No traits available in registry.[/yellow]")
    
    except Exception as e:
        console.print(f"[red]Error loading traits: {e}[/red]")
        selected_traits = []
    
    # Tool selection
    console.print("\n[bold cyan]Step 5: Tools[/bold cyan]")
    
    tools_table = Table(show_header=True, header_style="bold magenta")
    tools_table.add_column("Tool", style="green", width=15)
    tools_table.add_column("Description", style="dim")
    
    for tool, desc in AVAILABLE_TOOLS.items():
        tools_table.add_row(tool, desc)
    
    console.print(tools_table)
    
    selected_tools = []
    for tool in AVAILABLE_TOOLS:
        if Confirm.ask(f"Include {tool}?", default=False):
            selected_tools.append(tool)
    
    # Configuration settings
    console.print("\n[bold cyan]Step 6: Configuration[/bold cyan]")
    
    temperature = float(Prompt.ask("Temperature (0.0-2.0)", default="0.7"))
    max_tokens = int(Prompt.ask("Max tokens", default="1500"))
    
    # Create configuration
    config_data = {
        "agent_id": agent_id,
        "name": display_name,
        "description": description,
        "cognitive_core": {
            "model": selected_model,
            "system_prompt": system_prompt
        },
        "traits": selected_traits,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "tools": selected_tools
    }
    
    # Show preview
    console.print("\n[bold cyan]Configuration Preview:[/bold cyan]")
    preview_table = Table(show_header=False, box=None, padding=(0, 1))
    preview_table.add_row("[bold]Agent ID:[/bold]", agent_id)
    preview_table.add_row("[bold]Name:[/bold]", display_name)
    preview_table.add_row("[bold]Model:[/bold]", selected_model)
    preview_table.add_row("[bold]Traits:[/bold]", ", ".join(selected_traits) if selected_traits else "None")
    preview_table.add_row("[bold]Tools:[/bold]", ", ".join(selected_tools) if selected_tools else "None")
    preview_table.add_row("[bold]Temperature:[/bold]", str(temperature))
    preview_table.add_row("[bold]Max Tokens:[/bold]", str(max_tokens))
    
    console.print(Panel(preview_table, title="Agent Configuration", border_style="green"))
    
    # Save configuration
    if Confirm.ask("\nSave this configuration?", default=True):
        config_filename = f"configs/{agent_id}.yaml"
        
        # Ensure configs directory exists
        Path("configs").mkdir(exist_ok=True)
        
        try:
            with open(config_filename, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)
            
            console.print(f"[bold green]✅ Agent configuration saved to {config_filename}[/bold green]")
            console.print(f"[dim]You can now use: agent-factory chat {agent_id}[/dim]")
            
        except Exception as e:
            console.print(f"[red]Error saving configuration: {e}[/red]")
            raise typer.Exit(1)
    else:
        console.print("[yellow]Configuration not saved.[/yellow]")


@app.command()
def traits():
    """🎭 List all available personality traits from the registry."""
    
    console.print("\n")
    console.print(Panel(
        "[bold blue]🎭 Personality Traits Registry[/bold blue]",
        border_style="blue"
    ))
    
    try:
        traits_registry = get_traits_registry()
        traits_by_category = traits_registry.get_traits_by_category()
        
        if not traits_by_category:
            console.print("[yellow]No traits loaded from registry.[/yellow]")
            return
        
        # Create panels for each category
        category_panels = []
        
        for category, trait_names in traits_by_category.items():
            trait_table = Table(show_header=True, header_style="bold white", box=None, padding=(0, 1))
            trait_table.add_column("Trait", style="green", width=12)
            trait_table.add_column("Description", style="dim", width=35)
            
            available_traits = traits_registry.list_available_traits()
            
            for trait_name in sorted(trait_names):
                description = available_traits.get(trait_name, "No description")
                if len(description) > 35:
                    description = description[:32] + "..."
                trait_table.add_row(trait_name, description)
            
            category_title = category.replace('_', ' ').title()
            panel = Panel(
                trait_table,
                title=f"[bold]{category_title}[/bold]",
                border_style="cyan",
                padding=(0, 1)
            )
            category_panels.append(panel)
        
        console.print(Columns(category_panels, equal=True, expand=True))
        
        total_traits = sum(len(traits) for traits in traits_by_category.values())
        console.print(f"\n[dim]Total available traits: {total_traits}[/dim]")
        
    except Exception as e:
        console.print(f"[red]Error loading traits registry: {e}[/red]")


@app.command()
def models():
    """🤖 Show available AI models and their API key status."""
    
    console.print("\n")
    console.print(Panel(
        "[bold blue]🤖 Available AI Models[/bold blue]",
        border_style="blue"
    ))
    
    models_registry = get_models_registry()
    available_models = models_registry.get_available_models()
    missing_keys = models_registry.get_missing_api_keys()
    
    if not available_models and not missing_keys:
        console.print("[yellow]No models configured. Check models_registry.yaml file.[/yellow]")
        return
    
    # Show available models
    if available_models:
        console.print("[bold green]✅ Available Models (API keys present):[/bold green]")
        
        # Create table for available models
        available_table = Table(show_header=True, header_style="bold green")
        available_table.add_column("Model", style="cyan", width=20)
        available_table.add_column("Provider", style="blue", width=12)
        available_table.add_column("Cost Tier", style="yellow", width=10)
        available_table.add_column("Description", style="green", width=45)
        
        for model_name, model_data in sorted(available_models.items()):
            available_table.add_row(
                model_name,
                model_data.get('provider', 'Unknown'),
                model_data.get('cost_tier', 'Unknown'),
                model_data.get('description', 'No description')
            )
        
        console.print(available_table)
    
    # Show unavailable models
    if missing_keys:
        console.print(f"\n[bold red]❌ Unavailable Models (missing API keys):[/bold red]")
        
        # Create table for unavailable models
        unavailable_table = Table(show_header=True, header_style="bold red")
        unavailable_table.add_column("API Key Required", style="red", width=20)
        unavailable_table.add_column("Models", style="yellow", width=60)
        
        for api_key, models_list in missing_keys.items():
            unavailable_table.add_row(
                api_key,
                ", ".join(sorted(models_list))
            )
        
        console.print(unavailable_table)
        
        console.print("\n[bold yellow]💡 To enable these models, set the required environment variables.[/bold yellow]")
    
    # Show summary
    total_available = len(available_models)
    total_unavailable = sum(len(models) for models in missing_keys.values())
    
    console.print(f"\n[dim]Summary: {total_available} available, {total_unavailable} unavailable[/dim]")


@app.command()
def web(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host to bind the server to"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind the server to"),
    reload: bool = typer.Option(False, "--reload", "-r", help="Enable auto-reload for development")
):
    """🚀 Launch the Emreq web interface powered by Chainlit."""
    import subprocess
    
    # Display startup info
    console.print("\n")
    console.print(Panel.fit(
        f"[bold green]🚀 Starting Emreq Chainlit Interface[/bold green]\n\n"
        f"Server will be available at: [cyan]http://{host}:{port}[/cyan]\n"
        f"Auto-reload: [yellow]{'Enabled' if reload else 'Disabled'}[/yellow]",
        title="Emreq - AI Engineering Manager",
        border_style="green"
    ))
    
    try:
        # Start Chainlit server
        cmd = [
            sys.executable, "-m", "chainlit", "run", "app.py",
            "--host", host,
            "--port", str(port)
        ]
        
        if reload:
            cmd.append("--watch")
        
        console.print(f"[green]Starting server on {host}:{port}...[/green]")
        subprocess.run(cmd, check=True)
        
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error starting Chainlit server: {e}[/red]")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Shutting down server...[/yellow]")
        raise typer.Exit(0)


def main():
    """Main CLI entry point."""
    app()


if __name__ == "__main__":
    main() 