import os

from libraries import DeepLUtil
from libraries import OpenAIUtil
from libraries import SRTTranslator
import typer
import dotenv

def start(file_or_folder_name: str):
    """
    Parameter: file (.srt) or folder (the application will translate all srt files)
    """
    dotenv.load_dotenv(dotenv.find_dotenv(".srt-env"))
    
    #TODO if a folder is parsed in, create a loop
    srt_file = file_or_folder_name
    target_language = os.getenv("target_language")
    
    srt_parser = SRTTranslator(srt_file, target_language)
    deepL_handler = DeepLUtil(os.getenv("DeepL_KEY"), target_language)
    openAI_handler = OpenAIUtil(os.getenv("OpenAI_KEY"), target_language)

    translated = []
    for buffer in srt_parser.get_by_buffer_size(1):
        if deepL_handler.is_available():
            translated.append(deepL_handler.translate(buffer))
        else:
            translated.append(openAI_handler.translate(buffer))
    
    srt_parser.write(translated)
    
# start the main function
if __name__ == '__main__':
    typer.run(start)