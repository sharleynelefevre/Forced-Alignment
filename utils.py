def normalize_string(string):
    """
    Lowercases and removes punctuation from input string, also strips the spaces from the borders and removes multiple spaces
    """
    string =re.sub(r"([,.!?'-:])", r"", string).lower()
    string = re.sub(' +', ' ',string).strip()
    return string
