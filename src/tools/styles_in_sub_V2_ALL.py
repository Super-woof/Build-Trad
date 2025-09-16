import os, pysubs2, time, shutil

def is_style_equal(style1: pysubs2.SSAStyle, style2: pysubs2.SSAStyle):
    return style1.fontname == style2.fontname and style1.fontsize == style2.fontsize and style1.primarycolor == style2.primarycolor and style1.secondarycolor == style2.secondarycolor and style1.tertiarycolor == style2.tertiarycolor and style1.outlinecolor == style2.outlinecolor and style1.backcolor == style2.backcolor and style1.bold == style2.bold and style1.italic == style2.italic and style1.underline == style2.underline and style1.strikeout == style2.strikeout and style1.scalex == style2.scalex and style1.scaley == style2.scaley and style1.spacing == style2.spacing and style1.angle == style2.angle and style1.borderstyle == style2.borderstyle and style1.outline == style2.outline and style1.shadow == style2.shadow and style1.alignment == style2.alignment and style1.marginl == style2.marginl and style1.marginr == style2.marginr and style1.marginv == style2.marginv and style1.alphalevel == style2.alphalevel

def is_in_styles(styleName, styleParams: pysubs2.SSAStyle):
    for style in styles:
        if style == styleName:
            # if styles[style] == styleParams:
            if is_style_equal(styles[style], styleParams):
                # print(styleName + ' ' + str(styles[style]) + ' ' + str(styleParams))
                return (True, True)
            else:
                return (True, False)
        
    return (False, False)


def create_style_list(folder: str):
    for file in os.listdir(folder):
        to_modify: list[list[str]] = []
        
        if not file.endswith(".ass"):
            continue

        print("=====" + file + "=====")

        subs = pysubs2.load(os.path.join(folder, file), encoding="utf-8")
        for style in subs.styles:
            same_name, same_params = is_in_styles(style, subs.styles[style])
            # print(str(same_name) + ' ' + str(same_params))
            if same_name:
                if not same_params:
                    to_modify.append([style, file[:-4] + '_' + style])
                    styles[file[:-4] + '_' + style] = subs.styles[style]
            else:
                styles[style] = subs.styles[style]

        # print(to_modify)
        for names in to_modify:
            subs.rename_style(names[0], names[1])

        subs.save(os.path.join(os.path.curdir, folder, 'final', file), encoding="utf-8")

    

def addStyleInAllFiles(folder: str):
    for f in os.listdir(os.path.join(folder, "final")):
        if not f.endswith(".ass"):
            continue

        s = pysubs2.load(os.path.join(folder, 'final', f), encoding='utf-8')
        s.styles = styles

        s.save(os.path.join(os.path.curdir, folder, "final", f), overwrite=True)


if __name__ == "__main__":
    folder = input("enter sub folder path: ")
    
    if not os.path.isdir(folder):
        raise Exception("Not a valid folder")
    
    f = [ file for file in os.listdir(folder) if file.endswith(".ass")]
    if len(f) == 0:
        raise Exception("Not ass in folder")


    print("\n\nfolder: " + folder)
    try:
        os.remove(os.path.join(folder, "final")) 
    except:
        pass
    try:
        os.mkdir(os.path.join(folder, "final")) 
    except:
        pass

    styles: dict[str, pysubs2.SSAStyle] = {}
    create_style_list(folder)
    addStyleInAllFiles(folder)
    time.sleep(1)
    
    input("Done...")
    

