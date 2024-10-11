import random
import win32print
import win32ui
from PIL import Image, ImageWin, ImageOps, ImageColor
import os
import json

right_off = 6
def printImages(image_arr, test = False):
    print("Print Job Recieved")
    image_height = None
    logo_height = None
    marginx = None
    marginy = None
    logo_rotate= True
    logo_path = None
    logo2_path = None
    logo_square = None
    image_marginx =None
    image_marginy =None
    num_of_images =  len(image_arr)
    background_path = None
    include_background = None
    transparent_tuple = (255,255,255,0)

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
        logo2_path = layout_data['logo2_path']
        image_marginx = layout_data['image_marginx']
        image_marginy = layout_data['image_marginy']
        logo_pos = layout_data['logo_position']
        logo_square = layout_data['logo_square']
        background_path = layout_data['background_path']
        include_background = layout_data['include_background']
        background_color = layout_data['background_color']

        transparent_tuple = ImageColor.getcolor(background_color, "RGB") + (0,) 

    




    if test == False:
        image_arr = ['./photos/{0}'.format(element) for element in image_arr]
    elif test == True:
        image_arr = ['./test_photos/{0}'.format(element) for element in image_arr]
    image_arr.insert(logo_pos, logo_path)
    
    bmp_logo_2 = Image.open (logo2_path).convert("RGBA")
    bmp_logo_2.has_transparency_data = True
    bmp_logo_2 = bmp_logo_2.rotate (90, expand=True)        
    bmp_logo_2 = makeTransparent(bmp_logo_2, transparent_tuple)
    dib_logo2 = ImageWin.Dib (bmp_logo_2)

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

#Beginning Background Code
    # Removing this - 6/27/2024
    # if include_background == True:
    #     bmp = Image.open(background_path)
    #     bmp = changeBackgroundColor(bmp, transparent_tuple)
    #     dib = ImageWin.Dib(bmp)
    #     dib.draw (hDC.GetHandleOutput (), (0,0, int(printer_size[0]), int(printer_size[1])))
    #End comment 
        
#################
    # print("Printer Y Size: " + str(printer_size[0]))
    # print("Printer X Size: " + str(printer_size[1]/2))
    marginx =  10
    image_offset = 0
    for i in range(len(image_arr)):
        bmp = Image.open (image_arr[i]).convert("RGBA")
        bmp.has_transparency_data = True
        # print(bmp.size[0])
        # print(bmp.size[1])
        if bmp.size[0] > bmp.size[1] or (i == logo_pos and logo_rotate==True):
            bmp = bmp.rotate (90, expand=True)
        if logo_pos == i:
            
            bmp = makeTransparent(bmp, transparent_tuple)

    
        init = 20
        dib = ImageWin.Dib (bmp)
        if i == 0:
            if logo_pos !=i:

                dib.draw (hDC.GetHandleOutput (), ((image_offset) + marginy+init,marginx*3+right_off, image_offset + image_height, int(printer_size[1]/2)-(marginx*2)))
                dib.draw (hDC.GetHandleOutput (), ((image_offset) + marginy+init,int(printer_size[1]/2)+(marginx), image_offset + image_height, int(printer_size[1]-(marginx*4))))
                image_offset += image_height
            else:
                if logo_square == False:
                    dib.draw (hDC.GetHandleOutput (), ((image_offset) + marginy+init,marginx*3+right_off, image_offset + logo_height, int(printer_size[1]/2)-(marginx*2)))
                    dib_logo2.draw (hDC.GetHandleOutput (), ((image_offset) + marginy+init,int(printer_size[1]/2)+(marginx), image_offset + logo_height, int(printer_size[1]-(marginx*4))))
                elif logo_square == True:
                    marginx = 54
                    dib.draw (hDC.GetHandleOutput (), ((image_offset) + marginy+init,int(marginx*2.7)+right_off, image_offset + logo_height, int(printer_size[1]/2-(marginx*2.3))))
                    
                    dib_logo2.draw (hDC.GetHandleOutput (), ((image_offset) + marginy+init,int(printer_size[1]/2)+(marginx+70), image_offset + logo_height, int(printer_size[1]-(marginx*4-70))))
                    marginx = 10
                    
                image_offset += logo_height 
            
            if logo_pos != i and test == False:
                os.remove(image_arr[i])
        else:
            if logo_pos !=i:

                dib.draw (hDC.GetHandleOutput (), ((image_offset) + marginy,marginx*3+right_off, image_offset + image_height, int(printer_size[1]/2)-(marginx*2)))
                dib.draw (hDC.GetHandleOutput (), ((image_offset) + marginy,int(printer_size[1]/2)+(marginx), image_offset + image_height, int(printer_size[1]-(marginx*4))))
                image_offset += image_height
            else:
                if logo_square == False:
                    dib.draw (hDC.GetHandleOutput (), ((image_offset) + marginy,marginx*3+right_off, image_offset + logo_height, int(printer_size[1]/2)-(marginx*2)))
                    dib_logo2.draw (hDC.GetHandleOutput (), ((image_offset) + marginy,int(printer_size[1]/2)+(marginx), image_offset + logo_height, int(printer_size[1]-(marginx*4))))
                elif logo_square == True:
                    marginx = 54
                    dib.draw (hDC.GetHandleOutput (), ((image_offset) + marginy,int(marginx*2.7)+right_off, image_offset + logo_height, int(printer_size[1]/2-(marginx*2.3))))
                    
                    dib_logo2.draw (hDC.GetHandleOutput (), ((image_offset) + marginy,int(printer_size[1]/2)+(marginx+70), image_offset + logo_height, int(printer_size[1]-(marginx*4-70))))
                    marginx = 10
                    
                image_offset += logo_height 
            
            if logo_pos != i and test==False:
                os.remove(image_arr[i])

        # else:

        #     dib.draw (hDC.GetHandleOutput (), ((image_height*i) + marginy,marginx*2, image_height*i + image_height, int(printer_size[1]/2)-(marginx*2)))
        #     dib.draw (hDC.GetHandleOutput (), ((image_height*i) + marginy,int(printer_size[1]/2)+(marginx), image_height*i + image_height, int(printer_size[1])-(marginx*2)))

   

   

    hDC.EndPage ()
    hDC.EndDoc ()
    hDC.DeleteDC ()




def makeTransparent(img, transparent_tuple):
    rgba = img.convert("RGBA")
    datas = rgba.getdata() 
  
    newData = [] 
    for item in datas: 
        if item[3] == 0:  # finding black colour by its RGB value 
            # storing a transparent value when we find a black colour 
           
            newData.append(transparent_tuple) 
        else: 
            newData.append(item)  # other colours remain unchanged 
    
    rgba.putdata(newData) 

    return rgba

# Deprecated function 6/27/2024
# def get_random_pixel_rgb(image):
#     # Get image dimensions
#     width, height = image.size
    
#     # Get random coordinates
#     random_x = random.randint(0, width - 1)
#     random_y = random.randint(0, height - 1)

#     # Get RGB values of the random pixel
#     rgb_value = image.getpixel((random_x, random_y))

#     transparent_tuple = rgb_value + (0,)

#     return transparent_tuple

def changeBackgroundColor(img, transparent_tuple):
    rgba = img.convert("RGBA")
    datas = rgba.getdata() 
  
    newData = [] 
    for item in datas: 
        newData.append(transparent_tuple) 
        
    
    rgba.putdata(newData) 

    return rgba
    
    