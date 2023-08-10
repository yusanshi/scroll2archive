# scroll2archive

Scroll a very long webpage (or something similar), save as a long PNG file, split into pages and save as PDF.

How it works:

1. Take a screenshot, scroll, take another screenshot, scroll again.... In this way, we get a list of screenshots (called frames).
2. Stitch the frames with a very simple (but works well for webpages) algorithm. Save it as a long PNG file.
3. Split the long PNG into many PNG images, each as a page. We use a simple algorithm to make sure the cropping occurs at the gaps of text or images (but may not always work as expected).
4. Create a PDF file from these PNG pages.

See the comments in the code and `config.yaml` for details.
