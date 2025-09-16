from src.interface.config import *
from src.interface.stats import *

from pydantic import BaseModel, ConfigDict
import pysubs2, os, logging
from src.helpers import extract_first_number


logger = logging.getLogger(__name__)

class Time(BaseModel):
    hours: int
    minutes: int
    seconds: int
    milliseconds: int
    time: int

    def __str__(self):
        return f"{self.hours:02}:{self.minutes:02}:{self.seconds:02}"
    
    @property
    def mmss(self):
        return f"{self.minutes:02}:{self.seconds:02}"

    def __init__(self, ms: int):
        ms_time = ms
        hours = ms // 3600000
        ms %= 3600000
        minutes = ms // 60000
        ms %= 60000
        seconds = ms // 1000
        milliseconds = ms % 1000

        super().__init__(hours=hours, minutes=minutes, seconds=seconds, milliseconds=milliseconds, time=ms_time)

    def __lt__(self, other):
        if isinstance(other, Time):
            return self.time < other.time
        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, Time):
            return self.time > other.time
        return NotImplemented

    def __sub__(self, other):
        """return the difference between two Time objects

        Args:
            other (Time): the Time object to subtract

        Returns:
            int: the difference between the two Time objects
        """
        if isinstance(other, Time):
            difference = self.time - other.time
            return difference
        return NotImplemented

class Timecode(BaseModel):
    start: int
    end: int
    shift: Time
    sub_file_name: str
    episode_number: int

    def __init__(self, start: int, end: int, ms_shift: int, sub_file_name: str):
        shift = Time(ms_shift)
        number = extract_first_number(sub_file_name)
        super().__init__(start=start, end=end, shift=shift, sub_file_name=sub_file_name, episode_number=number)

    def __str__(self):
        return f"{self.start} - {self.end}: {self.sub_file_name} ({self.episode_number})"

    def __repr__(self):
        return str(self)
    
    @property
    def basename(self):
        return os.path.basename(self.sub_file_name)

class SubFile(BaseModel):
    pysub_file: pysubs2.SSAFile
    path: str
    episode_number: int

    def __init__(self, pysub_file: pysubs2.SSAFile, path: str):
        number = extract_first_number(os.path.basename(path))
        super().__init__(pysub_file=pysub_file, path=path, episode_number=number)
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @property
    def basename(self):
        return os.path.basename(self.path)
    

class Cut(BaseModel):
    film_time: Time

    ep_start: Time
    ep_end: Time
    length: Time
    episode_number: int
    file_name: str

    def __init__(self, timecode: Timecode):
        super().__init__(film_time=Time(timecode.start + timecode.shift.time), 
                         ep_start=Time(timecode.start), 
                         ep_end=Time(timecode.end),
                         length=Time(timecode.end - timecode.start),
                         episode_number=timecode.episode_number,
                         file_name=timecode.basename.replace(".ass", ""))

    def __str__(self):
        return f"{self.film_time} - ep {self.episode_number} ({self.ep_start.mmss} - {self.ep_end.mmss})"