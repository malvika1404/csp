# Cutting Stock Problem
Cutting Stock Problem (CSP) deals with planning the cutting of items (rods / sheets) from given stock items (which are usually of fixed size).


This implementation of CSP tries to answer
> How to minimize number of stock items used while cutting customer order


while doing so, it also caters
> How to cut the stock for customer orders so that waste is minimum


We use Gurobi Optimizer to see how many ways can we cut given order from fixed size Stock


## Quick Start
Install [Pipenv](https://pipenv.pypa.io/en/latest/), if not already installed
```sh
$ pip3 install --user pipenv
```


After cloning project, activate the virtual environment: 
# activate env
$ pipenv shell
```

## Run
If you run the `stock.py` file directly, it runs the example which uses 120 as length of stock Rod and generates some customer rods to cut. 