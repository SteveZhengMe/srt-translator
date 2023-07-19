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
        text = "Hello, Tom. || In today’s [globalized] world, language barriers are a challenge that businesses and individuals often face."
        
        chat_completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", 
            messages=[
                {"role": "system", "content": f"You are a helpful assistant that translates text from any language to {target_language}."},
                {"role": "user", "content": f"The text is movie dialogue. You should keep the the punctuations in the result except for comma and period. Also, if there is a person or city name, please keep the original language. Ex. Translate 'Hi, John || Good morning. I am (we are) from Berlin.' should translate to '你好，John|| 早上好。我(我们)来自Berlin。'. Translate it: {text}"}
            ],
            temperature=0 
        )
        #print(chat_completion.choices[0].message.content.strip())
        self.assertEquals(chat_completion.choices[0].message.content.strip(), "你好，Tom。|| 在今天的[全球化]世界中，语言障碍是企业和个人经常面临的挑战。")