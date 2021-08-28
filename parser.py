import asyncio
import logging.handlers
import string

import requests
import tika
import yaml
from nltk.corpus import stopwords
from nltk.tokenize import TweetTokenizer
from tika import parser
from wordfreq import zipf_frequency

from spreadsheet import Spreadsheet
from translation import WordsTranslator


def load_config(path: str):
    with open(path) as config_file:
        return yaml.safe_load(config_file)


def parse(book_path: str):
    logging.info(f'Parsing book: {book_path}')
    text = parser.from_file(book_path)['content']
    stop_words = stopwords.words('english')
    punctuation = [symbol for symbol in string.punctuation]
    exclude_words = set(punctuation + stop_words)
    tokenizer = TweetTokenizer()
    result = set(word.lower() for word in tokenizer.tokenize(text)) - exclude_words
    logging.info(f'Parsing of {book_path} finished')
    return result


async def retrieve_metadata(word: str) -> list:
    result = []
    response = requests.get(f'https://api.dictionaryapi.dev/api/v2/entries/en/{word}')
    if response.status_code != 200:
        logging.warning(f'Could not retrieve metadata for word {word}. Got {response.status_code} response')
        return []
    body = response.json()
    metadata = body[0]
    all_meanings = ''
    for meaning in metadata['meanings']:
        all_meanings = f'{all_meanings}{meaning.get("partOfSpeech")}: '
        for definition in meaning.get('definitions', []):
            all_meanings = f"{all_meanings}\n- {definition.get('definition', '')}. " \
                           f"Example: {definition.get('example', '')}"
        all_meanings = f'{all_meanings}\n'
    result.append(all_meanings)
    result.append('' if len(metadata.get('phonetics', '')) <= 0 else metadata['phonetics'][0].get('text'))
    result.append('' if len(metadata.get('phonetics', '')) <= 0 else f'https:{metadata["phonetics"][0]["audio"]}')
    logging.info(f'Retrieved metadata for {word}: {result}')
    return result


async def retrieve_frequency(word: str):
    return zipf_frequency(word, config['input']['source_language'])


async def retrieve_translation(word: str) -> str:
    result = translator.translate(word)
    logging.info(f'Retrieved translation for {word}: {result}')
    return result if type(result) is str else str(', '.join(result))


async def compose_rows(words: set):
    for word in words:
        result = [word]
        translation = await asyncio.create_task(retrieve_translation(word))
        metadata = await asyncio.create_task(retrieve_metadata(word))
        frequency = await asyncio.create_task(retrieve_frequency(word))
        result.append(translation)
        result.extend(metadata)
        result.append(frequency)
        spreadsheet.append([result])


async def main():
    await compose_rows(words)


""" Note: to use this script, you should install Java first """
if __name__ == '__main__':
    tika.initVM()
    logging.basicConfig(
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        level=logging.INFO,
        handlers=[
            logging.StreamHandler(),
            logging.handlers.RotatingFileHandler('parser.log', maxBytes=1000000, backupCount=5),
        ]
    )
    logging.info('Application started')
    config = load_config('config.yaml')
    sheet_config = config['output']['spreadsheet']
    words = parse(config['input']['book'])
    translator = WordsTranslator(config['input']['source_language'], config['input']['target_language'])
    spreadsheet = Spreadsheet(sheet_config['id'], sheet_config['page'], sheet_config['range'])
    asyncio.run(main())
