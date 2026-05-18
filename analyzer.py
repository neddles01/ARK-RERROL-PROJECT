import re
import difflib

def is_fuzzy_match(keyword: str, text: str, threshold: float = 0.85) -> bool:
    keyword = keyword.lower()
    text = text.lower()
    
    # 1. Busca exata de substring
    idx = text.find(keyword)
    if idx != -1:
        prefix = text[:idx]
        # Se não houver palavra de 2+ letras antes, é um match válido
        if not re.search(r'[a-z]{2,}', prefix):
            return True
        
    keyword_len = len(keyword)
    if keyword_len > len(text):
        return False
        
    # 2. Busca com janela deslizante do tamanho da palavra-chave (para erros do OCR)
    for i in range(len(text) - keyword_len + 1):
        segment = text[i:i+keyword_len]
        ratio = difflib.SequenceMatcher(None, keyword, segment).ratio()
        if ratio >= threshold:
            prefix = text[:i]
            if not re.search(r'[a-z]{2,}', prefix):
                return True
                
    return False

def analyze_text(raw_text: str, mode: str, target_stat: str, min_value: float) -> dict:
    """
    Analyzes the extracted OCR text based on the provided configuration.
    
    Returns a dictionary containing:
        - raw_text: The original OCR text
        - parsed_text: The text considered for analysis
        - stat_found: Boolean indicating if the stat was found
        - value_found: The numeric value extracted (or None)
        - approved: Boolean indicating if it meets the criteria
        - reason: Textual reason for the decision
        - found_line: The exact line where the stat was found (or None)
    """
    result = {
        "raw_text": raw_text,
        "parsed_text": raw_text,
        "stat_found": False,
        "value_found": None,
        "approved": False,
        "reason": f"Aguardando stat aparecer com valor >= {min_value}",
        "found_line": None
    }

    # 1. Slice text based on mode
    lines = raw_text.splitlines()
    parsed_lines = lines
    
    if mode == "Saddle unique":
        anchor_found = False
        parsed_lines = []
        for i, line in enumerate(lines):
            if "Random Stat Bonuses" in line:
                anchor_found = True
                idx = line.find("Random Stat Bonuses")
                after_anchor = line[idx + len("Random Stat Bonuses"):].strip()
                # Remove common garbage like ":"
                if after_anchor.startswith(":"):
                    after_anchor = after_anchor[1:].strip()
                if after_anchor:
                    parsed_lines.append(after_anchor)
                parsed_lines.extend(lines[i+1:])
                break
        
        if not anchor_found:
            result["parsed_text"] = ""
            result["reason"] = f"Aguardando stat aparecer com valor >= {min_value}"
            return result
            
        result["parsed_text"] = "\n".join(parsed_lines)

    # 2. Determine Keywords and Requirements
    stat_has_percent = "%" in target_stat
    
    # Strip common suffixes to get the core keyword
    base_keyword = target_stat.replace("Increased By %", "") \
                              .replace("Increase By %", "") \
                              .replace("Increased By", "") \
                              .replace("By %", "") \
                              .replace("%", "").strip().lower()
                              
    # 3. Search for the target stat
    found_line = None
    for line in parsed_lines:
        if is_fuzzy_match(base_keyword, line):
            # Check percentage rule
            line_has_percent = "%" in line
            if stat_has_percent != line_has_percent:
                continue  # Skip, percentage mismatch
                
            found_line = line
            break
            
    if not found_line:
        result["reason"] = f"Aguardando stat aparecer com valor >= {min_value}"
        return result
        
    result["stat_found"] = True
    result["found_line"] = found_line

    # 4. Extract numeric value
    # Matches integers or floats (e.g., 150, 150.5, 1,500.5)
    numbers = re.findall(r"[-+]?\d*[.,]?\d+", found_line)
    
    if not numbers:
        result["reason"] = f"Aguardando stat aparecer com valor >= {min_value}"
        return result

    # Extract the last valid number in the line (stats format: "Name: Value")
    try:
        val_str = numbers[-1].replace(',', '')
        value = float(val_str)
        result["value_found"] = value
    except ValueError:
        result["reason"] = f"Aguardando stat aparecer com valor >= {min_value}"
        return result

    # 5. Compare with minimum value
    if result["value_found"] >= min_value:
        result["approved"] = True
        result["reason"] = f"Aprovado: {result['value_found']} >= {min_value}"
    else:
        result["approved"] = False
        result["reason"] = f"Aguardando stat aparecer com valor >= {min_value}"

    return result
