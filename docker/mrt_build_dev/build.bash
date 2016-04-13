# Update mrt_tools
rsync -r -u -h --progress --links  ../../mrt_tools files/
# Build image
docker build $1 --force-rm -t mrt_build_dev .
