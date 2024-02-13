import win32print
import win32ui
from PIL import Image, ImageWin, ImageOps
import os
import json


def printImages(image_arr):

    image_height = None
    logo_height = None
    marginx = None
    marginy = None
    logo_rotate= True
    logo_path = None
    image_marginx =None
    image_marginy =None
    with open('./config/printing/layout.json', 'r') as layout_file:
        layout_data = json.load(layout_file)
        print(layout_data)

        image_height = layout_data['image_height']
        logo_height = layout_data['logo_height']
        marginx = layout_data['marginx']
        marginy = layout_data['marginy']
        logo_rotate = layout_data['logo_rotate']
        logo_path = layout_data['logo_path']
        image_marginx = layout_data['image_marginx']
        image_marginy = layout_data['image_marginy']







    image_arr = ['./photos/{0}'.format(element) for element in image_arr]

   
    PHYSICALWIDTH = 110
    PHYSICALHEIGHT = 111
   

    printer_name = win32print.GetDefaultPrinter ()
    file_name = "photo_strip"

  
    hDC = win32ui.CreateDC ()
    hDC.CreatePrinterDC (printer_name)
    # printable_area = hDC.GetDeviceCaps (HORZRES), hDC.GetDeviceCaps (VERTRES)

    printer_size = hDC.GetDeviceCaps (PHYSICALWIDTH), hDC.GetDeviceCaps (PHYSICALHEIGHT)
  
    #
    hDC.StartDoc (file_name)
    hDC.StartPage ()

    
    
    print("Printer Y Size: " + str(printer_size[0]))
    print("Printer X Size: " + str(printer_size[1]/2))
  

    for i in range(len(image_arr)):
        bmp = Image.open (image_arr[i]).convert('RGBA')
        print(bmp.size[0])
        print(bmp.size[1])
        if bmp.size[0] > bmp.size[1]:
            bmp = bmp.rotate (90, expand=True)

    
        
        dib = ImageWin.Dib (bmp)
        
        dib.draw (hDC.GetHandleOutput (), ((image_height*i) + marginy,marginx*2, image_height*i + image_height, int(printer_size[1]/2)-(marginx*2)))
        dib.draw (hDC.GetHandleOutput (), ((image_height*i) + marginy,int(printer_size[1]/2)+(marginx), image_height*i + image_height, int(printer_size[1])-(marginx*2)))
        os.remove(image_arr[i])

    bmp = Image.open (logo_path).convert('RGBA')
    if logo_rotate == True:
            bmp = bmp.rotate (90, expand=True)
    dib = ImageWin.Dib (bmp)
    dib.draw (hDC.GetHandleOutput (), ((image_height*len(image_arr)) + image_marginy,image_marginx*2, image_height*len(image_arr) + logo_height, int(printer_size[1]/2)-(image_marginx*2)))
    dib.draw (hDC.GetHandleOutput (), ((image_height*len(image_arr)) + image_marginy,int(printer_size[1]/2)+(image_marginx), image_height*len(image_arr) + logo_height, int(printer_size[1])-(image_marginx*2)))


   

    hDC.EndPage ()
    hDC.EndDoc ()
    hDC.DeleteDC ()

