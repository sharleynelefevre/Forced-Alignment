#!/usr/bin/env python
# coding: utf-8

# # Dependencies

#I/O
import json
import xml.etree.ElementTree as ET
import re
import os

#Meta
from typing import TextIO,Union
import warnings

#utils
from utils import normalize_string, do_this
from convert import *

#pyannote
from pyannote.core import Annotation,Segment,Timeline,notebook,SlidingWindowFeature,SlidingWindow

# # Hyperparameters

SERIE_URI="GameOfThrones"
SERIE_PATH=os.path.join("/vol/work/lerner/pyannote-db-plumcot","Plumcot","data",SERIE_URI)
TRANSCRIPTS_PATH=os.path.join(SERIE_PATH,"transcripts")
ALIGNED_PATH=os.path.join(SERIE_PATH,"forced-alignment")
SERIE_SPLIT={"test":[1],
            "dev":[2,3],
            "train":[4,5,6]
            }
EXPECTED_MIN_SPEECH_TIME=200.0
VRBS_CONFIDENCE_THRESHOLD=0.5#used in gecko_JSON_to_Annotation function
FORCED_ALIGNMENT_COLLAR=0.15#used in gecko_JSON_to_Annotation function
ANNOTATION_PATH=os.path.join(ALIGNED_PATH,"{}_{}collar.rttm".format(SERIE_URI,FORCED_ALIGNMENT_COLLAR))
ANNOTATED_PATH=os.path.join(ALIGNED_PATH,"{}_{}confidence.uem".format(SERIE_URI,VRBS_CONFIDENCE_THRESHOLD))

def write_brackets(SERIE_PATH,TRANSCRIPTS_PATH):
    """
    Puts brackets around the [speaker_id] (first token of each line of the script) in the scripts
    Also writes a file with all the file names in SERIE_PATH/file_list.txt
    """
    file_counter=0
    file_list=[]
    for file_name in os.listdir(TRANSCRIPTS_PATH):
        first_name,extension=os.path.splitext(file_name)
        if extension==".txt":
            file_list.append(first_name)#keep a list for qsub on m107

            #open file
            with open(os.path.join(TRANSCRIPTS_PATH,file_name),"r") as file:
                raw_script=file.read()

            #anonymyzes the script
            bracket_raw_script=""
            for speech_turn in raw_script.split("\n"):
                if speech_turn != '':
                    first_space=speech_turn.find(" ")
                    bracket_raw_script+="["+speech_turn[:first_space]+"]"+speech_turn[first_space:]+"\n"

            #writes back anonymized script .anonymous
            anonymous_path=os.path.join(TRANSCRIPTS_PATH,first_name+".brackets")
            print("\rWriting file #{} to {}".format(file_counter,anonymous_path),end="")
            with open(anonymous_path,"w") as file:
                file.write(bracket_raw_script)
            file_counter+=1
    if file_counter==0:
        raise ValueError(f"no txt files were found in {TRANSCRIPTS_PATH}")
    with open(os.path.join(SERIE_PATH,"file_list.txt"),"w") as file:
        file.write("\n".join(file_list)    )
    print("succesfully wrote file list to",os.path.join(SERIE_PATH,"file_list.txt"))


def write_id_aligned(ALIGNED_PATH,TRANSCRIPTS_PATH):
    """
    writes json files as defined in functions xml_to_GeckoJSON and aligned_to_id
    """
    file_counter=0
    for file_name in os.listdir(ALIGNED_PATH):
        first_name,extension=os.path.splitext(file_name)#first_name should be common to xml and txt file
        if extension==".xml":
            with open(os.path.join(TRANSCRIPTS_PATH,first_name+".txt"),"r") as file:
                raw_script=file.read()
            xml_tree=ET.parse(os.path.join(ALIGNED_PATH,file_name))
            xml_root = xml_tree.getroot()
            gecko_json=xml_to_GeckoJSON(xml_root,raw_script)
            json_path=os.path.join(ALIGNED_PATH,first_name+".json")
            print("\rWriting file #{} to {}".format(file_counter,json_path),end="")
            file_counter+=1
            with open(json_path,"w") as file:
                json.dump(gecko_json,file)
    if file_counter==0:
        raise ValueError(f"no xml files were found in {ALIGNED_PATH}")
    print()#new line for prettier print

def append_to_rttm(file: TextIO, output: Union[Timeline, Annotation]):
        """Write pipeline output to "rttm" file
        Parameters
        ----------
        file : file object
        output : `pyannote.core.Annotation`
            Pipeline output
        """
        warnings.warn("deprecated in favor of Annotation.write_rttm")
        if isinstance(output, Annotation):
            for s, t, l in output.itertracks(yield_label=True):
                line = (
                    f'SPEAKER {output.uri} 1 {s.start:.3f} {s.duration:.3f} '
                    f'<NA> <NA> {l} <NA> <NA>\n'
                )
                file.write(line)
            return

        msg = (
            f'Dumping {output.__class__.__name__} instances to "rttm" files '
            f'is not supported.'
        )
        raise NotImplementedError(msg)

def append_to_uem(file: TextIO,
                         output: Timeline):
        """Write pipeline output to "uem" file
        Parameters
        ----------
        file : file object
        output : `pyannote.core.Timeline`
            Pipeline output
        """
        warnings.warn("deprecated in favor of Timeline.write_uem")
        if isinstance(output, Timeline):
            for segment in output:
                line = "{} 1 {} {}\n".format(
                    output.uri,
                    segment.start,
                    segment.end
                    )
                file.write(line)
            return

        msg = (
            f'Dumping {output.__class__.__name__} instances to "uem" files '
            f'is not supported.'
        )
        raise NotImplementedError(msg)

def gecko_JSONs_to_aligned(ALIGNED_PATH):
    file_counter=0
    for i,file_name in enumerate(sorted(os.listdir(ALIGNED_PATH))):
        uri,extension=os.path.splitext(file_name)#uri should be common to xml and txt file
        if extension==".json":
            print("\rprocessing file #{} from {}".format(file_counter,os.path.join(ALIGNED_PATH,file_name)),end="")
            file_counter+=1
            #read file, convert to annotation and write rttm
            with open(os.path.join(ALIGNED_PATH,file_name),"r") as file:
                gecko_JSON=json.load(file)
            aligned=gecko_JSON_to_aligned(gecko_JSON,uri)
            with open(os.path.join(ALIGNED_PATH,uri+".aligned"),'w') as file:
                file.write(aligned)
    if file_counter==0:
        raise ValueError(f"no json files were found in {ALIGNED_PATH}")
    print("\ndone ;)")

def gecko_JSONs_to_RTTM(ALIGNED_PATH, ANNOTATION_PATH, ANNOTATED_PATH, VRBS_CONFIDENCE_THRESHOLD =0.0, FORCED_ALIGNMENT_COLLAR=0.0):
    """
    Converts gecko_JSON files to RTTM using pyannote `Annotation`.
    Also keeps a track of files in train, dev and test sets.
    Also adds annotated parts of the files to a UEM depending on FORCED_ALIGNMENT_COLLAR.

    Parameters:
    -----------
    ALIGNED_PATH : path where gecko_JSON files are stored.
    ANNOTATION_PATH : path where to store the annotations in RTTM.
    ANNOTATED_PATH : path where to store the annotated parts of the files in UEM.
    VRBS_CONFIDENCE_THRESHOLD : `float`, the segments with confidence under VRBS_CONFIDENCE_THRESHOLD won't be added to UEM file.
        Defaults to 0.0
    FORCED_ALIGNMENT_COLLAR: `float`, Merge tracks with same label and separated by less than `FORCED_ALIGNMENT_COLLAR` seconds.
        Defaults to 0.0
    """
    if os.path.exists(ANNOTATION_PATH):
        raise ValueError("""{} already exists.
                         You probably don't wan't to append any more data to it.
                         If you do, remove this if statement.""".format(ANNOTATION_PATH))
    if os.path.exists(ANNOTATED_PATH):
        raise ValueError("""{} already exists.
                         You probably don't wan't to append any more data to it.
                         If you do, remove this if statement.""".format(ANNOTATED_PATH))
    file_counter=0
    train_list,dev_list,test_list=[],[],[]#keep track of file name used for train, dev and test sets
    for i,file_name in enumerate(sorted(os.listdir(ALIGNED_PATH))):
        uri,extension=os.path.splitext(file_name)#uri should be common to xml and txt file
        if extension==".json":
            print("\rprocessing file #{} from {}".format(file_counter,os.path.join(ALIGNED_PATH,file_name)),end="")
            #read file, convert to annotation and write rttm
            with open(os.path.join(ALIGNED_PATH,file_name),"r") as file:
                gecko_JSON=json.load(file)
            annotation,annotated=gecko_JSON_to_Annotation(gecko_JSON,uri,'speaker',VRBS_CONFIDENCE_THRESHOLD,FORCED_ALIGNMENT_COLLAR,EXPECTED_MIN_SPEECH_TIME)
            with open(ANNOTATION_PATH,'a') as file:
                annotation.write_rttm(file)
            with open(ANNOTATED_PATH,'a') as file:
                annotated.write_uem(file)
            #train dev or test ?
            season_number=int(re.findall(r'\d+', file_name.split(".")[1])[0])
            if season_number in SERIE_SPLIT["test"]:
                test_list.append(uri)
            elif season_number in SERIE_SPLIT["dev"]:
                dev_list.append(uri)
            elif season_number in SERIE_SPLIT["train"]:
                train_list.append(uri)
            else:
                raise ValueError("Expected season_number to be in SERIE_SPLIT : {}\ngot {} instead".format(SERIE_SPLIT,season_number))
            file_counter+=1
    if file_counter==0:
        raise ValueError(f"no json files were found in {ALIGNED_PATH}")
    with open(os.path.join(SERIE_PATH,"train_list.lst"),"w") as file:
        file.write("\n".join(train_list))
    with open(os.path.join(SERIE_PATH,"dev_list.lst"),"w") as file:
        file.write("\n".join(dev_list))
    with open(os.path.join(SERIE_PATH,"test_list.lst"),"w") as file:
        file.write("\n".join(test_list))
    print("\nDone, succefully wrote the rttm file to {}\n and the uem file to {}".format(ANNOTATION_PATH,ANNOTATED_PATH))

def main(SERIE_PATH,TRANSCRIPTS_PATH,ALIGNED_PATH, ANNOTATION_PATH, ANNOTATED_PATH, VRBS_CONFIDENCE_THRESHOLD, FORCED_ALIGNMENT_COLLAR,EXPECTED_MIN_SPEECH_TIME):
    print("adding brackets around speakers id")
    write_brackets(SERIE_PATH,TRANSCRIPTS_PATH)
    try:
        os.mkdir(ALIGNED_PATH)
    except FileExistsError as e:
        print(e)
    print("done, you should now launch vrbs before converting")
    input("Press Enter when vrbs is done...")
    print("converting vrbs.xml to vrbs.json and adding proper id to vrbs alignment")
    write_id_aligned(ALIGNED_PATH,TRANSCRIPTS_PATH)
    if do_this("Would you like to convert annotations from gecko_JSON to RTTM ?"):
        gecko_JSONs_to_RTTM(ALIGNED_PATH, ANNOTATION_PATH, ANNOTATED_PATH, VRBS_CONFIDENCE_THRESHOLD, FORCED_ALIGNMENT_COLLAR)
    else:
        print("Okay, no hard feelings")
    if do_this("Would you like to convert annotations from gecko_JSON to LIMSI-compliant 'aligned' ?"):
        gecko_JSONs_to_aligned(ALIGNED_PATH)
    else:
        print("Okay then you're done ;)")

if __name__ == '__main__':
    main(SERIE_PATH,TRANSCRIPTS_PATH,ALIGNED_PATH,ANNOTATION_PATH, ANNOTATED_PATH, VRBS_CONFIDENCE_THRESHOLD, FORCED_ALIGNMENT_COLLAR,EXPECTED_MIN_SPEECH_TIME)
