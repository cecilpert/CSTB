#!/bin/bash

error_json () {
    echo "{\"emptySearch\": \"There is a problem, impossible to finish the program\"}" > fail.log
    cat fail.log
}

if [ "$pam" != "NGG" ]; then
    error_json
elif [ "$CRISPR_TOOL_SCRIPT_PATH" = "" ]; then
    error_json

elif  [ "$URL_CRISPR" = "" ]; then
    error_json
else

    url_db=""
    if [ $COMMAND = "all" ];then
        url_db="-url $URL_CRISPR -tree $TREE -m $MAP_BD"
    fi
    echo python $CRISPR_TOOL_SCRIPT_PATH/pre-treatment.py $COMMAND -file $FASTA_FILE $url_db 2> ./pre_treatment.err 1> ./pre_treatment.log

    if grep "Program terminated" ./pre_treatment.log > /dev/null;
    then
    perl -ne 'if ($_ =~ /Program terminated/){
        @error_split=split(/&/);
        $msg = $error_split[1];
        $msg =~ s/\n$//;
        print "{\"emptySearch\" :  \"$msg\" }";
    }' ./pre_treatment.log > ./fail.log;
    cat ./fail.log;
    else
        perl -ne 'if ($_ =~ /SUCCESS/){
            @success_split=split(/&/);
            $msg = $success_split[1];
            $msg =~ s/\n$//;
            print "{\"Success\" :  \"$msg\" }";
        };
        ' ./pre_treatment.log > ./success.log;
        cat ./success.log
    fi
fi