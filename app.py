import os
import time
import functools

from libraries import DeepLUtil
from libraries import OpenAIUtil
from libraries import SRTTranslator
from libraries import NtfyService

import typer
from typing_extensions import Annotated
import dotenv
import shutil
import schedule
import re

typer_app = typer.Typer()

def init_conf():
    # os.environ will convert all key to uppercase, convert them back if you use the lower cased key names
    conf = {
        **dotenv.dotenv_values(".env"),  # load shared development variables
        **{k.lower(): v for k, v in os.environ.items()}  # override loaded values with environment variables
    }
    
    return conf

def create_engine(conf, deepl=True, openai=True):
    engine_array = []
    # get the deepl key from conf
    if deepl:
        for key in conf.get("deepl_key","").split(",,"):
            if key.strip()[-2:] == "fx":
                a_conf = conf.copy()
                a_conf["deepl_key"] = key.strip()
                engine_array.append(DeepLUtil(a_conf))
    
    if openai:
        for key in conf.get("openai_key","").split(",,"):
            if key.strip()[:2] == "sk":
                a_conf = conf.copy()
                a_conf["openai_key"] = key.strip()
                engine_array.append(OpenAIUtil(a_conf))

    return engine_array

@typer_app.command("translate")
def translate(
    file_or_folder_name: Annotated[str, typer.Argument(help="The srt file or folder name to be translated")]="/app/data"
):
    """
    Parameter: file (.srt) or folder (the application will translate all srt files)
    """
    conf = init_conf()
    
    handlers = create_engine(conf)
    
    translated_file_name = []
    #if the input is a folder, translate all the srt files in the folder
    if os.path.isdir(file_or_folder_name):
        for file in os.listdir(file_or_folder_name):
            if file.endswith(".srt"):
                srt_file = os.path.join(file_or_folder_name, file)
                print(f"\r\n\r\nProcessing file: {srt_file}")
                srt_translator = SRTTranslator(srt_file, conf)
                translated_file_name.append(srt_translator.translate(handlers).save())
    else:
        srt_translator = SRTTranslator(file_or_folder_name, conf)
        translated_file_name.append(srt_translator.translate(handlers).save())
    
    return translated_file_name


@typer_app.command("scan")
def scan_folder(
    root_folder:Annotated[str,typer.Argument(help="The root folder that contains the srt files")]="/app/data", 
    export_folder:Annotated[str,typer.Argument(help="The export folder")]="/app/export", 
    target_language:Annotated[str,typer.Argument(help="The application finds the srt files that contain the target_language.")]=os.getenv("target_language_name","Chinese"),
    movie_language:Annotated[str,typer.Argument(help="The application translate the srt files that contain the movie_language.")]=os.getenv("movie_language_name","English"),
    dellete_target_folder:Annotated[str,typer.Argument(help="Delete the target folder if it exists")]="y"
):
    """
    Scan the srt files in the root folder(sub-folder) and copy them to a new folder with the target_language name
    """
    
    # get the current folder of the root_folder
    source_folder = os.path.abspath(root_folder)
    target_folder = os.path.abspath(export_folder)
    # check if the folder with parent_folder/target_language name exists, if true, print error message and exit
    if os.path.exists(os.path.join(target_folder, target_language)) or os.path.exists(os.path.join(target_folder, movie_language)):
        if dellete_target_folder.lower()[0:1] == "y":
            # delete the folder and all the sub folders and files
            shutil.rmtree(os.path.join(target_folder, target_language))
            shutil.rmtree(os.path.join(target_folder, movie_language))
        else:
            print(f"Folder {target_language} or {movie_language} already exists, please delete them first")
            exit()
    
    # create the folder with parent_folder/target_language name
    os.mkdir(os.path.join(target_folder, target_language))
    if movie_language != target_language:
        os.mkdir(os.path.join(target_folder, movie_language))
    
    # walk through the root_folder and sub folders to find the srt files
    processed_result = {
        "match_target_language":0,
        "match_movie_language":0,
        "size_of_srt_with_movie_language":0
    }
    for root, dirs, files in os.walk(source_folder):
        for file in files:
            if file.endswith(".srt"):
                # get the last folder name of the root, it should be the srt file name
                last_folder = os.path.basename(root)
                # if file name contains the target_language and the file is more than 0.5k, copy the file to the target folder and rename it to the root name
                file_size = os.path.getsize(os.path.join(root, file))
                if target_language.lower() in file.lower() and file_size > 512:
                    # if the file exits, ignore it
                    if not os.path.exists(os.path.join(target_folder, target_language, f"{last_folder}.srt")):
                        shutil.copyfile(os.path.join(root, file), os.path.join(target_folder, target_language, f"{last_folder}.srt"))
                elif movie_language.lower() in file.lower() and file_size > 512:
                    if not os.path.exists(os.path.join(target_folder, movie_language, f"{last_folder}.srt")):
                        shutil.copyfile(os.path.join(root, file), os.path.join(target_folder, movie_language, f"{last_folder}.srt"))

    # scan target_language folder, if the movie_language folder has the same file, delete it
    for target_srt in os.listdir(os.path.join(target_folder, target_language)):
        # if target_srt is a file
        if os.path.isfile(os.path.join(target_folder, target_language, target_srt)):
            if os.path.exists(os.path.join(target_folder, movie_language, target_srt)):
                os.remove(os.path.join(target_folder, movie_language, target_srt))
    
    # update the processed_result
    processed_result["match_target_language"] = len(os.listdir(os.path.join(target_folder, target_language)))
    processed_result["match_movie_language"] = len(os.listdir(os.path.join(target_folder, movie_language)))
    processed_result["size_of_srt_with_movie_language"] = sum([os.path.getsize(os.path.join(target_folder, movie_language, file)) for file in os.listdir(os.path.join(target_folder, movie_language))])

    if processed_result["match_target_language"] > 0:
        print(f">> Copied {processed_result['match_target_language']} {target_language} subtitles")
    if processed_result["match_movie_language"] > 0:
        print(f">> Copied {processed_result['match_movie_language']} {movie_language} subtitles, total size: {processed_result['size_of_srt_with_movie_language']/(1024):.0f}KB")
    
    return processed_result

@typer_app.command("interact")
def interact(
    root_folder:Annotated[str,typer.Argument(help="The root folder that contains the srt files")]="/app/data", 
    export_folder:Annotated[str,typer.Argument(help="The export folder")]="/app/export",
    target_language:Annotated[str,typer.Argument(help="The application finds the srt files that contain the target_language.")]=os.getenv("target_language_name","Chinese"),
    movie_language:Annotated[str,typer.Argument(help="The application translate the srt files that contain the movie_language.")]=os.getenv("movie_language_name","English"),
    dellete_target_folder:Annotated[str,typer.Argument(help="Delete the target folder if it exists")]="y"
):
    """
    scan and translate
    """
    # show version
    print("="*20)
    print_version()
    print("="*20)
    if_proceed = typer.prompt(f"I will copy the {target_language} subtitles or copy the {movie_language}(for translating) ones under \"{root_folder}\". Do you want to proceed? (y/n)")
    if if_proceed.lower()[0:1] == "y":
        processed_result = scan_folder(root_folder, export_folder, target_language, movie_language, dellete_target_folder)
        if processed_result["match_target_language"] > 0:
            print(f">> Found {processed_result['match_target_language']} subtitles and copied to {target_language} folder")
        else:
            print(f"No {target_language} subtitle is found")
        
        if processed_result["match_movie_language"] > 0:
            conf = init_conf()
            remain = 0
            total = 0
            # get only DeepLUtill handler
            for deepL_handler in list(filter(lambda x: isinstance(x, DeepLUtil), create_engine(conf))):
                usage = deepL_handler.get_usage()
                #print(usage)
                remain += usage[0]
                total += usage[1]
            if_proceed_translate = typer.prompt(f"I will translate {processed_result['size_of_srt_with_movie_language']/(1024):.0f}kb to {conf.get('target_language','zh_CN')}({target_language}). DeepL left {remain/(1024):.0f}kb out of {total/(1024):.0f}kb. Do you want to proceed? (y/n)")
            if if_proceed_translate.lower()[0:1] == "y":
                translated_file_name_list = translate(os.path.join(os.path.abspath(export_folder), movie_language))
                if len(translated_file_name_list) > 0:
                    print(f'\r\n\r\nPut the following Translated files in "/{movie_language}" folder.')
                    for file_name in translated_file_name_list:
                        # print the file name only. content after the last "/" is the file name
                        print(file_name.split("/")[-1])
        else:
            print(f"No {movie_language} subtitle is found")

@typer_app.command("version")
def print_version():
    """
    Show the currrent version
    """
    version = "Missing"
    # read the version from the file pyproject.toml
    with open(os.path.join(os.path.dirname(__file__), "pyproject.toml"), "r") as f:
        # find the line that start with version
        version = [line for line in f.readlines() if line.startswith("version")][0].split("=")[1].strip().replace("\"", "")
        
    print(f"Version: {version}")
    
@typer_app.command("debug")
def debug_mode():
    """
    Debug mode: the application will sleep 10 minusts and close
    """
    print("Entering sleep mode for 10 minutes...")
    time.sleep(600)  # 600 seconds is equivalent to 10 minutes
    print("Waking up from sleep mode.")

def catch_exceptions(cancel_on_failure=False):
    def catch_exceptions_decorator(job_func):
        @functools.wraps(job_func)
        def wrapper(*args, **kwargs):
            try:
                return job_func(*args, **kwargs)
            except:
                import traceback
                print(traceback.format_exc())
                if cancel_on_failure:
                    return schedule.CancelJob
        return wrapper
    return catch_exceptions_decorator

@catch_exceptions(cancel_on_failure=False)
def walk_and_translate(root_folders):
    conf = init_conf()
    target_language = conf.get('target_language','zh_CN')[:2]
    notify_dict = {}
    for root_folder in root_folders:
        translate_count = 0
        # root: current folder; 
        # dirs: all sub folders in root
        # files: all files in root
        for root, dirs, files in os.walk(root_folder):
            if "translate" in files:  # translate srt files an empty file translate exists.
                for file in files:
                    if file.endswith(".mp4") or file.endswith(".mkv"): # loop all videp files
                        if f"{file[:-4]}.en.srt" in files and not any(re.match(rf"{file[:-4]}\.{target_language}.*\.srt", f) for f in os.listdir(root)): # 如果没有file.zhXXXXXX.srt文件不存在，并且file.en.srt存在
                            # if file name contains the target_language and the file is more than 0.5k, copy the file to the target folder and rename it to the root name
                            en_subtitle_file = os.path.join(root, f"{file[:-4]}.en.srt")
                            translated_subtitle_file = translate(en_subtitle_file)
                            print(f"-> Translated: {translated_subtitle_file}")
                            translate_count += 1
                os.remove(os.path.join(root, "translate"))
        key = os.path.basename(root_folder)
        if key.startswith("Season"):
            key = os.path.basename(os.path.dirname(root_folder))
        notify_dict[key] = translate_count
    
    # send notification if any subtitle is translated
    if any(value > 0 for value in notify_dict.values()):
        # get Deepl usage
        usage_left = sum(deepl_translator.get_usage()[0] for deepl_translator in create_engine(conf, deepl=True, openai=False))
            
        ntfy = NtfyService(conf, tags="robot")
        ntfy.notify(f"{sum(notify_dict.values())} Subtitles are translated", "\n".join([f"{key} => {value};" for key, value in notify_dict.items()]) + f"\n\nDeepL has {(usage_left)/1000:.1f}k left")
    

@typer_app.command("schedule")
def run_schedule(
    debug_base_folder: Annotated[str, typer.Argument(help="debug mode change interval hours to interval seconds")]="",
):
    """
    Walk through all sub-folders, if the folder has an empyt file 'translate', it will translate all En subtitles to Zh
    """
    
    conf = init_conf()
    if debug_base_folder != "":
        schedule.every(10).seconds.do(walk_and_translate, root_folders=debug_base_folder.split(';'))
    else:
        # DAEMON_RUN_AT=17:00:00|America/Toronto
        schedule.every().day.at(conf.get("daemon_run_at").split("|")[0], conf.get("daemon_run_at").split("|")[1]).do(walk_and_translate, root_folders=conf.get("daemon_translator_base_folders","/movie|/tv").split('|'))
    
    while True:
        n = schedule.idle_seconds()
        if n is None:
            print("No schedule available, stop the application.")
            break
        elif n > 0:
            if n > 3600:
                print(f"Found schedule, sleep {round(n/3600)} hours.")
            elif n > 60 and n < 3600:
                print(f"Found schedule, sleep {round(n/60)} minutes.")
            else:
                print(f"Found schedule, sleep {n} seconds.")
            time.sleep(n)
        schedule.run_pending()


# start the main function
if __name__ == '__main__':
    typer_app()