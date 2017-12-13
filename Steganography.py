import numpy as np
import imageio
from zlib import compress, decompress
from base64 import b64encode, b64decode
from re import match
from copy import deepcopy
from scipy.misc import imsave

def loadJSON(jsonPath):
    with open(jsonPath, 'r') as mf:
        return mf.read()
def imageToArray(imagePath):
    return np.array(imageio.imread(imagePath), np.uint8)
def textToArray(textPath):
    with open(textPath, 'r') as mf:
        return np.array(list(mf.read()))
def getRawDataType(rawData):
    dataType = rawData.ndim
    if dataType == 3:
        return "color"
    if dataType == 2:
        return "gray"
    if dataType == 1:
        return "text"
def getRawDataShape(rawData, dataType):
    if dataType != "text":
        rows = rawData.shape[0]
        cols = rawData.shape[1]
        return "{},{}".format(rows, cols)
    return None
def generateJSON(dataType, shape, isCompressed, content):
    json = '{'+'"type":"{}",'.format(dataType)
    if shape:
        json += '"size":"{}",'.format(shape)
    else:
        json += '"size":null,'
    if isCompressed:
        json += '"isCompressed":true,'
    else:
        json += '"isCompressed":false,'
    json += '"content":"{}"'.format(content.decode("utf-8"))+'}'
    return json
def validatePayloadInputs(rawData, compressionLevel, json):
    if isinstance(rawData, np.ndarray):
        if len(rawData.shape) == 3 and rawData.shape[2] > 3:
            raise ValueError("rawData has over the maximum of 3 channels")
        if compressionLevel <= 9 and compressionLevel >= -1:
            return "rawData"
        else:
            raise ValueError("compressionLevel must be between -1 and 9 (inclusive)")
    elif rawData == None:
        if isinstance(json, str):
            return "json"
        elif json == None:
            raise ValueError("json or rawData must be provided")
        else:
            raise TypeError("json must a fully-constructed JSON string with all attributes populated")
    else:
        raise TypeError("rawData must be of type np.ndarray")
def shapeData(content, typeName, size):
    if typeName == 'color':
        rows, cols = (size.split(','))
        shape = (int(rows), int(cols), -1)
    elif typeName == 'gray':
        rows, cols = (size.split(','))
        shape = (int(rows), int(cols))
    else:
        shape = (-1,)
    return np.reshape(content, shape)
def parseJSON(json):
    expr = r'^\{"type":"(?P<type>[a-z]+)","size":"?(?P<size>(?:.+?)|(?:null))"?,' \
           r'"isCompressed":(?P<isCompressed>[^,]+),"content":"(?P<content>[^\}]+)"\}$'
    m = match(expr, json)
    return (m.group('type'), m.group('size'), m.group('isCompressed'), m.group('content'))
class Payload:
    def __init__(self, rawData=None, compressionLevel=-1, json=None):
        inputType = validatePayloadInputs(rawData, compressionLevel, json)
        if inputType == "rawData":
            dataType = getRawDataType(rawData)
            shape = getRawDataShape(rawData, dataType)
            content = rawData.flatten()  # Raster scan
            isCompressed = False
            if compressionLevel != -1:
                content = compress(rawData, compressionLevel) # Takes a long time
                isCompressed = True
            content = b64encode(content)
            self.json = generateJSON(dataType, shape, isCompressed, content)
            self.rawData = rawData
        elif inputType == "json":
            typeName, size, isCompressed, content = parseJSON(json)
            content = b64decode(content.encode('utf-8'))
            if isCompressed == 'true':
                content = decompress(content)
            content = np.fromstring(content, np.uint8)
            content = shapeData(content, typeName, size)
            self.rawData = content
            self.json = json
class Carrier:
    def __init__(self, img):
        if not isinstance(img, np.ndarray):
            raise TypeError("img must be an instance of np.ndarray")
        if len(img.shape) < 3:
            raise ValueError("img must have 3 dimensions")
        rows, cols, channels = img.shape
        if channels < 4:
            raise ValueError("img must have 4 channels")
        self.img = img.astype(np.uint8,copy=False)
    def payloadExists(self):
        extractor = np.full(self.img.shape, np.uint8(3))
        pieces = np.bitwise_and(self.img, extractor)
        shift = 0; value = 0; piecesJoined = 0; newValues = []
        for piece in np.nditer(pieces):
            if piecesJoined == 4:
                newValues.append(np.uint8(value))
                shift = 0; value = 0; piecesJoined = 0
            value = value | (piece<<shift)
            shift += 2; piecesJoined += 1
            if len(newValues) == 8:
                break
        result = [check == newVal for check, newVal in zip([123, 34, 116, 121, 112, 101, 34, 58], newValues)]
        if False in result:
            return False
        return True
    def clean(self):
        carrier = deepcopy(self.img)
        cleaner = np.reshape(np.random.randint(0, 4, size=self.img.size, dtype=np.uint8), self.img.shape)
        carrier = np.left_shift(np.right_shift(carrier, 2), 2)
        return np.bitwise_or(carrier, cleaner, dtype=np.uint8)
    def embedPayload(self, payload, override=False):
        if not isinstance(payload, Payload):
            raise TypeError("payload must be of the Payload class")
        if not override:
            if self.payloadExists():
                raise Exception("Carrier already contains a payload!")
        loadArr = np.fromstring(payload.json, dtype=np.uint8)
        if loadArr.size > self.img.size * 4:
            raise ValueError("Payload size is larger than what carrier can hold")
        pRight = np.right_shift(np.left_shift(loadArr, 6), 6)
        pRightMid = np.right_shift(np.left_shift(loadArr, 4), 6)
        pLeftMid = np.right_shift(np.left_shift(loadArr, 2), 6)
        pLeft = np.right_shift(loadArr, 6)
        pieces = np.ravel(np.column_stack((pRight, pRightMid, pLeftMid, pLeft)))
        carrier = deepcopy(self.img)
        pieces = np.concatenate((pieces, np.ravel(carrier)[pieces.size:]))
        pieces = pieces.reshape(self.img.shape)
        carrier = np.left_shift(np.right_shift(carrier, 2), 2)
        return np.bitwise_or(carrier, pieces)
    def extractPayload(self):
        carrier = deepcopy(self.img)
        carrier = np.swapaxes(np.swapaxes(carrier, 1, 2), 0, 1)
        R = np.right_shift(np.left_shift(np.ravel(carrier[0]), 6), 6)
        G = np.right_shift(np.left_shift(np.ravel(carrier[1]), 6), 4)
        B = np.right_shift(np.left_shift(np.ravel(carrier[2]), 6), 2)
        A = np.left_shift(np.ravel(carrier[3]), 6)
        payload = R + G + B + A
        end = np.where(payload == 125)[0][0]
        payload = np.resize(payload, end + 1)
        payload = ''.join([chr(num) for num in np.nditer(payload)])
        return Payload(json=payload)

if __name__ == "__main__":
    image = imageToArray('data/payload1.png')
    p = Payload(image)
    with open('data/test.txt', 'w') as mf:
        mf.write(str(p.rawData))
    c = Carrier(imageToArray('data/embedded1_-1.png'))
    extracted = c.extractPayload()
    imsave('data/test.png', extracted.rawData)

