import os
from typing import List, Dict

class RepoIndexer:
    """
    Bible II, Section 3: Context Indexer
    Traverses repo tree and collects metadata.
    Does NOT ingest full content or use embeddings in V0.
    """
    
    def index(self, root_path: str) -> Dict[str, List[str]]:
        """
        Walks the repository and returns a file structure.
        """
        file_list = []
        
        # Simple walk
        for root, dirs, files in os.walk(root_path):
            # Skip hidden dirs (simple filter for V0)
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                if file.startswith('.'):
                    continue
                    
                full_path = os.path.join(root, file)
                # Store relative path
                rel_path = os.path.relpath(full_path, root_path)
                file_list.append(rel_path)
        
        return {
            "files": sorted(file_list),
            "root": root_path
        }
