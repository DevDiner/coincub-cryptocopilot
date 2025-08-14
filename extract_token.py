#extract_token.py
import re

def extract_token_name_symbol(user_input: str) -> list[str]:
    """
    Extracts one or more token names or symbols from user input using a comprehensive
    stop word list and robust text normalization.
    """
    if not user_input:
        return []

    # A comprehensive, expanded list of words to ignore.
    stop_words = {
        # Standard Stop Words (articles, prepositions, pronouns, etc.)
        'a', 'about', 'after', 'all', 'also', 'am', 'an', 'and', 'any', 'are', 'as', 'at', 'be',
        'because', 'been', 'but', 'by', 'can', 'could', 'did', 'do', 'does', 'doing', 'for', 
        'from', 'further', 'had', 'has', 'have', 'having', 'he', 'her', 'how', 'i', 'if', 'in', 
        'into', 'is', 'it', 'its', 'just', 'me', 'more', 'my', 'no', 'not', 'now', 'of', 'on', 
        'or', 'our', 'should', 'so', 'some', 'than', 'that', 'the', 'their', 'them', 'then', 
        'there', 'these', 'they', 'this', 'to', 'up', 'us', 'was', 'we', 'were', 'what', 'when', 
        'where', 'which', 'who', 'why', 'will', 'with', 'would', 'you', 'your','goes', 'going',

        # Action & Intent Words
        'analyze', 'buy', 'check', 'compare', 'explain', 'find', 'get', 'give', 'go', 'going',
        'know', 'list', 'look', 'see', 'sell', 'show', 'tell', 'trade', 'view', 'tell', 'tells', 

        # Financial & Crypto Terms
        'cap', 'chart', 'coin', 'coins', 'crypto', 'data', 'details', 'info', 'information',
        'liquidity', 'market', 'movers', 'overview', 'performance', 'performing', 'price', 
        'prices', 'report', 'stats', 'summary', 'token', 'tokens', 'value', 'volatility', 'volume', 'tokens', 'token',

        # Descriptive & Qualitative Words
        'bad', 'best', 'good', 'high', 'hot', 'latest', 'low', 'new', 'recent', 'safe', 'top', 
        'trending', 'worse', 'worst', 'risky', 'trendiest', 'trendy'

        # Time-related Words
        'currently', 'today', 'tomorrow', 'tmrw', 'tmr','yesterday','ytd','now',        

        #Quantifiers
        'all', 'any', 'each', 'every', 'few', 'most', 'some',

        # Conversational Fillers
        'hello', 'help', 'hey', 'ok', 'okay', 'please', 'thanks', 'thank', 'pls' ,'plz', 'thx',

        # Other Common Nouns/Verbs
        'versus', 'vs' ,'compare', 'comparing',
    }

    # Normalize input: lowercase
    normalized_input = user_input.lower()

    # Find and handle $SYMBOLS first, and remove them from the string to avoid double-counting
    dollar_symbols = re.findall(r'\$([a-zA-Z0-9]{2,10})', normalized_input)
    normalized_input = re.sub(r'\$[a-zA-Z0-9]{2,10}', '', normalized_input)

    # Aggressively remove all punctuation, including apostrophes from contractions.
    normalized_input = re.sub(r'[^\w\s-]', '', normalized_input)

    # Add contraction variations to the stop word list
    stop_words.update(['hows', 'whats', 'wheres', 'whens', 'whys', 'its'])

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