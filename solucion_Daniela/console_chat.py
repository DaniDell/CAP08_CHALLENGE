from typing import Generator
import typer
import requests
from rich.console import Console
from rich.markdown import Markdown
import json

# Inicialización de las aplicaciones Typer y Rich Console
app = typer.Typer()
console = Console()

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
def chat():
    """Inicia una sesión interactiva de chat en la consola."""
    console.print("\n[bold blue]=== Chatbot Consola ===[/bold blue]")
    console.print("(Escribe 'salir' para terminar)\n")
    
    while True:
        try:
            # Entrada del usuario
            query = console.input("[bold green]Tú:[/bold green] ").strip()
            if query.lower() == 'salir':
                console.print("[yellow]¡Hasta luego![/yellow]")
                break
                
            if not query:
                continue
                
            # Llamada a la API local con streaming
            with console.status("[bold yellow]Pensando...[/bold yellow]"):
                response = requests.post(
                    "http://localhost:8000/api/chat/stream",
                    params={"query": query},
                    stream=True,
                    timeout=30
                )
                
                if response.status_code == 200:
                    console.print("\n[bold blue]Bot:[/bold blue]")
                    display_streaming_response(response)
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