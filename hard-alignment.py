#!/usr/bin/env python
# coding: utf-8

# # Dependencies

import json
import pysrt
import xml.etree.ElementTree as ET
import re
import os

# # Hyperparameters

SERIE_PATH=os.path.join("pyannote-db-plumcot","Plumcot","data","Friends")
TRANSCRIPTS_PATH=os.path.join(SERIE_PATH,"transcripts")
ALIGNED_PATH=os.path.join(SERIE_PATH,"hard-alignment")


# # Utils
def normalize_string(string):
    """
    Lowercases and removes punctuation from input string, also strips the spaces from the borders and removes multiple spaces
    """
    string =re.sub(r"([,.!?'-:])", r"", string).lower()
    string = re.sub(' +', ' ',string).strip()
    return string

# # Transform

def xml_to_GeckoJSON(xml_root,raw_script):
    """
    Parameters:
        xml_root : root of the xml tree defined by vrbs for hard alignment. root[3] should be SegmentList, a list of speech segments
        raw_script : `str` : the script as defined in https://github.com/hbredin/pyannote-db-plumcot/blob/develop/CONTRIBUTING.md#idepisodetxt
            Each line is a speech turn and the first (space-separated) token is the normalized speaker id.
    Returns:
        gecko_json : a JSON `dict` based on the demo file of https://github.com/gong-io/gecko/blob/master/samples/demo.json
            should be written to a file using json.dump"""
    gecko_json=json.loads("""{
      "schemaVersion" : "2.0",
      "monologues" : [  ]
    }""")
    gecko_json["monologues"]=[[] for _ in raw_script.split("\n")]
    json_i=0
    terms=[]
    current_speaker=xml_root[3][0][0].text.strip()[1:-1]
    for i,speech_segment in enumerate(xml_root[3]):
        for word in speech_segment:
            if word.text.strip()[0]=="[":#speaker id -> add new speaker
                speaker={
                "name" : None,
                "id" : current_speaker,#first and last charcater should be []
                "vrbs_id" : speech_segment.attrib['spkid']
                    }
                current_speaker=word.text.strip()[1:-1]
                gecko_json["monologues"][json_i]={
                    "speaker":speaker,
                    "terms":terms
                    }
                json_i+=1
                terms=[]
            else:
                terms.append(
                {
                    "start" : float(word.attrib['stime']),
                    "end" : float(word.attrib['stime'])+float(word.attrib['dur']),
                    "text" : word.text,
                    "type" : "WORD",
                    "confidence": word.attrib['conf']
                })
    speaker={
    "name" : None,
    "id" : current_speaker,#first and last charcater should be []
    "vrbs_id" : speech_segment.attrib['spkid']
        }
    new_monolog={
            "speaker":speaker,
            "terms":terms
            }
    if json_i<len(gecko_json["monologues"]):
        gecko_json["monologues"][json_i]=new_monolog
    else:
        gecko_json["monologues"].append(new_monolog)
    gecko_json["monologues"].pop(0)

    return gecko_json

# # Main

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
            print("Writing file #{} to {}".format(file_counter,anonymous_path),end="\r")
            with open(anonymous_path,"w") as file:
                file.write(bracket_raw_script)
            file_counter+=1

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
            print("Writing file #{} to {}".format(file_counter,json_path),end="\r")
            file_counter+=1
            with open(json_path,"w") as file:
                json.dump(gecko_json,file)
       
def main(SERIE_PATH,TRANSCRIPTS_PATH,ALIGNED_PATH):
    print("adding brackets around speakers id")
    write_brackets(SERIE_PATH,TRANSCRIPTS_PATH)
    print("done anonymizing, you should now launch vrbs before converting")
    input("Press Enter when vrbs is done...")
    print("converting vrbs.xml to vrbs.json and adding proper id to vrbs alignment")
    write_id_aligned(ALIGNED_PATH,TRANSCRIPTS_PATH)
    print("done :)")

if __name__ == '__main__':
    main(SERIE_PATH,TRANSCRIPTS_PATH,ALIGNED_PATH)
