import io
import math
import mimetypes
import re
from os.path import getsize
from pathlib import Path

import PyPDF2
import pyvips
from PIL import Image as PilImage
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile

from comics.util import get_upload_fp

RE_NAME_SLICER = re.compile(r'^(?P<label>(?:[-_a-z\s]+(?:\d+[-_\s]+)?)?0*(?P<number>\d+)).*'
                            r'\.(?P<ext>[a-z1-9]+)$',
                            re.I)


#########################################
# Image Files                           #
#########################################

def parse_pages(page_files):
    pages = []

    for f in page_files:
        if re.search('cover', f.name):
            pages.append({
                'number': 0,
                'file': f,
            })
        else:
            m = RE_NAME_SLICER.search(f.name)
            if m:
                number = int(m.group('number'))

                label = m.group('label')[1:]
                if label[0] == 'i' or label[0] == 'p':
                    label = str(number)
                else:
                    label = label[0] + str(number)

                pages.append({
                    'label': label,
                    'number': number,
                    'file': f,
                })

    pages.sort(key=lambda pi: pi['number'])

    for i, p in enumerate(pages):
        yield i, p['file']


#########################################
# PDF Files                             #
#########################################

def pt2px(pts, dpi=72):
    return math.floor(pts * dpi / 72)


def file_stem(pdf_file):
    try:
        return Path(pdf_file.name).stem
    except AttributeError:
        return 'page'


def page_name(pdf_name, i, ext):
    return '{}_{:04d}{}'.format(pdf_name, i, ext)


def get_pfr(pdf_file):
    # this is a non-trivial operation, and we can't close the tempfile anyway
    if not hasattr(pdf_file, 'pfr'):
        pdf_file.pfr = PyPDF2.PdfFileReader(get_upload_fp(pdf_file))
    return pdf_file.pfr


def get_page_info(pfr_page):
    # figure out if the page is just a simple image
    if '/Text' in pfr_page['/Resources']['/ProcSet']:
        simple = False
    else:
        simple = True

        x_object = pfr_page['/Resources']['/XObject'].getObject()

        obj = None
        for o in x_object:
            if x_object[o]['/Subtype'] == '/Image':
                if obj:
                    simple = False
                    break
                obj = o

        if not obj:
            simple = False

    crop_box = pfr_page.cropBox

    return {
        'simple': simple,
        'width': crop_box[2] - crop_box[0],
        'height': crop_box[3] - crop_box[1],
    }


# https://stackoverflow.com/a/54449010
def convert_pdf(pdf_file, page_info, dpi=300, ext='.png', **kwargs):
    # n is number of pages to load, -1 means load all pages
    if hasattr(pdf_file, 'temporary_file_path'):
        all_pages = pyvips.Image.new_from_file(pdf_file.temporary_file_path(),
                                               dpi=dpi,
                                               n=-1,
                                               access="sequential")
    elif hasattr(pdf_file, 'read'):
        # need to read here because storage may not be local
        pdf_file.seek(0)
        all_pages = pyvips.Image.new_from_buffer(pdf_file.read(), "",
                                                 dpi=dpi,
                                                 n=-1,
                                                 access="sequential")
    else:
        raise NotImplementedError('Unsure how to access file.')

    # That'll be RGBA ... flatten out the alpha
    all_pages = all_pages.flatten(background=255)
    print('Dims: {} x {}'.format(all_pages.width, all_pages.height))

    # make sure we're not crazy
    n_pages = all_pages.get("n-pages")
    assert n_pages == len(page_info)

    # the PDF is loaded as a very tall, thin image, with the pages joined
    # top-to-bottom ... we loop down the image cutting out each page
    pdf_name = file_stem(pdf_file)
    content_type = mimetypes.guess_type('a'+ext)[0]
    height_accum = 0
    for i in range(0, n_pages):
        print('Page {:04d} at {}px'.format(i+1, height_accum))

        # cut out our page
        width = pt2px(page_info[i]['width'], dpi)
        height = pt2px(page_info[i]['height'], dpi)
        page = all_pages.crop(0, height_accum, width, height)
        height_accum += height

        # would have to deal with ctypes to do this in memory
        name = page_name(pdf_name, i, ext)
        with TemporaryUploadedFile(name, content_type, 0, None) as file:
            page.write_to_file(file.temporary_file_path(), **kwargs)
            file.size = getsize(file.temporary_file_path())
            yield i, file


# https://stackoverflow.com/a/34116472
def rip_pdf(pdf_file, pfr):
    pdf_name = file_stem(pdf_file)

    # TODO: make use of /ColorSpace resources in Pillow if possible

    for i, page in enumerate(pfr.pages):
        x_object = page['/Resources']['/XObject'].getObject()

        obj = None
        for o in x_object:
            if x_object[o]['/Subtype'] == '/Image':
                obj = o
                break
        assert obj is not None

        fltr = x_object[obj]['/Filter']
        size = (x_object[obj]['/Width'], x_object[obj]['/Height'])
        data = x_object[obj].getData()
        if x_object[obj]['/ColorSpace'] == '/DeviceRGB':
            mode = "RGB"
        else:
            mode = "P"

        buf = io.BytesIO()

        if '/FlateDecode' in fltr:
            x_object[obj] = PilImage.frombytes(mode, size, data)
            x_object[obj].save(buf, 'PNG', optimize=True)
            ext = ".pdf"
        elif '/DCTDecode' in fltr:
            buf.write(data)
            ext = ".jpg"
        elif '/JPXDecode' in fltr:
            buf.write(data)
            ext = ".jpx"
        else:
            raise NotImplementedError('/Filter = %s not supported.' % fltr)

        name = page_name(pdf_name, i, ext)
        content_type = mimetypes.guess_type(name)[0]
        yield i, InMemoryUploadedFile(buf, None, name, content_type, buf.tell(), None)


def parse_pdf(pdf_file):
    pfr = get_pfr(pdf_file)
    page_info = [get_page_info(page) for page in pfr.pages]

    if any([not pi['simple'] for pi in page_info]):
        yield from convert_pdf(pdf_file, page_info, 150, ext='.jpg', Q=95)
    else:
        yield from rip_pdf(pdf_file, pfr)
