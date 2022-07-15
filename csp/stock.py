'''
Steps:
1. construct a model
2. decision variables:
    how many cuts of width w to make, given N orders and atmost K rolls
3. Objective function: minimize rolls and minimize waste in turn minimize cost
4. Constraints:
    1. demand satisfaction
    2. sum of consumer roll <= width of parent roll
'''
from gurobipy import GRB
import gurobipy as gp
import numpy as np
np.random.seed(0)
import math
import typer
import time

#user input of quantity and widths
def gen_data(num_orders):
    print('numorders',num_orders)
    R=[] # small rolls
    for i in range(num_orders):
      if i == 0:
        R.append([6,25])
      elif i == 1:
        R.append([12,21])
      else:
        R.append([7,26])
    return R

def get_initial_patterns(demands):
   num_orders = len(demands)
   return [[0 if j != i else 1 for j in range(num_orders)]\
           for i in range(num_orders)]

def SolVal(x):
  if type(x) is not list:
    return 0 if x is None \
      else x if isinstance(x,(int,float)) \
           else x.SolutionValue() if x.Integer() is False \
                else int(x.SolutionValue())
  elif type(x) is list:
    return [SolVal(e) for e in x]

def solve_model(demands, parent_width=120):
    num_orders = len(demands)
    solver = gp.Model()
    k,b  = bounds(demands, parent_width) 

    #create variables  
    y = [ i for i in range(k[1]) ] 
    x = [ [i,j] for i in range(num_orders) for j in range(k[1]) ]
    x1 = [x[i * 6:(i + 1) * 6] for i in range((len(x) + 6 - 1) // 6 )]
   
    # for i in range(k[1]):
    #     y1=solver.addVar(y[i],obj=1,vtype=GRB.INTEGER, name='y') 
    # x1= solver.addVar(0,x, vtype=GRB.INTEGER,name="x")   
    solver.update()
    nb = solver.addVar(k[0], k[1],vtype=GRB.INTEGER, name='nb')
    for j in range(k[1]):
        unused_widths = solver.addVar(0, parent_width,  name='unusedwidth' )
    solver.update()

    #objective: MINIMIZE COST

    #Cost = solver.Sum((j+1)*y[j] for j in range(k[1]))
    #solver.Minimize(Cost)
    cost =0
    for j in range(k[1]):
        cost = cost+ (j+1)*y[j]
    solver.setObjective(cost,GRB.MINIMIZE)
    
    #constraints
    #CONSTRAINT 1: DEMAND FULFILLMENT
    for i in range(num_orders):  
        for j in range(k[1]):
            solver.addConstr(gp.quicksum(x1[i][j]) >= demands[i][0])

    #CONSTRAINT 2: MAX SIZE LIMIT
    for j in range(k[1]):
        for i in range(num_orders):
            print('mult',i,j,demands[i][1]*x1[i][j] )
            solver.addConstrs(gp.quicksum(demands[i][1]*x1[i][j] <= parent_width*y[j] )) 

    solver.Add(parent_width*y[j] - sum(demands[i][1]*x[i][j] for i in range(num_orders)) == unused_widths[j])

    if j < k[1]-1: 
      solver.addConstr(gp.quicksum(x[i][j] for i in range(num_orders)) >= solver.addConstr(gp.quicksum(x[i][j+1] for i in range(num_orders))))

    # find & assign to nb, the number of big rolls used
    solver.addConstr(nb == solver.addConstr(gp.quicksum(y[j] for j in range(k[1]))))
    status = solver.Solve()
    numRollsUsed = SolVal(nb)

    return status, numRollsUsed


# defining the bounds
def bounds(demands, parent_width=120):
  num_orders = len(demands)
  b = []
  T = 0
  k = [0,1]
  TT = 0
  for i in range(num_orders):
    quantity, width = demands[i][0], demands[i][1]
    b.append( int(round(parent_width / width)))
    if T + quantity*width <= parent_width:
      T, TT = T + quantity*width, TT + quantity*width
    else:
      while quantity:
        if T + width <= parent_width:
          T, TT, quantity = T + width, TT + width, quantity-1
        else:
          k[1],T = k[1]+1, 0 # use next roll (k[1] += 1)
  k[0] = int(round(TT/parent_width+0.5))
  print('k: minimum big-rolls required,number of big rolls that can be consumed', k)
  print('b: sum of widths of individual small rolls (parent_width / width)', b)
  return k, b


#master problem
# def master_problem():
#     num_patterns = len(patterns)
#     solver = gp.Model("master problem")


#subproblem


#check widths
def checkWidths(demands, parent_width):
  sum=0
  for quantity, width in demands:
    sum=sum+width
    if sum > parent_width:
      print(f'Sum of Small rolls widths {sum} is greater than parent rolls width {parent_width}. Exiting')
      return False
  print(f'Sum of Small rolls widths {sum} is lesser than parent rolls width {parent_width}. Check!')
  return True

#define and call model
def StockCutter1D(child_rolls, parent_rolls,large_model=True):
    parent_width = parent_rolls[0][1]
    print(child_rolls)
    if not checkWidths(demands=child_rolls, parent_width=parent_width):
        return []
    print('child_rolls', child_rolls)
    print('parent_rolls', parent_rolls)
    if not large_model:
        consumed_big_rolls = solve_model(demands=child_rolls, parent_width=parent_width)
        status = solve_model(demands=child_rolls, parent_width=parent_width)
        numRollsUsed = solve_model(demands=child_rolls, parent_width=parent_width)
        new_consumed_big_rolls = []
        print('cbr',consumed_big_rolls)
        for big_roll in consumed_big_rolls:
            print(big_roll)
            if len(big_roll) < 2:
                # sometimes the solve_model return a solution that contanis an extra [0.0] entry for big roll
                consumed_big_rolls.remove(big_roll)
                continue
            unused_width = big_roll[0]
            subrolls = []
            for subitem in big_roll[1:]:
                if isinstance(subitem, list):
                # if it's a list, concatenate with the other lists, to make a single list for this big_roll
                    subrolls = subrolls + subitem
                else:
                    # if it's an integer, add it to the list
                    subrolls.append(subitem)
            new_consumed_big_rolls.append([unused_width, subrolls])
        consumed_big_rolls = new_consumed_big_rolls
    numRollsUsed = len(consumed_big_rolls)

    STATUS_NAME = ['OPTIMAL',
        'FEASIBLE',
        'INFEASIBLE',
        'UNBOUNDED',
        'ABNORMAL',
        'NOT_SOLVED'
        ]

    output = {
        "statusName": STATUS_NAME[status],
        "numSolutions": '1',
        "numUniqueSolutions": '1',
        "numRollsUsed": numRollsUsed,
        "solutions": consumed_big_rolls # unique solutions
    }
    print('numRollsUsed', numRollsUsed)
    print('Status:', output['statusName'])
    print('Solutions found :', output['numSolutions'])
    print('Unique solutions: ', output['numUniqueSolutions'])

def main():
    start = time.time()
    print(start)
    child_rolls = gen_data(3)
    parent_rolls = [[10, 120]] # 10 doesn't matter, its not used at the moment
    consumed_big_rolls = StockCutter1D(child_rolls, parent_rolls,large_model=False)
    print(consumed_big_rolls)
    typer.echo(f" [[Waste],[Consumed Big Rolls]]")
    typer.echo(f"{consumed_big_rolls}")
    end = time.time()
    print(end - start)

if __name__ == "__main__":
  typer.run(main)