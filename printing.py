import win32print
import win32ui
from PIL import Image, ImageWin, ImageOps
import os
import json


def printImages(image_arr):
    print("Print Job Recieved")
    image_height = None
    logo_height = None
    marginx = None
    marginy = None
    logo_rotate= True
    logo_path = None
    logo_square = None
    image_marginx =None
    image_marginy =None
    num_of_images =  len(image_arr)

    logo_pos = None
    with open('./config/printing/layout.json', 'r') as layout_file:
        layout_data = json.load(layout_file)
        # print(layout_data)

        image_height = layout_data['image_height']
        logo_height = layout_data['logo_height']
        marginx = layout_data['marginx']
        marginy = layout_data['marginy']
        logo_rotate = layout_data['logo_rotate']
        logo_path = layout_data['logo_path']
        image_marginx = layout_data['image_marginx']
        image_marginy = layout_data['image_marginy']
        logo_pos = layout_data['logo_position']
        logo_square = layout_data['logo_square']

    





    image_arr = ['./photos/{0}'.format(element) for element in image_arr]
    image_arr.insert(logo_pos, logo_path)
   
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

    
    
    # print("Printer Y Size: " + str(printer_size[0]))
    # print("Printer X Size: " + str(printer_size[1]/2))
    marginx =  10
    image_offset = 0
    for i in range(len(image_arr)):
        bmp = Image.open (image_arr[i])
        # print(bmp.size[0])
        # print(bmp.size[1])
        if bmp.size[0] > bmp.size[1] or (i == logo_pos and logo_rotate==True):
            bmp = bmp.rotate (90, expand=True)

    
        
        dib = ImageWin.Dib (bmp)
        
        if logo_pos !=i:

            dib.draw (hDC.GetHandleOutput (), ((image_offset) + marginy,marginx*3, image_offset + image_height, int(printer_size[1]/2)-(marginx*2)))
            dib.draw (hDC.GetHandleOutput (), ((image_offset) + marginy,int(printer_size[1]/2)+(marginx), image_offset + image_height, int(printer_size[1]-(marginx*4))))
            image_offset += image_height
        else:
            if logo_square == False:
                dib.draw (hDC.GetHandleOutput (), ((image_offset) + marginy,marginx*3, image_offset + logo_height, int(printer_size[1]/2)-(marginx*2)))
                dib.draw (hDC.GetHandleOutput (), ((image_offset) + marginy,int(printer_size[1]/2)+(marginx), image_offset + logo_height, int(printer_size[1]-(marginx*4))))
            elif logo_square == True:
                marginx = 54
                dib.draw (hDC.GetHandleOutput (), ((image_offset) + marginy,int(marginx*2.7), image_offset + logo_height, int(printer_size[1]/2-(marginx*2.3))))
                
                dib.draw (hDC.GetHandleOutput (), ((image_offset) + marginy,int(printer_size[1]/2)+(marginx+70), image_offset + logo_height, int(printer_size[1]-(marginx*4-70))))
                marginx = 10
                
            image_offset += logo_height 
           
        if logo_pos != i:
             os.remove(image_arr[i])
        # else:

        #     dib.draw (hDC.GetHandleOutput (), ((image_height*i) + marginy,marginx*2, image_height*i + image_height, int(printer_size[1]/2)-(marginx*2)))
        #     dib.draw (hDC.GetHandleOutput (), ((image_height*i) + marginy,int(printer_size[1]/2)+(marginx), image_height*i + image_height, int(printer_size[1])-(marginx*2)))

   

   

    hDC.EndPage ()
    hDC.EndDoc ()
    hDC.DeleteDC ()

def printTestImages(image_arr):
    print("Print Job Recieved: Test")
    image_height = None
    logo_height = None
    marginx = None
    marginy = None
    logo_rotate= True
    logo_path = None
    logo_square = None
    image_marginx =None
    image_marginy =None
    num_of_images =  len(image_arr)

    logo_pos = None
    with open('./config/printing/layout.json', 'r') as layout_file:
        layout_data = json.load(layout_file)
        # print(layout_data)

        image_height = layout_data['image_height']
        logo_height = layout_data['logo_height']
        marginx = layout_data['marginx']
        marginy = layout_data['marginy']
        logo_rotate = layout_data['logo_rotate']
        logo_path = layout_data['logo_path']
        image_marginx = layout_data['image_marginx']
        image_marginy = layout_data['image_marginy']
        logo_pos = layout_data['logo_position']
        logo_square = layout_data['logo_square']

    





    image_arr = ['./test_photos/{0}'.format(element) for element in image_arr]
    image_arr.insert(logo_pos, logo_path)
   
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

    
    
    # print("Printer Y Size: " + str(printer_size[0]))
    # print("Printer X Size: " + str(printer_size[1]/2))
    marginx =  10
    image_offset = 0
    for i in range(len(image_arr)):
        bmp = Image.open (image_arr[i])
        # print(bmp.size[0])
        # print(bmp.size[1])
        if bmp.size[0] > bmp.size[1] or (i == logo_pos and logo_rotate==True):
            bmp = bmp.rotate (90, expand=True)

    
        
        dib = ImageWin.Dib (bmp)
        
        if logo_pos !=i:

            dib.draw (hDC.GetHandleOutput (), ((image_offset) + marginy,marginx*3, image_offset + image_height, int(printer_size[1]/2)-(marginx*2)))
            dib.draw (hDC.GetHandleOutput (), ((image_offset) + marginy,int(printer_size[1]/2)+(marginx), image_offset + image_height, int(printer_size[1]-(marginx*4))))
            image_offset += image_height
        else:
            if logo_square == False:
                dib.draw (hDC.GetHandleOutput (), ((image_offset) + marginy,marginx*3, image_offset + logo_height, int(printer_size[1]/2)-(marginx*2)))
                dib.draw (hDC.GetHandleOutput (), ((image_offset) + marginy,int(printer_size[1]/2)+(marginx), image_offset + logo_height, int(printer_size[1]-(marginx*4))))
            elif logo_square == True:
                marginx = 54
                dib.draw (hDC.GetHandleOutput (), ((image_offset) + marginy,int(marginx*2.7), image_offset + logo_height, int(printer_size[1]/2-(marginx*2.3))))
                
                dib.draw (hDC.GetHandleOutput (), ((image_offset) + marginy,int(printer_size[1]/2)+(marginx+70), image_offset + logo_height, int(printer_size[1]-(marginx*4-70))))
                marginx = 10
                
            image_offset += logo_height 
           
        # if logo_pos != i:
        #      os.remove(image_arr[i])
        # else:

        #     dib.draw (hDC.GetHandleOutput (), ((image_height*i) + marginy,marginx*2, image_height*i + image_height, int(printer_size[1]/2)-(marginx*2)))
        #     dib.draw (hDC.GetHandleOutput (), ((image_height*i) + marginy,int(printer_size[1]/2)+(marginx), image_height*i + image_height, int(printer_size[1])-(marginx*2)))

   

   

    hDC.EndPage ()
    hDC.EndDoc ()
    hDC.DeleteDC ()