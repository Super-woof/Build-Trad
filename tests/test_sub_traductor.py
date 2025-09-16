import os, tempfile, logging
from pathlib import Path

from tests.helper import load_test_conf

from src.interface import Config, Timecode, Time
from src.sub_traductor import translate_subs_treaded, translate_subs_single_thread, print_cut_timecodes 


def test_config():
    json_data = {
        "films-path": "tests/test-subs/films/",
        "fr-subs-path": "tests/test-subs/fr/",
        "subs-to-translate-path": "tests/test-subs/to-build/",
        "save-path": "tests/test-subs/translated-subs/",
        "films-to-build": [
            {
                "file-name": "[Livaï] Black Clover Kaï 01 - Les Taureaux Noirs - 1080p.MULTI.x264.ass",
                "number": 1,
                "covered-episodes": ["1 - 10", "34", "56", "100-105"]
            },
            {
                "file-name": "[Livaï] Black Clover Kaï 02 - Le Donjon - 1080p.MULTI.x264.ass",
                "number": 2,
                "covered-episodes": ["11-19"]
            },
            {
                "file-name": "[Livaï] Black Clover Kaï 03 - Attaque de la capitale - 1080p.MULTI.x264.ass",
                "number": 3,
                "covered-episodes": ["20-27"]
            },
            {
                "file-name": "[Livaï] Black Clover Kaï 04 - Lumière et Ténèbres - 1080p.MULTI.x264.ass",
                "number": 4,
                "covered-episodes": ["27-39"]
            },
            {
                "file-name": "[Livaï] Black Clover Kaï 05 - Le sanctuaire englouti  - 1080p.MULTI.x264.ass",
                "number": 5,
                "covered-episodes": ["40-50"]
            }
        ]
    }

    config = Config(**json_data)

    assert config.films_path == str(Path("tests/test-subs/films/").resolve())
    assert config.fr_subs_path == str(Path("tests/test-subs/fr/").resolve())
    assert config.subs_to_translate_path == str(Path("tests/test-subs/to-build/").resolve())
    assert config.save_path == str(Path("tests/test-subs/translated-subs/").resolve())
    
    assert len(config.films_to_build) == 5
    assert config.films_to_build[0].file_name == "[Livaï] Black Clover Kaï 01 - Les Taureaux Noirs - 1080p.MULTI.x264.ass"
    assert config.films_to_build[0].number == 1
    assert config.films_to_build[0].covered_episodes == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 34, 56, 100, 101, 102, 103, 104, 105]
    

def test_sub_traductor_single_thread():

    config = load_test_conf()
    config.save_path = tempfile.gettempdir()

    def log_rich(self, message, level=logging.INFO):
        pass
    logging.Logger.rich = log_rich
    
    translate_subs_single_thread(config)

    import pysubs2 

        # {
        #     "file-name": "[Avalokitesvara] Fairy Tail Kai - 16 - Acnologia - 1080p.MULTI.x264.ass",
        #     "covered-episodes": [
        #         "117-121"
        #     ],
        #     "number": 16
        # }

    for film in config.films_to_build:
        result = pysubs2.load(
            os.path.join(config.save_path, f"en_{film.file_name}"), 
            encoding="utf-8") 
        expected = pysubs2.load(f"tests/test-subs/expected/en_{film.file_name}", encoding="utf-8")

        for event, expect_event in zip(result.events, expected.events):
            assert event.plaintext == expect_event.plaintext
        
        assert result.equals(expected) == True
