"""
Chunker module for converting analysis results into text chunks.
"""

def create_chunks(analysis_result):
    """
    Convert analysis result into text chunks for embedding.
    
    Args:
        analysis_result (dict): Result from analyze_file containing:
            - functions: list of {name, line}
            - classes: list of {name, line}
            - imports: list of import strings
            - relationships: dict mapping function name -> [callees]
    
    Returns:
        list: List of text chunks suitable for embedding.
    """
    chunks = []
    
    # Chunk for imports
    if analysis_result.get("imports"):
        imports_text = "Imports: " + ", ".join(analysis_result["imports"])
        chunks.append(imports_text)
    
    # Chunks for functions
    for func in analysis_result.get("functions", []):
        func_chunk = f"Function: {func['name']} at line {func['line']}"
        if func['name'] in analysis_result.get("relationships", {}):
            callees = analysis_result["relationships"][func['name']]
            func_chunk += f". Calls: {', '.join(callees)}"
        chunks.append(func_chunk)
    
    # Chunks for classes
    for cls in analysis_result.get("classes", []):
        cls_chunk = f"Class: {cls['name']} at line {cls['line']}"
        chunks.append(cls_chunk)
    
    return chunks if chunks else ["No code entities found in analysis"]
