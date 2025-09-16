import re, pysubs2, logging
from typing import List, Union

logger = logging.getLogger(__name__)

def extract_first_number(string):
    # Search for the first occurrence of a number in the string
    match = re.search(r'\d+', string)
    if match:
        # Convert the matched string to an integer
        return int(match.group())
    else:
        # Return None or a default value if no number is found
        return None
    

def shift(sub: pysubs2.SSAEvent, ms_shift: int):
    sub.start += ms_shift
    sub.end += ms_shift
    return time_round(sub)


def right_shift(film_sub: pysubs2.SSAEvent, ep_sub: pysubs2.SSAEvent, sub_shift: int) -> bool:
    return abs (((film_sub.start + (film_sub.end - film_sub.start)//2) - (ep_sub.start + (ep_sub.end - ep_sub.start)//2) - sub_shift)) < 120
    # return abs((film_sub.start - ep_sub.start) - sub_shift) < 80 #and abs((film_sub.end - ep_sub.end) - sub_shift) < 150

def time_round(sub: pysubs2.SSAEvent) -> pysubs2.SSAEvent:
    lastD = sub.start % 10
    if lastD > 4:
        sub.start -= lastD
        sub.start += 10
    else:
        sub.start -= lastD
    
    lastD = sub.end % 10
    if lastD > 4:
        sub.end -= lastD
        sub.end += 10
    else:
        sub.end -= lastD

    return sub


def unparse_covered_episodes(episodes: List[int]) -> List[str]:
        result = []
        start = None
        for i, episode in enumerate(episodes):
            if start is None:
                start = episode
            if i + 1 < len(episodes) and episodes[i + 1] == episode + 1:
                continue
            if start == episode:
                result.append(str(episode))
            else:
                result.append(f"{start}-{episode}")
            start = None
        return result


def parse_covered_episodes(episodes: List[Union[str, int]]) -> List[int]:
    result = []
    for item in episodes:
        if isinstance(item, int):
            result.append(item)
        else:
            # Handle string ranges like "1-8"
            if '-' in item:
                start, end = map(int, item.split('-'))
                result.extend(range(start, end + 1))
            else:
                result.append(int(item))
    return result