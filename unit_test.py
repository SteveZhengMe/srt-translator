import unittest
import os
import openai
import srt
import tarfile
import requests

from libraries import DeepLUtil
from libraries import OpenAIUtil
from libraries import SRTTranslator
from app import init_conf, create_engine, scan_folder, walk_and_translate

class TestStringMethods(unittest.TestCase):
    # setup
    def setUp(self):
        self.conf = init_conf()
        # find the DeepLUtil in the list
        self.deepl_engine = list(filter(lambda x: isinstance(x, DeepLUtil), create_engine(self.conf)))
        # find the OpenAIUtil in the list
        self.openai_engine = list(filter(lambda x: isinstance(x, OpenAIUtil), create_engine(self.conf)))
    
    def test_load_env(self):
        self.assertNotEquals(len(self.conf), 0)
        self.assertNotEquals(len(self.deepl_engine), 0)
        self.assertNotEquals(len(self.openai_engine), 0)
        self.assertEquals(self.conf["deepl_key"][-2:],"fx")
        self.assertEquals(self.conf["openai_key"][:2],"sk")

    def test_deepL_translate(self):
        for deepl_translator in self.deepl_engine:
            result = deepl_translator.translate_text(
                ["Hello, Tom. <br> In today’s [globalized] world, language barriers are a challenge that businesses and individuals often face.", "I speak Chinese"], 
                target_lang=self.conf["target_language"][0:2]
            )
            self.assertEquals(result[0].text,"你好，汤姆。<br> 在当今[全球化]的世界里，语言障碍是企业和个人经常面临的挑战。")
            self.assertEquals(result[1].text,"我会说中文")
            break
        
    def test_output(self):
        print("\r\n")
        print("+"*20)
        print(self.conf["deepl_key"])
        print("+"*20)
    
    def test_deepl_get_usage(self):
        print()
        for deepl_translator in self.deepl_engine:
            # get usage
            usage = deepl_translator.get_usage()
            print((usage[0] if usage[0]>0 else 0, usage[1]+1000))
            self.assertTrue(usage[1] > 0 and isinstance(usage[0], int))

    
    def test_available(self):
        for translater in self.deepl_engine:
            print(translater.is_available())
            
    def test_openai_translate(self):
        openai.api_key = self.conf["openai_key"]
        target_language = "zh_CN"
        text = "<p>Hello, <br>Tom. </p><p>In today’s [globalized] world, language barriers are a challenge that businesses and individuals often face.</p><p>I speak Chinese</p>"
        
        chat_completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", 
            messages=[
                {"role": "system", "content": f"{self.conf['openai_system_prompt']} {target_language}."},
                {"role": "user", "content": f"{self.conf['openai_user_prompt_default']} {text}"}
            ],
            temperature=0 
        )
        #print(chat_completion.choices[0].message.content.strip())
        self.assertEquals(chat_completion.choices[0].message.content.strip(), "<p>你好，<br>Tom。</p><p>在今天的[全球化]世界中，语言障碍是企业和个人经常面临的挑战。</p><p>我说中文</p>")
        
    def test_parse_srt(self):
        with open("test-data/test.srt") as srt_file:
            subtitles = list(srt.parse(srt_file.read()))
            self.assertEquals(len(subtitles), 177)
            self.assertEqual(subtitles[0].content.replace("\n","||"),"Downloaded from||YTS.MX")
    
    ########################################################################
    def test_SRTTranslator(self):
        srt_parser = SRTTranslator("test-data/test.srt", self.conf)
        self.assertEquals(len(srt_parser.subtitles), 136)
        
    def test_DeepLUtil(self):
        deepl_util = self.openai_engine[0]
        self.assertTrue(deepl_util.is_available())
        self.assertEquals(deepl_util.translate(["Hello, Tom. || language barriers are a [challenge] that businesses and individuals often face.", "I speak Chinese"]),['你好，Tom。|| 语言障碍是企业和个人经常面临的[挑战]。', '我会说中文'])
        
    def test_OpenAIUtil(self):
        openai_util = self.openai_engine[0]
        self.assertTrue(openai_util.is_available())
        self.assertEquals(openai_util.translate(["Hello, Tom.|| In today’s [globalized] world, language barriers are a challenge that businesses and individuals often face.", "I speak Chinese."]),["你好，Tom。|| 在今天的[全球化]世界中，语言障碍是企业和个人经常面临的挑战。","我说中文。"])
        
    def test_integrate(self):
        # delete file: test-data/test.zh.srt
        if os.path.exists("test-data/test.zh.srt"):
            os.remove("test-data/test.zh.srt")
        
        srt_parser = SRTTranslator("test-data/test.en.srt", self.conf)
        engine = []
        engine.extend(self.deepl_engine)
        engine.extend(self.openai_engine)
        
        srt_parser.translate(engine)
        srt_parser.save()
    
        self.assertTrue(os.path.exists("test-data/test.zh.srt"))
        self.assertGreater(os.path.getsize("test-data/test.zh.srt"), 500)
    
    def test_scan(self):
        root_folder = "./test-data/test"
        target_folder = "./test-data/export"
        
        # delete all folders and files
        for root, dirs, files in os.walk(target_folder, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
                
        # start scan
        scan_folder(root_folder, target_folder, "Chinese", "English", "y")
        
        self.assertTrue(os.path.exists("./test-data/export/Chinese"))
        self.assertTrue(os.path.exists("./test-data/export/English"))
        self.assertEqual(len(os.listdir("./test-data/export/Chinese")), 2)
        self.assertEqual(len(os.listdir("./test-data/export/English")), 1)
    
    def test_walk_and_translate(self):
        root_folder = "./test-data/walk_translate"
        
        # prepare testing environment, delete files and extract a new set.
        if not os.path.exists(root_folder):
            os.makedirs(root_folder)
        else:
            for root, dirs, files in os.walk(root_folder, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
        
        tar = tarfile.open("./test-data/walk_translate.tar.gz")
        tar.extractall(path=root_folder, filter='data')
        tar.close()
        
        # run testing
        walk_and_translate([root_folder])
        
        self.assertTrue(os.path.exists(os.path.join(root_folder, "The.Lord.of.the.Rings.S01","Extraordinary - S01E01 - Have Nots WEBRip-1080p.zh.srt")))
        self.assertTrue(os.path.exists(os.path.join(root_folder, "The.Lord.of.the.Rings.S01","Extraordinary - S01E02 - Have Nots WEBRip-1080p.zh.srt")))
        self.assertFalse(os.path.exists(os.path.join(root_folder, "The.Lord.of.the.Rings.S01","Extraordinary - S01E03 - Have Nots WEBRip-1080p.zh.srt")))
        self.assertFalse(os.path.exists(os.path.join(root_folder, "The.Lord.of.the.Rings.S01","translate")))
        
        self.assertTrue(os.path.exists(os.path.join(root_folder, "The.Lord.of.the.Rings.S02","Extraordinary - S01E01 - Have Nots WEBRip-1080p.zh.srt")))
        self.assertTrue(os.path.exists(os.path.join(root_folder, "The.Lord.of.the.Rings.S02","Extraordinary - S01E02 - Have Nots WEBRip-1080p.zh.srt")))
        self.assertFalse(os.path.exists(os.path.join(root_folder, "The.Lord.of.the.Rings.S02","Extraordinary - S01E03 - Have Nots WEBRip-1080p.zh.srt")))
        self.assertFalse(os.path.exists(os.path.join(root_folder, "The.Lord.of.the.Rings.S02","translate")))
        
        self.assertFalse(os.path.exists(os.path.join(root_folder, "The.Lord.of.the.Rings.S03","Extraordinary - S01E01 - Have Nots WEBRip-1080p.zh.srt")))
        self.assertFalse(os.path.exists(os.path.join(root_folder, "The.Lord.of.the.Rings.S03","Extraordinary - S01E02 - Have Nots WEBRip-1080p.zh.srt")))
        self.assertFalse(os.path.exists(os.path.join(root_folder, "The.Lord.of.the.Rings.S03","Extraordinary - S01E03 - Have Nots WEBRip-1080p.zh.srt")))
        self.assertFalse(os.path.exists(os.path.join(root_folder, "The.Lord.of.the.Rings.S03","translate")))

    def test_ntfy_service(self):
        ntfy_server = self.conf.get("ntfy_base_url", "")
        ntfy_topic = self.conf.get("ntfy_topic", "test")
        
        if ntfy_server != "":
            if ntfy_server.endswith("/"):
                ntfy_server = ntfy_server[:-1]
            
            self.assertEquals(
                requests.put(f"{ntfy_server}/{ntfy_topic}",
                    data="""
                        测试 **SRT** NTFY server.
                        
                        - 第二行
                        - 第三行
                    """.encode('utf-8'),
                    # data="Test_1".encode('utf-8'),
                    headers={
                        "Content-Type": "charset=utf-8",
                        "Title": "Testing Message [测试信息]".encode('utf-8'),
                        "Priority": "low",
                        "Markdown": "yes", # markdown only work in the web app
                        "Tags": "warning,skull"
                    }
                ).status_code, 200)