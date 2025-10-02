from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QLineEdit, QComboBox, QFileDialog, QMessageBox
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
import torch
from worker import ProcessingThread

class CellposeApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Cellpose Segmentation App (Threaded)")
        self.setGeometry(200, 200, 800, 600)

        self.processing_thread = None
        self.current_image = None
        self.output_folder = None
        self.is_processing = False

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()

        # Image preview (with drag & drop support)
        self.image_label = QLabel("Drag & Drop or Click to Upload Image")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("border: 2px dashed gray;")
        self.image_label.setFixedHeight(300)
        self.layout.addWidget(self.image_label)

        # Enable drag & drop
        self.setAcceptDrops(True)

        # Upload button
        self.upload_button = QPushButton("Upload Image")
        self.upload_button.clicked.connect(self.upload_image)
        self.layout.addWidget(self.upload_button)

        # Diameter input
        diameter_layout = QHBoxLayout()
        diameter_layout.addWidget(QLabel("Estimated Diameter (px):"))
        self.diameter_input = QLineEdit()
        diameter_layout.addWidget(self.diameter_input)
        self.layout.addLayout(diameter_layout)

        # Model dropdown
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Select Model:"))
        self.model_select = QComboBox()
        self.model_select.addItems(["cyto", "nuclei", "cyto2"])
        model_layout.addWidget(self.model_select)
        self.layout.addLayout(model_layout)

        # Output folder
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("Output Folder:"))
        self.output_button = QPushButton("Choose Folder")
        self.output_button.clicked.connect(self.select_output_folder)
        output_layout.addWidget(self.output_button)
        self.layout.addLayout(output_layout)

        # Start button
        self.start_button = QPushButton("Start Analysis")
        self.start_button.clicked.connect(self.start_analysis)
        self.layout.addWidget(self.start_button)

        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_analysis)
        self.cancel_button.setEnabled(False)  # disabled until task starts
        self.layout.addWidget(self.cancel_button)

        self.central_widget.setLayout(self.layout)

    # ---------------- Drag & Drop ----------------
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            fname = event.mimeData().urls()[0].toLocalFile()
            self.load_image(fname)

    # ---------------- UI slots ----------------
    def upload_image(self):
        """Load an image and show in preview"""
        fname, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Images (*.png *.jpg *.tif *.tiff)")
        if fname:
            self.load_image(fname)

    def load_image(self, fname):
        """Helper to set current image"""
        self.current_image = fname
        pixmap = QPixmap(fname)
        self.image_label.setPixmap(
            pixmap.scaled(self.image_label.width(), self.image_label.height(), Qt.KeepAspectRatio)
        )

    def select_output_folder(self):
        """Choose an output directory"""
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.output_folder = folder
            print("Output path:", folder)

    def start_analysis(self):
        """Start processing in a background thread"""
        if self.is_processing:
            QMessageBox.warning(self, "Warning", "Processing already running!")
            return
        if not self.current_image:
            QMessageBox.warning(self, "Warning", "Please upload an image first!")
            return

        # Warn if only CPU is available
        if not torch.cuda.is_available():
            QMessageBox.warning(self, "Warning", "No GPU detected. Running on CPU. This may be slow.")

        diameter_text = self.diameter_input.text()
        diameter = float(diameter_text) if diameter_text else None
        model = self.model_select.currentText()
        output_folder = self.output_folder or "."

        self.is_processing = True
        self.start_button.setEnabled(False)
        self.cancel_button.setEnabled(True)

        self.processing_thread = ProcessingThread(self.current_image, diameter, model, output_folder)
        self.processing_thread = ProcessingThread(self.current_image, diameter, model, output_folder)
        self.processing_thread.finished.connect(self.on_processing_finished)
        self.processing_thread.error.connect(self.on_processing_error)
        self.processing_thread.start()

    def on_processing_finished(self, results):
        """Handle finished processing"""
        self.is_processing = False
        self.start_button.setEnabled(True)
        self.cancel_button.setEnabled(False)

        QMessageBox.information(self, "Done", f"Processing finished!\nCell count: {results['cell_count']}")

    def on_processing_error(self, message):
        """Handle errors during processing"""
        self.is_processing = False
        self.start_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        QMessageBox.critical(self, "Error", f"Processing failed: {message}")

    def cancel_analysis(self):
        """Stop the processing thread"""
        if self.processing_thread and self.processing_thread.isRunning():
            self.processing_thread.stop()
            self.processing_thread.wait(1000)
        self.is_processing = False
        self.start_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
