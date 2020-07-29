from consolemenu.items import *
from consolemenu import *
from consolemenu.format import *
from consolemenu.menu_component import Dimension
import os, time, subprocess, platform, json, threading
from src.botFinalDraft import Bot
from cfonts import render, say



def termUI():
    # grab dir of file
    wd = os.path.dirname(os.path.realpath(__file__))



    # set the formatt of the Term UI
    thin = Dimension(width=79, height=40)
    menu_format = MenuFormatBuilder(max_dimension=thin)
    menu_format.set_prompt(">")
    menu_format.set_title_align('center')                   # Center the menu title (by default it's left-aligned)
    menu_format.set_subtitle_align('center')
    menu_format.set_prologue_text_align('center')           # Center the prologue text (by default it's left-aligned)
    menu_format.show_prologue_bottom_border(True)           # Show a border under the prologue
    menu_format.set_border_style_type(MenuBorderStyleType.DOUBLE_LINE_OUTER_LIGHT_INNER_BORDER)
    menu_format.set_items_top_padding(3)


    # create the menu w/ selection class
    a_list=["Start Bot", "Profiles & Task Config", "Proxies"] # the options available
    mainMenu = SelectionMenu(
        a_list, exit_option_text='Exit :(', formatter=menu_format, title='Off---White', subtitle='Jvnior AIO / MODUS IO'
        )

    mainMenu.show()
    mainMenu.join() # return the recent response from this

    menu = mainMenu.selected_option

    if mainMenu.selected_option == 0:
        # User Started Bot
        mainMenu.screen.clear()
        link = mainMenu.screen.input('Link: ')
        mainMenu.screen.clear()

        config_file = os.path.join(wd,'config.json')
        json_file = open(config_file, 'r', encoding='utf-8')
        info = json.load(json_file)
        json_file.close()
        hook = info['webhook']
        profiles = info['profiles']
        captcha = info['captcha']
        threads = list()

        # run the actual tasks for every profile in profiles
        output = render('Off White', colors=['red'], align='left', font='pallet')
        output2 = render('✨ c/o Jvnior OW ✨', colors=['candy'], align='left', font='console')
        print(output, output2)
        for profile in profiles:
            bot = Bot(url=link, info=profile, hook=hook, captcha=captcha)
            t = threading.Thread(target=bot.tasks, args=())
            t.start()
            threads.append(t)
        for thread in threads:
            thread.join()



    elif mainMenu.selected_option == 1:
        # User Viewing Task Configuration
        mainMenu.screen.clear()
        filepath = os.path.join(wd, 'config.json')
        if platform.system() == 'Darwin':       # macOS
            file = subprocess.call(('open', filepath))
        elif platform.system() == 'Windows':    # Windows
            file = os.startfile(filepath)

    elif mainMenu.selected_option == 2:
        # User Viewing Proxies
        mainMenu.screen.clear()
        filepath = os.path.join(wd, 'proxies.txt')
        if platform.system() == 'Darwin':       # macOS
            file = subprocess.call(('open', filepath))
        elif platform.system() == 'Windows':    # Windows
            file = os.startfile(filepath)

    elif mainMenu.selected_option == 3:
        # User Exited Program
        print("Exited bot")


if __name__ == "__main__":
    termUI()