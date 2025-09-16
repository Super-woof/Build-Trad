from pydantic import BaseModel, Field
import logging
from rich.table import Table
from rich.color import Color
from rich.console import Console
from rich.text import Text
from rich.style import Style

logger = logging.getLogger(__name__)

class Stats(BaseModel):
    film: str = Field(default="")

    found: int = Field(default=0)
    not_found: int = Field(default=0)
    total_to_find: int = Field(default=0)
    subs_not_found: list[str] = Field(default=[])

    @property
    def quality(self) -> float:
        return self.found / self.total_to_find * 100

    def __init__(self, film: str, total_to_find: int) -> None:
        super().__init__(film=film, total_to_find=total_to_find)

    def __str__(self) -> str:
        return f"{self.film} : {self.found}/{self.total_to_find} found"
    
    @staticmethod
    def quality_color(quality: float) -> Color:
        if quality < 90:
            return Color.from_rgb(255, 0, 0)
        
        ratio = (quality - 90) / (100 - 90)
        red = int(255 * (1 - ratio))
        green = int(255 * ratio)
        return Color.from_rgb(red, green, 0)
    
    @staticmethod
    def print_stats(results: list['Stats'], print_all=False) -> None:
        logger.rich("\r\n")
        stats_table = Table(title="Stats of translation", show_lines=True)

        stats_table.add_column("Film number", justify="left", style="cyan", no_wrap=True)
        stats_table.add_column("To Found", justify="center", style="cyan", no_wrap=True)
        stats_table.add_column("Not Found", justify="center", style="cyan", no_wrap=True)
        stats_table.add_column("Quality", justify="left", no_wrap=True)

        results = sorted(results, key=lambda x: int(x.film))

        for stats in results:
            if stats is None:
                continue
            color = Stats.quality_color(stats.quality)
            quality_str = Text(f"{stats.quality:.3f}%") if stats.total_to_find > 0 else Text("Episode sub files not found\nCheck path in config file", style="bold red")
            quality_str.stylize(Style(color=color))
            not_found_str = str(stats.not_found)
            if stats.not_found > 12 or stats.quality < 99:
                to_print = sorted(stats.subs_not_found, key=lambda e: len(e), reverse=True)[0:3] if not print_all else stats.subs_not_found
                not_found_str += f" - use this text to find missing file:\n{"\n".join(to_print)}"
            stats_table.add_row(stats.film, str(stats.total_to_find), not_found_str, quality_str)

        console = Console()
        console.print(stats_table)