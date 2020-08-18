# Stock Monitor

Monitor and tools for Stock Exchange.


## Issues:

- Cannot open externals hyperlinks under KDE: "Timeout on server www.google.com: Socket operation timed out"
  Try changing default application handling urls in *System Settings*->*Applications*->*Web Browser* from implicit application to explicit web browser (e.g. Firefox).


### Examples of not obvious Python mechanisms

- chaining redo/undo commands (*addfavcommand.py*)
- loading of UI files and inheriting from it
- properly killing (Ctrl+C) PyQt (*sigint.py*)
- persisting and versioning classes (*persist.py*)
