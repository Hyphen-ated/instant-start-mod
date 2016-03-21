#-----------------------
# instant-start-mod.py
# by Inschato and Zamiel
#-----------------------

# Configuration
version = 1.2

# Imports
import psutil
import winreg
import shutil, os, configparser
import xml.etree.ElementTree as ET
from tkinter import *
from random import seed, randint, random
from PIL import Image, ImageFont, ImageDraw, ImageTk
from subprocess import call

# Constants
mod_name = 'Instant Start Mod'
items_icons_path = 'otherFiles/collectibles/'
trinket_icons_path = 'otherFiles/trinkets/'
builds = ET.parse('otherFiles/builds.xml').getroot()
PI = ImageTk.PhotoImage
icon_zoom = 1.3
icon_filter = Image.BILINEAR
_raw_image_library = {} # Item images library
items_xml = ET.parse('otherFiles/items.vanilla.xml')
items_info = items_xml.getroot()

# --------------------------------------
# Utility functions
# --------------------------------------

# regkey_value - Used to find the path to Steam
def regkey_value(path, name='', start_key = None):
    if isinstance(path, str):
        path = path.split('\\')
    if start_key is None:
        start_key = getattr(winreg, path[0])
        return regkey_value(path[1:], name, start_key)
    else:
        subkey = path.pop(0)
    with winreg.OpenKey(start_key, subkey) as handle:
        assert handle
        if path:
            return regkey_value(path, name, handle)
        else:
            desc, i = None, 0
            while not desc or desc[0] != name:
                desc = winreg.EnumValue(handle, i)
                i += 1
            return desc[1]

# weighted_choice - http://eli.thegreenplace.net/2010/01/22/weighted-random-generation-in-python
def weighted_choice(weights):
    totals = []
    running_total = 0

    for w in weights:
        running_total += w
        totals.append(running_total)

    rnd = random() * running_total
    for i, total in enumerate(totals):
        if rnd < total:
            return i

# -----------------------------
# "Start Selector" window stuff
# -----------------------------

# get_image - Load the image from the provided path in a format suitable for Tk
def get_image(path):
    from os import sep

    image = _raw_image_library.get(path)
    if image is None:
        canonicalized_path = path.replace('/', sep).replace('\\', sep)
        image = Image.open(canonicalized_path)
        _raw_image_library[path] = image
    return image

# get_item_dict - Return an item dictionary based on the provided item id or name
def get_item_dict(id):
    id = str(id)
    if id.isdigit():
        for child in items_info:
            if child.attrib['id'] == id and child.tag != 'trinket':
                return child.attrib
    else:
        for child in items_info:
            if child.attrib['name'].lower() == id.lower() and child.tag != 'trinket':
                return child.attrib

# get_item_id - Given an item name or id, return its id
def get_item_id(id):
    id = str(id)
    if id.isdigit():
        for child in items_info:
            if child.attrib['id'] == id and child.tag != 'trinket':
                return child.attrib['id']
    else:
        for child in items_info:
            if child.attrib['name'].lower() == id.lower() and child.tag != 'trinket':
                return child.attrib['id']

# get_trinket_id - Given an item name or id, return its id
def get_trinket_id(id):
    id = str(id)
    if id.isdigit():
        for child in items_info:
            if child.attrib['id'] == id and child.tag == 'trinket':
                return child.attrib['id']
    else:
        for child in items_info:
            if child.attrib['name'].lower() == id.lower() and child.tag == 'trinket':
                return child.attrib['id']

# get_item_icon - Given the name or id of an item, return its icon image
def get_item_icon(id):
    dict = get_item_dict(id)
    if dict:
        icon_file = dict['gfx'][:16].lower() + '.png'
        return get_image(items_icons_path + icon_file)
    else:
        return get_image(items_icons_path + 'questionmark.png')

# get_trinket_icon - Given the name or id of a trinket, return its icon image
def get_trinket_icon(id):
    id = str(id)
    if id.isdigit():
        for child in items_info:
            if child.attrib['id'] == id and child.tag == 'trinket':
                return get_image(trinket_icons_path + child.attrib['gfx'])
    else:
        for child in items_info:
            if child.attrib['name'].lower() == id.lower() and child.tag == 'trinket':
                return get_image(trinket_icons_path + child.attrib['gfx'])
    return get_image(trinket_icons_path + 'questionmark.png')

# get_heart_icons - Process the hearts image into the individual heart icons and return them
def get_heart_icons():
    '''
    hearts_list[0] = # Full red
    hearts_list[1] = # Half red
    hearts_list[2] = # Empty heart
    hearts_list[3] = # Left half eternal
    hearts_list[4] = # Right half eternal overlap
    hearts_list[5] = # Full soul
    hearts_list[6] = # Half soul
    hearts_list[7] = # Full black
    hearts_list[8] = # Half black
    '''
    hearts_list = [None] * 9
    hearts = Image.open('otherFiles/ui_hearts.png')

    # 16x16 left upper right lower
    for index in range(0, 9):
        left = (16 * index) % 80
        top = 0 if index < 5 else 16
        bottom = top + 16
        right = left + 16
        hearts_list[index] = hearts.crop((left, top, right, bottom))
        hearts_list[index] = hearts_list[index].resize((int(hearts_list[index].width * icon_zoom), int(hearts_list[index].height * icon_zoom)), icon_filter)
        hearts_list[index] = PI(hearts_list[index])
    return hearts_list

def get_hud_icons():
    '''
    hud_icons[0] = # coins
    hud_icons[1] = # keys
    hud_icons[2] = # hardmode
    hud_icons[3] = # bombs
    hud_icons[4] = # golden key
    hud_icons[5] = # no achievements
    '''
    hud_icons = [None] * 6
    hud_image = Image.open('otherFiles/hudpickups.png')

    for index in range(0, 6):
        left = (16 * index) % 48
        top = 0 if index < 3 else 16
        bottom = top + 16
        right = left + 16
        hud_icons[index] = hud_image.crop((left, top, right, bottom))
        hud_icons[index] = hud_icons[index].resize((int(hud_icons[index].width * icon_zoom), int(hud_icons[index].height * icon_zoom)), icon_filter)
        hud_icons[index] = PI(hud_icons[index])
    return hud_icons

# chooseStartWindow - Display the "Start Selector" window
def chooseStartWindow(root):
    global p_win
    if not p_win:
        def close_window():
            global p_win
            root.bind_all('<MouseWheel>', lambda event: None)
            p_win.destroy()
            p_win = None

        def select_build(event=None, build_widget=None):
            global chosen_start
            widget = event.widget if event else build_widget
            while not hasattr(widget, 'build'):
                if widget == root:
                    return
                widget = widget._nametowidget(widget.winfo_parent())
            build = widget.build
            chosen_start = build.attrib['id']
            close_window()
            install_mod()

        # Callback for the search entry changing; will hide any builds that don't match the search.
        def search_builds(sv):
            search_term = sv.get().lower()
            for widget in build_frames:
                item_name = widget.build.attrib['id']
                try:
                    if not re.search('^' + search_term, item_name):
                        widget.grid_remove()
                    else:
                        widget.grid()
                except:
                    widget.grid()
            canvas.yview_moveto(0)

        # Callback for pressing enter in the search box: launch the topmost visible build.
        def select_search_builds():
            for child in build_frames:
                if child.winfo_manager() != '':
                    select_build(build_widget=child)
                    break

        def make_hearts_and_consumables_canvas(parent, build):
            current_canvas = Canvas(parent, bg=current_bgcolor)
            current = 0
            redhearts = build.attrib.get('redhearts')
            soulhearts = build.attrib.get('soulhearts')
            blackhearts = build.attrib.get('blackhearts')
            heartcontainers = build.attrib.get('heartcontainers')

            def add_hearts(amount, type):
                curr = current
                for i in range(0, amount):
                    widget = Label(current_canvas, bg=current_bgcolor)
                    widget.image = hearts_list[type]
                    widget.configure(image=widget.image)
                    widget.bind('<Button-1>', select_build)
                    widget.grid(column=curr % 6, row=0 if curr < 6 else 1)
                    curr += 1
                return curr

            if redhearts:
                fullreds = int(int(redhearts) / 2)
                current = add_hearts(fullreds, 0)
                if int(redhearts) % 2 == 1:
                    current = add_hearts(1, 1)
            if heartcontainers:
                current = add_hearts(int(heartcontainers) / 2, 2)
            if soulhearts:
                fullsouls = int(int(soulhearts) / 2)
                current = add_hearts(fullsouls, 5)
                if int(soulhearts) % 2 == 1:
                    current = add_hearts(1, 6)
            if blackhearts:
                fullblacks = int(int(blackhearts) / 2)
                current = add_hearts(fullblacks, 7)
                if int(blackhearts) % 2 == 1:
                    add_hearts(1, 8)
            if build.attrib.get('coins') or build.attrib.get('bombs') or build.attrib.get('keys'):
                widget = Label(current_canvas, text='     Consumables:', bg=current_bgcolor)
                widget.bind('<Button-1>', select_build)
                widget.grid(column=current, row=0, rowspan=2, sticky=NSEW)
                current += 1
            if build.attrib.get('coins'):
                widget = Label(current_canvas, bg=current_bgcolor)
                widget.image = hud_list[0]
                widget.configure(image=widget.image)
                widget.bind('<Button-1>', select_build)
                widget.grid(column=current, row=0, rowspan=2)
                current += 1
                widget = Label(current_canvas, text=build.attrib['coins'], bg=current_bgcolor)
                widget.bind('<Button-1>', select_build)
                widget.grid(column=current, row=0, rowspan=2, sticky=NSEW)
                current += 1
            if build.attrib.get('bombs'):
                widget = Label(current_canvas, bg=current_bgcolor)
                widget.image = hud_list[3]
                widget.configure(image=widget.image)
                widget.bind('<Button-1>', select_build)
                widget.grid(column=current, row=0, rowspan=2)
                current += 1
                widget = Label(current_canvas, text=build.attrib['bombs'], bg=current_bgcolor)
                widget.bind('<Button-1>', select_build)
                widget.grid(column=current, row=0, rowspan=2, sticky=NSEW)
                current += 1
            if build.attrib.get('keys'):
                widget = Label(current_canvas, bg=current_bgcolor)
                widget.image = hud_list[1]
                widget.configure(image=widget.image)
                widget.bind('<Button-1>', select_build)
                widget.grid(column=current, row=0, rowspan=2)
                current += 1
                widget = Label(current_canvas, text=build.attrib['keys'], bg=current_bgcolor)
                widget.bind('<Button-1>', select_build)
                widget.grid(column=current, row=0, rowspan=2, sticky=NSEW)
                current += 1
            if build.attrib.get('card'):
                card_info = ET.parse('gameFiles/pocketitems.xml').getroot()
                card_name = None
                for card in card_info:
                    if card.tag in ['card', 'rune'] and card.attrib['id'] == build.attrib['card']:
                        card_name = card.attrib['name']
                        break
                widget = Label(current_canvas, text='     Card: ' + card_name, bg=current_bgcolor)
                widget.bind('<Button-1>', select_build)
                widget.grid(column=current, row=0, rowspan=2, sticky=NSEW)
                current += 1

            return current_canvas

        p_win = Toplevel(root)
        p_win.title('Start Selector')
        p_win.resizable(False, True)
        p_win.protocol('WM_DELETE_WINDOW', close_window)
        p_win.tk.call('wm', 'iconphoto', p_win._w, PI(get_item_icon('More Options')))

        # Initialize the scrolling canvas
        canvas = Canvas(p_win, borderwidth=0)
        scrollbar = Scrollbar(canvas, orient='vertical', command=canvas.yview)
        scrollbar.pack(side='right', fill='y')
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.configure(scrollregion=canvas.bbox('all'), width=200, height=200)
        canvas.pack(side=LEFT, fill=BOTH, expand=TRUE)

        # Scrolling code taken from: http://stackoverflow.com/questions/16188420/python-tkinter-scrollbar-for-frame
        imageBox = LabelFrame(canvas, borderwidth=0)
        interior_id = canvas.create_window(0, 0, window=imageBox, anchor=NW)

        # _configure_interior - Track changes to the canvas and frame width and sync them (while also updating the scrollbar)
        def _configure_interior(event):
            # Update the scrollbars to match the size of the inner frame
            size = (imageBox.winfo_reqwidth(), imageBox.winfo_reqheight())
            canvas.config(scrollregion='0 0 %s %s' % size)
            if imageBox.winfo_reqwidth() != canvas.winfo_width():
                # Update the canvas's width to fit the inner frame
                canvas.config(width=imageBox.winfo_reqwidth())
        imageBox.bind('<Configure>', _configure_interior)

        def _configure_canvas(event):
            if imageBox.winfo_reqwidth() != imageBox.winfo_width():
                # Update the inner frame's width to fill the canvas
                canvas.itemconfigure(interior_id, width=canvas.winfo_width())
        canvas.bind('<Configure>', _configure_canvas)

        # _on_mousewheel - Code taken from: http://stackoverflow.com/questions/17355902/python-tkinter-binding-mousewheel-to-scrollbar
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')

        # Define keyboard bindings
        p_win.bind('<MouseWheel>', _on_mousewheel)
        p_win.bind('<Home>', lambda event: canvas.yview_moveto(0))
        p_win.bind('<End>', lambda event: canvas.yview_moveto(1))
        p_win.bind('<Prior>', lambda event: canvas.yview_scroll(-1, 'pages'))
        p_win.bind('<Next>', lambda event: canvas.yview_scroll(1, 'pages'))

        # Start to build the GUI window
        current_row = 0
        hearts_list = get_heart_icons()
        hud_list = get_hud_icons()
        Label(imageBox, text='Click a build to play it', font='font 32 bold').grid(row=current_row, pady=5)
        current_row += 1

        # Search label and entry box
        search_widget_space = Label(imageBox)
        Label(search_widget_space, text='Search: ').grid(row=0, column=0)
        build_search_string = StringVar()
        build_search_string.trace('w', lambda name, index, mode, sv=build_search_string: search_builds(sv))
        build_search_entry = Entry(search_widget_space, width=12, textvariable=build_search_string)
        build_search_entry.bind('<Escape>', lambda event: event.widget.delete(0, END))
        build_search_entry.bind('<Return>', lambda event: select_search_builds())
        build_search_entry.grid(row=0, column=1)
        search_widget_space.grid(row=current_row)
        p_win.entry = build_search_entry # Keep track of this for later
        current_row += 1

        # Build Frames
        current_bgcolor = '#949494'
        build_frames = [None] * len(builds)
        for index, child in enumerate(builds):
            # Draw dividers in between the different kinds of starts
            if index == 0:
                Message(imageBox, text='', font='font 12').grid(row=current_row) # Spacing
                current_row += 1
                Label(imageBox, text='Treasure Room Starts', font='font 20 bold').grid(row=current_row, pady=5)
                current_row += 1
            elif index == 19:
                Message(imageBox, text='', font='font 12').grid(row=current_row) # Spacing
                current_row += 1
                Label(imageBox, text='Devil Room Starts', font='font 20 bold').grid(row=current_row, pady=5)
                current_row += 1
            elif index == 22:
                Message(imageBox, text='', font='font 12').grid(row=current_row) # Spacing
                current_row += 1
                Label(imageBox, text='Angel Room Starts', font='font 20 bold').grid(row=current_row, pady=5)
                current_row += 1
            elif index == 25:
                Message(imageBox, text='', font='font 12').grid(row=current_row) # Spacing
                current_row += 1
                Label(imageBox, text='Custom Starts', font='font 20 bold').grid(row=current_row, pady=5)
                current_row += 1

            # Background color
            current_bgcolor = '#E0E0E0' if current_bgcolor == '#949494' else '#949494'

            # Draw the build frame here
            build_frame = LabelFrame(imageBox, bg=current_bgcolor)
            build_frame.bind('<Button-1>', select_build)
            build_frame.build = child
            build_frames[index] = build_frame

            # ID
            widget = Label(build_frame, text=child.attrib['id'], font='font 32 bold', bg=current_bgcolor, width=2)
            widget.bind('<Button-1>', select_build)
            widget.grid(row=0, rowspan=3)

            # Items
            widget = Label(build_frame, text='Item: ', bg=current_bgcolor)
            widget.bind('<Button-1>', select_build)
            widget.grid(row=0, column=1, sticky=E)
            items_frame = Canvas(build_frame)
            items = child.attrib.get('items')
            if items:
                items = items.split(' + ')
                luck_up = 0
                for i, item in enumerate(items):
                    if item == 'Lucky Foot':
                        luck_up += 1
                        continue
                    widget = Label(items_frame, bg=current_bgcolor)
                    widget.image = get_item_icon(item)
                    widget.image = PI(widget.image.resize((int(widget.image.width * icon_zoom),int(widget.image.height * icon_zoom)), icon_filter))
                    widget.configure(image=widget.image)
                    widget.bind('<Button-1>', select_build)
                    widget.grid(row=0, column=i)
                if luck_up > 0:
                    widget = Label(items_frame, bg=current_bgcolor)
                    widget.image = get_item_icon('Lucky Foot')
                    widget.image = PI(widget.image.resize((int(widget.image.width * icon_zoom),int(widget.image.height * icon_zoom)), icon_filter))
                    widget.configure(image=widget.image)
                    widget.bind('<Button-1>', select_build)
                    widget.grid(row=0, column = i + 1)
                    widget = Label(build_frame, text = 'x' + str(luck_up), bg=current_bgcolor)
                    widget.grid(row=0, column = i + 2)

            # Trinket (appended to the end of the items)
            trinket = child.attrib.get('trinket')
            if trinket:
                widget = Label(items_frame, bg=current_bgcolor)
                widget.image = get_trinket_icon(trinket)
                widget.image = PI(widget.image.resize((int(widget.image.width * icon_zoom),int(widget.image.height * icon_zoom)), icon_filter))
                widget.configure(image=widget.image)
                widget.bind('<Button-1>', select_build)
                widget.grid(row=0, column=len(items) + 1)
            items_frame.grid(row=0, column=2, sticky=W)

            # Health (currently commented out since all builds will start with default health)
            '''
            widget = Label(build_frame, text='Health: ', bg=current_bgcolor)
            widget.bind('<Button-1>', select_build)
            widget.grid(row=1, column=1, sticky=E)

            hearts_and_consumables_frame = make_hearts_and_consumables_canvas(build_frame, child)
            hearts_and_consumables_frame.bind('<Button-1>', select_build)
            hearts_and_consumables_frame.grid(row=1, column=2, sticky=W)
            '''

            # Removed Items (currently commented out since all builds will not have any removed items)
            '''
            widget = Label(build_frame, text='Removed Items: ', bg=current_bgcolor)
            widget.bind('<Button-1>', select_build)
            widget.grid(row=2, column=1, sticky=E)
            '''
            removed_items = child.attrib.get('removed')
            if removed_items:
                removed_items = removed_items.split(' + ')
                removed_items_frame = Canvas(build_frame, bg=current_bgcolor)
                for i, item in enumerate(removed_items):
                    widget = Label(removed_items_frame, bg=current_bgcolor)
                    widget.image = get_item_icon(item)
                    widget.image = PI(widget.image.resize((int(widget.image.width * icon_zoom),int(widget.image.height * icon_zoom)), icon_filter))
                    widget.configure(image=widget.image)
                    widget.bind('<Button-1>', select_build)
                    widget.grid(row=2, column=i)
                removed_items_frame.grid(row=2, column=2, sticky=W)
            else:
                # Keep the spacing consistent by adding an empty invisible frame of the same height as an item
                Frame(build_frame, width=0,  height=32, bg=current_bgcolor, borderwidth=0).grid(row=2, column=2, sticky=W)
            build_frame.grid(row=current_row, pady=5, padx=3, sticky=W+E)
            current_row += 1

        p_win.update() # Update the window so the widgets give their actual dimensions
        height = max(min(int(p_win.winfo_vrootheight() * 2 / 3), imageBox.winfo_height() + 4), p_win.winfo_height())
        width = imageBox.winfo_width() + scrollbar.winfo_width() + 2
        p_win.geometry('%dx%d' % (width, height))
        p_win.update() # Then update with the newly calculated height
        imageBox.grid_columnconfigure(0, minsize=imageBox.winfo_width()) # Maintain the maximum width

    p_win.entry.focus() # Put the focus on the entry box whenever this window is opened

# --------------------------------------
# Main window and installation functions
# --------------------------------------

# Given two images, return one image with the two connected vertically, centered if necessary
def join_images_vertical(top, bottom):
    # Create a new image big enough to fit both of the old ones
    result = Image.new(top.mode, (max(top.width, bottom.width), top.height+bottom.height))
    middle_paste = int(result.width / 2 - top.width / 2)
    result.paste(top, (middle_paste, 0))
    middle_paste = int(result.width / 2 - bottom.width / 2)
    result.paste(bottom, (middle_paste, top.height))
    return result

# Given two images, return one image with the two connected horizontally, centered if necessary
def join_images_horizontal(left, right):
    result = Image.new(left.mode, (left.width+right.width, max(left.height, right.height)))
    middle_paste = int(result.height / 2 - left.height / 2)
    result.paste(left, (0, middle_paste))
    middle_paste = int(result.height / 2 - right.height / 2)
    result.paste(right, (left.width, middle_paste))
    return result

# Create an image containing the specified text
def create_text_image(text, font):
    img = Image.new('RGBA', (1000,100)) # Dummy image
    w, h = ImageDraw.Draw(img).textsize(text, font=font)
    result = Image.new('RGBA', (w, h)) # Actual image, just large enough to fit the text
    ImageDraw.Draw(result).text((0,0), text, (0,0,0), font=font)
    return result.resize((int(result.width / 2),int(result.height / 2)), Image.ANTIALIAS)

# Draw and return the background image listing starting and removed items for the starting room and attach it to the controls image
def draw_startroom_background(items, removed_items = None, trinket = None, id = 'Undefined'):
    result = None
    font = ImageFont.truetype('otherFiles/olden.ttf', 32)
    if removed_items:
        if len(removed_items) > 1:
            text = 'Removed Items'
        else:
            text = 'Removed Item'
        result = create_text_image(text, font)
        removed_image = None
        for item in removed_items[:10]:
            item_image = get_item_icon(item)
            removed_image = join_images_horizontal(removed_image, item_image) if removed_image else item_image
        result = join_images_vertical(result, removed_image)
        removed_image = None
        for item in removed_items[10:19]:
            item_image = get_item_icon(item)
            removed_image = join_images_horizontal(removed_image, item_image) if removed_image else item_image
        if removed_image:
            if len(removed_items) > 19:
                removed_image = join_images_horizontal(removed_image, create_text_image('+' + str(len(removed_items)-19), font))
            result = join_images_vertical(result, removed_image)
    if items or trinket:
        items_image = None
        if items:
            luck_up = 0
            for item in items:
                if item == '46': # Lucky Foot
                    luck_up += 1
                    continue
                item_image = get_item_icon(item)
                items_image = join_images_horizontal(items_image, item_image) if items_image else item_image
            if luck_up > 0:
                item_image = get_item_icon(46)
                items_image = join_images_horizontal(items_image, item_image) if items_image else item_image
                items_image = join_images_horizontal(items_image, create_text_image('x' + str(luck_up), font))
        if trinket:
            items_image = join_images_horizontal(items_image, get_trinket_icon(trinket)) if items_image else item_image
        result = join_images_vertical(items_image, result) if result else items_image # Add the starting items
        if len(items) > 1:
            text = 'Starting Items'
        else:
            text = 'Starting Item'
        result = join_images_vertical(create_text_image(text, font), result) # Add start label
        result = join_images_vertical(Image.new('RGBA', (5, 15)), result) # Add some space
        #result = join_images_vertical(create_text_image('Build #' + id, font), result) # Add the build ID
    return result

def draw_character_menu(current_build):
    # Open the character menu graphic and write the item/build on it
    color = (54, 47, 45)
    character_menu = Image.open('otherFiles/charactermenu.png')
    character_menu_draw = ImageDraw.Draw(character_menu)
    smallfont = ImageFont.truetype('otherFiles/comicbd.ttf', 10)
    largefont = ImageFont.truetype('otherFiles/comicbd.ttf', 14)
    if chosen_start == '':
        seedtext = 'Random Item'
    elif int(chosen_start) >= 27:
        seedtext = 'Build #' + chosen_start
    else:
        seedtext = current_build.get('items')
    w, h = character_menu_draw.textsize(mod_name + ' v' + str(version), font = smallfont)
    w2, h2 = character_menu_draw.textsize(seedtext, font = largefont)
    character_menu_draw.text((240 - w / 2, 31), mod_name + ' v' + str(version), color, font = smallfont)
    character_menu_draw.text((240 - w2 / 2, 41), seedtext, color , font = largefont)
    character_menu.save(os.path.join(resource_path, 'gfx/ui/main menu/charactermenu.png'))

def install_mod_no_start():
    global chosen_start
    chosen_start = '0'
    install_mod()

def install_mod():
    global items_xml, items_info, chosen_start, seeded_mode

    # Remove everything from the resources directory EXCEPT the "packed" directory and config.ini
    for resource_file in os.listdir(resource_path):
        if resource_file != 'packed' and resource_file != 'config.ini':
            if os.path.isfile(os.path.join(resource_path, resource_file)):
                os.unlink(os.path.join(resource_path, resource_file))
            elif os.path.isdir(os.path.join(resource_path, resource_file)):
                shutil.rmtree(os.path.join(resource_path, resource_file))

    # Copy game files
    for resource_file in os.listdir('gameFiles'):
        current_file = os.path.join('gameFiles', resource_file)
        if os.path.isfile(current_file) and current_file not in ['players.xml', 'items.xml', 'itempools.xml']:
            shutil.copyfile(current_file, os.path.join(resource_path, resource_file))
        elif os.path.isdir(current_file):
            shutil.copytree(current_file, os.path.join(resource_path, resource_file))

    # Copy over the title menu graphic for this mod (different than the Jud6s one)
    if chosen_start != '0':
        shutil.copyfile('otherFiles/titlemenu.png', os.path.join(resource_path, 'gfx/ui/main menu/titlemenu.png'))

    # If this is seeded mode, copy over the special angel rooms
    if seeded_mode.get() == 1:
        shutil.copyfile('otherFiles/seeded/entities2.xml', os.path.join(resource_path, 'entities2.xml')) # This is the custom angel
        shutil.copyfile('otherFiles/seeded/00.special rooms.stb', os.path.join(resource_path, 'rooms/00.special rooms.stb'))

    # The user wants no start
    if chosen_start == '0':
        current_build = ET.Element('build')

    # The user wants a specific build
    elif chosen_start != '':
        current_build = None
        for build in builds:
            if build.attrib['id'] == chosen_start:
                current_build = build
                break

    # The user wants a random start
    else:
        seed()
        build_weights = [float(build.attrib['weight']) for build in builds]
        current_build = builds[weighted_choice(build_weights)]

    # Read the 3 mod files into memory
    players_xml = ET.parse('gameFiles/players.xml')
    players_info = players_xml.getroot()
    itempools_xml = ET.parse('otherFiles/itempools.vanilla.xml')
    itempools_info = itempools_xml.getroot()
    items_xml = ET.parse('otherFiles/items.vanilla.xml')
    items_info = items_xml.getroot()

    # Parse the build info
    items = current_build.get('items')
    trinket = current_build.get('trinket')
    removed_items = current_build.get('removed')
    redhearts = current_build.get('redhearts')
    soulhearts = current_build.get('soulhearts')
    blackhearts = current_build.get('blackhearts')
    heartcontainers = current_build.get('heartcontainers')
    keys = current_build.get('keys')
    coins = current_build.get('coins')
    bombs = current_build.get('bombs')
    card = current_build.get('card')
    blindfolded = current_build.get('blindfolded')

    # Add starting items
    if seeded_mode.get() == 1:
        if items:
            items += ' + The Compass'
        else:
            items = 'The Compass'
    if items or trinket:
        if items:
            items = items.split(' + ')
        for child in players_info:
            # These are the 10 characters that can receive the D6
            characterList = ['Isaac', 'Magdalene', 'Cain', 'Judas', '???', 'Samson', 'Azazel', 'Lazarus', 'The Lost', 'Lilith']

            # Go through the 10 characters
            if child.attrib['name'] in characterList:
                # Set a trinket
                if trinket:
                    child.set('trinket', get_trinket_id(trinket))

                # Set the item(s)
                if items:
                    for i in range(0, len(items)):
                        items[i] = get_item_id(items[i])

                    # Fix the D6 for the Guppy build (1/2)
                    if current_build.get('id') == '27':
                        child.attrib['items'] = '' # Remove the D6 so that we can add it later; the right-most spacebar item will take priority
                        # Note that this will delete the starting items for Cain, Samson, and Lilith, but no-one races those characters anyways

                    # Add the items to the player.xml
                    for item in items:
                        id = get_item_id(item)
                        if child.attrib['items'] != '':
                            child.attrib['items'] += ','
                        child.attrib['items'] += id

                    # Fix the D6 for the Guppy build (2/2)
                    if current_build.get('id') == '27':
                        child.attrib['items'] += ',105' # Add back the D6 so that the player will start with it instead of a Guppy item

                    # Remove soul hearts and black hearts from items in items.xml (normal health ups are okay)
                    for item in items_info:
                        if item.attrib['id'] in items:
                            for key in ['soulhearts', 'blackhearts']:
                                if key in item.attrib:
                                    del item.attrib[key]

                # Set pickups
                if coins:
                    child.set('coins', coins)
                if bombs:
                    child.set('bombs', bombs)
                if keys:
                    child.set('keys', keys)
                if card:
                    child.set('card', card)

                # Set blindfolded
                if blindfolded:
                    child.set('canShoot', 'false')

    # Remove items from the pools
    if seeded_mode.get() == 1:
        if removed_items:
            removed_items += ' + Pandora\'s Box + Teleport! + Undefined'
        else:
            removed_items = 'Pandora\'s Box + Teleport! + Undefined'
    if removed_items:
        removed_items = removed_items.split(' + ')
        for i in range(0, len(removed_items)):
            removed_items[i] = get_item_id(removed_items[i])
        for pool in itempools_info:
            for item in pool.findall('Item'):
                if item.attrib['Id'] in removed_items:
                    pool.remove(item)

    # We use the Black Candle to set the player's health (commented out since we always want the default health)
    '''
    for child in items_info:
        if child.attrib['name'] == 'Black Candle':
            child.set('hearts', redhearts)
            child.set('maxhearts', str(int(redhearts) + (int(redhearts) % 2) + (int(heartcontainers) if heartcontainers else 0)))
            if soulhearts:
                child.set('soulhearts', soulhearts)
            if blackhearts:
                child.set('blackhearts', blackhearts)
    '''

    # Write the changes to the copied over XML files
    players_xml.write(os.path.join(resource_path, 'players.xml'))
    itempools_xml.write(os.path.join(resource_path, 'itempools.xml'))
    items_xml.write(os.path.join(resource_path, 'items.xml'))

    # Draw the start room background and copy it over
    if chosen_start != '0':
        if not os.path.exists(os.path.join(resource_path, 'gfx/backdrop')):
            os.mkdir(os.path.join(resource_path, 'gfx/backdrop/'))
        if os.path.exists(os.path.join(resource_path, 'gfx/backdrop/controls.png')):
            os.unlink(os.path.join(resource_path, 'gfx/backdrop/controls.png'))
        draw_startroom_background(items, removed_items, trinket, current_build.attrib['id']).save(os.path.join(resource_path, 'gfx/backdrop/controls.png'))

    # Draw the character menu background and copy it over
    if chosen_start != '0':
        draw_character_menu(current_build)

    # Copy over info.txt
    if chosen_start != '0':
        with open(os.path.join(resource_path, 'info.txt'), 'w') as f:
            f.write(mod_name + ' ' + str(version))

    # Reset the "chosen_start" variable
    chosen_start = ''

    # If Isaac is running, kill it
    try:
        for p in psutil.process_iter():
            if p.name() == 'isaac-ng.exe':
                call(['taskkill', '/im', 'isaac-ng.exe', '/f'])
    except:
        print('There was an error closing Isaac:', e)

    # Start Isaac
    try:
        if os.path.exists(os.path.join(resource_path, '..', '..', '..', '..', 'steam.exe')):
            call([os.path.join(resource_path, '..', '..', '..', '..', 'steam.exe'), '-applaunch', '250900'])
        elif os.path.exists(os.path.join(resource_path, '..', 'isaac-ng.exe')):
            call(os.path.join(resource_path, '..', 'isaac-ng.exe'))
    except:
        print('Starting Isaac failed:', e)

def uninstall_mod():
    # Remove everything from the resources directory EXCEPT the "packed" directory and config.ini
    for resource_file in os.listdir(resource_path):
        if resource_file != 'packed' and resource_file != 'config.ini':
            if os.path.isfile(os.path.join(resource_path, resource_file)):
                os.unlink(os.path.join(resource_path, resource_file))
            elif os.path.isdir(os.path.join(resource_path, resource_file)):
                shutil.rmtree(os.path.join(resource_path, resource_file))

    # Copy everything from the temporary directory back to the resources directory
    if temp_directory:
        for tmp_file in os.listdir(os.path.join(resource_path, temp_directory)):
            if os.path.isfile(os.path.join(resource_path, temp_directory, tmp_file)):
                shutil.copyfile(os.path.join(resource_path, temp_directory, tmp_file), os.path.join(resource_path, tmp_file))
            elif os.path.isdir(os.path.join(resource_path, temp_directory, tmp_file)):
                shutil.copytree(os.path.join(resource_path, temp_directory, tmp_file), os.path.join(resource_path, tmp_file))

        # Remove the temporary directory we created
        shutil.rmtree(os.path.join(resource_path, temp_directory))

    # Exit the program
    sys.exit()

def set_custom_path():
    # Open file dialog
    isaacpath = filedialog.askopenfilename()

    # Check that the file is isaac-ng.exe and the path is good
    if isaacpath [-12:] == 'isaac-ng.exe' and os.path.exists(isaacpath[0:-12] + 'resources'):
        customs.set('options', 'custom_path', isaacpath [0:-12] + 'resources')
        with open('options.ini', 'wb') as configfile:
            customs.write(configfile)
        feedback.set('Your ' + mod_name + ' path has been correctly set.\nClose this window and restart ' + mod_name + '.')
    else:
        feedback.set('That file appears to be incorrect. Please try again to find "isaac-ng.exe".')
    root.update_idletasks()

if __name__ == '__main__':
    root = Tk()
    feedback = StringVar()
    chosen_start = ''
    no_start = False
    p_win = None # Keep track of whether the practice window is open

    # Import options.ini
    customs = configparser.RawConfigParser()
    customs.read('options.ini')
    if not customs.has_section('options'):
        customs.add_section('options')

    root.tk.call('wm', 'iconphoto', root._w, PI(get_item_icon('More Options'))) # Set the GUI icon
    root.title(mod_name + ' v' + str(version)) # Set the GUI title

    # Check and set the paths for file creation, exit if not found
    currentpath = os.getcwd()
    steam_path = regkey_value(r'HKEY_CURRENT_USER\Software\Valve\Steam', 'SteamPath')

    # First, check the custom path from the options.ini file
    if customs.has_option('options', 'custom_path') and os.path.exists(customs.get('options', 'custom_path')):
        resource_path = customs.get('options', 'custom_path')

    # Second, check the steam path that we found from the registry
    elif os.path.isdir(os.path.join(steam_path, 'steamapps/common/The Binding of Isaac Rebirth/resources')):
        resource_path = os.path.join(steam_path, 'steamapps/common/The Binding of Isaac Rebirth/resources')

    # Third, go through the motions of writing and saving a new path to options.ini
    else:
        feedback.set('')
        Message(root, justify=CENTER, font='font 10', text = mod_name + ' was unable to find your resources directory.\nNavigate to the program isaac-ng.exe in your Steam directories.', width=600).grid(row=0, pady=10)
        Message(root, justify=CENTER, font='font 12', textvariable=feedback, width=600).grid(row=1)
        Button(root, font='font 12', text='Navigate to "isaac-ng.exe".', command=set_custom_path).grid(row=2, pady=10)
        Message(root, justify=LEFT, font='font 10', text='Example:\nC:\Program Files (x86)\Steam\steamapps\common\The Binding of Isaac Rebirth\isaac-ng.exe', width=800).grid(row=3, padx=15, pady=10)
        mainloop()
        sys.exit()

    # Check if you're inside the resources path (giving warning and closing if necessary)
    if os.path.normpath(resource_path).lower() in os.path.normpath(currentpath).lower():
        Message(root, justify = CENTER, font = 'font 12', text = mod_name + ' is in your resources directory.\nMove it elsewhere before running it.', width = 600).grid(row = 0, pady = 10)
        mainloop()
        sys.exit()

    # Create a directory to temporarily hold files until the mod is closed
    install_check = 'None'
    if os.path.isfile(os.path.join(resource_path, 'info.txt')):
        with open(os.path.join(resource_path, 'info.txt'), 'r') as f:
            install_check = f.readline()
    for file in os.listdir(resource_path):
        if file == 'packed':
            pass
        else:
            break
    else:
        install_check = mod_name
    mod_name_length = len(mod_name)
    if install_check[:mod_name_length] != mod_name:
        seed()
        temp_directory = '../resources_tmp' + str(randint(100000, 999999))
        if not os.path.exists(os.path.join(resource_path, temp_directory)):
            os.mkdir(os.path.join(resource_path, temp_directory))

        # Copy everything from the resources directory to a temporary directory EXCEPT for the "packed" directory and config.ini
        for resource_file in os.listdir(resource_path):
            if resource_file != 'packed' and resource_file != 'config.ini':
                try:
                    if os.path.isfile(os.path.join(resource_path, resource_file)):
                        shutil.copyfile(os.path.join(resource_path, resource_file), os.path.join(resource_path, temp_directory, resource_file))
                    elif os.path.isdir(os.path.join(resource_path, resource_file)):
                        shutil.copytree(os.path.join(resource_path, resource_file), os.path.join(resource_path, temp_directory, resource_file))
                except:
                    print('Exception occured when copying the files in the Isaac resources directory to a temporary location: ' + e)
    else:
        temp_directory = None

    # "Choose a Start" button
    choose_start_button = Button(root, text=' Choose a Start (1) ', compound='left', command=lambda:chooseStartWindow(root), font='font 16')
    choose_start_button.icon = PI(get_item_icon('More Options'))
    choose_start_button.configure(image = choose_start_button.icon)
    choose_start_button.grid(row=0, column=0, pady=5)
    root.bind('1', lambda event: choose_start_button.invoke())

    # "Random Start" button
    random_start_button = Button(root, text=' Random Start (2) ', compound='left', command=install_mod, font='font 16')
    random_start_button.icon = PI(get_item_icon('???'))
    random_start_button.configure(image=random_start_button.icon)
    random_start_button.grid(row=1, column=0, pady=5)
    root.bind('2', lambda event: random_start_button.invoke())

    # "No Start" button
    no_start_button = Button(root, text=' No Start (3) ', compound='left', command=install_mod_no_start, font='font 16')
    no_start_button.icon = PI(get_trinket_icon('88')) # NO!
    no_start_button.configure(image=no_start_button.icon)
    no_start_button.grid(row=2, column=0, pady=5)
    root.bind('3', lambda event: no_start_button.invoke())

    # Seeded checkbox
    seeded_mode = IntVar()
    seeded_checkbox = Checkbutton(root, justify=CENTER, text='Seeded Mode (4)', font='font 14', variable=seeded_mode)
    seeded_checkbox.grid(row=3, column=0, pady=5)
    root.bind('4', lambda event: seeded_checkbox.invoke())

    # Spacing
    m = Message(root, text='', font='font 7')
    m.grid(row=4, column=0)

    # Instructions
    m = Message(root, justify=CENTER, text='Isaac will open when you start the mod.', font='font 13', width=400)
    m.grid(row=5, column=0)
    m = Message(root, justify=CENTER, text='Keep this program open while playing.', font='font 13', width=400)
    m.grid(row=6, column=0)
    m = Message(root, justify=CENTER, text='Isaac will return to normal when this program is closed.\n\n', font='font 13', width=400)
    m.grid(row=7, column=0)

    # Uninstall mod files when the window is closed
    root.protocol('WM_DELETE_WINDOW', uninstall_mod)

    # Infinite loop
    mainloop()
