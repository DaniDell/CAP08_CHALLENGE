from typing import Generator
import typer
import requests
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich import box
import json
from uuid import uuid4
import os
from datetime import datetime
from app.utils.helpers import save_conversation

# Inicialización de las aplicaciones Typer y Rich Console
app = typer.Typer()
console = Console()

# Generar un session_id único para la sesión de chat
session_id = str("default")

def display_streaming_response(response: requests.Response):
    """
    Muestra la respuesta del servidor en tiempo real (streaming).
    """
    try:
        sources = []
        # Procesar la respuesta en chunks
        for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
            if chunk and chunk.startswith('data: '):
                try:
                    # Extraer el JSON del chunk
                    json_str = chunk.replace('data: ', '', 1).strip()
                    content = json.loads(json_str)
                    
                    if content.get("type") == "message":
                        # Mostrar el contenido del mensaje como Markdown
                        console.print(Markdown(content["content"]))
                        console.print()  # Línea en blanco para mejor legibilidad
                    elif content.get("type") == "sources":
                        # Guardar las fuentes para mostrarlas al final
                        sources = content["content"]
                
                except json.JSONDecodeError:
                    console.print(chunk, end='')
                    
        # Mostrar las fuentes al final
        if sources:
            console.print("\n[bold cyan]Fuentes consultadas:[/bold cyan]")
            for source in sources[:5]:  # Limitamos a 5 fuentes para mantener la salida limpia
                title = source.get('title', 'Sin título')
                link = source.get('link', 'Sin enlace')
                console.print(f"- {title}")
                console.print(f"  [blue]{link}[/blue]")
        
        console.print()  # Línea en blanco final
    except Exception as e:
        console.print(f"\n[red]Error al procesar la respuesta: {str(e)}[/red]")


@app.command()
def chat(
    prompt_type: str = typer.Option(
        "default", 
        "--prompt-type", "-p", 
        help="Tipo de prompt a utilizar: default, friendly o technical"
    )
):
    """Inicia una sesión interactiva de chat en la consola."""
    if prompt_type not in ["default", "friendly", "technical"]:
        console.print("[red]Error: El tipo de prompt debe ser 'default', 'friendly' o 'technical'[/red]")
        return

    prompt_style_desc = {
        "default": "conciso y directo",
        "friendly": "amigable y cercano",
        "technical": "técnico y preciso"
    }

    console.print("\n[bold blue]=== Chatbot Consola ===[/bold blue]")
    console.print(f"Usando prompt: [cyan]{prompt_style_desc[prompt_type]}[/cyan]")
    console.print("(Escribe 'salir' para terminar, 'cambiar prompt' para cambiar el estilo)\n")
    
    current_prompt_type = prompt_type
    
    while True:
        try:
            # Entrada del usuario
            query = console.input("[bold green]Tú:[/bold green] ").strip()
            
            # Comandos especiales
            if query.lower() == 'salir':
                console.print("[yellow]¡Hasta luego![/yellow]")
                break
            
            if query.lower() == 'cambiar prompt':
                options = ["default", "friendly", "technical"]
                console.print("\n[bold cyan]Selecciona un tipo de prompt:[/bold cyan]")
                for i, option in enumerate(options):
                    console.print(f"[cyan]{i+1}.[/cyan] {option} - {prompt_style_desc[option]}")
                
                selection = console.input("[bold cyan]Selección (1-3):[/bold cyan] ").strip()
                try:
                    idx = int(selection) - 1
                    if 0 <= idx < len(options):
                        current_prompt_type = options[idx]
                        console.print(f"\n[green]Prompt cambiado a: {current_prompt_type} - {prompt_style_desc[current_prompt_type]}[/green]\n")
                    else:
                        console.print("[red]Selección inválida. Usando el prompt actual.[/red]\n")
                except ValueError:
                    console.print("[red]Entrada inválida. Usando el prompt actual.[/red]\n")
                continue
                
            if not query:
                continue
                
            # Llamada a la API local con streaming
            with console.status("[bold yellow]Pensando...[/bold yellow]"):
                response = requests.post(
                    "http://localhost:8000/api/chat/stream",
                    params={
                        "query": query, 
                        "session_id": session_id,
                        "prompt_type": current_prompt_type
                    },
                    stream=True,
                    timeout=30
                )
                
                if response.status_code == 200:
                    console.print("\n[bold blue]Bot:[/bold blue]")
                    sources = []
                    bot_response = ""

                    # Procesar la respuesta en streaming
                    for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
                        if chunk and chunk.startswith('data: '):
                            try:
                                json_str = chunk.replace('data: ', '', 1).strip()
                                content = json.loads(json_str)

                                if content.get("type") == "message":
                                    bot_response += content["content"] + "\n"
                                    console.print(Markdown(content["content"]))
                                    console.print()
                                elif content.get("type") == "sources":
                                    sources = content["content"]

                            except json.JSONDecodeError:
                                console.print(chunk, end='')



                    # Mostrar las fuentes al final
                    if sources:
                        console.print("\n[bold cyan]Fuentes consultadas:[/bold cyan]")
                        for source in sources[:5]:
                            title = source.get('title', 'Sin título')
                            link = source.get('link', 'Sin enlace')
                            console.print(f"- {title}")
                            console.print(f"  [blue]{link}[/blue]")

                    console.print()  # Línea en blanco final
                else:
                    console.print(f"\n[red]Error: {response.json().get('detail', 'Error desconocido')}[/red]")
                    
        except requests.exceptions.ConnectionError:
            console.print("\n[red]Error: No se pudo conectar al servidor. Asegúrate de que esté corriendo con:[/red]")
            console.print("[yellow]uvicorn app.main:app --reload[/yellow]")
        except KeyboardInterrupt:
            console.print("\n[yellow]Sesión terminada por el usuario.[/yellow]")
            break
        except Exception as e:
            console.print(f"\n[red]Error: {str(e)}[/red]")

if __name__ == "__main__":
    app()