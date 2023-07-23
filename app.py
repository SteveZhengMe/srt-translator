import os

from libraries import DeepLUtil
from libraries import OpenAIUtil
from libraries import SRTTranslator
import typer
from typing_extensions import Annotated
import dotenv
import shutil

typer_app = typer.Typer()

def init_conf():
    # if the .env-private file exists, load the environment variables from it, else if the .env-prod file exists, load the environment variables from it
    if os.path.exists(".env-private"):
        dotenv.load_dotenv(dotenv.find_dotenv(".env-private"))
    elif os.path.exists(".env-prod"):
        dotenv.load_dotenv(dotenv.find_dotenv(".env-prod"))
    
    # get all the os environment variables that start with "st__", and save them to a dictionary
    conf = {}
    for key, value in os.environ.items():
        if key.startswith("st__"):
            conf[key[4:].lower()] = value
    return conf

@typer_app.command("translate")
def translate(file_or_folder_name: Annotated[str, typer.Argument(help="The srt file or folder name to be translated")]):
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

@typer_app.command("scan")
def scan_folder(
    root_folder:Annotated[str,typer.Argument(help="The root folder that contains the srt files")], 
    target_language:Annotated[str,typer.Argument(help="The application finds the srt files that contain the target_language.")],
    movie_language:Annotated[str,typer.Argument(help="The application translate the srt files that contain the movie_language.")],
    dellete_target_folder:Annotated[str,typer.Argument(help="Delete the target folder if it exists")]="n"
):
    """
    Scan the srt files in the root folder(sub-folder) and copy them to a new folder with the target_language name
    """
    
    # get the parent folder of the root_folder
    parent_folder = os.path.abspath(os.path.join(root_folder, os.pardir))
    # check if the folder with parent_folder/target_language name exists, if true, print error message and exit
    if os.path.exists(os.path.join(parent_folder, target_language)) or os.path.exists(os.path.join(parent_folder, movie_language)):
        if dellete_target_folder.lower()[0:1] == "y":
            # delete the folder and all the sub folders and files
            shutil.rmtree(os.path.join(parent_folder, target_language))
            shutil.rmtree(os.path.join(parent_folder, movie_language))
        else:
            print(f"Folder {target_language} or {movie_language} already exists, please delete them first")
            exit()
    
    # create the folder with parent_folder/target_language name
    os.mkdir(os.path.join(parent_folder, target_language))
    if movie_language != target_language:
        os.mkdir(os.path.join(parent_folder, movie_language))
    
    # walk through the root_folder and sub folders to find the srt files
    processed_result = {
        "match_target_language":0,
        "match_movie_language":0,
        "size_of_srt_with_movie_language":0
    }
    for root, dirs, files in os.walk(root_folder):
        for file in files:
            if file.endswith(".srt"):
                # get the last folder name of the root, it should be the srt file name
                last_folder = os.path.basename(root)
                # there are multiple versions of a the same language. EX. 1_English.srt and 2_English.srt, we just need the first of them
                is_found = True
                # if file name contains the target_language, copy the file to the target folder and rename it to the root name
                if target_language.lower() in file.lower():
                    processed_result["match_target_language"] += 1
                    shutil.copyfile(os.path.join(root, file), os.path.join(parent_folder, target_language, f"{last_folder}.srt"))
                elif movie_language.lower() in file.lower():
                    processed_result["match_movie_language"] += 1
                    processed_result["size_of_srt_with_movie_language"] += os.path.getsize(os.path.join(root, file))
                    shutil.copyfile(os.path.join(root, file), os.path.join(parent_folder, movie_language, f"{last_folder}.srt"))
                else:
                    is_found = False
                
                # break the inner loop if the file is found
                if is_found:
                    break
    
    if processed_result["match_target_language"] > 0:
        print(f">> Copied {processed_result['match_target_language']} {target_language} subtitles")
    if processed_result["match_movie_language"] > 0:
        print(f">> Copied {processed_result['match_movie_language']} {movie_language} subtitles, total size: {processed_result['size_of_srt_with_movie_language']/(1024):.0f}KB")
    return processed_result

@typer_app.command("interact")
def interact(
    root_folder:Annotated[str,typer.Argument(help="The root folder that contains the srt files")], 
    target_language:Annotated[str,typer.Argument(help="The application finds the srt files that contain the target_language.")],
    movie_language:Annotated[str,typer.Argument(help="The application translate the srt files that contain the movie_language.")],
    dellete_target_folder:Annotated[str,typer.Argument(help="Delete the target folder if it exists")]="n"
):
    """
    scan and translate
    """
    if_proceed = typer.prompt(f"I will copy the {target_language} subtitles or copy the {movie_language}(for translating) ones under \"{root_folder}\". Do you want to proceed? (y/n)")
    if if_proceed.lower()[0:1] == "y":
        processed_result = scan_folder(root_folder, target_language, movie_language, dellete_target_folder)
        if processed_result["match_target_language"] > 0:
            print(f">> Found {processed_result['match_target_language']} subtitles and copied to {target_language} folder")
        
        if processed_result["match_movie_language"] > 0:
            conf = init_conf()
            deepL_handler = DeepLUtil(conf)
            deepl_usage = deepL_handler.get_usage()
            if_proceed_translate = typer.prompt(f"I will translate {processed_result['size_of_srt_with_movie_language']/(1024):.0f}kb to {conf['target_language']}({target_language}). DeepL left {deepl_usage[0]/(1024):.0f} out of {deepl_usage[1]/(1024):.0f}. Do you want to proceed? (y/n)")
            if if_proceed_translate.lower()[0:1] == "y":
                translate(os.path.join(os.path.abspath(os.path.join(root_folder, os.pardir)), movie_language))
        else:
            print(f"No {movie_language} subtitles found")
    pass

# start the main function
if __name__ == '__main__':
    typer_app()