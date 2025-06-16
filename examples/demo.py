#!/usr/bin/env python3
"""
Agent Factory Demo
Showcases the different agent personalities and capabilities.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import agent_factory
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_factory.config import load_config, validate_model_availability
from agent_factory.agent import create_agent
from agent_factory.traits import get_traits_registry
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.text import Text
from rich.rule import Rule
from rich.columns import Columns


console = Console()


def show_traits_registry():
    """Display the traits registry information."""
    
    console.print("\n")
    console.print(Rule("[bold magenta]🎭 Personality Traits Registry[/bold magenta]"))
    
    try:
        traits_registry = get_traits_registry()
        traits_by_category = traits_registry.get_traits_by_category()
        
        if not traits_by_category:
            console.print("[yellow]No traits loaded from registry.[/yellow]")
            return
        
        console.print("\n[bold cyan]Available Personality Traits:[/bold cyan]\n")
        
        # Create panels for each category
        category_panels = []
        
        for category, trait_names in traits_by_category.items():
            # Create table for this category
            trait_table = Table(show_header=True, header_style="bold white", box=None, padding=(0, 1))
            trait_table.add_column("Trait", style="green", width=12)
            trait_table.add_column("Description", style="dim", width=35)
            
            available_traits = traits_registry.list_available_traits()
            
            for trait_name in sorted(trait_names):
                description = available_traits.get(trait_name, "No description")
                # Truncate long descriptions
                if len(description) > 35:
                    description = description[:32] + "..."
                trait_table.add_row(trait_name, description)
            
            # Create panel for this category
            category_title = category.replace('_', ' ').title()
            panel = Panel(
                trait_table,
                title=f"[bold]{category_title}[/bold]",
                border_style="blue",
                padding=(0, 1)
            )
            category_panels.append(panel)
        
        # Display panels in columns
        console.print(Columns(category_panels, equal=True, expand=True))
        
        # Show trait resolution example
        console.print(f"\n[bold yellow]💡 Trait Resolution Example:[/bold yellow]")
        example_traits = ["empathy", "analytical", "practical"]
        resolved_instructions = traits_registry.resolve_traits(example_traits)
        
        example_table = Table(show_header=True, header_style="bold magenta", box=None)
        example_table.add_column("Trait", style="green", width=12)
        example_table.add_column("Resolved Instruction", style="cyan")
        
        for trait, instruction in zip(example_traits, resolved_instructions):
            # Truncate long instructions for display
            display_instruction = instruction if len(instruction) <= 60 else instruction[:57] + "..."
            example_table.add_row(trait, display_instruction)
        
        console.print(example_table)
        
    except Exception as e:
        console.print(f"[red]Error loading traits registry: {e}[/red]")


def demo_agent_factory():
    """Demonstrate the Agent Factory with different agent personalities."""
    
    console.print("\n")
    console.print(Panel(
        "[bold blue]🏭 Welcome to Agent Factory Demo![/bold blue]\n\n"
        "This demo showcases configurable AI agents with different personalities,\n"
        "tools, and capabilities built with LangGraph.\n\n"
        "[bold yellow]✨ Now featuring Cognitive Core agents with Personality Traits![/bold yellow]",
        title="Agent Factory",
        border_style="blue"
    ))
    
    # Show traits registry first
    show_traits_registry()
    
    # Load and demonstrate each agent with enhanced trait-focused questions
    agents_info = [
        {
            "config_file": "configs/simple_agent.yaml",
            "demo_message": "Hello! How are you today?",
            "description": "A basic conversational agent",
            "category": "Legacy"
        },
        {
            "config_file": "configs/growth_coach.yaml", 
            "demo_message": "I'm struggling with confidence in my coding abilities. I feel like everyone else knows more than me.",
            "description": "An empathetic growth coach for developers",
            "category": "Legacy"
        },
        {
            "config_file": "configs/math_helper.yaml",
            "demo_message": "What's 25 * 17 + 42?",
            "description": "A math assistant with calculator tools",
            "category": "Legacy"
        },
        {
            "config_file": "configs/anthropic_coach.yaml",
            "demo_message": "I'm feeling overwhelmed with my workload and don't know how to prioritize. Can you help me think through this?",
            "description": "An empathetic engineering growth coach using Claude",
            "category": "Cognitive Core"
        },
        {
            "config_file": "configs/openai_analyst.yaml",
            "demo_message": "Should our startup use microservices or a monolithic architecture? We have 5 developers and need to move fast.",
            "description": "A logical technical analyst using GPT-4",
            "category": "Cognitive Core"
        },
        {
            "config_file": "configs/traits_demo_coach.yaml",
            "demo_message": "I want to transition from frontend to full-stack development but I'm not sure where to start or if I'm ready.",
            "description": "A demo agent showcasing multiple personality traits",
            "category": "Traits Demo"
        }
    ]
    
    loaded_agents = []
    
    for agent_info in agents_info:
        console.print(f"\n[bold cyan]Loading {agent_info['config_file']}...[/bold cyan]")
        
        try:
            config = load_config(agent_info["config_file"])
            if config:
                # Check API key availability for cognitive core agents
                api_key_status = ""
                if hasattr(config, 'cognitive_core') and config.cognitive_core:
                    is_valid, error_msg = validate_model_availability(config.cognitive_core.model)
                    if is_valid:
                        api_key_status = "[green]✓ API Key Available[/green]"
                    else:
                        api_key_status = f"[red]✗ {error_msg}[/red]"
                        console.print(f"[yellow]Warning: {error_msg}[/yellow]")
                        console.print("[dim]Agent will be loaded but may not function properly without API key.[/dim]")
                
                agent = create_agent(config)
                loaded_agents.append((agent, agent_info))
                
                # Show agent info with enhanced traits display
                info_table = Table(show_header=False, box=None, padding=(0, 1))
                info_table.add_row("[bold]Category:[/bold]", f"[{'magenta' if agent_info['category'] == 'Traits Demo' else 'blue' if agent_info['category'] == 'Cognitive Core' else 'dim'}]{agent_info['category']}[/{'magenta' if agent_info['category'] == 'Traits Demo' else 'blue' if agent_info['category'] == 'Cognitive Core' else 'dim'}]")
                info_table.add_row("[bold]Name:[/bold]", config.name)
                info_table.add_row("[bold]Description:[/bold]", agent_info["description"])
                
                # Show cognitive core info if available
                if hasattr(config, 'cognitive_core') and config.cognitive_core:
                    info_table.add_row("[bold]Model:[/bold]", f"[blue]{config.cognitive_core.model}[/blue]")
                    # Show first line of system prompt
                    first_line = config.cognitive_core.system_prompt.split('\n')[0].strip()
                    if len(first_line) > 60:
                        first_line = first_line[:57] + "..."
                    info_table.add_row("[bold]System Prompt:[/bold]", f"[dim]{first_line}[/dim]")
                    if api_key_status:
                        info_table.add_row("[bold]API Status:[/bold]", api_key_status)
                else:
                    # Legacy agent info
                    info_table.add_row("[bold]LLM Provider:[/bold]", config.llm.provider)
                    info_table.add_row("[bold]Model:[/bold]", config.llm.model_name)
                
                # Show traits information
                if hasattr(config, 'traits') and config.traits:
                    traits_display = ", ".join(config.traits)
                    info_table.add_row("[bold]Traits:[/bold]", f"[yellow]{traits_display}[/yellow]")
                    
                    # Show resolved trait instructions
                    try:
                        traits_registry = get_traits_registry()
                        resolved_instructions = traits_registry.resolve_traits(config.traits)
                        if resolved_instructions:
                            info_table.add_row("[bold]Trait Instructions:[/bold]", "")
                            for i, instruction in enumerate(resolved_instructions):
                                display_instruction = instruction if len(instruction) <= 50 else instruction[:47] + "..."
                                info_table.add_row(f"  {config.traits[i]}:", f"[dim]{display_instruction}[/dim]")
                    except Exception as e:
                        info_table.add_row("[bold]Trait Instructions:[/bold]", f"[red]Error: {e}[/red]")
                else:
                    info_table.add_row("[bold]Traits:[/bold]", "[dim]None[/dim]")
                
                info_table.add_row("[bold]Temperature:[/bold]", str(config.temperature))
                info_table.add_row("[bold]Max Tokens:[/bold]", str(config.max_tokens))
                info_table.add_row("[bold]Tools:[/bold]", ", ".join(config.tools) if config.tools else "None")
                
                border_color = "magenta" if agent_info['category'] == 'Traits Demo' else "blue" if agent_info['category'] == 'Cognitive Core' else "green"
                console.print(Panel(info_table, title=f"📋 {config.name} Info", border_style=border_color))
                
                # Demo conversation
                console.print(f"\n[bold yellow]Demo Question:[/bold yellow] {agent_info['demo_message']}")
                
                try:
                    response = agent.chat(agent_info["demo_message"])
                    console.print(Panel(
                        response, 
                        title=f"💬 {config.name} Response",
                        border_style="magenta"
                    ))
                except Exception as e:
                    console.print(f"[red]Error during chat: {e}[/red]")
                    
                    # Provide specific API key guidance
                    if hasattr(config, 'cognitive_core') and config.cognitive_core:
                        model = config.cognitive_core.model.lower()
                        if "claude" in model:
                            console.print("[yellow]Note: Make sure ANTHROPIC_API_KEY is set in your environment[/yellow]")
                        elif "gpt" in model:
                            console.print("[yellow]Note: Make sure OPENAI_API_KEY is set in your environment[/yellow]")
                    else:
                        console.print("[yellow]Note: Make sure OPENAI_API_KEY is set in your .env file[/yellow]")
                
            else:
                console.print(f"[red]Failed to load {agent_info['config_file']}[/red]")
                
        except Exception as e:
            console.print(f"[red]Error loading {agent_info['config_file']}: {e}[/red]")
            
            # Check if it's an API key validation error
            if "requires" in str(e) and "API_KEY" in str(e):
                console.print(f"[yellow]💡 Tip: {e}[/yellow]")
    
    return loaded_agents


def interactive_chat(loaded_agents):
    """Interactive chat session with loaded agents."""
    
    if not loaded_agents:
        console.print("[red]No agents loaded successfully. Cannot start interactive mode.[/red]")
        return
    
    console.print("\n")
    console.print(Rule("[bold blue]Interactive Chat Mode[/bold blue]"))
    
    while True:
        console.print("\n[bold cyan]Available Agents:[/bold cyan]")
        
        # Create agent selection table with enhanced info including traits
        agent_table = Table(show_header=True, header_style="bold magenta")
        agent_table.add_column("ID", style="cyan", width=3)
        agent_table.add_column("Name", style="green")
        agent_table.add_column("Model", style="blue", width=15)
        agent_table.add_column("Traits", style="yellow", width=20)
        agent_table.add_column("Temp", style="red", width=6)
        
        for i, (agent, agent_info) in enumerate(loaded_agents, 1):
            # Get model info
            if hasattr(agent.config, 'cognitive_core') and agent.config.cognitive_core:
                model_name = agent.config.cognitive_core.model
            else:
                model_name = agent.config.llm.model_name
            
            # Get traits info
            if hasattr(agent.config, 'traits') and agent.config.traits:
                traits_display = ", ".join(agent.config.traits[:3])  # Show first 3 traits
                if len(agent.config.traits) > 3:
                    traits_display += "..."
            else:
                traits_display = "None"
            
            agent_table.add_row(
                str(i), 
                agent.config.name,
                model_name,
                traits_display,
                str(agent.config.temperature)
            )
        
        console.print(agent_table)
        
        # Agent selection
        try:
            choice = Prompt.ask(
                "\n[bold]Choose an agent (number) or 'quit' to exit[/bold]",
                choices=[str(i) for i in range(1, len(loaded_agents) + 1)] + ["quit", "q"]
            )
            
            if choice.lower() in ["quit", "q"]:
                console.print("\n[bold green]Thanks for trying Agent Factory! 👋[/bold green]")
                break
            
            selected_agent, agent_info = loaded_agents[int(choice) - 1]
            
            # Show selected agent info
            if hasattr(selected_agent.config, 'cognitive_core') and selected_agent.config.cognitive_core:
                model_info = f"[blue]{selected_agent.config.cognitive_core.model}[/blue]"
            else:
                model_info = f"[dim]{selected_agent.config.llm.model_name}[/dim]"
            
            # Show traits info
            traits_info = ""
            if hasattr(selected_agent.config, 'traits') and selected_agent.config.traits:
                traits_info = f" | Traits: [yellow]{', '.join(selected_agent.config.traits)}[/yellow]"
            
            # Chat session with selected agent
            console.print(f"\n[bold green]💬 Chatting with {selected_agent.config.name}[/bold green] ({model_info}{traits_info})")
            console.print("[dim]Type 'back' to choose a different agent, 'quit' to exit[/dim]\n")
            
            while True:
                user_input = Prompt.ask("[bold]You")
                
                if user_input.lower() == "back":
                    break
                elif user_input.lower() in ["quit", "q"]:
                    console.print("\n[bold green]Thanks for trying Agent Factory! 👋[/bold green]")
                    return
                
                try:
                    response = selected_agent.chat(user_input)
                    
                    # Format response with agent name
                    response_text = Text()
                    response_text.append(f"{selected_agent.config.name}: ", style="bold magenta")
                    response_text.append(response)
                    
                    console.print(response_text)
                    console.print()  # Add spacing
                    
                except Exception as e:
                    console.print(f"[red]Error: {e}[/red]")
                    
                    # Provide specific API key guidance
                    if hasattr(selected_agent.config, 'cognitive_core') and selected_agent.config.cognitive_core:
                        model = selected_agent.config.cognitive_core.model.lower()
                        if "claude" in model:
                            console.print("[yellow]Note: Make sure ANTHROPIC_API_KEY is set in your environment[/yellow]")
                        elif "gpt" in model:
                            console.print("[yellow]Note: Make sure OPENAI_API_KEY is set in your environment[/yellow]")
                    else:
                        console.print("[yellow]Note: Make sure OPENAI_API_KEY is set in your .env file[/yellow]")
        
        except (ValueError, IndexError):
            console.print("[red]Invalid choice. Please try again.[/red]")
        except KeyboardInterrupt:
            console.print("\n\n[bold green]Thanks for trying Agent Factory! 👋[/bold green]")
            break


def show_system_info():
    """Show system information and requirements."""
    
    # Check API key availability
    api_status = []
    if os.getenv("OPENAI_API_KEY"):
        api_status.append("✓ OPENAI_API_KEY found")
    else:
        api_status.append("✗ OPENAI_API_KEY not found")
    
    if os.getenv("ANTHROPIC_API_KEY"):
        api_status.append("✓ ANTHROPIC_API_KEY found")
    else:
        api_status.append("✗ ANTHROPIC_API_KEY not found")
    
    api_status_text = "\n".join(f"• {status}" for status in api_status)
    
    info_panel = Panel(
        "[bold blue]🔧 System Requirements:[/bold blue]\n\n"
        "• Python 3.9+ with required packages\n"
        "• API keys for LLM functionality:\n"
        f"{api_status_text}\n\n"
        "[bold blue]📁 Project Structure:[/bold blue]\n\n"
        "• agent_factory/ - Core package\n"
        "• configs/ - Agent configuration files\n"
        "• examples/ - Demo and example scripts\n\n"
        "[bold blue]🎯 Features Demonstrated:[/bold blue]\n\n"
        "• YAML-based agent configuration\n"
        "• Multiple agent personalities (Legacy + Cognitive Core + Traits)\n"
        "• Personality traits system with 20+ configurable traits\n"
        "• Tool integration (calculator, file reader)\n"
        "• Multi-LLM support (OpenAI GPT-4, Anthropic Claude)\n"
        "• Temperature control and token limits\n"
        "• Interactive chat sessions\n"
        "• API key validation and error handling",
        title="📖 Agent Factory Overview",
        border_style="cyan"
    )
    
    console.print(info_panel)


def main():
    """Main demo function."""
    
    try:
        # Show system info
        show_system_info()
        
        # Run agent demonstrations
        loaded_agents = demo_agent_factory()
        
        # Ask if user wants interactive mode
        if loaded_agents:
            console.print("\n")
            if Confirm.ask("[bold]Would you like to try interactive chat mode?[/bold]", default=True):
                interactive_chat(loaded_agents)
            else:
                console.print("\n[bold green]Demo complete! Thanks for trying Agent Factory! 🎉[/bold green]")
        else:
            console.print("\n[red]No agents were loaded successfully. Please check your configuration files and API key.[/red]")
    
    except KeyboardInterrupt:
        console.print("\n\n[bold green]Demo interrupted. Thanks for trying Agent Factory! 👋[/bold green]")
    except Exception as e:
        console.print(f"\n[red]Unexpected error: {e}[/red]")
        console.print("[yellow]Please check your setup and try again.[/yellow]")


if __name__ == "__main__":
    main() 