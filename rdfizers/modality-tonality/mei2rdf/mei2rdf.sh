SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

for f in $MEI_DIR/*.mei
do
    echo $f
    python3 $SCRIPT_DIR/main.py \
        --input_mei_file $f \
        --cache $CACHE \
        --output_mei_folder $OUTPUT_MEI_FOLDER \
        --output_ttl_folder $OUTPUT_TTL_FOLDER
done