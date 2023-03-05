# SXCTrack
SXCTrack is a project which scrapes data from fillmore.homelinux.net/cgi-bin/Athletes and other related pages into a JSON format to be displayed on sxctrack.com

## Files included:
### oneStep.py
Is the entire update checking, web scraping, and upload process baked into one python file.

It initially connects to an FTP server to check which meets are already on the sxctrack.com website

Then it checks a list of meets on fillmore, and if there are any more than there are "locally" (already on sxctrack), then it will add these missing meets to be scraped.

* need to also re-scrape any meet less than two weeks old, because coaches often change data after the first upload

Finally, it incorporated into the existing data that was fetched from sxctrack.com initially, and the python file regenerates all the files for sxctrack.

Each file is then uploaded to a "temp" directory on sxctrack.
Once this is done, it deletes everything in the "old" directory, moves everything from "curr" to "old", and then copies "temp" to "curr". I call this the great shuffle.

The "curr" directory is fetched by front-end ajax, and the "old" directory and "temp" directories are kept in case something goes terribly wrong, and I can always view an archived version of the website's data. The file structure has not changed since I devised it, they are all backwards and forwards compatible with the front end.

#### 2/22/2023 addition:
* Added -neuter, -nuclear, implemented -textarg to further fine-tune one-time script runs
* Added creation of report.txt. Doesn't need to be parsed as json, but didn't bother adjusting ftpStor function.

#### 3/04/2023:
* fixed bug caused by new fresh_ids concept and old array merging process
