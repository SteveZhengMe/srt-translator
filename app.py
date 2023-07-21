import os

from libraries import DeepLUtil
from libraries import OpenAIUtil
from libraries import SRTTranslator
import typer
import dotenv

def init_conf():
    dotenv.load_dotenv(dotenv.find_dotenv(".srt-env"))
    
    # get all the os environment variables that start with "st__", and save them to a dictionary
    conf = {}
    for key, value in os.environ.items():
        if key.startswith("st__"):
            conf[key[4:].lower()] = value
    return conf

def start(file_or_folder_name: str):
    """
    Parameter: file (.srt) or folder (the application will translate all srt files)
    """
    conf = init_conf()
    
    deepL_handler = DeepLUtil(conf)
    openAI_handler = OpenAIUtil(conf)
    
    #if the input is a folder, translate all the srt files in the folder
    if os.path.isdir(file_or_folder_name):
        for file in os.listdir(file_or_folder_name):
            if file.endswith(".srt"):
                srt_file = os.path.join(file_or_folder_name, file)
                print(f"\r\n\r\nProcessing file: {srt_file}")
                srt_translator = SRTTranslator(srt_file, conf)
                srt_translator.translate([deepL_handler, openAI_handler]).save()
    else:
        srt_translator = SRTTranslator(file_or_folder_name, conf)
        srt_translator.translate([deepL_handler, openAI_handler]).save()

# start the main function
if __name__ == '__main__':
    typer.run(start)