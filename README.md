# SWENG-Git
Student number:15317659
Webapp to retrieve a user's github information and display aspects of that information
For instance repos and their corresponding language
Written in python3, requires Flask library and PyGithub library.
Requires the following libraries:
+ Flask
+ werkzeug.contrib.cache
+ Datetime
+ PyGithub
+ Collections
use pip install to get them.
To run the webapp simply run run.py in the repo with python3
Caches the result of the lines of code query then will check if there has been anymore commits since the last query if there has been it adds them to the current result if not then it just returns the cached results alone.