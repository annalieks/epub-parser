import logging

from deep_translator import LingueeTranslator, GoogleTranslator


class WordsTranslator:
    def __init__(self, source_lang, target_lang):
        self.translator = LingueeTranslator(source=source_lang, target=target_lang)
        self.google_translator = GoogleTranslator(source=source_lang, target=target_lang)

    def translate(self, text):
        if any(char.isdigit() for char in text):
            return ''
        try:
            try:
                logging.info(f'Translating {text}')
                return self.translator.translate(word=text, return_all=True)
            except Exception:
                return self.google_translator.translate(text=text)
        except Exception:
            return ''
