import os
from pydantic import BaseModel, model_validator, Field, field_validator, field_serializer, ConfigDict
from typing import List, Union, Optional
from pathlib import Path
from rich.table import Table
from rich.console import Console
from rich.text import Text

from src.constants import *
from src.helpers import extract_first_number, unparse_covered_episodes, parse_covered_episodes

class FilmInfos(BaseModel):
    file_name: str = Field(alias="file-name") # TODO verif on file name
    covered_episodes: List[int] = Field(alias="covered-episodes")
    number: int = Field(alias="number", default=-1)

    model_config = ConfigDict(populate_by_name = True)

    @staticmethod
    def create(film_name: str) -> 'FilmInfos':
        return FilmInfos(file_name=film_name, covered_episodes=[], number=extract_first_number(film_name))


    @field_validator('covered_episodes', mode='before')
    def validate_covered_episodes(cls, v):
        if isinstance(v, list):
            return parse_covered_episodes(v)
        raise ValueError(f"Invalid covered_episodes format: {v}")
    
    
    @field_serializer('covered_episodes')
    def serialize_covered_episodes(self, covered_episodes: List[int], _info) -> List[str]:
        return unparse_covered_episodes(covered_episodes)


class Config(BaseModel):
    films_path: str = Field(alias="films-path", default=FILMS_PATH)
    fr_subs_path: str = Field(alias="fr-subs-path", default="")
    save_path: str = Field(alias="save-path", default="")
    subs_to_translate_path: str = Field(alias="subs-to-translate-path", default="")
    films_to_build: List[FilmInfos] = Field(
        alias="films-to-build", 
        default=[] # FilmInfos(**{"file-name": FILE_NAME, "number": -1, "covered-episodes": COVERED_EPISODES})
    )

    @field_validator('save_path', mode='before')
    def validate_save_path(cls, v, info):
        if not v:
            films_path = info.data.get('films_path', '')
            return films_path
        return v
    
    @field_validator('*', mode='before')
    def ensure_absolute_paths(cls, v, field):
        if 'path' in field.field_name and isinstance(v, str):
            return str(Path(v).resolve())
        return v
    
    @model_validator(mode='after')
    def validate_films_to_build(self):
        if not self.fr_subs_path:
            self.fr_subs_path = os.path.join(os.path.dirname(self.films_path), FR_SUBS_FOLDER)

        if not self.save_path:
            self.save_path = os.path.join(os.path.dirname(self.films_path), SAVE_FOLDER)

        if not self.subs_to_translate_path:
            self.subs_to_translate_path = os.path.join(os.path.dirname(self.films_path), SUBS_TO_TRANSLATE_FOLDER)
        
    def is_to_build(self, film_sub_name) -> bool:
        return any(film.file_name == film_sub_name for film in self.films_to_build)


    def get_film_info(self, film_name: str) -> Optional[FilmInfos]:
        for film in self.films_to_build:
            if film.file_name == film_name:
                return film
        raise ValueError(f"Film {film_name} not found in config")
    

    def field_message(self, field_value, field_name):
        # Validation for films_path
        if field_name == 'films_path':
            if not os.path.exists(field_value):
                return Text(f"The path \"{field_value}\" does not exist!", style="bold red")
            if not os.path.isdir(field_value):
                return Text(f"The path \"{field_value}\" is not a directory!", style="bold red")
            if not os.listdir(field_value):
                return Text(f"The directory \"{field_value}\" is empty!", style="bold red")
            if not any(file.endswith('.ass') for file in os.listdir(field_value)):
                return Text(f"No ASS files were found", style="bold red")
            return Text("Valid", style="bold green")
        
        # Validation for fr_subs_path
        if field_name == 'fr_subs_path':
            if not os.path.exists(field_value):
                return Text(f"The path \"{field_value}\" does not exist!", style="bold red")
            if not os.path.isdir(field_value):
                return Text(f"The path \"{field_value}\" is not a directory!", style="bold red")
            # Check for .ass files directly in the folder
            if not any(file.endswith('.ass') for file in os.listdir(field_value)):
                return Text(f"No ASS files found directly in the folder \"{field_value}\"!", style="bold red")
            return Text("Valid", style="bold green")

        # Validation for save_path
        if field_name == 'save_path':
            if os.path.exists(field_value):
                return Text(f"The path \"{field_value}\" already exists.", style="bold green")
            else:
                return Text(f"The path \"{field_value}\" does not exist, but it will be created.", style="bold yellow")

        # Validation for subs_to_translate_path
        if field_name == 'subs_to_translate_path':
            if not os.path.exists(field_value):
                return Text(f"The path \"{field_value}\" does not exist!", style="bold red")
            if not os.path.isdir(field_value):
                return Text(f"The path \"{field_value}\" is not a directory!", style="bold red")
            # Check subfolders for .ass files
            subfolders = [os.path.join(field_value, f) for f in os.listdir(field_value) if os.path.isdir(os.path.join(field_value, f))]
            if not any(file.endswith('.ass') for subfolder in subfolders for file in os.listdir(subfolder)):
                return Text(f"No ASS files found in the subfolders of \"{field_value}\"!", style="bold red")
            return Text("Valid", style="bold green")

        return Text("Unknown field", style="bold red")


    def log(self):
        table = Table(title="Configuration Information")
        table.add_column("Field", justify="left", style="cyan", no_wrap=True)
        table.add_column("Value", justify="left", style="magenta")
        table.add_column("Message", justify="left", style="green")

        table.add_row("Films Path", self.films_path, self.field_message(self.films_path, 'films_path'))
        table.add_row("French Subs Path", self.fr_subs_path, self.field_message(self.fr_subs_path, 'fr_subs_path'))
        table.add_row("Save Path", self.save_path, self.field_message(self.save_path, 'save_path'))
        table.add_row("Subs to Translate Path", self.subs_to_translate_path, self.field_message(self.subs_to_translate_path, 'subs_to_translate_path'))

        films_info_table = Table(title="Films Information", show_lines=True)
        films_info_table.add_column("File Name", justify="left", style="cyan", no_wrap=True)
        films_info_table.add_column("Number", justify="left", style="cyan", no_wrap=True)
        films_info_table.add_column("Covered Episodes", justify="left", style="magenta")

        for film in self.films_to_build:
            films_info_table.add_row(film.file_name, str(film.number), ", ".join(map(str, film.covered_episodes)))

        console = Console()
        console.print(table)
        console.print(films_info_table)
        return self.model_dump_json(indent=4) # for logging in file
