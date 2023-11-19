import os
import inspect

import wx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure

from PIL import Image, ImagePalette 
import numpy as np

from pyo import *
import time


PL_MIN_FREQ = 20
PL_MAX_FREQ = 20000
PL_DEFAULT_FREQ_GAP = 110

server = Server().boot()
table = HarmTable([1])
osc = Osc(table=table, freq=[440], mul=[1])
osc.muls = []


def play_osc(lvls):
    print(osc.freq)
    print(lvls)

    osc.setMul(list(lvls))
    # table.replace(list(mul))
    # print(osc.mul)
    server.start()
    time.sleep(.2)

    time.sleep(2)
    server.stop()




GLOBAL_DATA = None
GLOBAL_READER = None
GLOBAL_SERVER = None


DEFAULT_DIRECTORY = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
DEFAULT_FILENAME = 'binary.png'


# IDs
ID_CANVAS_IMAGE = 1000
ID_FILE_CTRL = 2000
ID_SLID_WHITE = 3000
ID_SLID_BLACK = 3001
ID_SLID_INDEX = 3002
# for disable when loading process
ID_BTN_REVERSE = 4000
ID_BTN_FLIP_H = 4001
ID_BTN_FLIP_V = 4002
ID_BTN_ROTATE = 4003

ID_TOG_SERVER = 4004
ID_SLID_FOND = 3004
ID_SLID_STEP = 3005

# DEV
DIRECTION_CHOICES = ['left to right', 'right to left', 'up to down', 'down to up']
DIRECTION_DENOM = ['lr', 'rl', 'ud', 'du']

INIT_READ_INDEX = 0
INIT_READ_DIRECTION = 'lr'


###############################################################
# Image Data
class ImageData():

    def __init__(self, path=None) -> None:
    
        if path != None:
            self.init_data_from_path(path)

 
    # # change only this function to init data according to use it
    def init_data_from_path(self, path):
        self.image = Image.open(path)
        self.image = self.image.convert(mode='L')

        print('Data loaded --------------------------')
        # print(f'image info: {self.image.info}')
        # print(f'image size: {self.image.size}')

        self.image = self.constrain_image(self.image, 1000, 1000)

        self.pix_data = np.asarray(self.image, dtype=float)
        self.pix_data = np.flipud(self.pix_data) # lines are fliped for according to the normal image viewer direction (down - up)
        print(f'pix_data shape: {self.pix_data.shape}')


        self.norm = ImageData.normalize(self.pix_data)
        self.lvls = self.norm

        # self.current_lvls = self.get_global_lvls(self.lvls, self.read_index, self.read_direction)


    @classmethod
    def constrain_image(cls, image, max_width, max_height):
        # test redim
        if image.size[1] > max_height:
            # calcul pour le resize
            pix_highers = image.size[1] - max_height
            percent_highers = pix_highers * (1/image.size[1])

            width_highers = image.size[0] * percent_highers
            new_width = image.size[0] - width_highers
            
            image = image.resize((int(new_width), max_height))

        if image.size[0] > max_width:
            pix_highers = image.size[0] - max_width
            percent_highers = pix_highers * (1/image.size[0])

            height_highers = image.size[1] * percent_highers
            new_height = image.size[1] - height_highers
            
            image = image.resize((max_width, int(new_height)))

        print(f'new image size: {image.size}')
        return image

    @classmethod
    def get_data_from_file(cls, path):
        # image = Image.open(path)
        # print(image.__dict__)
        return np.asarray(Image.open(path), dtype=float)

    @classmethod
    def convert_on_gray(cls, data):
        temp_data = data[:, :, 1].copy()

        temp_data = temp_data.reshape(temp_data.shape[0], temp_data.shape[1])
        temp_data[:, :] <- data[:, :, 0] * 0.2126 + data[:, :, 1] * 0.7152 + data[:, :, 2] * 0.0722

        return temp_data

    @classmethod
    def normalize(cls, data):
        temp_data = data[:, :].copy()
        # temp_data = cls.reverse_colors(data)   # for made black = max
        temp_data[...] = temp_data[:, :] * (1 / 255)

        return temp_data


    @classmethod
    def reverse_colors(cls, data):
        temp_data = data[:, :].copy()

        with np.nditer(temp_data, op_flags=['readwrite']) as it:
            for x in it:
                x[...] = 255 - x

        return temp_data

    @classmethod
    def trim_colors(cls, data, min=0, max=255):
        temp_data = data[:, :].copy()
        # print(f'to trim: {temp_data}')

        with np.nditer(temp_data, op_flags=['readwrite']) as it:
            for x in it:
                x[...] = min if x < min else max if x > max else x 

        # print(f'trimed: {temp_data}')

        return temp_data  
    

    @classmethod
    def reverse_lvls(cls, lvls):
        temp_data = lvls[:, :].copy()
        
        with np.nditer(temp_data, op_flags=['readwrite']) as it:
            for x in it:
                x[...] = 1 - x

        return temp_data

    @classmethod
    def trim_lvls(cls, data, min=0.0, max=1.0):
        # print(f'data: {data}')

        # black: 0. toutes values en dessous de min: 0
        # white: 1. toutes values en dessus de max: 1. Plus de blanc 
        temp_data = data[:, :].copy()

        with np.nditer(temp_data, op_flags=['readwrite']) as it:
            for x in it:
                x[...] = 0.0 if (x < min) else 1.0 if (x > max) else x 


        return temp_data  

    @classmethod
    def redim(cls, data, coeff=3):
        """Reduce data with coeff."""

        columns = list(range(0, data.shape[1]))
        columns = columns[0::coeff]

        lines = list(range(0, data.shape[0]))
        lines = lines[0::coeff]

        if len(data.shape) == 3:
            temp_image = data[lines, :, :]
            temp_image = temp_image[:, columns, :]

        else:
            temp_image = data[lines, :]
            temp_image = temp_image[:, columns]

        return temp_image

###############################################################
# File Modal
class FileModal(wx.Dialog):
    """
    Made appear a modal (wx Dialog) containing an input file.
    """

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.SetEscapeId(12345)

        panel = wx.Panel(self, size=(100, 100))
        sizer = wx.BoxSizer(wx.VERTICAL)

        inp_file = wx.FileCtrl(panel, ID_FILE_CTRL, defaultDirectory=DEFAULT_DIRECTORY, defaultFilename=DEFAULT_FILENAME, wildCard="Images Files (*.bmp;*.dib;*.gif;*.jpg;*.png)|*.bmp;*.dib;*.gif;*.jpg;*.png")
        sizer.Add(inp_file)

        sizer_btn = wx.StdDialogButtonSizer()
        btn_valid = wx.Button(panel, wx.ID_OK)
        sizer_btn.AddButton(btn_valid)
        sizer_btn.Realize()
        sizer.Add(sizer_btn)

        panel.SetSizer(sizer)
        self.SetPosition(pt=(550, 200))

###############################################################
# Main Frame
class ImageFrame(wx.Frame):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.process_is_enable = False
        self.enable_process(False)

        self.create_menu()
        self.CreateStatusBar()

        self.panel = wx.Panel(self)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(self.sizer)

        # sizer for image edit controls and canvas image
        sizer_img = wx.BoxSizer()
        self.panel_img_controls = ImageControls(self.panel)
        sizer_img.Add(self.panel_img_controls, -1, wx.LEFT, border=10)

        self.panel_img = ImagePanel(self.panel)
        sizer_img.Add(self.panel_img, -1, wx.LEFT)

        self.sizer.Add(sizer_img, 0, wx.EXPAND)


        # sizer for read control
        sizer_reader = wx.BoxSizer()
        self.panel_reader_controls = ReaderControls(self.panel)
        sizer_reader.Add(self.panel_reader_controls, -1, wx.LEFT, border=10)
        self.sizer.Add(sizer_reader, 0, wx.EXPAND)

        # player controls
        sizer_player = wx.BoxSizer()
        self.panel_player_controls = PlayerControls(self.panel)
        sizer_player.Add(self.panel_player_controls, -1, wx.LEFT, border=10)
        self.sizer.Add(sizer_player, 0, wx.EXPAND)

        self.Show()
        self.enable_process()

    ###############################################################
    # Menu
    def create_menu(self):
        menu_file = wx.Menu()

        item_file = menu_file.Append(wx.ID_FILE, '&Load', 'Load an image file')
        self.Bind(wx.EVT_MENU, self.on_file, item_file)

        menu_file.AppendSeparator()

        item_exit = menu_file.Append(wx.ID_EXIT, '&Exit', "Exit program")
        self.Bind(wx.EVT_MENU, self.on_exit, item_exit)

        menu_bar = wx.MenuBar()
        menu_bar.Append(menu_file, "&File")

        self.SetMenuBar(menu_bar)
    

    def on_file(self, event):
        modal = FileModal(self)

        if modal.ShowModal() == wx.ID_OK:
            input = self.FindWindowById(ID_FILE_CTRL)
            self.load_file(input.GetDirectory(), input.GetFilename())

        modal.Destroy()


    def on_exit(self, event):
        self.Close(True)


    # create these functions for call them outside event context
    def load_file(self, directory, filename):
        global GLOBAL_DATA, GLOBAL_READER, GLOBAL_SERVER
        print(directory + filename)
        GLOBAL_DATA = ImageData(f'{directory}\{filename}')
        GLOBAL_READER = DataReader()    # props init from GLOBAL_DATA.lvls
        GLOBAL_READER.control_panel = self.panel_reader_controls

        GLOBAL_READER.init_frequencies()

        self.update(f'Image loaded: {filename}')


    def update(self, text=''):
        self.panel_reader_controls.update()
        self.panel_player_controls.update_controls()

        self.panel_img.display(GLOBAL_DATA.lvls)

        self.SetStatusText(text)
        self.enable_process()

    def enable_process(self, enable=True):
        if enable == True and self.process_is_enable == False:
            self.SetCursor(wx.Cursor(wx.CURSOR_DEFAULT))

        elif enable == False and self.process_is_enable == True:
            self.SetCursor(wx.Cursor(wx.CURSOR_WAIT))

        self.process_is_enable = enable
        # print(f'process enable set to {enable}')

###############################################################
# Control Panel
class ImageControls(wx.Panel):

    def __init__(self, parent, *args, **kw):
        super().__init__(parent, *args, **kw)
        self.parent = parent
        self.parent_frame = parent.Parent
        # self.SetBackgroundColour('gray')

        sizer = wx.BoxSizer(wx.VERTICAL)

        title = wx.StaticText(self, -1, 'Image Edition')
        font = title.GetFont()
        font.PointSize += 8
        # font = font.Bold()
        title.SetFont(font)
        sizer.Add(title, 0, wx.CENTER)

        # reverse button
        sizer.AddSpacer(20)
        btn_reverse = wx.Button(self, ID_BTN_REVERSE, "Reverse colors")
        sizer.Add(btn_reverse, 0, wx.ALIGN_LEFT)
        self.Bind(wx.EVT_BUTTON, self.on_reverse_colors, btn_reverse)


        # white lim detect
        sizer.AddSpacer(10)
        sizer_w = wx.BoxSizer()
        text_white = wx.StaticText(self, -1, "White detection")
        sizer_w.Add(text_white, 0, wx.ALIGN_LEFT)
        slid_white = wx.Slider(self, ID_SLID_WHITE, 255, 0, 255, style=wx.SL_LABELS)
        #  | wx.SL_INVERSE
        sizer_w.Add(slid_white, 0, wx.CENTER)
        self.Bind(wx.EVT_SLIDER, self.on_trim_lvls, slid_white)

        sizer.Add(sizer_w, 0, wx.ALIGN_LEFT)

        # black lim detect
        sizer.AddSpacer(10)
        sizer_b = wx.BoxSizer()
        text_black = wx.StaticText(self, -1, "Black detection")
        sizer_b.Add(text_black, 0, wx.ALIGN_LEFT)
        slid_black = wx.Slider(self, ID_SLID_BLACK, 0, 0, 255, style=wx.SL_LABELS)
        sizer_b.Add(slid_black, 0, wx.CENTER)
        self.Bind(wx.EVT_SLIDER, self.on_trim_lvls, slid_black)

        sizer.Add(sizer_b, 0, wx.ALIGN_LEFT)


        # flip buttons
        sizer.AddSpacer(10)

        sizer_flip = wx.BoxSizer()
        btn_flip_horizontal = wx.Button(self, ID_BTN_FLIP_H, "Horizontal flip")
        sizer_flip.Add(btn_flip_horizontal, 0, wx.ALIGN_LEFT)
        self.Bind(wx.EVT_BUTTON, self.on_flip_horizontal, btn_flip_horizontal)
        
        sizer_flip.AddSpacer(10)
        btn_flip_vertical = wx.Button(self, ID_BTN_FLIP_V, "Vertical flip")
        sizer_flip.Add(btn_flip_vertical, 0, wx.ALIGN_LEFT)
        self.Bind(wx.EVT_BUTTON, self.on_flip_vertical, btn_flip_vertical)

        sizer.Add(sizer_flip, 0, wx.LEFT)


        # rotate button
        sizer.AddSpacer(10)
        btn_rotate = wx.Button(self, ID_BTN_ROTATE, "Rotate 90°")
        self.Bind(wx.EVT_BUTTON, self.on_rotate, btn_rotate)
        sizer.Add(btn_rotate, 0, wx.ALIGN_LEFT)

        self.SetSizer(sizer)


    def update_global_lvls(self, lvls):
        global GLOBAL_DATA
        GLOBAL_DATA.lvls = lvls
        GLOBAL_READER.init_lvls_from_global()

    def update_global_norm(self, norm_lvls):
        global GLOBAL_DATA
        GLOBAL_DATA.norm = norm_lvls

        min, max = self.get_sliders_values()
        self.update_global_lvls(ImageData.trim_lvls(norm_lvls, min, max))


    def on_reverse_colors(self, event):
        self.parent_frame.enable_process(False)

        temp_data = ImageData.reverse_lvls(GLOBAL_DATA.norm)
        self.update_global_norm(temp_data)

        self.parent_frame.update('Colors are reversed')
        

    def on_flip_horizontal(self, event):
        self.parent_frame.enable_process(False)

        temp_data = np.fliplr(GLOBAL_DATA.norm)
        self.update_global_norm(temp_data)

        self.parent_frame.update('Horizontal flip')


    def on_flip_vertical(self, event):
        self.parent_frame.enable_process(False)

        temp_data = np.flipud(GLOBAL_DATA.norm)
        self.update_global_norm(temp_data)

        self.parent_frame.update('Vertical flip')


    def get_sliders_values(self):
        min = float(self.FindWindowById(ID_SLID_BLACK).Value)
        min = min * (1/255)

        max = float(self.FindWindowById(ID_SLID_WHITE).Value)
        max = max * (1/255)

        return min, max

    def on_trim_lvls(self, event):
        self.parent_frame.enable_process(False)

        min, max = self.get_sliders_values() 

        lvls = ImageData.trim_lvls(GLOBAL_DATA.norm, min, max)
        self.update_global_lvls(lvls)

        self.parent_frame.update('Colors lvls are trimed')


    def on_rotate(self, event):
        self.parent_frame.enable_process(False)

        temp_data = np.rot90(GLOBAL_DATA.norm)
        self.update_global_norm(temp_data)

        self.parent_frame.update('Rotate 90°')

###############################################################
# Image Panel
class ImagePanel(wx.Panel):

    def __init__(self, parent, *args, **kw):
        super().__init__(parent, *args, **kw)
        self.parent = parent
        self.SetBackgroundColour('green')

        sizer = wx.BoxSizer(wx.VERTICAL)

        self.fig = Figure(figsize=(3, 3))
        self.canvas = FigureCanvas(self, ID_CANVAS_IMAGE, self.fig)
        sizer.Add(self.canvas, 0, wx.ALIGN_TOP)

        self.ax = self.fig.subplots()
        self.ax.tick_params(length=1, labelsize=6)

        self.SetSizer(sizer)


    def display(self, data):
        self.ax.clear()

        self.ax.imshow(data, cmap='gray')
        self.ax.invert_yaxis()

        self.plot_current(GLOBAL_READER.index, GLOBAL_READER.direction)

        self.canvas.draw()

        
    def plot_current(self, index, direction):
        index = GLOBAL_READER.get_display_index(index)

        if direction == 'lr' or direction == 'rl':
            self.ax.plot([index, index], [self.ax.get_ylim()[0], self.ax.get_ylim()[1]])

        else:
            self.ax.plot(self.ax.get_xlim(), [index, index])

###############################################################
# Data Reader 
class DataReader():

    def __init__(self):
        self.index = INIT_READ_INDEX
        self.direction = None
        self.lvls = [None]

        self.freq_base = PL_MIN_FREQ
        self.freq_gap = PL_DEFAULT_FREQ_GAP
        self.freqs = [None]

        # init direction and lvls
        self.set_direction(INIT_READ_DIRECTION)


    def set_index(self, value):
        self.index = value
        if self.index < 0:
            self.index = 0
        elif self.index > self.get_max_index():
            self.index = self.get_max_index()

        return self.index
    
    def set_direction(self, direction_denom):
        if self.direction != direction_denom:
            self.direction = direction_denom
            self.init_lvls_from_global()


    def init_lvls_from_global(self):
        lvls = GLOBAL_DATA.lvls.copy()

        if self.direction == 'lr':
            self.lvls = np.flipud(np.rot90(lvls))

        elif self.direction == 'rl':
            self.lvls = np.rot90(lvls)

        elif self.direction == 'ud':
            self.lvls = np.flipud(lvls)

        elif self.direction == 'du':
            self.lvls = lvls

        # osc set muls
        self.init_frequencies() 
        osc.muls = self.lvls


    def init_frequencies(self):
        # update des sliders 
        nbr = self.get_nbr_lvls()
        min = self.freq_base
        step = self.freq_gap
        
        max = min + (nbr * step)

        freqs = np.arange(min, max +1, step)
        self.freqs = freqs

        osc.setFreq(list(freqs))
        print(f'osc init {len(freqs)} freqs with gap of {step}, range from {freqs[0]} Hz, {freqs[1]} Hz, {freqs[2]} Hz... to {freqs[-1]} Hz')


    def set_freq_base(self, freq):
        self.freq_base = freq
        self.init_frequencies()

    def set_freq_gap(self, value):
        self.freq_gap = value
        self.init_frequencies()


    def get_display_index(self, index=None):
        disp_id = index if index != None else self.index

        if self.direction == 'ud' or self.direction == 'rl':
            disp_id = self.get_max_index() - disp_id

        if disp_id > self.get_max_index():
            disp_id = self.get_max_index()

        return disp_id

    def get_max_index(self):
        return len(self.lvls) -1

    def get_nbr_lvls(self):
        return len(self.lvls[0]) -1 

###############################################################
# Reader Controls 
class ReaderControls(wx.Panel):
    def __init__(self, parent, *args, **kw):
        super().__init__(parent, *args, **kw)
        self.parent = parent
        self.parent_frame = parent.Parent
        # self.SetBackgroundColour('gray')

        sizer = wx.BoxSizer(wx.VERTICAL)

        title = wx.StaticText(self, -1, 'Reader')
        font = title.GetFont()
        font.PointSize += 8
        title.SetFont(font)
        sizer.Add(title, 0, wx.CENTER)
        sizer.AddSpacer(20)

        # set direction
        sizer_dir = wx.BoxSizer()
        text_dir = wx.StaticText(self, -1, 'Reading direction: ')
        sizer_dir.Add(text_dir, 0, wx.LEFT)

        inp_direction = wx.Choice(self, -1, choices=DIRECTION_CHOICES)
        inp_direction.SetStringSelection('left to right')
        sizer_dir.Add(inp_direction, 0, wx.LEFT)
        self.Bind(wx.EVT_CHOICE, self.on_direction, inp_direction)

        sizer.Add(sizer_dir)
        sizer.AddSpacer(10)

        # set index
        sizer_index = wx.BoxSizer()

        btn_index_down = wx.Button(self, -1, '<', style=wx.BU_EXACTFIT)
        sizer_index.Add(btn_index_down, 0, wx.ALIGN_BOTTOM)
        self.Bind(wx.EVT_BUTTON, self.on_index_down, btn_index_down)
        sizer_index.AddSpacer(10)

        inp_index = wx.Slider(self, ID_SLID_INDEX, 0, 0, 100, style=wx.SL_LABELS)
        sizer_index.Add(inp_index)
        self.Bind(wx.EVT_SLIDER, self.on_index, inp_index)
        sizer_index.AddSpacer(10)

        btn_index_up = wx.Button(self, -1, '>', style=wx.BU_EXACTFIT)
        sizer_index.Add(btn_index_up, 0, wx.ALIGN_BOTTOM)
        self.Bind(wx.EVT_BUTTON, self.on_index_up, btn_index_up)

        sizer.Add(sizer_index)
        sizer.AddSpacer(10)
        
        self.SetSizer(sizer)

            
    def update(self):
        max = GLOBAL_READER.get_max_index()

        inp = self.FindWindowById(ID_SLID_INDEX)
        inp.SetMax(max)
        inp.SetValue(GLOBAL_READER.index)
        
        if inp.Value > max:
            inp.SetValue(max)


    def on_direction(self, event):
        denom = DIRECTION_DENOM[event.GetInt()]
        GLOBAL_READER.set_direction(denom)

        self.parent_frame.update(f'Set reading direction: {event.GetString()}')


    def set_reader_index(self, index):
        GLOBAL_READER.set_index(index)

        self.parent_frame.update(f'Go to index {GLOBAL_READER.index}')

    def on_index(self, event):
        self.set_reader_index(event.GetInt())
        # play_osc(GLOBAL_READER.get_display_index())
        # only if play_state != play
        # play_osc(GLOBAL_READER.lvls[GLOBAL_READER.index])

    def on_index_down(self, event):
        index = GLOBAL_READER.index -1

        if index >= 0:
            self.set_reader_index(index)
            # play_osc(GLOBAL_READER.get_display_index())
            # play_osc(GLOBAL_READER.lvls[GLOBAL_READER.index])


    def on_index_up(self, event):
        index = GLOBAL_READER.index + 1

        if index <= GLOBAL_READER.get_max_index():
            self.set_reader_index(index)
            # play_osc(GLOBAL_READER.get_display_index())
            # play_osc(GLOBAL_READER.lvls[GLOBAL_READER.index])

# ###############################################################
# Player Controls 
class PlayerControls(wx.Panel):
    def __init__(self, parent, *args, **kw):
        super().__init__(parent, *args, **kw)
        self.parent = parent
        self.parent_frame = parent.Parent
        self.SetBackgroundColour('gray')

        sizer = wx.BoxSizer(wx.VERTICAL)

        # play stop server
        sizer_server = wx.BoxSizer()
        btn_stop = wx.Button(self, -1, 'stop')
        sizer_server.Add(btn_stop, 0, wx.LEFT)
        self.Bind(wx.EVT_BUTTON, self.on_stop, btn_stop)

        tog_play = wx.ToggleButton(self, ID_TOG_SERVER, 'play')
        sizer_server.Add(tog_play, 0, wx.LEFT)
        self.Bind(wx.EVT_TOGGLEBUTTON, self.on_play_toggle, tog_play)
        sizer.Add(sizer_server)

        # player config
        sizer_player = wx.BoxSizer()
        text_fond = wx.StaticText(self, -1, 'Fondamental Freq (Hz)')
        sizer_player.Add(text_fond, 0, wx.LEFT)
        sizer_player.AddSpacer(10)

        btn_fond_down = wx.Button(self, -1, '<', size=(20, 20))
        sizer_player.Add(btn_fond_down, 0, wx.ALIGN_CENTER_VERTICAL)
        self.Bind(wx.EVT_BUTTON, self.on_fond_buttons, btn_fond_down)

        inp_fond = wx.Slider(self, ID_SLID_FOND, PL_MIN_FREQ, PL_MIN_FREQ, PL_MAX_FREQ, style=wx.SL_LABELS)
        sizer_player.Add(inp_fond, 0, wx.LEFT)
        self.Bind(wx.EVT_SLIDER, self.on_fond_slid, inp_fond)

        btn_fond_up = wx.Button(self, -1, '>', size=(20, 20))
        sizer_player.Add(btn_fond_up, 0, wx.ALIGN_CENTER_VERTICAL)
        self.Bind(wx.EVT_BUTTON, self.on_fond_buttons, btn_fond_up)
        
        text_step = wx.StaticText(self, -1, 'Frequency gap')
        sizer_player.Add(text_step, 0, wx.LEFT)
        sizer_player.AddSpacer(10)

        btn_step_down = wx.Button(self, -1, '<', size=(20, 20))
        sizer_player.Add(btn_step_down, 0, wx.ALIGN_CENTER_VERTICAL)
        self.Bind(wx.EVT_BUTTON, self.on_step_buttons, btn_step_down)

        inp_freq_gap = wx.Slider(self, ID_SLID_STEP, PL_DEFAULT_FREQ_GAP, 1, PL_MAX_FREQ, style=wx.SL_LABELS)
        sizer_player.Add(inp_freq_gap, 0, wx.LEFT)
        self.Bind(wx.EVT_SLIDER, self.on_step_slid, inp_freq_gap)

        btn_step_up = wx.Button(self, -1, '>', size=(20, 20))
        sizer_player.Add(btn_step_up, 0, wx.ALIGN_CENTER_VERTICAL)
        self.Bind(wx.EVT_BUTTON, self.on_step_buttons, btn_step_up)

        sizer.Add(sizer_player)


        self.play_toggle = tog_play
        self.play_state = 'pause'
        self.inp_freq_base = inp_fond
        self.inp_freq_gap = inp_freq_gap

        self.SetSizer(sizer)


    def update_controls(self):
        max_fond = PL_MAX_FREQ - GLOBAL_READER.get_nbr_lvls()
        self.inp_freq_base.SetMax(max_fond)

        if self.inp_freq_base.Value > max_fond:
            self.inp_freq_base.SetValue(max_fond)

        max_step = self.get_max_step_value(self.inp_freq_base.Value, GLOBAL_READER.get_nbr_lvls())
        self.inp_freq_gap.SetMax(max_step)

        if self.inp_freq_gap.Value > max_step:
            self.inp_freq_gap.SetValue(max_step)
            GLOBAL_READER.set_freq_base(max_step)


    def on_fond_buttons(self, event):
        if event.GetEventObject().GetLabel() == '<':
            self.inp_freq_base.Value -= 1
        else:
            self.inp_freq_base.Value += 1

        GLOBAL_READER.set_freq_base(self.inp_freq_base.Value)

    def on_step_buttons(self, event):
        if event.GetEventObject().GetLabel() == '<':
            self.inp_freq_gap.Value -= 1
        else:
            self.inp_freq_gap.Value += 1

        GLOBAL_READER.set_freq_gap(self.inp_freq_gap.Value)


    def get_max_step_value(self, min, nbr):
        step = 1
        max = min + (nbr * step)

        while max < PL_MAX_FREQ:
            step += 1
            max = min + (nbr * step)

        return step

    def on_fond_slid(self, event):
        print(event.GetInt())
        GLOBAL_READER.set_freq_base(event.GetInt())

    def on_step_slid(self, event):
        print(event.GetInt())
        GLOBAL_READER.set_freq_gap(event.GetInt())


    def on_stop(self, event):
        self.stop()

    def on_play_toggle(self, event):
        value = event.GetInt()

        if value == 0: 
            self.pause()

        elif value == 1:
            self.play()


    def play(self):
        self.play_state = 'play'
        self.play_toggle.SetLabel('pause')

        # server.start()
        self.read()
        print('play') 

    def pause(self):
        self.play_state = 'pause'
        self.play_toggle.SetLabel('play')

        server.stop()
        print('pause') 

    def stop(self):
        self.pause()
        GLOBAL_READER.set_index(0)
        self.parent_frame.update('Stop player')
        print('stop')


    def read(self):
        freqs = osc.freq

        synth = Osc(table=table, freq=freqs, mul=1).out()
        synth.muls = osc.muls

        server.start()

        # iterate sur osc muls
        max = GLOBAL_READER.get_max_index()
        max = 50
        max = GLOBAL_READER.get_max_index() if max > GLOBAL_READER.get_max_index() else max

        for i in range(GLOBAL_READER.index, GLOBAL_READER.index + max):
            GLOBAL_READER.set_index(i)

            mul = list(synth.muls[i])
            # print(mul)
            # table.replace(list(mul))
            synth.setMul(mul)
            self.parent_frame.panel_img.display(GLOBAL_DATA.lvls)
            time.sleep(.2)


        server.stop()

###############################################################
# App 
if __name__ == "__main__":
    app = wx.App()
    frame = ImageFrame(None, -1, "Image Frame", size=(600, 600))

    # frame.load_file(DEFAULT_FILENAME)

    app.MainLoop()