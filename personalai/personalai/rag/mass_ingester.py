import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Callable
import re

logger = logging.getLogger(__name__)

# Supported document & code extensions
DOCUMENT_EXTENSIONS: Set[str] = {
    ".md", ".txt", ".pdf", ".rst", ".csv", ".json", ".yaml", ".yml", ".xml", ".html", ".ipynb"
}

CODE_EXTENSIONS: Set[str] = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".cpp", ".c", ".h", ".hpp",
    ".cs", ".go", ".rs", ".php", ".rb", ".sh", ".ps1", ".sql", ".dart"
}

SUPPORTED_EXTENSIONS: Set[str] = DOCUMENT_EXTENSIONS | CODE_EXTENSIONS

# Directories and patterns to ignore during recursive scan
DEFAULT_IGNORE_DIRS: Set[str] = {
    ".git", ".hg", ".svn", "node_modules", "__pycache__", ".venv", "venv", "env",
    "build", "dist", ".idea", ".vscode", ".pytest_cache", ".mypy_cache",
    ".chroma", ".system_generated", "target", "out", "bin", "obj"
}

DEFAULT_IGNORE_EXTS: Set[str] = {
    ".pyc", ".pyo", ".pyd", ".exe", ".dll", ".so", ".dylib", ".bin",
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".svg", ".webp",
    ".mp3", ".mp4", ".mov", ".avi", ".zip", ".tar", ".gz", ".7z", ".rar",
    ".db", ".sqlite", ".sqlite3", ".pth", ".onnx", ".safetensors"
}


class MassIngester:
    """Recursively scans codebase and document folders, applies smart chunking,
    and prepares structured documents with metadata for local ChromaDB RAG ingestion.
    """

    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def is_ignored(self, path: Path, base_dir: Optional[Path] = None) -> bool:
        """Determines if a file or directory path should be ignored."""
        parts = path.parts
        for part in parts:
            if part in DEFAULT_IGNORE_DIRS:
                return True

        if path.suffix.lower() in DEFAULT_IGNORE_EXTS:
            return True

        # Skip hidden files/directories starting with '.'
        if any(p.startswith(".") and p not in (".", "..") for p in parts):
            return True

        return False

    def read_file_content(self, file_path: Path) -> Optional[str]:
        """Reads file text content safely, supporting PDF and plain text / source code files."""
        ext = file_path.suffix.lower()
        
        if ext == ".pdf":
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
                except Exception as e:
                    logger.warning(f"Could not extract PDF text for {file_path}: {e}")
                    return None
            except Exception as e:
                logger.warning(f"Error reading PDF {file_path}: {e}")
                return None

        try:
            return file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            logger.warning(f"Error reading text file {file_path}: {e}")
            return None

    def chunk_text(self, text: str, file_path: Path, base_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
        """Splits file content into overlapping chunks with line number tracking and metadata."""
        if not text or not text.strip():
            return []

        rel_path = str(file_path.relative_to(base_dir)) if base_dir and file_path.is_relative_to(base_dir) else str(file_path)
        ext = file_path.suffix.lower()
        file_type = "code" if ext in CODE_EXTENSIONS else "document"

        lines = text.splitlines(keepends=True)
        chunks = []
        
        current_chunk_lines = []
        current_chunk_length = 0
        start_line = 1
        current_line = 1

        for line in lines:
            line_len = len(line)
            if current_chunk_length + line_len > self.chunk_size and current_chunk_lines:
                chunk_text = "".join(current_chunk_lines).strip()
                if chunk_text:
                    chunks.append((start_line, current_line - 1, chunk_text))
                
                # Maintain overlap by retaining trailing lines
                overlap_lines = []
                overlap_len = 0
                for rev_line in reversed(current_chunk_lines):
                    if overlap_len + len(rev_line) <= self.chunk_overlap:
                        overlap_lines.insert(0, rev_line)
                        overlap_len += len(rev_line)
                    else:
                        break
                
                current_chunk_lines = overlap_lines
                current_chunk_length = overlap_len
                start_line = max(1, current_line - len(overlap_lines))

            current_chunk_lines.append(line)
            current_chunk_length += line_len
            current_line += 1

        if current_chunk_lines:
            chunk_text = "".join(current_chunk_lines).strip()
            if chunk_text:
                chunks.append((start_line, current_line - 1, chunk_text))

        doc_chunks = []
        total_chunks = len(chunks)
        clean_rel_path = rel_path.replace("\\", "/")
        for idx, (s_line, e_line, chunk_content) in enumerate(chunks, start=1):
            chunk_id = f"{clean_rel_path}::chunk_{idx}_L{s_line}-L{e_line}"
            metadata = {

                "source": rel_path,
                "filename": file_path.name,
                "relative_path": rel_path,
                "file_type": file_type,
                "extension": ext,
                "start_line": s_line,
                "end_line": e_line,
                "chunk_index": idx,
                "total_chunks": total_chunks,
            }
            doc_chunks.append({
                "id": chunk_id,
                "text": f"--- File: {rel_path} (Lines {s_line}-{e_line}) ---\n" + chunk_content,
                "metadata": metadata,
            })

        return doc_chunks

    def scan_directory(self, target_dir: Path, progress_callback: Optional[Callable[[str, int, int], None]] = None) -> List[Dict[str, Any]]:
        """Recursively scans directory and extracts doc chunks for ChromaDB RAG."""
        target_dir = Path(target_dir).resolve()
        if not target_dir.exists():
            raise FileNotFoundError(f"Target directory does not exist: {target_dir}")

        all_files: List[Path] = []
        if target_dir.is_file():
            if not self.is_ignored(target_dir):
                all_files.append(target_dir)
        else:
            for file_path in target_dir.rglob("*"):
                if file_path.is_file() and not self.is_ignored(file_path, base_dir=target_dir):
                    if file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                        all_files.append(file_path)

        all_doc_chunks = []
        total_files = len(all_files)

        for idx, file_path in enumerate(all_files, start=1):
            if progress_callback:
                progress_callback(file_path.name, idx, total_files)

            content = self.read_file_content(file_path)
            if content:
                chunks = self.chunk_text(content, file_path, base_dir=target_dir if target_dir.is_dir() else target_dir.parent)
                all_doc_chunks.extend(chunks)

        return all_doc_chunks
