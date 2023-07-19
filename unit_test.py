import os
import unittest
import dotenv
import deepl
import openai
class TestStringMethods(unittest.TestCase):
    # setup
    def setUp(self):
        dotenv.load_dotenv(dotenv.find_dotenv(".srt-env"))
    
    def test_load_env(self):
        self.assertNotEquals(os.getenv("DeepL_KEY","NOT FOUND"),"NOT FOUND")
        self.assertEquals(os.getenv("DeepL_KEY")[-2:],"fx")

    def test_deepL_translate(self):
        deepl_translator =  deepl.Translator(os.getenv("DeepL_KEY"))
        result = deepl_translator.translate_text(
            ["Hello, How are you?", "I speak Chinese"], 
            target_lang="ZH"
        )
        self.assertEquals(result[0].text,"你好吗？")
        self.assertEquals(result[1].text,"我会说中文")
        
    def test_openai_translate(self):
        openai.api_key = os.getenv("OpenAI_KEY")
        target_language = "Chinese"
        text = "Hello. || In today’s globalized world, language barriers are a challenge that businesses and individuals often face."
        
        chat_completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", 
            messages=[
                {"role": "system", "content": f"You are a helpful assistant that translates text from any language to {target_language}."},
                {"role": "user", "content": f"The text is movie dialogue. You should keep the '||' in the result. Ex. Translate 'Hi. || Good morning' should translate to '你好。|| 早上好'. Translate it: {text}"}
            ],
            temperature=0 
        )
        #print(chat_completion.choices[0].message.content.strip())
        self.assertEquals(chat_completion.choices[0].message.content.strip(), "你好。|| 在当今全球化的世界中，语言障碍是企业和个人经常面临的挑战。")