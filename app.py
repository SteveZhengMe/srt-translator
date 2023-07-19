from libraries import DeepLUtil
from libraries import OpenAIUtil
from libraries import SRTUtil
import typer
import dotenv

def start(file_or_folder_name: str):
    """
    Parameter: file (.srt) or folder (the application will translate all srt files)
    """
    dotenv.load_dotenv(dotenv.find_dotenv(".srt-env"))
    

# start the main function
if __name__ == '__main__':
    typer.run(start)