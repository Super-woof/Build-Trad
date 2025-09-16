import os, json, logging
from rich.prompt import Prompt

from src.interface import Config, FilmInfos
from src.tools.fandom_scrapper import ask_for_fandom_serie, FandomSerie

logger = logging.getLogger(__name__)

def load_config(config_file_path: str) -> Config | None:
    config: Config = None

    try:
        with open(os.path.join(os.path.curdir, config_file_path), 'r', encoding="utf-8") as file:
            json_data = json.load(file)
            config = Config(**json_data)
    except Exception as e:
        logger.error(e)
        logger.error(f"Try replace Single quote ' with double quote \"")
    
    return config
    

def validate_film_path(films_path: str) -> bool:
    if not os.path.exists(films_path):
        logger.rich(f"[red]The path [bold]\"{films_path}\"[/bold] does not exist![/red]", level=logging.WARNING)
        return False

    if not os.path.isdir(films_path):
        logger.rich(f"[red]The path [bold]\"{films_path}\"[/bold] is not a directory![/red]", level=logging.WARNING)
        return False

    if not os.listdir(films_path):
        logger.rich(f"[red]The directory [bold]\"{films_path}\"[/bold] is empty![/red]", level=logging.WARNING)
        return False

    if not any(file.endswith('.ass') for file in os.listdir(films_path)):
        logger.rich(f"[red]No ASS file were found[/red]", level=logging.WARNING)
        return False

    return True

def generate_config(config_file_path: str) -> Config:
    if not config_file_path.endswith(".conf"):
        config_file_path += ".conf"
    
    logger.rich(f"Generating config file: [bold]{config_file_path}[/bold]")
    config = Config()

    config.films_path = Prompt.ask("Enter the path to the films subs folder or 's' to skip", default="films").strip()

    while config.films_path != 's' and not validate_film_path(config.films_path):
        print("Invalid path. Please enter a valid path.")
        config.films_path = Prompt.ask("Enter the path to the films subs folder or 's' to skip", default="films").strip()
    if config.films_path != 's':
        populate_films_to_build(config)

    try:
        base_path = os.path.dirname(config.films_path)
    except:
        pass

    base_path = "." if base_path.strip() == "" else base_path
    
    config.fr_subs_path = Prompt.ask("Enter path of french subtitles", default=f"{base_path}/French", show_default=True).strip()
    config.subs_to_translate_path = Prompt.ask("Enter path of the sub subtitles to translate", default=f"{base_path}/to-translate", show_default=True).strip()
    config.save_path = Prompt.ask("Enter path to save the translated subtitles", default=f"{base_path}/translated", show_default=True).strip()

    logger.rich(f"[green italic]Config file populated![/green italic]\n", level=logging.INFO)
    logger.debug(config.log())

    with open(config_file_path, 'w', encoding="utf-8") as file:
        json.dump(config.model_dump(by_alias=True), file, indent=4, ensure_ascii=False)
   
    return


def update_config(config: Config, fandom_serie: FandomSerie):
    for film in config.films_to_build:
        for fandom_film in fandom_serie.films:
            if film.number == fandom_film.number and isinstance(fandom_film.episodes_range, list):
                film.covered_episodes = fandom_film.episodes_range
                break


def populate_films_to_build(config: Config):
    logger.rich(f"Populating config file with films infos from [bold]{config.films_path}[/bold]")

    films = [film for film in os.listdir(config.films_path) if film.endswith(".ass")]

    for film in films:
        logger.rich(f"[green bold]{film}[/green bold]")
        config.films_to_build.append(FilmInfos.create(film))

    fandom_serie = ask_for_fandom_serie()

    if fandom_serie:
        update_config(config, fandom_serie)

    logger.rich("[orange3]Check if the config file is all correct using the fandom[/]")
    logger.rich("[blue] https://fan-kai.fandom.com/fr/wiki/Guide_des_%C3%A9pisodes [/]")

   