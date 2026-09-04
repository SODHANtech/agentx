import asyncio
import shutil
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
from personalai.orchestration import PersonalAIAgentOrchestrator, ModelRouter
from personalai.mesh import P2PEventBroker, MobileADBBridge

app = typer.Typer(name="personalai", help="Zero-leak Personal AI System CLI")
console = Console()


def _read_file_text(file_path: Path) -> str:
    """Reads text from .txt, .md, .pdf files safely."""
    if file_path.suffix.lower() == ".pdf":
        try:
            import pypdf
            reader = pypdf.PdfReader(file_path)
            pages = [page.extract_text() for page in reader.pages if page.extract_text()]
            return "\n".join(pages)
        except ImportError:
            try:
                import pdfplumber
                with pdfplumber.open(file_path) as pdf:
                    pages = [p.extract_text() for p in pdf.pages if p.extract_text()]
                    return "\n".join(pages)
            except Exception:
                return f"[PDF text extraction requires pypdf or pdfplumber: pip install pypdf]"
    return file_path.read_text(encoding="utf-8", errors="ignore")


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
def router(prompt: Optional[str] = typer.Option(None, "--prompt", "-p", help="Test prompt intent classification & routing")):
    """Displays dynamic multi-model router diagnostic status and rules."""
    console.print(Panel.fit("[bold cyan]Dynamic Multi-Model Router Diagnostics[/bold cyan]"))
    mr = ModelRouter()
    installed = mr.get_installed_ollama_models()

    table = Table(title="Model Mapping Rules & Local Status")
    table.add_column("Intent Domain", style="cyan")
    table.add_column("Configured Model", style="white")
    table.add_column("Installed Status", style="bold green")

    mappings = [
        ("TOOL_CALLING", settings.tool_calling_model),
        ("CODING", settings.coding_model),
        ("REASONING", settings.reasoning_model),
        ("VISION", settings.vision_model),
        ("GENERAL", settings.general_model),
    ]

    for intent, model_tag in mappings:
        is_pulled = any(model_tag in m for m in installed)
        status_str = "[green]INSTALLED[/green]" if is_pulled else f"[yellow]FALLBACK TO {settings.general_model}[/yellow]"
        table.add_row(intent, model_tag, status_str)

    console.print(table)

    if prompt:
        res = mr.select_model(prompt)
        console.print(f"\n[bold yellow]Prompt Classification Result:[/bold yellow]")
        console.print(f"Prompt: [italic]'{prompt}'[/italic]")
        console.print(f"Intent Domain: [bold cyan]{res['intent']}[/bold cyan]")
        console.print(f"Target Model: [bold white]{res['target_model']}[/bold white]")
        console.print(f"Selected Model: [bold green]{res['model']}[/bold green]")
        if res["fallback_used"]:
            console.print(f"[dim](Fallback used because '{res['target_model']}' is not pulled yet)[/dim]")


@app.command()
def ingest(
    path: Path = typer.Argument(..., help="Path to file or codebase/document directory to ingest into local RAG"),
    chunk_size: int = typer.Option(800, "--chunk-size", "-c", help="Target chunk size in characters"),
    chunk_overlap: int = typer.Option(100, "--chunk-overlap", "-o", help="Target chunk overlap in characters"),
):
    """Ingests codebase files (.py, .ts, .java, etc.) and documents (.md, .pdf, .txt, etc.) into local RAG vector store."""
    console.print(Panel.fit(f"[bold cyan]Mass RAG Ingestion Pipeline[/bold cyan]\nTarget: [bold yellow]{path}[/bold yellow]"))
    store = LocalVectorStore()
    
    if not path.exists():
        console.print(f"[bold red]Error: Path '{path}' does not exist.[/bold red]")
        raise typer.Exit(code=1)

    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    from personalai.rag.mass_ingester import MassIngester

    ingester = MassIngester(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        scan_task = progress.add_task("Scanning & Chunking files...", total=100)
        
        def p_callback(filename: str, current: int, total: int):
            percent = int((current / max(1, total)) * 100)
            progress.update(scan_task, description=f"Processing [yellow]{filename}[/yellow] ({current}/{total})", completed=percent)

        chunks = ingester.scan_directory(path, progress_callback=p_callback)
        progress.update(scan_task, description="Upserting chunks to ChromaDB...", completed=100)
        count = store.ingest_documents(chunks)

    console.print(f"[bold green]Successfully ingested {count} chunks across supported documents & source files into ChromaDB RAG store.[/bold green]")



@app.command()
def clean(
    reset_rag: bool = typer.Option(False, "--reset-rag", help="Resets local RAG vector database (does not delete source files)"),
    temp_only: bool = typer.Option(True, "--temp-only", help="Cleans temporary bytecode and cache files safely"),
):
    """Safely cleans temporary caches, bytecode, and optional RAG vector indexes without breaking anything."""
    console.print(Panel.fit("[bold yellow]Personal AI Cache Cleaning[/bold yellow]"))
    cleaned_count = 0

    # 1. Clean __pycache__ and .pyc
    for pycache in Path(".").glob("**/__pycache__"):
        if pycache.is_dir():
            shutil.rmtree(pycache, ignore_errors=True)
            cleaned_count += 1

    for pyc in Path(".").glob("**/*.pyc"):
        if pyc.is_file():
            pyc.unlink(missing_ok=True)
            cleaned_count += 1

    console.print(f"[green]Cleaned {cleaned_count} temporary bytecode cache files.[/green]")

    # 2. Reset RAG if requested
    if reset_rag:
        store = LocalVectorStore()
        try:
            store.client.reset()
            console.print("[bold green]Local ChromaDB RAG vector store reset successfully.[/bold green]")
        except Exception as e:
            console.print(f"[red]Could not reset ChromaDB: {e}[/red]")

    console.print("[bold green]System cache cleanup completed safely![/bold green]")


@app.command()
def chat(prompt: Optional[str] = typer.Option(None, "--prompt", "-p", help="Single prompt execution mode")):
    """Launches interactive zero-leak personal AI prompt session."""
    console.print(Panel.fit("[bold green]Personal AI Interactive Shell (Zero-Leak Mode)[/bold green]"))
    orchestrator = PersonalAIAgentOrchestrator()

    if prompt:
        res = asyncio.run(orchestrator.execute_query(prompt))
        console.print(f"\n[bold yellow]AI Response ({res.get('used_model', 'local')}):[/bold yellow]\n{res['response']}")
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
            console.print(f"\n[bold yellow]Personal AI ({res.get('used_model', 'local')}) > [/bold yellow]\n{res['response']}\n")
        except (KeyboardInterrupt, EOFError):
            break


@app.command()
def gui():
    """Launches modern Fintech Desktop Application GUI."""
    console.print("[bold cyan]Launching Personal AI Fintech Desktop GUI...[/bold cyan]")
    from personalai.gui.app import launch_gui
    launch_gui()


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
