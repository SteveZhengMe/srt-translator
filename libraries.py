import errno
import os
import openai
import deepl
import srt

class TranslatorBase:
    def __init__(self, auth_key, target_lang="zh_CN"):
        self.auth_key = auth_key
        self.target_lang = target_lang
    
    def translate(self, batch):
        # Dummy. Do nothing but return the original
        return batch
    
    def is_available(self):
        # Default to True
        return True


class DeepLUtil(TranslatorBase):
    def __init__(self, auth_key, target_lang="zh_CN"):
        TranslatorBase.__init__(self, auth_key, target_lang)
        self.translator = deepl.Translator(auth_key)
        self.limit = self.translator.get_usage().character.limit - 500
        self.current_count = self.translator.get_usage().character.count
        self.last_count_check = self.current_count
    
    def is_available(self):
        # sync the usage every 10000 characters
        if (self.current_count - self.last_count_check > 10000) or (self.current_count - self.last_count_check > 500 and self.current_count > 490000):
            self.current_count = self.translator.get_usage().character.count
            self.last_count_check = self.current_count
        
        return self.current_count < self.limit
    
    def translate(self, batch):
        # TODO
        pass

class OpenAIUtil(TranslatorBase):
    def __init__(self, auth_key, target_lang="zh_CN"):
        TranslatorBase.__init__(self, auth_key, target_lang)
    
    def translate(self, batch):
        # TODO
        pass

class SRTTranslator:
    def __init__(self, srt_file, target_language="zh_CN"):
        if os.path.isfile(srt_file):
            # add language information to the target file name
            self.target_file = srt_file[:-4] + "_" + target_language + ".srt"
            with open(srt_file) as file:
                self.subtitles = list(srt.parse(file.read()))
        else:
            # raise file not found exception
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), srt_file)
    
    def translate(self, translator_list, buffer_size=1536):
        translated_list = []
        batch = []
        batch_size = 0
        for subtitle in self.subtitles:
            content = self.before_translate(subtitle.content)
            batch.append(content)
            batch_size += len(content)
            if batch_size > buffer_size:
                is_translated = False
                for translator in translator_list:
                    if translator.is_available():
                        translated_list = translator.translate(batch)
                        batch = []
                        batch_size = 0
                        is_translated = True
                    break
                if not is_translated:
                    raise Exception("All translators are not available")
        
        # replace the content with the translated text in the subtitles
        if len(self.subtitles) == len(translated_list):
            for i in range(len(self.subtitles)):
                self.subtitles[i].content = self.after_translate(translated_list[i])
    
    def before_translate(self, text):
        result = text
        # replace the "{\an8}" in the text
        result = result.replace("{\an8}", "")
        result = result.replace("\n","||")
        return result
    
    def after_translate(self, text):
        result = text
        result = result.replace("||","\n")
        return result
    
    def write(self):
        # write to the target file
        with open(self.target_file, "w") as target:
            target.write(srt.compose(self.subtitles))
