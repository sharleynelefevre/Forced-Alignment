# Hard-Alignment
Tool which aligns audio and transcript of [Plumcot data](https://github.com/hbredin/pyannote-db-plumcot) using vrbs.

`hard-alignment.py` first adds brackets around normalized-characters names in the scripts defined in [pyannote.db](https://github.com/hbredin/pyannote-db-plumcot/blob/develop/CONTRIBUTING.md#idepisodetxt)

You should then launch `hard-alignment-friends.sh` to align audio and transcription. Unfortunately, it requires vrbs which is closed source.

Once vrbs is done you can continue with `hard-alignment.py` (press `Enter`) which will transform the XML output of vrbs into [Gecko](https://github.com/gong-io/gecko) compliant-JSON. The file formats are described below. The script also removes speakers id from the transcript and puts them instead in a proper JSON attribute : `speaker["id"]`.

*You're done !*

# Format
## XML (limsi)
```
AudioDoc  
└───ProcList    0  
│   ChannelList 1  
│   SpeakerList 2  
│   SegmentList 3  (list)  
│   └───SpeechSegment (dict[attrib], list[Word])  
│   │   └───Word
│   │   │   └───id (unique for all words, regardless of speechsegment)
│   │   │   │   stime (start time in seconds)
│   │   │   │   dur (duration in seconds)
│   │   │   │   conf (confidence between 0 and 1)
│   │   │   spkid (speaker id, could be used as name or vrbs_id)
```

## JSON (Gecko)

```
Root
└───monologues (list of speakers)
│   └───monolog_0 (1st speech turn)
│   │   └──speaker (1st speech turn's speaker)
│   │   │  terms (list of terms)
│   │   │   └──term_0 (1st speech turn's 1st term)
│   │   │   │  └──start (1st speech turn's 1st term start time in SECONDS)
│   │   │   │  │  confidence (1st speech turn's 1st term start confidence (between 0.0 and 1.0))
```