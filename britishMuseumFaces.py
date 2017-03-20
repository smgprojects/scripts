from SPARQLWrapper import SPARQLWrapper, JSON
import urllib
import os
from PIL import Image
import subprocess


# Function defined for resize and crop of an image
def resize_and_crop(img_path, modified_path, size, crop_type='top'):
    """
    Resize and crop an image to fit the specified size.
    args:
        img_path: path for the image to resize.
        modified_path: path to store the modified image.
        size: (width, height) tuple. Eg (300,300)
        crop_type: can be 'top', 'middle' or 'bottom'
    raises:
        Exception: if can not open the file in img_path of there is problems
            to save the image.
        ValueError: if an invalid `crop_type` is provided.
    """
    # If height is higher we resize vertically, if not we resize horizontally
    img = Image.open(img_path)
    # Get current and desired ratio for the images
    img_ratio = img.size[0] / float(img.size[1])
    ratio = size[0] / float(size[1])
    # The image is scaled/cropped vertically or horizontally depending on the ratio
    if ratio > img_ratio:
        img = img.resize((size[0], size[0] * img.size[1] / img.size[0]),
                Image.ANTIALIAS)
        # Crop in the top, middle or bottom
        if crop_type == 'top':
            box = (0, 0, img.size[0], size[1])
        elif crop_type == 'middle':
            box = (0, (img.size[1] - size[1]) / 2, img.size[0], (img.size[1] + size[1]) / 2)
        elif crop_type == 'bottom':
            box = (0, img.size[1] - size[1], img.size[0], img.size[1])
        else :
            raise ValueError('Error detected: That option is not valid for crop type')
        img = img.crop(box)
    elif ratio < img_ratio:
        img = img.resize((size[1] * img.size[0] / img.size[1], size[1]),
                Image.ANTIALIAS)
        # Switch for where to crops
        if crop_type == 'top':
            box = (0, 0, size[0], img.size[1])
        elif crop_type == 'middle':
            box = ((img.size[0] - size[0]) / 2, 0, (img.size[0] + size[0]) / 2, img.size[1])
        elif crop_type == 'bottom':
            box = (img.size[0] - size[0], 0, img.size[0], img.size[1])
        else :
            raise ValueError('Error detected: That option is not valid for crop type')
        img = img.crop(box)
    else :
        img = img.resize((size[0], size[1]),
                Image.ANTIALIAS)
    img.save(modified_path)

# Makde sure you are in correct directory
os.chdir('/Users/danielpett/githubProjects/scripts/')

# Set up your sparql endpoint
sparql = SPARQLWrapper("http://collection.britishmuseum.org/sparql")

# Set your query
sparql.setQuery("""PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX crm: <http://erlangen-crm.org/current/>
PREFIX fts: <http://www.ontotext.com/owlim/fts#>
PREFIX bmo: <http://collection.britishmuseum.org/id/ontology/>

SELECT DISTINCT ?image
WHERE {
  ?object bmo:PX_object_type ?object_type .
  ?object_type skos:prefLabel "bust" .
  ?object bmo:PX_has_main_representation ?image .
} LIMIT 160""")

# Return the JSON triples
sparql.setReturnFormat(JSON)
results = sparql.query().convert()

# Open the file for writing urls (this is for image magick)
listImages = open('files.txt', 'w')


# Iterate over the results
for result in results["results"]["bindings"]:
    print result
    image = result["image"]["value"]
    if os.path.isfile(os.path.join('bmimages', os.path.basename(image))):
        listImages.write(os.path.join('bmimagesResized', os.path.basename(image)) + "\n")
        print "File already exists"
    else:
        path = os.path.join('bmimages', os.path.basename(image))
        urllib.urlretrieve(image, path)
        print "Image " + os.path.basename(image) + " downloaded"

# Iterate through files and crop as required
for file in os.listdir('bmimages'):
    # Make sure file is not a hidden one etc
    if not file.startswith('.') and os.path.isfile(os.path.join('bmimages', file)):
        # Open the file checking if it is valid or not. It fails otherwise :-(
        print os.path.join('bmimages', file)
        try:
            if not os.path.exists(os.path.join('bmimagesResized', file)):
                resize_and_crop(os.path.join('bmimages', file), os.path.join('bmimagesResized', file), (300, 300))
                print file + " resized"
            else:
                print "Resized file exists"
        except:
            pass

# Create the montage if files.txt exists with a try catch block
if os.path.isfile('files.txt'):
    print ("File exists")
    try:
        # This will produce multiple tiles for large results
        subprocess.call("montage @files.txt -border 0 -geometry 660x -tile 10x8 bmPortraitBusts.jpg", shell=True)
    except:
        print "Montage generation failed"
