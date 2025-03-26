import re
import mojimoji
import jaconv


class TextProcessor:
    def __init__(self):
        """Initializes the TextProcessor."""
        # Compile regex patterns for efficiency
        self.whitespace_pattern = re.compile(r'\s+')
        self.ascii_pattern = re.compile(r'[a-zA-Z0-9()[\]{}]')

    def process_japanese_text(self, text: str) -> str:
        """Process Japanese text for proper formatting and character width.
        
        Handles:
        - Whitespace normalization (converts to full-width spaces)
        - Full-width ASCII conversion
        - Number conversion to full-width
        - Proper Japanese punctuation
        - Line break normalization
        
        Args:
            text (str): The Japanese text to process.
        Returns:
            str: The processed Japanese text with full-width characters.
        """
        # First normalize all whitespace to single ASCII spaces
        text = self.whitespace_pattern.sub(' ', text)
        
        # Convert numbers and ASCII characters to full-width, excluding spaces
        text = mojimoji.han_to_zen(text, digit=True, ascii=True, kana=False)
        
        # Normalize Japanese characters (half-width kana to full-width)
        text = jaconv.h2z(text, kana=True, ascii=False, digit=False)
        
        # Convert brackets to their proper Japanese forms
        text = text.replace('(', '（').replace(')', '）')
        text = text.replace('[', '［').replace(']', '］')
        text = text.replace('{', '｛').replace('}', '｝')
        
        # Convert ASCII spaces to Japanese full-width spaces (U+3000)
        text = text.replace(' ', '　')
        
        return text.strip()


    def process_text(self, text: str, language_code: str) -> str:
        """Process text based on the language code.

        Args:
            text (str): The text to process.
            language_code (str): The language code (e.g., "en" for English).
        Returns:
            str: The processed text.
        """
        if language_code == "ja":
            return self.process_japanese_text(text)
        
        return self.whitespace_pattern.sub(' ', text).strip()

if __name__ == '__main__':
    # Example usage
    text_processor = TextProcessor()
    japanese_text = "これは[kanji]です。"  # This is [kanji].
    english_text = "This is a test.  "

    processed_japanese_text = text_processor.process_text(japanese_text, "ja")
    processed_english_text = text_processor.process_text(english_text, "en")

    print(f"Processed Japanese text: {processed_japanese_text}")
    print(f"Processed English text: {processed_english_text}")
