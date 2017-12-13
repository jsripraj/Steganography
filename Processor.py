import sys
from PySide.QtGui import *
from PySide.QtCore import *
from SteganographyGUI import *
import Steganography as S
from scipy.misc import imsave
import numpy as np

class Processor(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(Processor, self).__init__(parent)
        self.setupUi(self)
        self.setAcceptDrops(False)

        # Related to viewCarrier1
        self.viewCarrier1.setAcceptDrops(True)
        self.viewCarrier1.dragEnterEvent = self.viewCarrier1DragEnterEvent
        self.viewCarrier1.dragMoveEvent = self.viewCarrier1DragMoveEvent
        self.viewCarrier1.dropEvent = self.viewCarrier1DropEvent
        self.viewCarrier1.dragLeaveEvent = self.viewCarrier1DragLeaveEvent

        # Related to viewPayload1
        self.viewPayload1.setAcceptDrops(True)
        self.viewPayload1.dragEnterEvent = self.viewPayload1DragEnterEvent
        self.viewPayload1.dragMoveEvent = self.viewPayload1DragMoveEvent
        self.viewPayload1.dropEvent = self.viewPayload1DropEvent
        self.viewPayload1.dragLeaveEvent = self.viewPayload1DragLeaveEvent

        # Related to viewCarrier2
        self.viewCarrier2.setAcceptDrops(True)
        self.viewCarrier2.dragEnterEvent = self.viewCarrier2DragEnterEvent
        self.viewCarrier2.dragMoveEvent = self.viewCarrier2DragMoveEvent
        self.viewCarrier2.dropEvent = self.viewCarrier2DropEvent
        self.viewCarrier2.dragLeaveEvent = self.viewCarrier2DragLeaveEvent

        # Tab 1 Payload Compression
        self.chkApplyCompression.toggled.connect(self.compressionChecked)
        self.slideCompression.sliderMoved.connect(self.sliderMoved)
        self.slideCompression.sliderReleased.connect(self.sliderReleased)

        # Tab 1 Carrier
        self.chkOverride.toggled.connect(self.checkEmbedEnabled)
        self.btnSave.clicked.connect(self.embed)

        # Tab 2 Buttons
        self.btnExtract.clicked.connect(self.extract)
        self.btnClean.clicked.connect(self.clean)

    # Related to viewPayload1
    def viewPayload1DragLeaveEvent(self, event):
        event.ignore()
    def viewPayload1LoadImage(self):
        pixmap = QPixmap(self.P1fname)
        pixmap = pixmap.scaled(self.viewPayload1.maximumViewportSize(), Qt.KeepAspectRatio)
        scene = QGraphicsScene()
        scene.addPixmap(pixmap)
        scene.update()
        self.viewPayload1.setScene(scene)
    def viewPayload1DragEnterEvent(self, event):
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()
    def viewPayload1DragMoveEvent(self, event):
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()
    def viewPayload1DropEvent(self, event):
        if event.mimeData().hasUrls:
            event.setDropAction(Qt.CopyAction)
            for url in event.mimeData().urls():
                fname = str(url.toLocalFile())
            if fname and fname.endswith(".png"):
                self.P1fname = fname
                try:
                    img = S.imageToArray(self.P1fname)
                    self.payload1 = S.Payload(rawData=img)
                    size = len(self.payload1.json)
                    self.viewPayload1LoadImage()
                    self.txtPayloadSize.setText(str(size))
                    self.chkApplyCompression.setCheckState(Qt.Unchecked)
                    self.lblLevel.setEnabled(False)
                    self.slideCompression.setEnabled(False)
                    self.txtCompression.setEnabled(False)
                    self.slideCompression.setValue(0)
                    self.txtCompression.setText('0')
                    self.checkEmbedEnabled()
                except ValueError:
                    event.ignore()
            else:
                event.ignore()
    def compressionChecked(self):
        if self.chkApplyCompression.isChecked():
            self.lblLevel.setEnabled(True)
            self.slideCompression.setEnabled(True)
            self.txtCompression.setEnabled(True)
            self.sliderReleased()
        else:
            self.lblLevel.setEnabled(False)
            self.slideCompression.setEnabled(False)
            self.txtCompression.setEnabled(False)
            img = S.imageToArray(self.P1fname)
            payload = S.Payload(rawData=img)
            self.txtPayloadSize.setText(str(len(payload.json)))
        self.checkEmbedEnabled()
    def sliderMoved(self):
        self.txtCompression.setText(str(self.slideCompression.sliderPosition()))
    def sliderReleased(self):
        img = S.imageToArray(self.P1fname)
        payload = S.Payload(rawData=img, compressionLevel=self.slideCompression.sliderPosition())
        self.txtPayloadSize.setText(str(len(payload.json)))
        self.checkEmbedEnabled()

    # Related to viewCarrier1
    def viewCarrier1DragLeaveEvent(self, event):
        event.ignore()
    def viewCarrier1lLoadImage(self):
        pixmap = QPixmap(self.C1fname)
        pixmap = pixmap.scaled(self.viewCarrier1.maximumViewportSize(), Qt.KeepAspectRatio)
        scene = QGraphicsScene()
        scene.addPixmap(pixmap)
        scene.update()
        self.viewCarrier1.setScene(scene)
    def viewCarrier1DragEnterEvent(self, event):
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()
    def viewCarrier1DragMoveEvent(self, event):
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()
    def viewCarrier1DropEvent(self, event):
        if event.mimeData().hasUrls:
            event.setDropAction(Qt.CopyAction)
            for url in event.mimeData().urls():
                fname = str(url.toLocalFile())
            if fname and fname.endswith(".png"):
                self.C1fname = fname
                try:
                    img = S.imageToArray(self.C1fname)
                    self.carrier1 = S.Carrier(img)
                    self.txtCarrierSize.setText(str(img.size))
                    self.viewCarrier1lLoadImage()
                    self.chkOverride.setEnabled(False)
                    self.chkOverride.setChecked(Qt.Unchecked)
                    self.lblPayloadFound.setText("")
                    if self.carrier1.payloadExists():
                        self.lblPayloadFound.setText(">>>>Payload Found<<<<")
                        self.chkOverride.setEnabled(True)
                    self.checkEmbedEnabled()
                except ValueError:
                    event.ignore()
            else:
                event.ignore()

    # Other Tab 1
    def checkEmbedEnabled(self):
        if self.viewCarrier1.scene() and self.viewPayload1.scene():
            if int(self.txtCarrierSize.text()) >= int(self.txtPayloadSize.text()):
                if not self.lblPayloadFound.text() or self.chkOverride.isChecked():
                    self.btnSave.setEnabled(True)
                    return
        self.btnSave.setEnabled(False)
    def embed(self):
        filePath, _ = QFileDialog.getOpenFileName(self, caption='Choose target file location...', filter="PNG files (*.png)")
        result = self.carrier1.embedPayload(self.payload1, override=self.chkOverride.isChecked())
        if filePath and str(filePath).endswith(".png"):
            imsave(filePath, result)

    # Related to viewCarrier2
    def viewCarrier2DragLeaveEvent(self, event):
        event.ignore()
    def viewCarrier2lLoadImage(self):
        pixmap = QPixmap(self.C2fname)
        pixmap = pixmap.scaled(self.viewCarrier2.maximumViewportSize(), Qt.KeepAspectRatio)
        scene = QGraphicsScene()
        scene.addPixmap(pixmap)
        scene.update()
        self.viewCarrier2.setScene(scene)
    def viewCarrier2DragEnterEvent(self, event):
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()
    def viewCarrier2DragMoveEvent(self, event):
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()
    def viewCarrier2DropEvent(self, event):
        if event.mimeData().hasUrls:
            event.setDropAction(Qt.CopyAction)
            for url in event.mimeData().urls():
                fname = str(url.toLocalFile())
            if fname and fname.endswith(".png"):
                self.C2fname = fname
                try:
                    self.carrier2 = S.Carrier(S.imageToArray(self.C2fname))
                    self.viewCarrier2lLoadImage()
                    self.viewPayload2.setScene(QGraphicsScene())
                    self.setCarrier2Widgets(self.carrier2)
                except ValueError:
                    event.ignore()
            else:
                event.ignore()
    def setCarrier2Widgets(self, carrier):
        if not carrier.payloadExists():
            self.lblCarrierEmpty.setText(">>>>Carrier Empty<<<<")
            self.btnExtract.setEnabled(False)
            self.btnClean.setEnabled(False)
        else:
            self.lblCarrierEmpty.setText("")
            self.btnExtract.setEnabled(True)
            self.btnClean.setEnabled(True)
    def extract(self):
        payload = self.carrier2.extractPayload()
        if S.getRawDataType(payload.rawData) == 'color':
            height, width, depth = payload.rawData.shape
            img = QImage(payload.rawData, width, height, width * depth, QImage.Format_RGB888)
        else:
            rgbData = self.grayToRgb(payload.rawData)
            height, width, depth = rgbData.shape
            img = QImage(rgbData, width, height, width * depth, QImage.Format_RGB888)
        pixmap = QPixmap(img)
        pixmap = pixmap.scaled(self.viewPayload2.maximumViewportSize(), Qt.KeepAspectRatio)
        scene = QGraphicsScene()
        scene.addPixmap(pixmap)
        scene.update()
        self.viewPayload2.setScene(scene)
    def grayToRgb(self, grayData):
        return np.tile(grayData[..., None], 3)
    def clean(self):
        cleanData = self.carrier2.clean()
        h, w, d = cleanData.shape
        img = QImage(cleanData, w, h, w * d, QImage.Format_ARGB32)
        pixmap = QPixmap(img).scaled(self.viewCarrier2.maximumViewportSize(), Qt.KeepAspectRatio)
        scene = QGraphicsScene()
        scene.addPixmap(pixmap)
        scene.update()
        self.viewCarrier2.setScene(scene)
        self.viewPayload2.setScene(QGraphicsScene())
        self.setCarrier2Widgets(S.Carrier(cleanData))

if __name__ == "__main__":
    currentApp = QApplication(sys.argv)
    currentForm = Processor()

    currentForm.show()
    currentApp.exec_()