from __future__ import annotations
from typing import List, Dict, Union, Tuple, Callable, TYPE_CHECKING
if TYPE_CHECKING:
    from instruments.classes import PriceInstrument
    from timeseries.classes import ParentTimeSeries
    from exchanges.classes import ExchangeInfo
    from workers import WebsocketWorker
    from gui import Window

from PySide6 import QtCore, QtWidgets
import gui
from custom_qt_classes.subplot_widget import SubplotWidget  

windows: Dict[str, Window] = {}

    

class Application(QtWidgets.QApplication):
    create_window_signal = QtCore.Signal(dict, str, tuple)
    window_titles_signal = QtCore.Signal(list)
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_instance(cls):
        return cls._instance
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._initialized = True
        self.window_titles_opened=[]
        self.n_windows=0
        
        
    def add_subplot_widgets(self, subplot_widget_container: Dict[str, SubplotWidget], ) -> None:
        self.subplot_widget_container=subplot_widget_container
        self.max_possible_windows = len(self.subplot_widget_container)
        for subplot_widget in self.subplot_widget_container.values():
            subplot_widget.menu.toggle_window_structure_menu(self.max_possible_windows)
            self.window_titles_signal.connect(subplot_widget.menu.window_titles_slot)
            subplot_widget.menu.window_structure_signal.connect(self.toggle_subplot)

    def add_data(self,
                 instrument_container: Dict[str, PriceInstrument],
                 timeseries_parent_container: Dict[str, ParentTimeSeries],
                 exchange_dataclass_container: Dict[str, ExchangeInfo],
                 ) -> None:
        self.instrument_container=instrument_container
        self.timeseries_parent_container=timeseries_parent_container
        self.exchange_dataclass_container=exchange_dataclass_container
        
    def add_streaming_apps(self, websocket_worker: WebsocketWorker, streaming_client) -> None:
        self._websocket_worker=websocket_worker
        self._websocket_worker.update_signal.connect(self._websocket_response)
        self._streaming_client=streaming_client
    
    def start(self):       
        self._websocket_worker.start()
        self.open_window(self.subplot_widget_container)        
        self.aboutToQuit.connect(self._cleanup)
        
    @QtCore.Slot(str, float, float, float)
    def _websocket_response(cls, name, timestamp, bid, ask):
        instrument_object = cls.instrument_container[name]
        instrument_object.update(timestamp=timestamp, bid=bid, ask=ask)
        
    def open_window(self, subplot_widget_container: Dict[str, SubplotWidget]):
        self.n_windows+=1
        
        for i in range(1, 9999):
            window_title = f"Window {i}"
            if not window_title in self.window_titles_opened:
                break 
        window = gui.Window(subplot_widget_container, window_title)
        window.add_close_event_callbacks(self.window_closed_responder)
        windows[window_title] = window
        
        self.window_titles_opened.append(window_title)    

        self.window_titles_signal.emit(self.window_titles_opened)
        for subplot_widget in subplot_widget_container.values():
            subplot_widget.menu.set_window_title(window_title)
        window.showMaximized()

    def close_window(self, window: Window):
        window.hide()
        self.window_titles_opened.remove(window.window_title)
        del windows[window.window_title]
        self.window_titles_signal.emit(self.window_titles_opened)
        window.setWindowTitle(None)

    def toggle_subplot(self, action: str, windows_adjusting: Tuple[str, str], subplot_widget: SubplotWidget):

        if action == "Pop-Out":
            
            window_losing = windows[windows_adjusting[0]]

            window_losing.menu.disconnect_subplot_widget_from_signals(subplot_widget)
            window_losing.remove_subplot_widget(subplot_widget)
            
            subplot_widget_container = {subplot_widget.title() : subplot_widget}
            self.open_window(subplot_widget_container)
            
        if action == "Move":
            window_losing = windows[windows_adjusting[0]]
            window_gaining = windows[windows_adjusting[1]]
            
            subplot_widget.menu.set_window_title(windows_adjusting[1])
            window_losing.menu.disconnect_subplot_widget_from_signals(subplot_widget)
            window_losing.remove_subplot_widget(subplot_widget)
        
            window_gaining.menu.connect_subplot_widget_to_signals(subplot_widget)

            window_gaining.add_subplot_widget(subplot_widget)

            window_gaining.restructure_subplots()
            window_gaining.subplot_widget_container.update({subplot_widget.title() : subplot_widget})
            
            if window_losing.count_subplots() == 0:
                self.close_window(window_losing)

    def window_closed_responder(self, window_closing: Window):
        window_gaining=None
        for win in windows.values():
            if win.isVisible():
                window_gaining = win
                break
        if window_gaining is None:
            self.closeAllWindows()
        else:
            subplots_from_closing_win = list(window_closing.subplot_widget_container.values())
            for subplot_widget in subplots_from_closing_win:
                self.toggle_subplot("Move", [window_closing.window_title, window_gaining.window_title], subplot_widget)
            self.window_titles_signal.emit(self.window_titles_opened)
    
                
            

            
    def _cleanup(self):
        self._websocket_worker.stop()
        self._streaming_client.disconnect()
        
    