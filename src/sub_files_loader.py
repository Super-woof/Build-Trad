import os, logging, pysubs2
from typing import List

from src.interface import SubFile
from src.helpers import extract_first_number

logger = logging.getLogger(__name__)


def is_style_equal(style1: pysubs2.SSAStyle, style2: pysubs2.SSAStyle):
    return style1.fontname == style2.fontname and style1.fontsize == style2.fontsize and style1.primarycolor == style2.primarycolor and style1.secondarycolor == style2.secondarycolor and style1.tertiarycolor == style2.tertiarycolor and style1.outlinecolor == style2.outlinecolor and style1.backcolor == style2.backcolor and style1.bold == style2.bold and style1.italic == style2.italic and style1.underline == style2.underline and style1.strikeout == style2.strikeout and style1.scalex == style2.scalex and style1.scaley == style2.scaley and style1.spacing == style2.spacing and style1.angle == style2.angle and style1.borderstyle == style2.borderstyle and style1.outline == style2.outline and style1.shadow == style2.shadow and style1.alignment == style2.alignment and style1.marginl == style2.marginl and style1.marginr == style2.marginr and style1.marginv == style2.marginv and style1.alphalevel == style2.alphalevel


def is_in_styles(styleName, styleParams: pysubs2.SSAStyle, styles: dict[str, pysubs2.SSAStyle]):
    for style in styles:
        if style == styleName:
            # if styles[style] == styleParams:
            if is_style_equal(styles[style], styleParams):
                # print(styleName + ' ' + str(styles[style]) + ' ' + str(styleParams))
                return (True, True)
            else:
                return (True, False)
        
    return (False, False)


def create_style_list(sub_files: List[SubFile]) -> dict[str, pysubs2.SSAStyle]:
    styles: dict[str, pysubs2.SSAStyle] = {}

    for file in sub_files:
        to_modify: list[list[str]] = []
        
        subs = file.pysub_file
        for style in subs.styles:
            same_name, same_params = is_in_styles(style, subs.styles[style], styles)
            if same_name:
                if not same_params:
                    to_modify.append([style, file.basename[:-4] + '_' + style])
                    styles[file.basename[:-4] + '_' + style] = subs.styles[style]
            else:
                styles[style] = subs.styles[style]

        for names in to_modify:
            subs.rename_style(names[0], names[1])

    return styles
    

def addStyleInAllFiles(styles: dict[str, pysubs2.SSAStyle], sub_files: List[SubFile]):
    for f in sub_files:
        f.pysub_file.styles = styles



def styles_in_sub(sub_files: List[SubFile]):
    styles = create_style_list(sub_files)
    addStyleInAllFiles(styles, sub_files)


def load_sub_files(path: str, covered_episodes: List[int], to_build=False) -> List[SubFile]:
    sub_files: List[SubFile] = []

    for sub_file in os.listdir(path):
        if not sub_file.endswith(".ass"):
            logger.info(f"{sub_file} is not a valid ass file")
            continue

        if not (extract_first_number(sub_file) in covered_episodes):
            continue

        sub_path = os.path.join(path, sub_file)
        try:
            sub = pysubs2.load(sub_path, encoding="utf-8")
            sub_files.append(SubFile(pysub_file=sub, path=sub_path))
            logger.info(f"[green]Subtitle file loaded successfully: {os.path.basename(sub_path)}[/]")
        except Exception as e:
            logger.warning(f"[red]Error loading subtitle file {sub_path}: {e}[/]")

    if to_build:
        styles_in_sub(sub_files)
    return sub_files