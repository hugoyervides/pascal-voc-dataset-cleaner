import os
import sys
import xml.etree.ElementTree as ET

#Declare train and validation folders
IMAGE_FOLDER = "images"
ANOTATIONS_FOLDER = "anotations"
TRAIN_PATH = "train"
VALIDATE_PATH = "validate"

def move_to_train(images, anotations):
    anotations_directory = os.path.join(TRAIN_PATH, "anotations")
    images_directory = os.path.join(TRAIN_PATH, "images")
    os.makedirs(anotations_directory)
    os.makedirs(images_directory)
    for image in images:
        image_file_name = image['name'] + image['extension']
        destination = os.path.join(images_directory, image_file_name)
        os.rename(image['path'], destination)
    for anotation in anotations:
        anotation_file_name = anotation['name'] + anotation['extension']
        destination = os.path.join(anotations_directory, anotation_file_name)
        os.rename(anotation['path'], destination)


def separate_images(tags, element_counter, val_per, images, anotations):
    #Create directory
    anotations_directory = os.path.join(VALIDATE_PATH, "anotations")
    images_directory = os.path.join(VALIDATE_PATH, "images")
    os.makedirs(anotations_directory)
    os.makedirs(images_directory)
    moved_xml = []
    total = 0
    val_per = val_per / 100
    current_count = {}
    for tag in tags:
        total += element_counter[tag]
        current_count[tag] = 0
    for tag in tags:
        print(element_counter[tag], "(" , str(element_counter[tag] / total * 100) , "%)" , " tags for ", tag)
    print(total, " tags detected")
    print(val_per*100 , "%" , " of each tag into validation folder, separating")
    #update element counter
    for tag in tags:
        element_counter[tag] = element_counter[tag] * val_per
    for tag in tags:
        for anotation in anotations:
            #Check if this tag is completed
            if current_count[tag] >= element_counter[tag]:
                break
            #Check if the tag is in this anotation
            if tag in anotation['elements']:
                #Overflow check
                overflow = False
                for element in anotation['elements']:
                    if current_count[element] > element_counter[element]:
                        overflow = True
                #Add if we dont overflow the data
                if not overflow:
                    #Update counter
                    for element in anotation['elements']:
                        current_count[element] += 1
                    #move xml to validation
                    xml_file_name = anotation['name']+anotation['extension']
                    destination = os.path.join(anotations_directory, xml_file_name)
                    moved_xml.append(anotation)
                    #delete from stack
                    anotations.pop(anotations.index(anotation))
                    os.rename(anotation['path'], destination)
    #move the images
    for image in images:
        for anotation in moved_xml:
            if image['name'] == anotation['name']:
                #move the image too
                image_file_name = image['name'] + image['extension']
                destination = os.path.join(images_directory, image_file_name)
                os.rename(image['path'], destination)

    #Display results
    for tag in tags:
        print(current_count[tag], " elements from tag ", tag, " moved to validation folder")


#Function to separate each file into anotation type
def organize_anotations(tags, anotations):
    element_counter = {}
    final_anotations = []
    #init element counter
    for tag in tags:
        element_counter[tag] = 0
    #iterate thru anotations
    for anot in anotations:
        #Get objects asociated with this anotation
        tree = ET.parse(anot['path'])
        root = tree.getroot()
        elements = []
        #Iterate thru objects and add them to the array
        for objects in root.findall('object'):
            element_counter[objects.find('name').text] += 1
            elements.append(objects.find('name').text)
        #Add to final anotations
        final_anotations.append({
            'name' : anot['name'],
            'extension': anot['extension'],
            'path': anot['path'],
            'elements' : elements
        })
    return final_anotations, element_counter

#function to check empty tags
def check_empty_tags(anotations):
    counter = 0
    changes = False
    for anotation in anotations:
        tree = ET.parse(anotation['path'])
        root = tree.getroot()
        if(len(root.findall('object')) < 1):
            #Delete the file
            counter += 1
            os.remove(anotation['path'])
            changes = True
    print(counter, " empty xml files deleted!")
    return changes

#function to delete unused tags
def delete_missmatch_tags(tags, images, anotations):
    counter = 0
    counter_files = 0
    changes = False #Indicates if we have changes in our tags
    #navigate thru tags
    for anotation in anotations:
        tree = ET.parse(anotation['path'])
        root = tree.getroot()
        for element in root.findall('object'):
            #Check if the object element name is in the tags
            if not element.find('name').text in tags:
                counter += 1
                root.remove(element)
                changes = True
        #Check if we have changes
        if changes:
            #Rewrite the file
            tree.write(anotation['path'])
            changes = False
            counter_files += 1
    print(counter, " tags deleted")
    print(counter_files, " xml filed edited")


#Function to delete unused images
def delete_unused_images(images, tags):
    #Iterate thru images
    counter = 0
    for image in images:
        if not image["name"] in [x['name'] for x in tags]:
            #delete the imagen
            os.remove(image['path'])
            counter+=1
    print(counter, " images deleted!")

#Function to delete unused images
def delete_unused_tags(images, tags):
    #Iterate thru images
    counter = 0
    for tag in tags:
        if not tag["name"] in [x['name'] for x in images]:
            #delete the imagen
            os.remove(tag['path'])
            counter+=1
    print(counter, " tags deleted!")

#Function to process the images
def process_images():
    images = []
    counter = 0
    #iterate thr directory
    for file in os.listdir(IMAGE_FOLDER):
        images.append({
            'name':         os.path.splitext(file)[0],
            'extension':    os.path.splitext(file)[1],
            'path':         os.path.join(IMAGE_FOLDER, file)
        })
        counter += 1
    print(counter, " images loaded into memory")
    return images

#Function to process the images
def process_tags():
    tags = []
    counter = 0
    #iterate thr directory
    for file in os.listdir(ANOTATIONS_FOLDER):
        tags.append({
            'name':         os.path.splitext(file)[0],
            'extension':    os.path.splitext(file)[1],
            'path':         os.path.join(ANOTATIONS_FOLDER, file)
        })
        counter += 1
    print(counter, " tags loaded into memory")
    return tags

def main():
    tags = []
    images = []
    anotations = []
    element_counter = {}
    #Ask the user for the tags
    print("Type the tags to evaluate, when done enter $")
    while True:
        tag = input()
        if tag == '$':
            break
        tags.append(tag)
    #Ask porcentage to destinate to validation
    print("Porcentage destinated to validation?")
    val_per = int(input())
    #Process images
    print("Loading images into memory")
    images = process_images()
    anotations = process_tags()
    print("Deleting unused anotations or images")
    #Delete unused images
    delete_unused_images(images, anotations)
    delete_unused_tags(images, anotations)
    print("Reloading images")
    images = process_images()
    anotations = process_tags()
    print("Deleting unlisted tags")
    #delete unused tags
    delete_missmatch_tags(tags, images, anotations)
    print("Checking empty tags")
    if(check_empty_tags(anotations)):
        print("XML files deleted! recalculating")
        print("Loading images into memory")
        images = process_images()
        anotations = process_tags()
        print("Deleting unused anotations or images")
        #Delete unused images
        delete_unused_images(images, anotations)
        delete_unused_tags(images, anotations)
        print("Loading images into memory")
        images = process_images()
        anotations = process_tags()
    #organize anotation
    anotations, element_counter = organize_anotations(tags, anotations)
    #Separate train and validation images
    separate_images(tags, element_counter, val_per, images, anotations)
    print("Recalcualting folders")
    images = process_images()
    anotations = process_tags()
    print("Moving rest of files to train folder")
    move_to_train(images, anotations)
    
main()