import re
import mojimoji
import jaconv
from nltk.tokenize import PunktSentenceTokenizer
from typing import List, Dict


class TextProcessor:
    def __init__(self):
        """Initializes the TextProcessor with tokenizer and character maps."""
        try:
            import nltk
            nltk.download('punkt', quiet=True)
        except ImportError:
            raise ImportError("NLTK is required. Please install it with 'pip install nltk'")
        
        # Initialize the sentence tokenizer
        self.sentence_tokenizer = PunktSentenceTokenizer()
        
        # Compile regex patterns for efficiency
        self.whitespace_pattern = re.compile(r'\s+')
        self.multiple_period_pattern = re.compile(r'\.{2,}')
        self.number_with_unit_pattern = re.compile(r'(\d+)([a-zA-Z]+)')
        
        # Japanese specific patterns
        self.japanese_period_pattern = re.compile(r'。\s*')
        self.japanese_comma_pattern = re.compile(r'、\s*')
        
        # Character maps for replacements
        self.bracket_map = {
            '(': '（', ')': '）',
            '[': '［', ']': '］',
            '{': '｛', '}': '｝',
            '「': '「', '」': '」',
            '【': '【', '】': '】'
        }
        
        # Common English contractions
        self.contractions = {
            "won't": "will not",
            "can't": "cannot",
            "n't": " not",
            "'re": " are",
            "'s": " is",
            "'d": " would",
            "'ll": " will",
            "'ve": " have",
            "'m": " am"
        }

    def expand_contractions(self, text: str) -> str:
        """Expand English contractions in the text."""
        for contraction, expansion in self.contractions.items():
            text = text.replace(contraction, expansion)
        return text

    def normalize_numbers(self, text: str) -> str:
        """Add spaces between numbers and units."""
        return self.number_with_unit_pattern.sub(r'\1 \2', text)

    def process_japanese_text(self, text: str) -> str:
        """Process Japanese text for proper formatting and character width.
        
        Handles:
        - Whitespace normalization (converts to full-width spaces)
        - Full-width ASCII conversion
        - Number conversion to full-width
        - Proper Japanese punctuation
        - Line break normalization
        - Bracket style normalization
        
        Args:
            text (str): The Japanese text to process.
        Returns:
            str: The processed Japanese text with full-width characters.
        """
        # Convert numbers and ASCII characters to full-width, excluding spaces
        text = mojimoji.han_to_zen(text, digit=True, ascii=True, kana=False)
        
        # Normalize Japanese characters (half-width kana to full-width)
        text = jaconv.h2z(text, kana=True, ascii=False, digit=False)
        
        # Convert brackets to their proper Japanese forms
        for western, japanese in self.bracket_map.items():
            text = text.replace(western, japanese)
        
        # Ensure proper spacing around Japanese punctuation
        text = self.japanese_period_pattern.sub('。', text)
        text = self.japanese_comma_pattern.sub('、', text)
        
        # Handle spaces - convert sequences of spaces to single full-width space
        text = ' '.join(text.split())  # Normalize ASCII spaces
        text = text.replace(' ', '　')  # Convert to full-width spaces
        
        return text.strip()

    def process_english_text(self, text: str) -> str:
        """Process English text using NLTK for sentence tokenization.
        
        Handles:
        - Sentence segmentation
        - Proper spacing
        - Number and unit handling
        - Contraction expansion
        - Punctuation normalization
        
        Args:
            text (str): The English text to process.
        Returns:
            str: The processed English text.
        """
        # First expand contractions
        text = self.expand_contractions(text)
        
        # Add spaces after sentence-ending punctuation if missing
        text = re.sub(r'([.!?])([A-Z])', r'\1 \2', text)
        
        # Split into sentences using NLTK
        sentences = self.sentence_tokenizer.tokenize(text)
        
        processed_sentences = []
        for sentence in sentences:
            # Normalize whitespace within sentence
            sentence = ' '.join(sentence.split())
            
            # Handle numbers with units
            sentence = self.normalize_numbers(sentence)
            
            # Handle multiple periods
            sentence = re.sub(r'\.{2,}', '...', sentence)
            
            processed_sentences.append(sentence)
        
        # Join sentences with proper spacing
        return ' '.join(processed_sentences).strip()

    def process_text(self, text: str, language_code: str) -> str:
        """Process text based on the language code.

        Args:
            text (str): The text to process.
            language_code (str): The language code (e.g., "en" for English, "ja" for Japanese).
        Returns:
            str: The processed text.
        """
        if not text:
            return text
            
        if language_code == "ja":
            return self.process_japanese_text(text)
        elif language_code == "en":
            return self.process_english_text(text)
        
        # For unsupported languages, just normalize whitespace and handle basic punctuation
        text = ' '.join(text.split())
        return re.sub(r'\.{2,}', '...', text).strip()

if __name__ == '__main__':
    # Example usage
    text_processor = TextProcessor()
    
    # Japanese examples
    japanese_text = "これは[kanji]です。(テスト)123"
    print(f"Original Japanese: {japanese_text}")
    print(f"Processed Japanese: {text_processor.process_text(japanese_text, 'ja')}")
    
    # English examples
    english_text = "This is a test... It's working! The temp is 20C and speed is 60mph."
    print(f"\nOriginal English: {english_text}")
    print(f"Processed English: {text_processor.process_text(english_text, 'en')}")
