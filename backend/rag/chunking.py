def recursive_character_splitter(text: str, chunk_size: int = 1000, chunk_overlap: int = 250) -> list[str]:
    """
    Splits text recursively based on a hierarchy of separators to keep semantic blocks together.
    """
    separators = ["\n\n", "\n", " ", ""]
    
    def _split(text_to_split: str, sep_idx: int) -> list[str]:
        if len(text_to_split) <= chunk_size:
            return [text_to_split]
            
        separator = separators[sep_idx]
        
        # If separator is empty string, we just force split by character
        if separator == "":
            return [text_to_split[i:i+chunk_size] for i in range(0, len(text_to_split), chunk_size - chunk_overlap)]
            
        splits = text_to_split.split(separator)
        
        # If splitting by this separator didn't do anything, try the next one
        if len(splits) == 1:
            return _split(text_to_split, sep_idx + 1)
            
        chunks = []
        current_chunk = ""
        
        for split in splits:
            # If a single split is larger than chunk size, we need to split it further
            if len(split) > chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                chunks.extend(_split(split, sep_idx + 1))
                continue
                
            if len(current_chunk) + len(separator) + len(split) > chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                # Start new chunk with overlap
                if current_chunk:
                    overlap_text = current_chunk[-chunk_overlap:]
                    overlap_idx = overlap_text.find(" ")
                    if overlap_idx != -1:
                        overlap_text = overlap_text[overlap_idx+1:]
                    current_chunk = overlap_text + separator + split
                else:
                    current_chunk = split
            else:
                if current_chunk:
                    current_chunk += separator + split
                else:
                    current_chunk = split
                    
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks

    return _split(text, 0)
