import time
from PyQt5.QtCore import QThread, pyqtSignal

class ProcessingThread(QThread):
    finished = pyqtSignal(object)   # emit results
    error = pyqtSignal(str)         # emit error message

    def __init__(self, image_path, diameter, model, output_folder):
        super().__init__()
        self.image_path = image_path
        self.diameter = diameter
        self.model = model
        self.output_folder = output_folder
        self._is_running = True

    def run(self):
        try:
            # ---- simulate long processing task ----
            for i in range(3):
                if not self._is_running:
                    return
                time.sleep(1)

            # Later: replace with real Cellpose code
            results = {
                "cell_count": 42,  # dummy result
                "output_path": self.output_folder
            }
            self.finished.emit(results)

        except Exception as e:
            self.error.emit(str(e))

    def stop(self):
        self._is_running = False
