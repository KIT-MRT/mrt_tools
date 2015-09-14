_MRT_COMPLETE=source mrt
for command in $(ls mrt_py_tools/commands/*.py); do
    cmd=$(basename $command)
    cmd="${cmd%.*}"
    if [ ! "$cmd" == "__init__" ]; then
        alias mrt_$cmd="mrt $cmd"
    fi
done