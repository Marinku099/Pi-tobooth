from PIL import Image
import numpy as np
import random
import math
from pack.FrequencyDomainManager import FrequencyDomainManager

class ImageManager:
    #attributes
    width = None
    height = None
    bitDepth = None
    img = None
    data = None
    original = None
    def read(self, fileName):
        global img
        global data
        global original
        global width
        global height
        global bitDepth
        print(fileName)
        img = Image.open(fileName)
        data = np.array(img)
        original = np.copy(data)
        width = data.shape[0]
        height = data.shape[1]
        mode_to_bpp = {"1": 1, "L": 8, "P": 8, "RGB": 24, "RGBA": 32, "CMYK": 32,"YCbCr": 24, "LAB": 24, "HSV": 24, "I": 32, "F": 32}
        bitDepth = mode_to_bpp[img.mode]

        self.img = img
        self.data = data
        self.original = original
        self.width = width
        self.height = height
        self.bitDepth = bitDepth

        # print("Image %s with %s x %s pix-els (%s bits per pixel) has been read!" % (img.tile, width, height, bitDepth))

    def write(self, fileName):
        global img
        img = Image.fromarray(data)
        try:
            img.save(fileName)
        except:
            print("Write file error")
        # else:
            # print("Image %s has been written!" % (fileName))
    
    def convertToRed(self):
        global data
        for y in range(height):
            for x in range(width):
                data[x, y, 1] = 0
                data[x, y, 2] = 0

    def convertToGreen(self):
        global data
        for y in range(height):
            for x in range(width):
                data[x, y, 0] = 0
                data[x, y, 2] = 0
    
    def convertToBlue(self):
        global data
        for y in range(height):
            for x in range(width):
                data[x, y, 0] = 0
                data[x, y, 1] = 0

    def convertToGrayscale(self):
        global data
        for y in range(height):
            for x in range(width):
                r = int(data[x, y, 0])
                g = int(data[x, y, 1])
                b = int(data[x, y, 2])

                gray = (r + g + b) // 3

                data[x, y, 0] = gray
                data[x, y, 1] = gray
                data[x, y, 2] = gray

    def convertToBinary(self, threshold):
        global data
        for y in range(height):
            for x in range(width):
                r = int(data[x, y, 0])
                g = int(data[x, y, 1])
                b = int(data[x, y, 2])

                gray = (r + g + b) // 3

                if gray >= threshold:
                    data[x, y, 0] = 255
                    data[x, y, 1] = 255
                    data[x, y, 2] = 255
                else:
                    data[x, y, 0] = 0
                    data[x, y, 1] = 0
                    data[x, y, 2] = 0

    def convertToEdgeBinary(self, threshold, edgeColor=0, darkThreshold=60):
        """
        Black & white edge map (like convertToBinary, but thresholds the
        gradient magnitude instead of the intensity).
        threshold     : gradient magnitude needed to count as an edge (try 60-150)
        edgeColor     : 0   -> black edges on white background
                        255 -> white edges on black background
        darkThreshold : pixels with gray < darkThreshold are filled solid black
                        (use 0 to disable)
        """
        global data

        # 1) grayscale copy (same formula as convertToGrayscale), don't touch data yet
        gray = np.zeros((width, height), dtype=np.float64)
        for y in range(height):
            for x in range(width):
                r = int(data[x, y, 0])
                g = int(data[x, y, 1])
                b = int(data[x, y, 2])
                gray[x, y] = (r + g + b) // 3

        # 2) Sobel kernels
        sobelX = [[-1, 0, 1],
                  [-2, 0, 2],
                  [-1, 0, 1]]
        sobelY = [[-1, -2, -1],
                  [ 0,  0,  0],
                  [ 1,  2,  1]]

        backgroundColor = 255 - edgeColor
        output = np.full(data.shape, backgroundColor, dtype=data.dtype)

        # 3) gradient magnitude -> threshold -> draw edge pixel
        for y in range(1, height - 1):
            for x in range(1, width - 1):
                gx = 0.0
                gy = 0.0
                for i in range(-1, 2):
                    for j in range(-1, 2):
                        v = gray[x + j, y + i]
                        gx += v * sobelX[i + 1][j + 1]
                        gy += v * sobelY[i + 1][j + 1]

                magnitude = math.sqrt(gx * gx + gy * gy)

                if magnitude >= threshold:
                    output[x, y, 0] = edgeColor
                    output[x, y, 1] = edgeColor
                    output[x, y, 2] = edgeColor

        # 4) fill dark regions solid black (applied last so it wins over edges)
        for y in range(height):
            for x in range(width):
                if gray[x, y] < darkThreshold:
                    output[x, y, 0] = 0
                    output[x, y, 1] = 0
                    output[x, y, 2] = 0

        data = output
        
    def restoreToOriginal(self):
        global data
        global width
        global height
        
        width = original.shape[0]
        height = original.shape[1]
        data = np.copy(original)

        self.width = width
        self.height = height
        self.data = data

    def adjustBrightness(self, brightness):
        global data
        for y in range(height):
            for x in range(width):
                r = data[x, y, 0]
                g = data[x, y, 1]
                b = data[x, y, 2]
                r = r + brightness
                r = 255 if r > 255 else r
                r = 0 if r < 0 else r
                g = g + brightness
                g = 255 if g > 255 else g
                g = 0 if g < 0 else g
                b = b + brightness
                b = 255 if b > 255 else b
                b = 0 if b < 0 else b
                data[x, y, 0] = r
                data[x, y, 1] = g
                data[x, y, 2] = b
    
    def getGrayscaleHistogram(self):
        self.convertToGrayscale()
        histogram = np.array([0] * 256)
        for y in range(height):
            for x in range(width):
                histogram[data[x, y, 0]] += 1
        # self.restoreToOriginal()
        return histogram

    def writeHistogramToCSV(self, histogram, fileName):
        histogram.tofile(fileName,sep=',',format='%s')

    def getContrast(self):
        contrast = 0.0
        histogram = self.getGrayscaleHistogram()
        avgIntensity = 0.0
        pixelNum = width * height

        for i in range(len(histogram)):
            avgIntensity += histogram[i] * i

        avgIntensity /= pixelNum

        for y in range(height):
            for x in range(width):
                contrast += (data[x, y, 0] - avgIntensity) ** 2

        contrast = (contrast / pixelNum) ** 0.5

        return contrast

    def adjustContrast(self, contrast):
        global data
        currentContrast = self.getContrast()
        histogram = self.getGrayscaleHistogram()
        avgIntensity = 0.0
        pixelNum = width * height
        
        for i in range(len(histogram)):
            avgIntensity += histogram[i] * i
        
        avgIntensity /= pixelNum
        min = avgIntensity - currentContrast
        max = avgIntensity + currentContrast

        newMin = avgIntensity - currentContrast - contrast / 2
        newMax = avgIntensity + currentContrast + contrast / 2
        newMin = 0 if newMin < 0 else newMin

        newMax = 0 if newMax < 0 else newMax
        newMin = 255 if newMin > 255 else newMin
        newMax = 255 if newMax > 255 else newMax

        if (newMin > newMax):
            temp = newMax
            newMax = newMin
            newMin = temp

        contrastFactor = (newMax - newMin) / (max - min)

        for y in range(height):
            for x in range(width):
                r = data[x, y, 0]
                g = data[x, y, 1]
                b = data[x, y, 2]
                contrast += (data[x, y, 0] - avgIntensity) ** 2
                r = (int)((r - min) * contrastFactor + newMin)
                r = 255 if r > 255 else r
                r = 0 if r < 0 else r
                g = (int)((g - min) * contrastFactor + newMin)
                g = 255 if g > 255 else g
                g = 0 if g < 0 else g
                b = (int)((b - min) * contrastFactor + newMin)
                b = 255 if b > 255 else b
                b = 0 if b < 0 else b
                data[x, y, 0] = r
                data[x, y, 1] = g
                data[x, y, 2] = b

    def invert(self):
        global data
        for y in range(height):
            for x in range(width):
                r = data[x, y, 0]
                g = data[x, y, 1]
                b = data[x, y, 2]
                r = 255 - r
                g = 255 - g
                b = 255 - b
                data[x, y, 0] = r
                data[x, y, 1] = g
                data[x, y, 2] = b

    def Power_lowTransformation(self, gamma):
        global data

        for y in range(height):
            for x in range(width):

                for ch in range(3):
                    r = data[x, y, ch] / 255
                    s = 255 * (r ** gamma)
                    
                    s = 0 if s < 0 else s
                    s = 255 if s > 255 else s

                    data[x, y, ch] = int(s)

    def grayscaleHistogramEqualisation(self):
        global data
        histogram = np.array([0] * 256)
        
        for y in range(height):
            for x in range(width):
                r = data[x, y, 0]
                g = data[x, y, 1]
                b = data[x, y, 2]
                
                gray = int((0.2126*r) + int(0.7152*g) + int(0.0722*b))


                histogram[gray] += 1


            
        histogramCDF = np.array([0] * 256)
        cdfMin = 0


        for i in range(len(histogram)):
            if (i == 0):
                histogramCDF[i] = histogram[i]
            else:
                histogramCDF[i] = histogramCDF[i-1] + histogram[i]
            if (histogram[i] > 0 and cdfMin == 0):
                cdfMin = i


        for y in range(height):
            for x in range(width):
                r = data[x, y, 0]
                g = data[x, y, 1]
                b = data[x, y, 2]
                
                gray = (int)((0.2126*r) + int(0.7152*g) + int(0.0722*b))
                gray = (int)(round(255.0 * (histogramCDF[gray] - cdfMin)/(width*height-cdfMin)))
                gray = 255 if gray > 255 else gray
                gray = 0 if gray < 0 else gray


                data[x, y, 0] = gray
                data[x, y, 1] = gray
                data[x, y, 2] = gray

    def colorHistogramEqualisation(self):
        global data
        histogramRed = np.array([0] * 256)
        histogramGreen = np.array([0] * 256)
        histogramBlue = np.array([0] * 256)


        for y in range(height):
            for x in range(width):
                r = data[x, y, 0]
                g = data[x, y, 1]
                b = data[x, y, 2]


                histogramRed[r] += 1
                histogramGreen[g] += 1
                histogramBlue[b] += 1


        pixelNum = width * height


        histogramRedMin = 0
        histogramGreenMin = 0
        histogramBlueMin = 0


        histogramRedCDF = np.array([0] * len(histogramRed))
        histogramGreenCDF = np.array([0] * len(histogramGreen))
        histogramBlueCDF = np.array([0] * len(histogramBlue))


        for i in range(256):
            if (i == 0):
                histogramRedCDF[i] = histogramRed[i]
                histogramGreenCDF[i] = histogramGreen[i]
                histogramBlueCDF[i] = histogramBlue[i]
            else:
                histogramRedCDF[i] = histogramRedCDF[i - 1] + histogramRed[i]
                histogramGreenCDF[i] = histogramGreenCDF[i - 1] + histogramGreen[i]
                histogramBlueCDF[i] = histogramBlueCDF[i - 1] + histogramBlue[i]


            if (histogramRed[i] > 0 and histogramRedMin == 0):
                histogramRedMin = i


            if (histogramGreen[i] > 0 and histogramGreenMin == 0):
                histogramGreenMin = i


            if (histogramBlue[i] > 0 and histogramBlueMin == 0):
                histogramBlueMin = i
        
        for y in range(height):
            for x in range(width):
                r = data[x, y, 0]
                g = data[x, y, 1]
                b = data[x, y, 2]
                
                r = (int)(255.0 * (histogramRedCDF[r] - histogramRedCDF[histogramRedMin])/(pixelNum - histogramRedCDF[histogramRedMin]))
                r = 255 if r > 255 else r
                r = 0 if r < 0 else r
                
                g = (int)(255.0 * (histogramGreenCDF[g] - histogramGreenCDF[histogramGreenMin])/(pixelNum - histogramGreenCDF[histogramGreenMin]))
                g = 255 if g > 255 else g
                g = 0 if g < 0 else g


                b = (int)(255.0 * (histogramBlueCDF[b] - histogramBlueCDF[histogramBlueMin])/(pixelNum - histogramBlueCDF[histogramBlueMin]))
                b = 255 if b > 255 else b
                b = 0 if b < 0 else b
                
                data[x, y, 0] = r
                data[x, y, 1] = g
                data[x, y, 2] = b

    def setTemperature(self, rTemp, gTemp, bTemp):
        global data
        for y in range(height):
            for x in range(width):
                r = data[x, y, 0]
                g = data[x, y, 1]
                b = data[x, y, 2]


                r *= (rTemp / 255.0)
                r = 255 if r > 255 else r
                r = 0 if r < 0 else r
                
                g *= (gTemp / 255.0)
                g = 255 if g > 255 else g
                g = 0 if g < 0 else g


                b *= (bTemp / 255.0)
                b = 255 if b > 255 else b
                b = 0 if b < 0 else b


                data[x, y, 0] = r
                data[x, y, 1] = g
                data[x, y, 2] = b

    def averagingFilter(self, size):
        global data
        if (size % 2 == 0):
            print("Size Invalid: must be odd number!")
            return
        data_zeropaded = np.zeros([width + int(size/2) * 2, height + int(size/2) * 2, 3])

        data_zeropaded[int(size/2):width + int(size/2), int(size/2):height + int(size/2), :] = data

        for y in range(int(size/2), int(size/2) + height):
            for x in range(int(size/2), int(size/2) + width):

                subData = data_zeropaded[x - int(size/2):x + int(size/2) + 1, y - int(size/2):y + int(size/2) + 1, :]

                avgRed = np.mean(subData[:,:,0:1])
                avgGreen = np.mean(subData[:,:,1:2])
                avgBlue = np.mean(subData[:,:,2:3])
                avgRed = 255 if avgRed > 255 else avgRed
                avgRed = 0 if avgRed < 0 else avgRed
                avgGreen = 255 if avgGreen > 255 else avgGreen
                avgGreen = 0 if avgGreen < 0 else avgGreen
                avgBlue = 255 if avgBlue > 255 else avgBlue
                avgBlue = 0 if avgBlue < 0 else avgBlue
                data[x - int(size/2), y - int(size/2), 0] = avgRed
                data[x - int(size/2), y - int(size/2), 1] = avgGreen
                data[x - int(size/2), y - int(size/2), 2] = avgBlue
    
    def medianFilter(self, size):
        global data
        if (size % 2 == 0):
            print("Size Invalid: must be odd number!")
            return
        data_zeropadded = np.zeros([width + int(size/2) * 2, height + int(size/2) * 2, 3])

        data_zeropadded[int(size/2):width + int(size/2), int(size/2):height + int(size/2), :] = data

        for y in range(int(size/2), int(size/2) + height):
            for x in range(int(size/2), int(size/2) + width):

                subData = data_zeropadded[x - int(size/2):x + int(size/2) + 1, y - int(size/2):y + int(size/2) + 1, :]

                medRed = np.median(subData[:,:, 0])
                medGreen = np.median(subData[:,:, 1])
                medBlue = np.median(subData[:,:, 2])
                medRed = 255 if medRed > 255 else medRed
                medRed = 0 if medRed < 0 else medRed
                medGreen = 255 if medGreen > 255 else medGreen
                medGreen = 0 if medGreen < 0 else medGreen
                medBlue = 255 if medBlue > 255 else medBlue
                medBlue = 0 if medBlue < 0 else medBlue
                data[x - int(size/2), y - int(size/2), 0] = int(medRed)
                data[x - int(size/2), y - int(size/2), 1] = int(medGreen)
                data[x - int(size/2), y - int(size/2), 2] = int(medBlue)

    def unsharpmasking(self, size, k):
        global data
        if (size % 2 == 0):
            print("Size Invalid: must be odd number!")
            return
        
        OGImg = np.copy(data)
        self.averagingFilter(size)
        AveragingImg = np.copy(data)

        for x in range(height):
            for y in range(width):
                for ch in range(3):
                    OGVal = int(OGImg[x, y, ch])
                    AveragingVal = int(AveragingImg[x, y, ch])

                    MaskVal = OGVal - AveragingVal
                    SharpVal = int(OGVal + k * MaskVal)

                    SharpVal = 255 if SharpVal > 255 else SharpVal
                    SharpVal = 0 if SharpVal < 0 else SharpVal

                    data[x, y, ch] = SharpVal

    def addSaltNoise(self, percent):
        global data
        noOfPX = height * width
        noiseAdded = (int)(percent * noOfPX)
        whiteColor = 255
        for i in range(noiseAdded):
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)

            data[x, y, 0] = whiteColor
            data[x, y, 1] = whiteColor
            data[x, y, 2] = whiteColor

    def addPepperNoise(self, percent):
        global data
        noOfPX = height * width
        noiseAdded = (int)(percent * noOfPX)
        blackColor = 0
        for i in range(noiseAdded):
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)

            data[x, y, 0] = blackColor
            data[x, y, 1] = blackColor
            data[x, y, 2] = blackColor

    def addUniformNoise(self, percent, distribution):
        global data
        noOfPX = height * width
        noiseAdded = (int)(percent * noOfPX)
        for i in range(noiseAdded):
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)
            gray = data[x, y, 0]
            gray = int(gray)
            gray += random.randint(0, distribution * 2 - 1) - distribution
            gray = 255 if gray > 255 else gray
            gray = 0 if gray < 0 else gray
            gray = np.uint8(gray)
            data[x, y, 0] = gray
            data[x, y, 1] = gray
            data[x, y, 2] = gray

    def getFrequencyDomain(self):
        self.convertToGrayscale()
        fft = FrequencyDomainManager(self)
        # self.restoreToOriginal()
        return fft

    def contraharmonicFilter(self, size, Q):
        global data
        if (size % 2 == 0):
            print("Size Invalid: must be odd number!")
            return
        
        data_temp = np.zeros([width, height, 3])
        data_temp = data.copy()

        for y in range(height):
            for x in range(width):
                sumRedAbove = 0
                sumGreenAbove = 0
                sumBlueAbove = 0
                sumRedBelow = 0
                sumGreenBelow = 0
                sumBlueBelow = 0

                subData = data_temp[x - int(size/2):x + int(size/2) + 1, y - int(size/2):y + int(size/2)+ 1, :].copy()
                subData = subData ** (Q + 1)
                sumRedAbove = np.sum(subData[:,:,0:1], axis=None)
                sumGreenAbove = np.sum(subData[:,:,1:2], axis=None)
                sumBlueAbove = np.sum(subData[:,:,2:3], axis=None)

                subData = data_temp[x - int(size/2):x + int(size/2) + 1, y - int(size/2):y + int(size/2)+ 1, :].copy()
                subData = subData ** Q
                sumRedBelow = np.sum(subData[:,:,0:1], axis=None)
                sumGreenBelow = np.sum(subData[:,:,1:2], axis=None)
                sumBlueBelow = np.sum(subData[:,:,2:3], axis=None)

                if (sumRedBelow != 0):
                    sumRedAbove /= sumRedBelow
                    sumRedAbove = 255 if sumRedAbove > 255 else sumRedAbove
                    sumRedAbove = 0 if sumRedAbove < 0 else sumRedAbove

                if (math.isnan(sumRedAbove)):
                    sumRedAbove = 0

                if (sumGreenBelow != 0):
                    sumGreenAbove /= sumGreenBelow
                    sumGreenAbove = 255 if sumGreenAbove > 255 else sumGreenAbove
                    sumGreenAbove = 0 if sumGreenAbove < 0 else sumGreenAbove

                if (math.isnan(sumGreenAbove)):
                    sumGreenAbove = 0

                if (sumBlueBelow != 0):
                    sumBlueAbove /= sumBlueBelow
                    sumBlueAbove = 255 if sumBlueAbove > 255 else sumBlueAbove
                    sumBlueAbove = 0 if sumBlueAbove < 0 else sumBlueAbove

                if (math.isnan(sumBlueAbove)):
                    sumBlueAbove = 0

                data[x, y, 0] = sumRedAbove
                data[x, y, 1] = sumGreenAbove
                data[x, y, 2] = sumBlueAbove

    def alphaTrimmedFilter(self, size, d):
        global data
        if (size % 2 == 0):
            print("Size Invalid: must be odd number!")
            return

        data_zeropaded = np.zeros([width + int(size/2) * 2, height + int(size/2) * 2, 3])

        data_zeropaded[int(size/2):width + int(size/2), int(size/2):height + int(size/2), :] = data

        for y in range(height):
            for x in range(width):
                subData = data_zeropaded[x:x + size + 1, y:y + size + 1, :]
                sortedRed = np.sort(subData[:,:,0:1], axis=None)
                sortedGreen = np.sort(subData[:,:,1:2], axis=None)
                sortedBlue = np.sort(subData[:,:,2:3], axis=None)
                r = np.mean(sortedRed[int(d/2) : size * size - int(d/2) + 1])
                r = 255 if r > 255 else r
                r = 0 if r < 0 else r
                g = np.mean(sortedGreen[int(d/2) : size * size - int(d/2) + 1])
                g = 255 if g > 255 else g
                g = 0 if g < 0 else g
                b = np.mean(sortedBlue[int(d/2) : size * size - int(d/2) + 1])
                b = 255 if b > 255 else b
                b = 0 if b < 0 else b
                data[x, y, 0] = r
                data[x, y, 1] = g
                data[x, y, 2] = b

    def resizeNearestNeighbour(self, scaleX, scaleY):
        global data
        global width
        global height
        if scaleX <= 0 or scaleY <= 0:
            print("Scale must be greater than zero.")
            return
        newWidth = (int)(round(width * scaleX))
        newHeight = (int)(round(height * scaleY))
        newWidth = 1 if newWidth < 1 else newWidth
        newHeight = 1 if newHeight < 1 else newHeight
        data_temp = data.copy()
        data = np.zeros([newWidth, newHeight, 3], dtype=data_temp.dtype)
        for y in range(newHeight):
            for x in range(newWidth):
                oldX = (x + 0.5) / scaleX - 0.5
                oldY = (y + 0.5) / scaleY - 0.5
                xNearest = (int)(round(oldX))
                yNearest = (int)(round(oldY))
                xNearest = width - 1 if xNearest >= width else xNearest
                xNearest = 0 if xNearest < 0 else xNearest
                yNearest = height - 1 if yNearest >= height else yNearest
                yNearest = 0 if yNearest < 0 else yNearest
                data[x, y, :] = data_temp[xNearest, yNearest, :]
        width = newWidth
        height = newHeight

    def resizeBilinear(self, scaleX, scaleY):
        global data
        global width
        global height
        if scaleX <= 0 or scaleY <= 0:
            print("Scale must be greater than zero.")
            return
        newWidth = (int)(round(width * scaleX))
        newHeight = (int)(round(height * scaleY))
        newWidth = 1 if newWidth < 1 else newWidth
        newHeight = 1 if newHeight < 1 else newHeight
        data_temp = data.copy()
        data = np.zeros([newWidth, newHeight, 3], dtype=data_temp.dtype)
        for y in range(newHeight):
            for x in range(newWidth):
                oldX = (x + 0.5) / scaleX - 0.5
                oldY = (y + 0.5) / scaleY - 0.5
                oldX = 0 if oldX < 0 else oldX
                oldX = width - 1 if oldX > width - 1 else oldX
                oldY = 0 if oldY < 0 else oldY
                oldY = height - 1 if oldY > height - 1 else oldY
                #get 4 coordinates
                x1 = (int)(np.floor(oldX))
                y1 = (int)(np.floor(oldY))
                x2 = min(x1 + 1, width - 1)
                y2 = min(y1 + 1, height - 1)
                #get colours
                color11 = np.array(data_temp[x1, y1, :], dtype=float)
                color12 = np.array(data_temp[x2, y1, :], dtype=float)
                color21 = np.array(data_temp[x1, y2, :], dtype=float)
                color22 = np.array(data_temp[x2, y2, :], dtype=float)
                #interpolate x
                dx = oldX - x1
                P1 = (1 - dx) * color11 + dx * color12
                P2 = (1 - dx) * color21 + dx * color22
                #interpolate y
                dy = oldY - y1
                P = (1 - dy) * P1 + dy * P2
                P = np.round(P)
                P = np.clip(P, 0, 255)
                data[x, y, :] = P
        width = newWidth
        height = newHeight

        self.width = width
        self.height = height
        self.data = data

    def thresholding(self, threshold):
        global data
        self.convertToGrayscale()
        for y in range(height):
            for x in range(width):
                gray = data[x, y, 0]
                gray = 0 if gray < threshold else 255
                data[x, y, 0] = gray
                data[x, y, 1] = gray
                data[x, y, 2] = gray

    def ChangeColor(self):
        global data
        New_Image = np.copy(self.data)
        self.ChangeColorOnebyone(New_Image,0,9,0,0,0) # แว่นตากับคอปก
        self.ChangeColorOnebyone(New_Image,10,17,244,200,40) # พื้นหลัง
        self.ChangeColorOnebyone(New_Image,18,30,112,48,160) # ผม
        self.ChangeColorOnebyone(New_Image,31,40,45,100,210) # เสื้อ
        self.ChangeColorOnebyone(New_Image,41,53,198,134,86) # ผิว
        self.ChangeColorOnebyone(New_Image,54,99,150,150,150) # หนวด
        self.ChangeColorOnebyone(New_Image,100,255,255,255,255) # ตา
        data = np.copy(New_Image)

    def ChangeColorOnebyone(self,New_Image, threshold_lowest , threshold_highest , R , G , B):
        global data
        self.convertToGrayscale()
        for y in range(height):
            for x in range(width):
                gray = data[x, y, 0]
                if (gray >= threshold_lowest) & (gray <= threshold_highest):
                    New_Image.data[x, y, 0] = R
                    New_Image.data[x, y, 1] = G
                    New_Image.data[x, y, 2] = B

    def otsuThreshold(self):
        global data
        self.convertToGrayscale()
        histogram = np.zeros(256)

        for y in range(height):
            for x in range(width):
                histogram[data[x, y, 0]] += 1

        histogramNorm = np.zeros(len(histogram))
        pixelNum = width * height
        
        for i in range(len(histogramNorm)):
            histogramNorm[i] = histogram[i] / pixelNum

        histogramCS = np.zeros(len(histogram))
        histogramMean = np.zeros(len(histogram))

        for i in range(len(histogramNorm)):
            if (i == 0):
                histogramCS[i] = histogramNorm[i]
                histogramMean[i] = 0
            else:
                histogramCS[i] = histogramCS[i - 1] + histogramNorm[i]
                histogramMean[i] = histogramMean[i - 1] + histogramNorm[i] * i
        globalMean = histogramMean[len(histogramMean) - 1]
        maxValue = 0
        maxVariance = -1
        countMax = 0
        for i in range(len(histogramCS)):
            if (histogramCS[i] <= 0 or histogramCS[i] >= 1):
                continue

            variance = ((globalMean * histogramCS[i] - histogramMean[i]) ** 2) / (histogramCS[i] * (1 - histogramCS[i]))

            if (variance > maxVariance):
                maxVariance = variance
                maxValue = i
                countMax = 1
            elif (variance == maxVariance):
                countMax += 1
                maxValue = ((maxValue * (countMax - 1)) + i) / countMax
        threshold = round(maxValue)
        # print("Otsu threshold = %s" % threshold)
        self.thresholding(threshold)

    def SaveToOriginal(self):
        global data
        global original

        original = np.copy(data)
        self.original = original

    def erosion(self, se):
        global data
        source = np.copy(data)
        temp = np.zeros([width, height, 3], dtype=data.dtype)
        for y in range(height):
            for x in range(width):
                isEroded = True
                for seY in range(se.height):
                    for seX in range(se.width):
                        if (complex(seX, seY) in se.ignoreElements or
                            se.elements[seY, seX] != 255):
                            continue
                        imageX = x + seX - int(se.origin.real)
                        imageY = y + seY - int(se.origin.imag)
                        if (imageX < 0 or imageX >= width or
                            imageY < 0 or imageY >= height):
                            isEroded = False
                            break
                        if source[imageX, imageY, 0] != 255:
                            isEroded = False
                            break
                    if not isEroded:
                        break
                newGray = 255 if isEroded else 0
                temp[x, y] = newGray
        data = temp

    def dilation(self, se):
        global data
        source = np.copy(data)
        temp = np.zeros([width, height, 3], dtype=data.dtype)
        for y in range(height):
            for x in range(width):
                isDilated = False
                for seY in range(se.height):
                    for seX in range(se.width):
                        if (complex(seX, seY) in se.ignoreElements or
                            se.elements[seY, seX] != 255):
                            continue
                        imageX = x - (seX - int(se.origin.real))
                        imageY = y - (seY - int(se.origin.imag))
                        if (imageX < 0 or imageX >= width or
                            imageY < 0 or imageY >= height):
                            continue
                        if source[imageX, imageY, 0] == 255:
                            isDilated = True
                            break
                    if isDilated:
                        break
                newGray = 255 if isDilated else 0
                temp[x, y] = newGray
        data = temp

    def innerBoundary(self, se):
        global data

        original = np.copy(data)

        self.erosion(se)
        eroded = np.copy(data)

        data = np.zeros_like(original)

        for y in range(height):
            for x in range(width):

                if original[x, y, 0] == 255 and eroded[x, y, 0] == 0:
                    data[x, y] = 255
                else:
                    data[x, y] = 0

    def linearSpatialFilter(self, kernel, size):
        global data
        if (size % 2 == 0):
            print("Size Invalid: must be odd number!")
            return
        if (len(kernel) != size * size):
            print("Kernel size invalid!")
            return
        data_zeropaded = np.zeros([width + int(size/2) * 2, height + int(size/2) * 2, 3])
        data_zeropaded[int(size/2):width + int(size/2), int(size/2):height + int(size/2), :] = data

        for y in range(int(size/2), int(size/2) + height):
            for x in range(int(size/2), int(size/2) + width):
                subData = data_zeropaded[x - int(size/2):x + int(size/2) + 1, y - int(size/2):y + int(size/2) + 1, :]

                sumRed = np.sum(np.multiply(subData[:, :, 0:1].flatten(), kernel))
                sumGreen = np.sum(np.multiply(subData[:, :, 1:2].flatten(), kernel))
                sumBlue = np.sum(np.multiply(subData[:, :, 2:3].flatten(), kernel))
                sumRed = 255 if sumRed > 255 else sumRed
                sumRed = 0 if sumRed < 0 else sumRed
                sumGreen = 255 if sumGreen > 255 else sumGreen
                sumGreen = 0 if sumGreen < 0 else sumGreen
                sumBlue = 255 if sumBlue > 255 else sumBlue
                sumBlue = 0 if sumBlue < 0 else sumBlue
                data[x - int(size/2), y - int(size/2), 0] = sumRed
                data[x - int(size/2), y - int(size/2), 1] = sumGreen
                data[x - int(size/2), y - int(size/2), 2] = sumBlue

    def cannyEdgeDetector(self, lower, upper):
        global data
        #Step 1 - Apply 5 x 5 Gaussian filter
        gaussian = [2.0 / 159.0, 4.0 / 159.0, 5.0 / 159.0, 4.0 / 159.0, 2.0 / 159.0,
        4.0 / 159.0, 9.0 / 159.0, 12.0 / 159.0, 9.0 / 159.0, 4.0 / 159.0,
        5.0 / 159.0, 12.0 / 159.0, 15.0 / 159.0, 12.0 / 159.0, 5.0 / 159.0,
        4.0 / 159.0, 9.0 / 159.0, 12.0 / 159.0, 9.0 / 159.0, 4.0 / 159.0,
        2.0 / 159.0, 4.0 / 159.0, 5.0 / 159.0, 4.0 / 159.0, 2.0 / 159.0]
        self.linearSpatialFilter(gaussian, 5)
        self.convertToGrayscale()
        #Step 2 - Find intensity gradient
        sobelX = [1, 0, -1,
        2, 0, -2,
        1, 0, -1]
        sobelY = [1, 2, 1,
        0, 0, 0,
        -1, -2, -1]
        magnitude = np.zeros([width, height])
        direction = np.zeros([width, height])
        data_zeropaded = np.zeros([width + 2, height + 2, 3])
        data_zeropaded[1:width + 1, 1:height + 1, :] = data
        for y in range(height):
            for x in range(width):
                subData = data_zeropaded[x:x + 3, y:y + 3, :]
                gx = np.sum(np.multiply(subData[:, :, 0:1].flatten(), sobelX))
                gy = np.sum(np.multiply(subData[:, :, 0:1].flatten(), sobelY))
                magnitude[x, y] = math.sqrt(gx * gx + gy * gy)
                direction[x, y] = math.atan2(gy, gx) * 180 / math.pi
        #Step 3 - Nonmaxima Suppression
        gn = np.zeros([width, height])
        maxMagnitude = 0
        for y in range(1, height - 1):
            for x in range(1, width - 1):
                targetX = 0
                targetY = 0
                #find closest direction
                if (direction[x, y] <= -157.5):
                    targetX = 1
                    targetY = 0
                elif (direction[x, y] <= -112.5):
                    targetX = 1
                    targetY = -1
                elif (direction[x, y] <= -67.5):
                    targetX = 0
                    targetY = 1
                elif (direction[x, y] <= -22.5):
                    targetX = 1
                    targetY = 1
                elif (direction[x, y] <= 22.5):
                    targetX = 1
                    targetY = 0
                elif (direction[x, y] <= 67.5):
                    targetX = 1
                    targetY = -1
                elif (direction[x, y] <= 112.5):
                    targetX = 0
                    targetY = 1
                elif (direction[x, y] <= 157.5):
                    targetX = 1
                    targetY = 1
                else:
                    targetX = 1
                    targetY = 0
                current = magnitude[x, y]
                nextValue = magnitude[x + targetY, y + targetX]
                previousValue = magnitude[x - targetY, y - targetX]
                if (current < nextValue or current < previousValue):
                    gn[x, y] = 0
                else:
                    gn[x, y] = current
                if (gn[x, y] > maxMagnitude):
                    maxMagnitude = gn[x, y]
        #Step 4 - Hysteresis Thresholding
        for y in range(height):
            for x in range(width):
                newGray = 0
                if (maxMagnitude > 0):
                    newGray = round(gn[x, y] * 255.0 / maxMagnitude)
                data[x, y, 0] = newGray
                data[x, y, 1] = newGray
                data[x, y, 2] = newGray
            #upper threshold checking with recursive
        for y in range(height):
            for x in range(width):
                if (data[x, y, 0] >= upper):
                    data[x, y, 0] = 255
                    data[x, y, 1] = 255
                    data[x, y, 2] = 255
                    self.hystConnect(x, y, lower)

        #clear unwanted values
        for y in range(height):
            for x in range(width):
                if (data[x, y, 0] != 255):
                    data[x, y, 0] = 0
                    data[x, y, 1] = 0
                    data[x, y, 2] = 0

    def hystConnect(self, x, y, threshold):
        global data
        for i in range(y - 1, y + 2):
            for j in range(x - 1, x + 2):
                if (j < width and i < height and j >= 0 and i >= 0 and not (j == x and i == y)):
                    value = data[j, i, 0]
                    if (value != 255):
                        if (value >= threshold):
                            data[j, i, 0] = 255
                            data[j, i, 1] = 255
                            data[j, i, 2] = 255
                            self.hystConnect(j, i, threshold)
                        else:
                            data[j, i, 0] = 0
                            data[j, i, 1] = 0
                            data[j, i, 2] = 0

    def houghTransform(self, percent):
        global data

        if (percent <= 0 or percent > 1):
            print("Percent must be greater than 0 and not greater than 1.")
            return

        #The image should be converted to a binary edge map first

        #Work out how the Hough space is quantized
        numOfTheta = 180
        thetaStep = math.pi / numOfTheta
        highestR = int(round(max(width, height) * math.sqrt(2)))
        centreX = int(width / 2)
        centreY = int(height / 2)

        print("Hough array size %s x %s"
            % (numOfTheta, 2 * highestR))

        cosTheta = [0.0] * numOfTheta
        sinTheta = [0.0] * numOfTheta

        for i in range(numOfTheta):
            cosTheta[i] = math.cos(i * thetaStep)
            sinTheta[i] = math.sin(i * thetaStep)

        #Create the Hough array and initialize to zero
        houghArray = np.zeros(
            [numOfTheta, 2 * highestR], dtype=np.int32)

        #Step 1 - find each white edge pixel
        #Step 2 - apply the line equation and vote in the array
        for x in range(width):
            for y in range(height):
                pointColor = int(data[x, y, 0])

                if (pointColor == 255):
                    for i in range(numOfTheta):
                        r = int(round(
                            (x - centreX) * cosTheta[i]
                            + (y - centreY) * sinTheta[i]))

                        r = r + highestR

                        if (r < 0 or r >= 2 * highestR):
                            continue

                        houghArray[i, r] += 1

        #Step 3 - find the maximum vote
        maxHough = int(np.amax(houghArray))
        if (maxHough == 0):
            print("No edge pixels found.")
            return

        #Write the normalized Hough array for demonstration
        houghImage = np.zeros(
        [2 * highestR, numOfTheta, 3], dtype=np.uint8)
        for j in range(2 * highestR):
            for i in range(numOfTheta):
                gray = int(round(houghArray[i, j] * 255.0 / maxHough))
                houghImage[j, i, 0] = gray
                houghImage[j, i, 1] = gray
                houghImage[j, i, 2] = gray
        Image.fromarray(houghImage).save("images/HoughArray.bmp")
        print("Image HoughArray.bmp has been written!")

        #The threshold is a proportion of the maximum vote
        threshold = int(round(percent * maxHough))
        threshold = 1 if threshold < 1 else threshold
        print("Maximum vote = %s" % maxHough)
        print("Hough threshold = %s" % threshold)

        #Step 4 - search for local peaks and draw complete lines
        for i in range(numOfTheta):
            for j in range(2 * highestR):
                if (houghArray[i, j] >= threshold):
                    draw = True
                    peak = houghArray[i, j]

                    for k in range(-4, 5):
                        for l in range(-4, 5):
                            if (k == 0 and l == 0):
                                continue

                            testTheta = i + k
                            testOffset = j + l

                            if (testTheta < 0
                                or testTheta >= numOfTheta
                                or testOffset < 0
                                or testOffset >= 2 * highestR):
                                continue

                            testPeak = houghArray[
                                testTheta, testOffset]

                            if (testPeak > peak
                                or (testPeak == peak
                                and (testTheta < i
                                or (testTheta == i
                                and testOffset < j)))):
                                draw = False
                                break

                        if (not draw):
                            break

                    if (not draw):
                        continue

                    tsin = sinTheta[i]
                    tcos = cosTheta[i]

                    if (i <= numOfTheta / 4
                        or i >= (3 * numOfTheta) / 4):
                        for y in range(height):
                            x = int(round(
                                ((j - highestR)
                                - (y - centreY) * tsin)
                                / tcos + centreX))

                            if (x >= 0 and x < width):
                                data[x, y, 0] = 255
                                data[x, y, 1] = 0
                                data[x, y, 2] = 0
                    else:
                        for x in range(width):
                            y = int(round(
                                ((j - highestR)
                                - (x - centreX) * tcos)
                                / tsin + centreY))

                            if (y >= 0 and y < height):
                                data[x, y, 0] = 255
                                data[x, y, 1] = 0
                                data[x, y, 2] = 0

    def regionGrowing(self, seedX, seedY,threshold, useEightConnectivity):

        global data
        if (seedX < 0 or seedX >= width or seedY < 0 or seedY >= height or threshold < 0):
            print("Region growing parameters invalid!")
            return
        self.convertToGrayscale()
        source = np.copy(data[:, :, 0])
        visited = np.zeros([width, height], dtype=bool)
        output = np.zeros_like(data)
        seedGray = int(source[seedX, seedY])
        queue = [(seedX, seedY)]
        visited[seedX, seedY] = True
        current = 0
        while (current < len(queue)):
            pointX = queue[current][0]
            pointY = queue[current][1]
            current += 1
            output[pointX, pointY, 0] = 255
            output[pointX, pointY, 1] = 255
            output[pointX, pointY, 2] = 255
            for y in range(-1, 2):
                for x in range(-1, 2):
                    if (x == 0 and y == 0):
                        continue
                    if (not useEightConnectivity and abs(x) + abs(y) != 1):
                        continue
                    newX = pointX + x
                    newY = pointY + y
                    if (newX < 0 or newX >= width or newY < 0 or newY >= height or visited[newX, newY]):
                        continue
                    visited[newX, newY] = True
                    if (abs(int(source[newX, newY]) - seedGray) <= threshold):
                        queue.append((newX, newY))

        data = output

    def kMeansClustering(self, k):
        global data
        if (k < 2 or k > 256):
            print("Invalid number of clusters!")
            return
        self.convertToGrayscale()
        means = np.zeros(k, dtype=float)
        clusters = np.zeros([height, width], dtype=int)
        for i in range(k):
            means[i] = 255.0 * i / (k - 1)

        changed = True
        while (changed):
            changed = False
            sums = np.zeros(k, dtype=float)
            counts = np.zeros(k, dtype=int)
            for y in range(height):
                for x in range(width):
                    gray = int(data[y, x, 0])
                    nearest = 0
                    minDistance = abs(gray - means[0])
                    for i in range(1, k):
                        distance = abs(gray - means[i])
                        if (distance < minDistance):
                            minDistance = distance
                            nearest = i
                    clusters[y, x] = nearest
                    sums[nearest] += gray
                    counts[nearest] += 1
            for i in range(k):
                if (counts[i] > 0):
                    newMean = sums[i] / counts[i]
                    if (newMean != means[i]):
                        changed = True
                        means[i] = newMean
        for y in range(height):
            for x in range(width):
                gray = int(round(means[clusters[y, x]]))
                data[y, x, 0] = gray
                data[y, x, 1] = gray
                data[y, x, 2] = gray

    def ADIAbsolute(self, sequences, threshold, step):
        global data
        data_temp = np.zeros([height, width, 3])
        data_temp = np.copy(data)
        data[data > 0] = 0
        for n in range(len(sequences)):
            #read file
            otherImage = Image.open(sequences[n])
            otherData = np.array(otherImage)
            for y in range(height):
                for x in range(width):
                    dr = int(data_temp[y, x, 0]) - int(otherData[y, x, 0])
                    dg = int(data_temp[y, x, 1]) - int(otherData[y, x, 1])
                    db = int(data_temp[y, x, 2]) - int(otherData[y, x, 2])
                    dGray = int(round(0.2126*dr + 0.7152*dg + 0.0722*db))
                    if (abs(dGray) > threshold):
                        newColor = data[y, x, 0] + step
                        newColor = 255 if newColor > 255 else newColor
                        newColor = 0 if newColor < 0 else newColor
                        data[y, x] = newColor

    def ADIPositive(self, sequences, threshold, step):
        global data
        data_temp = np.copy(data)
        data[data > 0] = 0
        for n in range(len(sequences)):
            #read file
            otherImage = Image.open(sequences[n])
            otherData = np.array(otherImage)
            for y in range(height):
                for x in range(width):
                    dr = int(data_temp[x, y, 0]) - int(otherData[x, y, 0])
                    dg = int(data_temp[x, y, 1]) - int(otherData[x, y, 1])
                    db = int(data_temp[x, y, 2]) - int(otherData[x, y, 2])
                    dGray = int(round(0.2126*dr + 0.7152*dg + 0.0722*db))
                    if (dGray > threshold):
                        newColor = data[x, y, 0] + step
                        newColor = 255 if newColor > 255 else newColor
                        newColor = 0 if newColor < 0 else newColor
                        data[x, y] = newColor

    def ADINegative(self, sequences, threshold, step):
        global data
        data_temp = np.copy(data)
        data[data > 0] = 0
        for n in range(len(sequences)):
            #read file
            otherImage = Image.open(sequences[n])
            otherData = np.array(otherImage)
            for y in range(height):
                for x in range(width):
                    dr = int(data_temp[x, y, 0]) - int(otherData[x, y, 0])
                    dg = int(data_temp[x, y, 1]) - int(otherData[x, y, 1])
                    db = int(data_temp[x, y, 2]) - int(otherData[x, y, 2])
                    dGray = int(round(0.2126*dr + 0.7152*dg + 0.0722*db))
                    if (dGray < -threshold):
                        newColor = data[x, y, 0] + step
                        newColor = 255 if newColor > 255 else newColor
                        newColor = 0 if newColor < 0 else newColor
                        data[x, y] = newColor

    def traceBoundary(self):
        boundary = []
        start = None
        for y in range(height):
            for x in range(width):
                if data[y, x, 0] > 0:
                    start = (x, y)
                    break
            if start is not None:
                break
        if start is None:
            return boundary
        dx = [-1, -1, 0, 1, 1, 1, 0, -1]
        dy = [ 0, -1,-1,-1, 0, 1, 1, 1]
        current = start
        c = (start[0] - 1, start[1])
        while True:
            boundary.append(current)
            startDirection = 0
            for i in range(8):
                if current[0] + dx[i] == c[0] and current[1] + dy[i] == c[1]:
                    startDirection = i
                    break
            nextPoint = None
            nextC = None
            for i in range(8):
                direction = (startDirection + i) % 8
                testX = current[0] + dx[direction]
                testY = current[1] + dy[direction]
                if testX >= 0 and testX < width and testY >= 0 and testY < height:
                    if data[testY, testX, 0] > 0:
                        nextPoint = (testX, testY)
                        previousDirection = (direction + 7) % 8
                        nextC = (current[0] + dx[previousDirection],current[1] + dy[previousDirection])
                        break
            if nextPoint is None:
                break
            current = nextPoint
            c = nextC
            if current == start:
                break
        return boundary

    def getFreemanChainCode(self, boundary):
        chainCode = []
        if len(boundary) < 2:
            return chainCode
        dx = [1, 1, 0,-1,-1,-1, 0, 1]
        dy = [0,-1,-1,-1, 0, 1, 1, 1]
        for i in range(len(boundary)):
            current = boundary[i]
            nextPoint = boundary[(i + 1) % len(boundary)]
            moveX = nextPoint[0] - current[0]
            moveY = nextPoint[1] - current[1]
            for direction in range(8):
                if moveX == dx[direction] and moveY == dy[direction]:
                    chainCode.append(direction)
                    break
        return chainCode

    def getRegionDescriptors(self, boundary):
        area = 0
        for y in range(height):
            for x in range(width):
                if data[y, x, 0] > 0:
                    area += 1
        perimeter = 0.0
        for i in range(len(boundary)):
            current = boundary[i]
            nextPoint = boundary[(i + 1) % len(boundary)]
            moveX = abs(nextPoint[0] - current[0])
            moveY = abs(nextPoint[1] - current[1])
            if moveX + moveY == 1:
                perimeter += 1
            elif moveX == 1 and moveY == 1:
                perimeter += math.sqrt(2)
        compactness = 0.0
        circularity = 0.0
        if area > 0 and perimeter > 0:
            compactness = perimeter * perimeter / area
            circularity = 4 * math.pi * area / (perimeter * perimeter)
        return [area, perimeter, compactness, circularity]
    def drawBoundary(self, boundary):
        global data
        for p in boundary:
            data[p[1], p[0], 0] = 255
            data[p[1], p[0], 1] = 0
            data[p[1], p[0], 2] = 0

    def drawRedX(self,x, y):
        data[x, y] = [255, 0, 0]
        data[x + 1, y + 1] = [255, 0, 0]
        data[x + 1, y - 1] = [255, 0, 0]
        data[x - 1, y + 1] = [255, 0, 0]
        data[x - 1, y - 1] = [255, 0, 0]

    def MarkRed(self,x, y):
        data[x, y] = [255, 0, 0]

    def MarkBlue(self,x, y):
        data[x, y] = [0, 0, 255]

    def MarkGreen(self,x, y):
        data[x, y] = [0, 255, 0]

    def MarkColor(self, x, y, color):
        data[x, y] = color
        
    def detectHarrisFeatures(self, strongest):
        global data
        # Convert to grayscale
        self.convertToGrayscale()
        # Compute gradients Ix and Iy, drop the border
        Ix = np.zeros((width, height), dtype=np.float64)
        Iy = np.zeros((width, height), dtype=np.float64)
        # Initialize matrices to store products of gradients
        Ix2 = np.zeros((width, height), dtype=np.float64)
        Iy2 = np.zeros((width, height), dtype=np.float64)
        Ixy = np.zeros((width, height), dtype=np.float64)
        for y in range(1, height - 1):
            for x in range(1, width - 1):
                Ix[x, y] = (float(data[x + 1, y, 0]) - float(data[x - 1, y, 0])) / 2.0
                Iy[x, y] = (float(data[x, y + 1, 0]) - float(data[x, y - 1, 0])) / 2.0
                Ix2[x, y] = Ix[x, y] * Ix[x, y]
                Iy2[x, y] = Iy[x, y] * Iy[x, y]
                Ixy[x, y] = Ix[x, y] * Iy[x, y]

        # Apply 3x3 Gaussian smoothing
        gaussian = [
        [1.0 / 16.0, 2.0 / 16.0, 1.0 / 16.0],
        [2.0 / 16.0, 4.0 / 16.0, 2.0 / 16.0],
        [1.0 / 16.0, 2.0 / 16.0, 1.0 / 16.0]
        ]
        Sx2 = np.zeros((width, height), dtype=np.float64)
        Sy2 = np.zeros((width, height), dtype=np.float64)
        Sxy = np.zeros((width, height), dtype=np.float64)
        for y in range(1, height - 1):
            for x in range(1, width - 1):
                for i in range(-1, 2):
                    for j in range(-1, 2):
                        Sx2[x, y] += Ix2[x + j, y + i] * gaussian[i + 1][j + 1]
                        Sy2[x, y] += Iy2[x + j, y + i] * gaussian[i + 1][j + 1]
                        Sxy[x, y] += Ixy[x + j, y + i] * gaussian[i + 1][j + 1]

        # Compute the corner response function R
        corners = np.zeros((width, height))
        for y in range(height):
            for x in range(width):
                det = Sx2[x, y] * Sy2[x, y] - Sxy[x, y] * Sxy[x, y]
                trace = Sx2[x, y] + Sy2[x, y]
                corners[x, y] = det - 0.04 * (trace ** 2)

        cornerPoints = []
        cornerValues = []

        # Maxima Suppression
        for y in range(1, height - 1):
            for x in range(1, width - 1):
                if corners[x, y] <= 0:
                    continue

                peak = corners[x, y]
                isMaxima = True

                # Check 3x3 neighborhood
                for k in range(-1, 2):
                    for l in range(-1, 2):
                        if k == 0 and l == 0:
                            continue

                        if corners[x + l, y + k] > peak:
                            isMaxima = False
                            break

                    if not isMaxima:
                        break

                if isMaxima:
                    insertPos = 0
                    while insertPos < len(cornerValues) and cornerValues[insertPos] > peak:
                        insertPos += 1

                    cornerPoints.insert(insertPos, (x, y))
                    cornerValues.insert(insertPos, peak)

                    if len(cornerPoints) > strongest:
                        cornerPoints.pop()
                        cornerValues.pop()

        self.restoreToOriginal()
        self.convertToGrayscale()

        # Draw red X on the image at the corner points
        # for p in cornerPoints:
        #     self.drawRedX(p[0], p[1])

        return cornerPoints

    def calculateHomography(self, srcPoints, dstPoints):
        A = np.zeros([8, 8])
        b = np.zeros(8)
        for i in range(4):
            xSrc = srcPoints[i][0]
            ySrc = srcPoints[i][1]
            xDst = dstPoints[i][0]
            yDst = dstPoints[i][1]
            A[2 * i, 0] = xSrc
            A[2 * i, 1] = ySrc
            A[2 * i, 2] = 1
            A[2 * i, 3] = 0
            A[2 * i, 4] = 0
            A[2 * i, 5] = 0
            A[2 * i, 6] = -xSrc * xDst
            A[2 * i, 7] = -ySrc * xDst
            A[2 * i + 1, 0] = 0
            A[2 * i + 1, 1] = 0
            A[2 * i + 1, 2] = 0
            A[2 * i + 1, 3] = xSrc
            A[2 * i + 1, 4] = ySrc
            A[2 * i + 1, 5] = 1
            A[2 * i + 1, 6] = -xSrc * yDst
            A[2 * i + 1, 7] = -ySrc * yDst
            b[2 * i] = xDst
            b[2 * i + 1] = yDst
        return self.gaussianElimination(A, b)

    def gaussianElimination(self, A, b):
        n = len(b)
        for i in range(n):
            maxIndex = i
            for j in range(i + 1, n):
                if abs(A[j, i]) > abs(A[maxIndex, i]):
                    maxIndex = j
            for j in range(n):
                temp = A[i, j]
                A[i, j] = A[maxIndex, j]
                A[maxIndex, j] = temp
            temp = b[i]
            b[i] = b[maxIndex]
            b[maxIndex] = temp
            for k in range(i + 1, n):
                factor = A[k, i] / A[i, i]
                b[k] -= factor * b[i]
                for j in range(i, n):
                    A[k, j] -= factor * A[i, j]
        x = np.zeros(n)
        for i in range(n - 1, -1, -1):
            sum = 0
            for j in range(i + 1, n):
                sum += A[i, j] * x[j]
            x[i] = (b[i] - sum) / A[i, i]
        H = np.zeros(9)
        for i in range(8):
            H[i] = x[i]
        H[8] = 1
        return H

    def invertHomography(self, H):
        det = (H[0] * (H[4] * H[8] - H[5] * H[7]) - H[1] * (H[3] * H[8] - H[5] * H[6]) + H[2] * (H[3] * H[7] - H[4] * H[6]))
        if det == 0:
            raise ValueError("Matrix is not invertible")
        invDet = 1.0 / det
        invH = np.zeros(9)
        invH[0] = invDet * (H[4] * H[8] - H[5] * H[7])
        invH[1] = invDet * (H[2] * H[7] - H[1] * H[8])
        invH[2] = invDet * (H[1] * H[5] - H[2] * H[4])
        invH[3] = invDet * (H[5] * H[6] - H[3] * H[8])
        invH[4] = invDet * (H[0] * H[8] - H[2] * H[6])
        invH[5] = invDet * (H[2] * H[3] - H[0] * H[5])
        invH[6] = invDet * (H[3] * H[7] - H[4] * H[6])
        invH[7] = invDet * (H[1] * H[6] - H[0] * H[7])
        invH[8] = invDet * (H[0] * H[4] - H[1] * H[3])
        return invH

    def applyHomographyToPoint(self, H, x, y):
        xh = H[0] * x + H[1] * y + H[2]
        yh = H[3] * x + H[4] * y + H[5]
        w = H[6] * x + H[7] * y + H[8]
        return [xh / w, yh / w]

    def applyHomography(self, H):
        global data
        source = np.copy(data)
        output = np.zeros_like(data)
        invH = self.invertHomography(H)
        for y in range(height):
            for x in range(width):
                sourcePoint = self.applyHomographyToPoint(invH, x, y)
                srcX = int(round(sourcePoint[0]))
                srcY = int(round(sourcePoint[1]))
                if (srcX >= 0 and srcX < width
                    and srcY >= 0 and srcY < height):
                    output[x, y] = source[srcX, srcY]
        data = output

    def minimumDistanceClassifier(self, pattern, prototypes):
        nearest = 0
        minDistance = float("inf")
        for i in range(len(prototypes)):
            distance = 0
            for j in range(len(pattern)):
                difference = pattern[j] - prototypes[i][j]
                distance += difference * difference
            distance = math.sqrt(distance)
            if distance < minDistance:
                minDistance = distance
                nearest = i
        return nearest

    def connectedComponent(self):
        h, w = data.shape[0], data.shape[1]
        visited = np.zeros((h, w), dtype=bool)
        ans = []

        for y in range(h):
            for x in range(w):
                if not visited[y, x] and data[y, x, 0] == 0:
                    area = self.floodFill(x, y, visited)

                    xs = [p[0] for p in area]
                    ys = [p[1] for p in area]
                    minX, maxX = min(xs), max(xs)
                    minY, maxY = min(ys), max(ys)

                    ans.append(Component(area,
                                        maxX - minX + 1,
                                        maxY - minY + 1,
                                        minX, maxX, minY, maxY))

        ans.sort(key=lambda c: c.originX)
        return ans


    def floodFill(self, startX, startY, visited):
        h, w = data.shape[0], data.shape[1]
        pixels = []
        stack = [(startX, startY)]
        visited[startY, startX] = True

        while stack:
            cx, cy = stack.pop()
            pixels.append((cx, cy))

            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):   # 4-connectivity
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < w and 0 <= ny < h and not visited[ny, nx]:
                    if data[ny, nx, 0] == 0:
                        visited[ny, nx] = True
                        stack.append((nx, ny))

        return pixels

class Component:
    def __init__(self, pixels, width, height, minX, maxX, minY, maxY):
        self.pixels = pixels
        self.width = width
        self.height = height
        self.minX = minX
        self.maxX = maxX
        self.minY = minY
        self.maxY = maxY
        self.originX = (minX + maxX) // 2
        self.originY = (minY + maxY) // 2
# 68050341 Pongsaton Kultumyotin