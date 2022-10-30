#!/usr/bin/env python3

from io import BytesIO
from math import ceil
from PIL import Image
from fpdf import FPDF
from PyPDF2 import PdfReader, PdfWriter
from pathlib import Path


def divideListToChunck(_list, chunck_num):
    def __divideListToChunck_helper():
        for i in range(0, len(_list), chunck_num):
            yield _list[i:i + chunck_num]
    return list(__divideListToChunck_helper())


class mangaBuilder:
    
    def __init__(self, width:int, height:int, mode:str):
        """
            Construct mangaBuilder object
            
            Param:
                width       => int pdf page width
                height      => int pdf page height
                mode        => string image color mode (same color mode in PIL.Image library)
        """
        
        self.page_width = width
        self.page_height = height
        self.page_mode = mode
        self.have_empty_page = False
        self.pdf:FPDF = FPDF(orientation="portrait", format=(self.page_width, self.page_height))
        self.pdf.set_margin(0)
    
    def __del__(self):
        self.pdf.close()
    
    
    def buildEpisode(self, eps_title:str, eps_file_list:list) -> None:
        """
            Build a single episode pdf
            
            Param:
                eps_title       => string episode title
                eps_file_list   => sorted list of file paths (str,Path) to all files in the episode
        """
        
        # setup
        img_data:Image.Image = None
        eps_file_list = [Path(i) for i in eps_file_list]
        eps_file_list = divideListToChunck(eps_file_list, 3)
        self.pdf.add_page()
        self.have_empty_page = True
        self.pdf.start_section(eps_title)
        
        # loop through episode file chunks & create pdf
        for img_buf_list in eps_file_list:
            
            for i in img_buf_list:
                print(i.name)
            
            # setup
            cursor = 0
            img_buf_list = [Image.open(i) for i in img_buf_list]
            loc_img_height = sum([i.height for i in img_buf_list])
            # create new img_data with sum of img height & height of left over img_data
            if img_data is None:
                img_data = Image.new(mode=self.page_mode, size=(self.page_width, loc_img_height))
            else:
                cursor = img_data.height
                tmp = Image.new(mode=self.page_mode, size=(self.page_width, img_data.height+loc_img_height))
                tmp.paste(img_data, (0, 0))
                img_data = tmp
            
            
            # merge all 3 imgs together
            for ib in img_buf_list:
                # fix aspect ratio issue
                if ib.width != self.page_width:
                    ratio = self.page_width / ib.width
                    ib = ib.resize((ceil(self.page_width), ceil(ib.height * ratio)))
                img_data.paste(ib, (0, cursor))
                cursor += ib.height
                ib.close()
            
            # make long image into pages
            img_data = self.__buildPages(img_data)
        
        # add left over img_data to a new page
        if img_data is not None:
            self.pdf.image(img_data, w=self.pdf.epw, h=img_data.height)
            self.have_empty_page = False
    
    def buildManga(self, manga_title:str, manga_file_list:list, manga_eps_list:list) -> None:
        """
            Build Mange pdf
            
            Param:
                manga_title     => string manga title
                manga_file_list => sorted list of file paths (str,Path) to all files in the manga
                manga_eps_list  => sorted list of episode information of manga
                                   Sample manga_eps_list: [ (str episode title, int episode start index (include), int episode end index (include)), (str,int,int), ... ]
                                        * str episode title
                                        * int episode start index (include)
                                            * int index for manga_file_list, the element referenced will be include in current episode
                                        * int episode end index (include)
                                            * int index for manga_file_list, the element referenced will be include in current episode
        """
        
        print(manga_title)
        self.pdf.set_title(manga_title)
        
        for (eps_title, eps_sidx, eps_eidx) in manga_eps_list:
            print(eps_title)
            self.buildEpisode(eps_title, manga_file_list[eps_sidx:eps_eidx+1])
        
    
    def saveManga(self, path) -> None:
        path = str(Path(path).resolve())
        
        # use PyPDF2 to write a new pdf without last empty page
        if self.have_empty_page:
            reader = PdfReader(BytesIO(self.pdf.output()))
            writer = PdfWriter()
            
            length = len(reader.pages) - 1
            for i in range(length):
                writer.add_page(reader.pages[i])
            
            with open(path, "wb") as file:
                writer.write(file)
        
        # output pdf directly
        else:
            self.pdf.output(path)
    
    def closePdf(self) -> None:
        self.pdf.close()
    
    def __buildPages(self, img:Image.Image) -> Image.Image:
        # img is too short, return it
        if img.height < self.page_height:
            return img
        
        # split img into pdf pages
        cursor = self.page_height
        while cursor <= img.height:
            img_data = img.crop((0, cursor-self.page_height, img.width, cursor))
            self.pdf.image(img_data, w=self.pdf.epw, h=self.pdf.eph)
            self.pdf.add_page()
            self.have_empty_page = True
            cursor += self.page_height
        
        # return left over img
        cursor = cursor-self.page_height
        if cursor < img.height:
            img = img.crop((0, cursor, img.width, img.height))
            return img
        
        return None


