# Forced-Alignment
Tool which aligns audio and transcript of [Plumcot data](https://github.com/hbredin/pyannote-db-plumcot) using vrbs.

`forced-alignment.py` first adds brackets around normalized-characters names in the scripts defined in [pyannote.db](https://github.com/hbredin/pyannote-db-plumcot/blob/develop/CONTRIBUTING.md#idepisodetxt)

You should then launch `forced-alignment.sh` to align audio and transcription. Unfortunately, it requires vrbs which is closed source. Usage :
```bash
forced-alignment.sh /path/to/your/data/${SERIE_URI}/file_list.txt ${SERIE_URI}
```

You can customize logs outputs directories directly in the file using

```bash
#$ -o /path/to/logs/output/
#$ -e /path/to/logs/error/
```

Once vrbs is done you can continue with `forced-alignment.py` (press `Enter`) which will transform the XML output of vrbs into [Gecko](https://github.com/gong-io/gecko) compliant-JSON. The file formats are described below. The script also removes speakers id from the transcript and puts them instead in a proper JSON attribute : `speaker["id"]`.

After that, you may or may not want to convert all the annotations from gecko_JSON to RTTM, this relies on pyannote.core
Type "n" or "no" (case insensitive) if you don't want to.

*You're done !*

# Format
## XML (VRBS)
```py
AudioDoc  
└───ProcList    #0  
│   ChannelList #1  
│   SpeakerList #2  
│   SegmentList #3  (list)  
│   └───SpeechSegment #(dict[attrib], list[Word])  
│   │   └───Word
│   │   │   └───id #(unique for all words, regardless of speechsegment)
│   │   │   │   stime #(start time in seconds)
│   │   │   │   dur #(duration in seconds)
│   │   │   │   conf #(confidence between 0 and 1)
│   │   │   spkid #(speaker id, could be used as name or vrbs_id)
```

## JSON (Gecko)

```py
Root
└───monologues #(list of speakers)
│   └───monolog_0 #(1st speech turn)
│   │   └──speaker #(1st speech turn's speaker)
│   │   │  terms #(list of terms)
│   │   │   └──term_0 #(1st speech turn's 1st term)
│   │   │   │  └──start #(1st speech turn's 1st term start time in SECONDS)
│   │   │   │  │  confidence #(1st speech turn's 1st term start confidence (between 0.0 and 1.0))
│   │   │   │  │  text #str: content of the word
```

## Aligned (LIMSI)
Inspired by [`stm`](http://www1.icsi.berkeley.edu/Speech/docs/sctk-1.2/infmts.htm#stm_fmt_name_0) the `aligned` format provides additionally the confidence of the model in the transcription :

```
<file_uri> <speaker_id> <start_time> <end_time> <token> <confidence_score>
```
e.g. :
```
TheBigBangTheory.Season01.Episode01 sheldon_cooper start_time end_time How 0.9
TheBigBangTheory.Season01.Episode01 sheldon_cooper start_time end_time are 0.6
TheBigBangTheory.Season01.Episode01 sheldon_cooper start_time end_time you 0.8
TheBigBangTheory.Season01.Episode01 sheldon_cooper start_time end_time , 0.1
TheBigBangTheory.Season01.Episode01 sheldon_cooper start_time end_time Leonard 0.5
TheBigBangTheory.Season01.Episode01 sheldon_cooper start_time end_time ? 0.2
```
