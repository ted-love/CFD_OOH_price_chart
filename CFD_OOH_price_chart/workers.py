from PySide6 import QtCore
import asyncio
import queue
import time

class WebsocketWorker(QtCore.QThread):
    update_signal = QtCore.Signal(str, float, float, float)  
    
    def __init__(self, queue: queue.Queue=None):
        super().__init__()
        self.queue=queue
        self._should_stop = False
        self._is_running = True  
        self.use_callbacks=False
        self.use_run_queue=True
    
    def run_queue(self):
        while True:
            try:
                response = self.queue.get_nowait()
                self.update_signal.emit(*response)
            except queue.Empty:
                break 

    def run(self):
        if self.use_run_queue:
            self.queue_timer = QtCore.QTimer()
            self.queue_timer.timeout.connect(self.run_queue)
            self.queue_timer.start(1)
        
        self.exec_() 

    def stop(self):
        self._is_running = False
        if hasattr(self, 'queue_timer'):
            self.queue_timer.stop()
        self.quit() 
        self.wait()