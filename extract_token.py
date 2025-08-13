# extract_token.py
import re

def extract_token_name_symbol(user_input: str) -> list[str]:
    """
    Extracts one or more token names or symbols from user input using a comprehensive
    stop word list and robust text normalization.
    """
    if not user_input:
        return []

    # A comprehensive list of words to ignore.
    stop_words = {
        'a', 'about', 'after', 'all', 'also', 'am', 'an', 'and', 'any', 'are', 'as', 'at', 'be',
        'because', 'been', 'but', 'by', 'can', 'compare', 'could', 'did', 'do', 'does', 'doing',
        'for', 'from', 'further', 'had', 'has', 'have', 'having', 'he', 'her', 'how', 'i', 'if',
        'in', 'into', 'is', 'it', 'its', 'just', 'latest', 'me', 'more', 'my', 'no', 'not', 'now',
        'of', 'on', 'or', 'our', 'price', 'risk', 'risky', 'safe', 'should', 'so', 'some',
        'tell', 'than', 'that', 'the', 'their', 'them', 'then', 'there', 'these', 'they', 'this',

        'to', 'today', 'tomorrow', 'up', 'us', 'versus', 'vs', 'was', 'we', 'were', 'what', 'when',
        'where', 'which', 'who', 'why', 'will', 'with', 'would', 'yesterday', 'you', 'your','ytd','tmr','tmrw'
    }

    # Normalize input: lowercase
    normalized_input = user_input.lower()

    # Find and handle $SYMBOLS first, and remove them from the string to avoid double-counting
    dollar_symbols = re.findall(r'\$([a-zA-Z0-9]{2,10})', normalized_input)
    normalized_input = re.sub(r'\$[a-zA-Z0-9]{2,10}', '', normalized_input)

    # **THE CRITICAL CHANGE**: Aggressively remove all punctuation, including apostrophes from contractions.
    # This turns "how's" into "hows", "what's" into "whats", etc.
    normalized_input = re.sub(r'[^\w\s-]', '', normalized_input)

    # Add contraction variations to the stop word list
    stop_words.update(['hows', 'whats', 'wheres', 'whens', 'whys', 'its', 'whos'])

    # Find all remaining word-based tokens and filter them
    potential_tokens = re.findall(r'\b[a-zA-Z0-9-]{2,20}\b', normalized_input)
    word_tokens = [token for token in potential_tokens if token not in stop_words and not token.isdigit()]

    # Combine, ensure uniqueness, and maintain order
    all_tokens = []
    seen = set()
    for token in dollar_symbols + word_tokens:
        if token not in seen:
            seen.add(token)
            all_tokens.append(token)

    print(f"Extracted tokens: {all_tokens} from query: '{user_input}'")
    return all_tokens