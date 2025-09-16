import unicodedata, re, logging, rich
import fandom
from typing import List, Optional
import fandom.error
from pydantic import BaseModel, Field, model_validator, field_validator
from rich.table import Table
from rich.console import Console

from src.constants import WIKI_PAGES
from src.helpers import unparse_covered_episodes, parse_covered_episodes

logger = logging.getLogger(__name__)
class Film(BaseModel):
    title: str
    number: int
    episodes_range: str | List[int]
    season: Optional[int] = None
    is_invalid: bool = False

    @field_validator('episodes_range')
    def process_episode_range(cls, v: str):
        # Remove substrings within parentheses
        v = re.sub(r'\(.*?\)', '', v)
        v = v.replace(',', '+').replace(' ', '')
        return v


    @model_validator(mode='after')
    def check_if_invalid(self):
        # Example validation: check if any of the required fields are empty
        if not self.title or not self.number or not self.episodes_range:
            self.is_invalid = True
        
        # Add more complex validation logic as needed
        # For example, check if episodes_range has an expected format
        episodes_range = self.episodes_range
        if not re.match(r'^\d+(-\d+)?(\+(\d+(-\d+)?))*$', episodes_range):
            self.is_invalid = True
        else:
            try:
                self.episodes_range = parse_covered_episodes(episodes_range.split('+'))
            except ValueError:
                self.is_invalid = True

        return self
    
    def __str__(self):
        color = "red" if self.is_invalid else "green"
        return f"[{color}]{self.title}[/] - {str(self.number)} ({self.episodes_range})"


class FandomSerie(BaseModel):
    title: str
    films: List[Film] = Field(default_factory=list)

    def add_film(self, title: str, number: str, episodes_range: str, season: Optional[int] = None):
        film = Film(title=title, number=number, episodes_range=episodes_range, season=season)
        self.films.append(film)

    @property
    def invalid_films (self) -> List[Film]:
        return [film for film in self.films if film.is_invalid]
    
    @property
    def get_season (self) -> set[str]:
        return set(film.season for film in self.films)

    def update_episodes_number(self, nep_season: dict[str, int]):
        for film in self.films:
            if isinstance(film.episodes_range, List):
                total_increment = sum(episodes for season, episodes in nep_season.items() if season < (film.season or 0))
                film.episodes_range = [episode_num + total_increment for episode_num in film.episodes_range]

    def __str__(self):
        print("\n")
        table = Table(title=self.title)
        table.add_column("Title", justify="left")
        table.add_column("Number", justify="center")
        table.add_column("Episodes", justify="center")
        table.add_column("Season", justify="center")
        table.add_column("Invalid", justify="center")

        for film in self.films:
            is_invalid_text = "[red]Yes[/]" if film.is_invalid else "[green]No[/]"
            episode_range = ", ".join(unparse_covered_episodes(film.episodes_range)) if isinstance(film.episodes_range, list) else film.episodes_range
            table.add_row(film.title, str(film.number), episode_range, str(film.season or "-"), is_invalid_text)

        console = Console()
        console.print(table)

        return ''


def remove_accents(input_str) -> str:
    # Normalize the string to decompose characters (e.g., é -> e + ´)
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    # Filter out the combining diacritical marks (accents)
    return ''.join([c for c in nfkd_form if not unicodedata.combining(c)])

def parse_fandom_page(Fandom_page: fandom.FandomPage) -> FandomSerie:
    serie = FandomSerie(title=Fandom_page.title)
    
    lines = Fandom_page.content["content"].split('\n')
    current_season = None

    # from header structure get position of episodes related to the film
    idx: int = 1
    is_film: bool = False
    for line in lines:
        if re.match(r"FILMS", line):
            is_film = True
            continue
        if is_film:
            if re.match(r"EPISODES", remove_accents(line)):
                break
            idx += 1

    for line in lines:
        line = line.strip()
        
        # Check for season lines
        season_match = re.match(r"Saison (\d+)", line)
        if season_match:
            current_season = int(season_match.group(1))
            continue
        
        # Check for film lines (e.g., 1 - Film Title)
        film_match = re.match(r"(\d+) - (.+)", line)
        # film_match = re.match(r"(\d+) - (?=.*[A-Za-z]).+", line)
        if film_match and not film_match.group(2).isdigit():
            number = int(film_match.group(1))
            title = film_match.group(2)

            i = 0

            while not all(word.isdigit() for word in re.split(r'[-/+]', lines[lines.index(line)+i])[0:3]):
                i += 1
            
            # if all(word.isdigit() for word in lines[lines.index(line)+1].split(['-', '/', '+'])[0:3]): # If resume after title
            #     episode_range_line = next((l for l in lines[lines.index(line)+idx:] if l.strip()), None)  # Look ahead for the episodes range
            # else:
            # episode_range_line = next((l for l in lines[lines.index(line)+idx+i-1:] if l.strip()), None)
            episode_range_line = lines[lines.index(line)+idx+i-1:][0].strip()
            
            if episode_range_line:
                serie.add_film(title=title, number=number, episodes_range=episode_range_line, season=current_season)
                
    return serie


def get_fandom_page_data(title_page: str) -> FandomSerie | None:
    fandom.set_wiki("fan-kai")
    fandom.set_lang("fr")

    try:
        page = fandom.page(title=title_page)
    except fandom.error.PageError:
        logger.rich(f"Page {title_page} not found", logging.ERROR)
        return None
    except ValueError:
        logger.rich(f"Invalid page title: {title_page}", logging.ERROR)
        return None
    
    # # TODO remove this
    with open("page.txt", "w", encoding="utf-8") as file:
        file.write(page.content["content"])

    return parse_fandom_page(page)


def print_all_invalids():
    for page_name in WIKI_PAGES:
        try:
            serie = get_fandom_page_data(page_name)
        except Exception as e:
            print(page_name)
            continue

        filtered_series = FandomSerie(title=serie.title, films=serie.invalid_films)
        if len(filtered_series.films) > 0:
            print(filtered_series.model_dump_json(indent=4))


def ask_for_fandom_serie() -> FandomSerie | None:
    choice = input("Try populate films infos with fandom data? ([y]/n): ")
    while choice not in ['y', 'n', '']:
        choice = input("Invalid input, Try populate films infos with fandom data? ([y]/n): ")
    if choice == 'n':
        return

    column_range = len(WIKI_PAGES) // 3
    for i in range(0, len(WIKI_PAGES) // 3):
        print(f"{''.join(f'{i + j * column_range + 1:2d} - {WIKI_PAGES[i + j * column_range]:<45}' for j in range(3))}")

    if len(WIKI_PAGES) % 3:
        i = len(WIKI_PAGES) - len(WIKI_PAGES) % 3
        print(''.join(f'{j + 1:2d} - {WIKI_PAGES[j]:<45}' for j in range(i, len(WIKI_PAGES), 1)))

    serie_choice = input("Choose a serie or enter fandom serie page name or 'c' to cancel: ").strip()
    while True:
        if serie_choice.isdigit() and int(serie_choice) > 0 and int(serie_choice) <= len(WIKI_PAGES):
            wiki_page = WIKI_PAGES[int(serie_choice) - 1]
            break
        elif not get_fandom_page_data(serie_choice) is None:
            wiki_page = serie_choice
            break
        elif serie_choice == 'c':
            return
        
        serie_choice = input("Invalid input, choose a serie or enter fandom serie page name: ").strip()

    serie = get_fandom_page_data(wiki_page)

    print(serie)

    if not serie or len(serie.get_season) < 2:
        return serie
    
    update_season = input("Seasons detected, do you want to update numbering of covered episodes to absolute? (y/n): ")
    while update_season not in ['y', 'n']:
        update_season = input("Invalid input, do you want to update numbering of covered episodes to absolute? (y/n): ")

    if update_season == 'n':
        return serie

    nep_season = dict()
    for season in serie.get_season:
        input_season = input(f"Enter number of episodes of season {season}: ")
        while not re.match(r'^\d+$', input_season):
            input_season = input(f"Invalid input, enter number of episodes of season {season}: ")
        nep_season[season] = int(input_season)     
        
    serie.update_episodes_number(nep_season)

    return serie
    

if __name__ == '__main__':
    logger.rich = lambda x, _=None : rich.print(x)
    # ss = get_fandom_page_data("L'attaque des Titans Henshū")
    # ss = get_fandom_page_data("Détective Conan Kaï")
    serie = ask_for_fandom_serie()

    print(serie)
    # attaque = get_fandom_page_data("Fairy Tail Kaï")
    # attaque = get_fandom_page_data("L'attaque des Titans Henshū")