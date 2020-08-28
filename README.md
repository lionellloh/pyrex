# PyRex 

```
 ____  _  _  ____  ____  _  _ 
(  _ \( \/ )(  _ \( ___)( \/ )
 )___/ \  /  )   / )__)  )  ( 
(__)   (__) (_)\_)(____)(_/\_)
```

[![Build Status](https://travis-ci.org/joemccann/dillinger.svg?branch=master)](https://travis-ci.org/joemccann/dillinger)

PyRex is a fuss-free way to generate a requirements file from your code base. This is an alternative method to `pip freeze` as the packages `pip` installs is seldom an equivalent set of all the third-party libraries your code base uses. 

**PyRex solves two problems:**
1) When you have more requirements than you truly need. This increases build time when deploying and takes up space. 

2) When you have less requirements than you truly need. This is common when your local machine has packages installed universally, and is not registered within your virtual environment. This can cause painful delays and retries when deploying later on.  


### Installation
PyRex current uses [pip-tools](https://github.com/jazzband/pip-tools/tree/master/piptools) to resolve dependencies. 
Other dependencies include `wcmatch` and `stdlib-list` 
Simply run `pip install -r requirements.txt` to install all the required dependencies

License
----

GPL-3.0
