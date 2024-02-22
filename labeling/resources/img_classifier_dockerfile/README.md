Suppose that:

* You unpacked the archive with the task (where this file is located)

* You are in the task directory (that appeared after the task unpacking)

* You have Docker installed on your computer

* You have the Internet connection

Read the manifest file (manifest.pdf)

Build the container for labeling and run it

```bash
docker build -t labeling .

docker run -ti --rm -p 5555:5555 labeling 
```

Open localhost:5555 in your browser. 