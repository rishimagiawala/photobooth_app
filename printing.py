import win32print
import win32ui
from PIL import Image, ImageWin
import os
def printImages(image_arr):

    image_arr = ['./photos/{0}'.format(element) for element in image_arr]

    # Constants for GetDeviceCaps
    #
    #
    # HORZRES / VERTRES = printable area
    #
    HORZRES = 4
    VERTRES = 6
    #
    # LOGPIXELS = dots per inch
    #
    LOGPIXELSX = 300
    LOGPIXELSY = 300
    #
    # PHYSICALWIDTH/HEIGHT = total area
    #
    PHYSICALWIDTH = 110
    PHYSICALHEIGHT = 111
    #
    # PHYSICALOFFSETX/Y = left / top margin
    #
    PHYSICALOFFSETX = 112
    PHYSICALOFFSETY = 113

    printer_name = win32print.GetDefaultPrinter ()
    file_name = "whateva"

    #
    # You can only write a Device-independent bitmap
    #  directly to a Windows device context; therefore
    #  we need (for ease) to use the Python Imaging
    #  Library to manipulate the image.
    #
    # Create a device context from a named printer
    #  and assess the printable size of the paper.
    #
    hDC = win32ui.CreateDC ()
    hDC.CreatePrinterDC (printer_name)
    # printable_area = hDC.GetDeviceCaps (HORZRES), hDC.GetDeviceCaps (VERTRES)

    printer_size = hDC.GetDeviceCaps (PHYSICALWIDTH), hDC.GetDeviceCaps (PHYSICALHEIGHT)
    # printer_margins = hDC.GetDeviceCaps (PHYSICALOFFSETX), hDC.GetDeviceCaps (PHYSICALOFFSETY)

    #
    # Open the image, rotate it if it's wider than
    #  it is high, and work out how much to multiply
    #  each pixel by to get it as big as possible on
    #  the page without distorting.
    #
    # bmp = Image.open (file_name)
    # if bmp.size[0] > bmp.size[1]:
    #     bmp = bmp.rotate (90)

    # ratios = [1.0 * printable_area[0] / bmp.size[0], 1.0 * printable_area[1] / bmp.size[1]]
    scale = 1
    
    #
    # Start the print job, and draw the bitmap to
    #  the printer device at the scaled size.
    #
    hDC.StartDoc (file_name)
    hDC.StartPage ()

    # dib = ImageWin.Dib (bmp)

    marginx = 25
    marginy = 25
    rx = 0
    ty= 0 
    print("Printer Y Size: " + str(printer_size[0]))
    print("Printer X Size: " + str(printer_size[1]))

    for i in range(len(image_arr)):
        bmp = Image.open (image_arr[i])
        if bmp.size[0] > bmp.size[1]:
            bmp = bmp.rotate (90)
        dib = ImageWin.Dib (bmp)
        dib.draw (hDC.GetHandleOutput (), ((409*i)+ marginy,rx+25, 409*i + 409, int(printer_size[1]/2)-25))
        dib.draw (hDC.GetHandleOutput (), ((409*i)+ marginy,int(printer_size[1]/2)+25, 409*i + 409, int(printer_size[1])))
        os.remove(image_arr[i])
    bmp = Image.open ('./assets/images/westside-motor-lounge.png')
    # if bmp.size[0] > bmp.size[1]:
    #         bmp = bmp.rotate (90)
    dib = ImageWin.Dib (bmp)
    dib.draw (hDC.GetHandleOutput (), ((409*5)+ marginy,rx+25, 409*5 + 205, int(printer_size[1]/2)-25))
    dib.draw (hDC.GetHandleOutput (), ((409*5)+ marginy,int(printer_size[1]/2)+25, 409*5 + 205, int(printer_size[1])))

    # dib.draw (hDC.GetHandleOutput (), (0,0, int(printer_size[0]/2), int(printer_size[1]/2)))

    hDC.EndPage ()
    hDC.EndDoc ()
    hDC.DeleteDC ()

