#!/bin/bash

#$ -N hard-alignment
#$ -S /bin/bash
#$ -o /vol/work/lerner/logs/output/
#$ -e /vol/work/lerner/logs/error/
#$ -v LD_LIBRARY_PATH
#$ -v PATH

echo "This is task ${SGE_TASK_ID} of job ${JOB_ID}."
export VRBS_ROOT=/vol/jlg1/gauvain/vrbs
export VRBS_TMP=/usr/tmp
export VRBS_BIN=$VRBS_ROOT/bin
export VRBS_PART=$VRBS_ROOT/part
export VRBS_LID=$VRBS_ROOT/lid
export VRBS_TRANS=$VRBS_ROOT/trans
export VRBS_SID=$VRBS_ROOT/sid
export PATH=$PATH:$VRBS_BIN
export FILE_NAME=`head -n ${SGE_TASK_ID} $1 | tail -n 1`
echo $FILE_NAME
`which vrbs_align` -f /vol/work3/maurice/dvd_extracted/$2/$FILE_NAME.en48kHz.wav -o /vol/work/lerner/pyannote-db-plumcot/Plumcot/data/$2/hard-alignment/$FILE_NAME.xml -p -qs -v /vol/work/lerner/pyannote-db-plumcot/Plumcot/data/$2/transcripts/$FILE_NAME.brackets
