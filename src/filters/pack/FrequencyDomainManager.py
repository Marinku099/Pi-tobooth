from PIL import Image
import numpy as np
import math

class FrequencyDomainManager:
    data = None
    width = None
    height = None
    imgWidth = None
    imgHeight = None
    original = None
    im = None

    def __init__(self, im):
        self.im = im
        self.imgWidth = im.data.shape[0]
        self.imgHeight = im.data.shape[1]
        self.width = self.nextPowerOf2(self.imgWidth)
        self.height = self.nextPowerOf2(self.imgHeight)
        self.data = np.zeros((self.width, self.height), dtype=np.complex128)

        for y in range(self.imgHeight):
            for x in range(self.imgWidth):
                gray = im.data[x, y, 0]
                self.data[x, y] = gray + 0j

        self.fft2d(False)
        self.shifting()

        self.original = np.copy(self.data)

    def nextPowerOf2(self, a):
        b = 1
        while (b < a):
            b = b << 1
        return b

    def fft(self, x):
        n = self.nextPowerOf2(len(x))
        # base case
        if (n == 1):
            return x
        # radix 2 Cooley-Tukey FFT
        # even terms
        evenFFT = np.array(self.fft(x[0::2]), dtype=np.complex128)
        # odd terms
        oddFFT = np.array(self.fft(x[1::2]), dtype=np.complex128)
        # compute FFT
        factor = np.array([math.cos(-2 * k * math.pi / n) + math.sin(-2 * k * math.pi / n) * 1j for k in range(n // 2)], dtype=np.complex128)
        factor = factor * oddFFT

        return [evenFFT[k] + factor[k] for k in range(n // 2)] + [evenFFT[k] - factor[k] for k in range(n // 2)]

    def writeSpectrumLogScaled(self, fileName):
        temp = np.zeros((self.height, self.width, 3))
        spectrum = np.absolute(self.data)
        max = np.max(spectrum)
        min = np.min(spectrum)
        min = 0 if min < 1 else math.log10(min)
        max = 0 if max < 1 else math.log10(max)
        for y in range(self.height):
            for x in range(self.width):
                spectrumV = spectrum[x, y]
                spectrumV = 0 if spectrumV < 1 else math.log10(spectrumV)
                spectrumV = ((spectrumV - min) * 255 / (max - min))
                spectrumV = 255 if spectrumV > 255 else spectrumV
                spectrumV = 0 if spectrumV < 0 else spectrumV
                temp[x, y, 0] = spectrumV
                temp[x, y, 1] = spectrumV
                temp[x, y, 2] = spectrumV
        img = Image.fromarray(temp.astype(np.uint8))
        try:
            img.save(fileName)
        except:
            print("Write file error")
        else:
            print("Image %s has been written!" % (fileName))

    def writePhase(self, fileName):
        temp = np.zeros((self.height, self.width, 3))
        phase = np.angle(self.data)
        max = np.max(phase)
        min = np.min(phase)
        for y in range(self.height):
            for x in range(self.width):
                phaseV = phase[x,y]
                phaseV = ((phaseV - min) * 255 / (max - min))
                phaseV = 255 if phaseV > 255 else phaseV
                phaseV = 0 if phaseV < 0 else phaseV
                temp[x, y, 0] = phaseV
                temp[x, y, 1] = phaseV
                temp[x, y, 2] = phaseV
        img = Image.fromarray(temp.astype(np.uint8))
        try:
            img.save(fileName)
        except:
            print("Write file error")
        else:
            print("Image %s has been written!" % (fileName))

    def shifting(self):
        halfWidth = self.width // 2
        halfHeight = self.height // 2
        self.data = np.roll(self.data, halfHeight, axis = 0)
        self.data = np.roll(self.data, halfWidth, axis = 1)

    def fft2d(self, invert):
        # horizontal first
        if (not invert):
            self.data = [self.fft(row) for row in self.data]
            self.data = np.transpose(self.data)
        else:
            self.data = [self.ifft(row) for row in self.data]
            self.data = np.transpose(self.data)
            # then vertical
        if (not invert):
            self.data = [self.fft(row) for row in self.data]
            self.data = np.transpose(self.data)
        else:
            self.data = [self.ifft(row) for row in self.data]
            self.data = np.transpose(self.data)

    def ifft(self, x):
        n = len(x)
        # conjugate then fft for the inverse
        x = np.conjugate(x)
        x = self.fft(x)
        x = np.conjugate(x)
        x = x / n
        return x
    
    def getInverse(self):
        self.shifting()
        self.fft2d(True)
        dataRe = np.real(self.data)
        for y in range(self.height):
            for x in range(self.width):
                color = dataRe[x, y]
                color = 255 if color > 255 else color
                color = 0 if color < 0 else color
                self.im.data[x, y, 0] = color
                self.im.data[x, y, 1] = color
                self.im.data[x, y, 2] = color

    def ILPF(self, radius):
        if (radius <= 0 or radius > min(self.width/2, self.height/2)):
            print("INVALID Radius!")
            return
        centerX = self.width // 2
        centerY = self.height // 2
        for y in range(self.height):
            for x in range(self.width):
                if ((x - centerX) ** 2 + (y - centerY) ** 2 > radius ** 2):
                    self.data[x, y] = 0 + 0j

    def GLPF(self, radius):
        if (radius <= 0 or radius > min(self.width/2, self.height/2)):
            print("INVALID Radius!")
            return
        centerX = self.width // 2
        centerY = self.height // 2
        for y in range(self.height):
            for x in range(self.width):
                distanceSquared = (x - centerX) ** 2 + (y - centerY) ** 2
                h = math.exp(-distanceSquared / (2 * radius ** 2))
                self.data[x, y] = self.data[x, y] * h

    def IHPF(self, radius):
        if (radius <= 0 or radius > min(self.width/2, self.height/2)):
            print("INVALID Radius!")
            return
        centerX = self.width // 2
        centerY = self.height // 2
        for y in range(self.height):
            for x in range(self.width):
                if ((x - centerX) ** 2 + (y - centerY) ** 2 <= radius ** 2):
                    self.data[x, y] = 0 + 0j

    def GHPF(self, radius):
        if (radius <= 0 or radius > min(self.width/2, self.height/2)):
            print("INVALID Radius!")
            return
        centerX = self.width // 2
        centerY = self.height // 2
        for y in range(self.height):
            for x in range(self.width):
                distanceSquared = (x - centerX) ** 2 + (y - centerY) ** 2
                h = 1 - math.exp(-distanceSquared / (2 * radius ** 2))
                self.data[x, y] = self.data[x, y] * h

# 68050341 Pongsaton Kultumyotin