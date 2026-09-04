import asyncio
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from personalai.config import settings
from personalai.storage import StorageSyncDaemon
from personalai.inference import LocalInferenceEngine
from personalai.rag import LocalVectorStore
from personalai.orchestration import PersonalAIAgentOrchestrator
from personalai.mesh import P2PEventBroker, MobileADBBridge

app = typer.Typer(name="personalai", help="Zero-leak Personal AI System CLI")
console = Console()


@app.command()
def sync(category: str = typer.Option("all", help="Category to sync: base-models, adapters, knowledge, or all")):
    """Syncs cold storage artifacts from Google Drive to local SSD cache."""
    console.print(Panel.fit("[bold blue]Personal AI Cold Storage Sync[/bold blue]"))
    daemon = StorageSyncDaemon()
    success = daemon.sync_from_remote(category=category)
    if success:
        console.print("[bold green]Synchronization completed successfully.[/bold green]")
    else:
        console.print("[yellow]Sync completed with warnings or running in local offline mode.[/yellow]")


@app.command()
def status():
    """Displays local AI system diagnostics and health overview."""
    console.print(Panel.fit("[bold magenta]Personal AI System Diagnostics[/bold magenta]"))
    
    table = Table(title="Component Status")
    table.add_column("Component", style="cyan")
    table.add_column("Details", style="white")
    table.add_column("Status", style="bold green")

    # Local Inference
    engine = LocalInferenceEngine()
    health = engine.check_health()
    table.add_row(
        "Local Inference Engine",
        f"{engine.host}:{engine.port} ({engine.model})",
        "[green]ONLINE[/green]" if health else "[red]OFFLINE (Start Ollama/llama.cpp)[/red]",
    )

    # Storage Cache
    daemon = StorageSyncDaemon()
    manifest = daemon.verify_local_artifacts()
    n_models = len(manifest.get("base-models", {}))
    n_adapters = len(manifest.get("adapters", {}))
    table.add_row("SSD Cache Storage", f"{settings.local_cache_dir} ({n_models} models, {n_adapters} adapters)", "[green]READY[/green]")

    # RAG Vector Store
    table.add_row("ChromaDB RAG Store", f"{settings.chroma_persist_dir}", "[green]READY[/green]")

    # Mesh Network
    table.add_row("P2P Event Broker", f"ws://{settings.mesh_host}:{settings.mesh_port}", "[green]CONFIGURED[/green]")

    console.print(table)


@app.command()
def ingest(path: Path = typer.Argument(..., help="Path to markdown/text file or directory to ingest into local RAG")):
    """Ingests documents into local ChromaDB RAG vector store."""
    console.print(f"[bold cyan]Ingesting documents from {path}...[/bold cyan]")
    store = LocalVectorStore()
    
    docs = []
    if path.is_file():
        docs.append({"id": path.name, "text": path.read_text(encoding="utf-8"), "metadata": {"source": str(path)}})
    elif path.is_dir():
        for file in path.glob("**/*.md"):
            docs.append({"id": file.name, "text": file.read_text(encoding="utf-8"), "metadata": {"source": str(file)}})

    count = store.ingest_documents(docs)
    console.print(f"[bold green]Successfully ingested {count} document chunks into local RAG vector store.[/bold green]")


@app.command()
def chat(prompt: Optional[str] = typer.Option(None, "--prompt", "-p", help="Single prompt execution mode")):
    """Launches interactive zero-leak personal AI prompt session."""
    console.print(Panel.fit("[bold green]Personal AI Interactive Shell (Zero-Leak Mode)[/bold green]"))
    orchestrator = PersonalAIAgentOrchestrator()

    if prompt:
        res = asyncio.run(orchestrator.execute_query(prompt))
        console.print(f"\n[bold yellow]AI Response:[/bold yellow]\n{res['response']}")
        if res.get("citations"):
            console.print(f"\n[bold dim]Citations: {res['citations']}[/bold dim]")
        return

    console.print("[dim]Type 'exit' or 'quit' to end session.[/dim]\n")
    while True:
        try:
            user_input = console.input("[bold cyan]You > [/bold cyan]")
            if user_input.strip().lower() in ["exit", "quit"]:
                break
            res = asyncio.run(orchestrator.execute_query(user_input))
            console.print(f"\n[bold yellow]Personal AI > [/bold yellow]\n{res['response']}\n")
        except (KeyboardInterrupt, EOFError):
            break


async def _run_broker():
    broker = P2PEventBroker()
    await broker.start()
    try:
        await asyncio.Future()  # Keeps server running forever
    except (asyncio.CancelledError, KeyboardInterrupt):
        await broker.stop()


@app.command()
def mesh_start():
    """Starts the P2P WebSocket event broker over Tailscale mesh."""
    console.print(f"[bold green]Starting P2P Event Broker on {settings.mesh_host}:{settings.mesh_port}...[/bold green]")
    try:
        asyncio.run(_run_broker())
    except (KeyboardInterrupt, SystemExit):
        console.print("[yellow]P2P Event Broker stopped.[/yellow]")


if __name__ == "__main__":
    app()
