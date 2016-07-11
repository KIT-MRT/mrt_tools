# Update mrt_tools
rsync -r -u -h -v --links --delete --exclude "*.pyc"  ../../setup.py ../../requirements.txt files/
rsync -r -u -h -v --links --delete --exclude "*.pyc"   ../../mrt_tools files/mrt_tools

# Build image
docker build $1 --force-rm -t mrt_build_dev .
