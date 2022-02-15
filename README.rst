iFit Sync
---------
Automatically parse running FIT files that include structured workouts and convert them as a submissions within the iFit ecosystem. This script was created specifically to aid in the process of converting structured running workouts from TrainingPeaks over to the iFit platform. Certain NordicTrack treadmills allow for automated speed/incline adjustments based on a workout file. iFit provides a workout builder, but it's cumbersome to use. This script speeds up the process by taking already published data within a FIT file and converts it to iFit formats. 

Installation
-------------
This script can be ran directly from within the repository. The package depends on several external libraries. If these are not present, they will be installed automatically. A ``requirements.txt`` file is included in the repository which outlines these dependencies in detail.

Setup
-----
Users are required to have a valid account within the iFit platform.

    $ python ifit_sync setup -e <EMAIL> -p <PASSWORD>

Configuration parameters are stored in **$HOME/.config/ifit_sync/config.json**.

Usage
-----
Every command-line script has several sub-commands that may be passed to it. The
commands usage may be described with the ``-h/--help`` option.

For example::

    usage: ifit_sync.py [-h] {setup,sync} ...

    positional arguments:
      {setup,sync}
        sync        Sync a FIT file to iFit

    optional arguments:
      -h, --help    show this help message and exit
      
      
Considerations
---------------
This code is presented "as-is" and does not do much in the form of error handling. The authentication and submission process leverage scraping which relies on the iFit website not changing in substantial ways. Over time, this script may mature, though there is no committed roadmap planned.
