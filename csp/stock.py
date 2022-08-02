from gurobipy import *
import gurobipy as gp
from gurobipy import GRB
import typer 
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import time

EPS = 1.e-6

# Randomly generate input data

# def gen_data(num_orders):
#     print('numorders',num_orders)
#     print("child_rolls: [quantity, width]")
#     R=[] # small rolls
#     for i in range(num_orders):
#       R.append([randint(20,100), randint(5,80)])
#     return R

#manually enter data for testing
def gen_data(num_orders):
    print('numorders',num_orders)
    print("child_rolls: [quantity, width]")
    R=[] # small rolls
    for i in range(num_orders):
      if i == 0:
        R.append([6,25])
      elif i == 1:
        R.append([12,21])
      else:
        R.append([7,26])
    return R

def checkWidths(demands, parent_width):
  sum=0
  for quantity, width in demands:
    sum=sum+width
    if sum > parent_width:
      print(f'Sum of Small rolls widths {sum} is greater than parent rolls width {parent_width}. Exiting')
      return False
  print(f'Sum of Small rolls widths {sum} is lesser than parent rolls width {parent_width}. Check!')
  return True

# Column Generation method - 
# small subset of the variables is used initially and sequentially adds more columns
def cuttingStock(parent_rolls,child_rolls):
    cut = []
    parent_width = parent_rolls[0][1]
    num_orders = len(child_rolls)

    q=[]
    for i in range(num_orders):
        q.append(child_rolls[i][0])
    w=[]
    for i in range(num_orders):
        w.append(child_rolls[i][1])

#generate initial set of patterns
    for i in range(num_orders):
        pat = [0]*num_orders
        pat[i] = int(parent_width/w[i])
        cut.append(pat) 
    print('initial patterns generated: ',cut)
    solveMaster(cut,parent_width,w,q,num_orders, child_rolls)
    return cut,parent_width,w,q,num_orders

#CSP Subproblem
def solveSubProblem(solver,x,orders,K,cut,parent_width,w,q,num_orders, child_rolls):
    print("subproblem ")
    iter =0
    while 1:
        iter += 1
        relax = solver.relax()
        relax.optimize()
        pi = [rel.Pi for rel in relax.getConstrs()] # keep dual variables
# Knapsack Subproblem
        sub_solver = gp.Model("Subproblem_Knapsack")   # knapsack sub-problem
        sub_solver.ModelSense=-1   # maximize
        y = {}
        for i in range(num_orders):
            y[i] = sub_solver.addVar(obj=pi[i], ub=q[i], vtype=GRB.INTEGER, name="y[%d]"%i)
        sub_solver.update()

        lin = gp.LinExpr(w, [y[i] for i in range(num_orders)])
        sub_solver.addConstr(lin, "<", parent_width, name="width")
        sub_solver.setObjective(gp.quicksum(pi[i]*y[i] for i in range(num_orders)), GRB.MAXIMIZE)
        sub_solver.update()
        sub_solver.optimize()
        if sub_solver.ObjVal < 1+EPS: # break if no more columns
            break

        pat = [int(y[i].X+0.5) for i in y]	
        cut.append(pat)
        print('Patterns',pat)
        
        # add new column to the master problem
        col = gp.Column()
        for i in range(num_orders):
            if cut[K][i] > 0:
                col.addTerms(cut[K][i], orders[i])
        x[K] = solver.addVar(obj=1, vtype=GRB.INTEGER, name="x[%d]"%K, column=col)
        solver.update() 
        K += 1
    solver.optimize()
    rolls = []
    waste =[]
    for k in x:
        for j in range(int(x[k].X + 0.5)):
            rolls.append(sorted([w[i] for i in range(num_orders) if cut[k][i]>0 for j in range(cut[k][i])]))
            waste.append(parent_width - sum(rolls[j]))
    rolls.sort() 
    print (len(rolls), "rolls:" )
    print("[[Rolls][Waste]", rolls, waste)
    end = time.time()
    print(end)
    drawGraph(rolls, waste,child_rolls, parent_width)
    
#CSP Master Problem
def solveMaster(cut,parent_width,w,q,num_orders, child_rolls):
    print("master problem")
    K = len(cut)
    solver = gp.Model("Cutting_Stock_Master_Problem") # master problem
    x = {}
    for k in range(K):
        x[k] = solver.addVar(obj=1, vtype=GRB.INTEGER, name="x[%d]"%k)
    solver.update()
    orders={}
    for i in range(num_orders):
        coef = [cut[k][i] for k in range(K) if cut[k][i] > 0]
        var = [x[k] for k in range(K) if cut[k][i] > 0]
        orders[i] = solver.addConstr(gp.LinExpr(coef,var), ">", q[i], name="Order[%d]"%i)
    solver.setObjective(gp.quicksum(x[k] for k in range(K)), GRB.MINIMIZE)
    solver.update()
    a = solveSubProblem(solver,x,orders,K,cut,parent_width,w,q,num_orders, child_rolls)
    return a

def drawGraph(rolls, waste,child_rolls, parent_width ):
  xSize = parent_width
  ySize = 10 * len(rolls)
  fig,ax = plt.subplots(1)
  plt.xlim(0, xSize)
  plt.ylim(0, ySize)
  plt.gca().set_aspect('equal', adjustable='box')
    
  # print coords
  coords = []
  colors = ['r', 'g', 'b', 'y', 'brown', 'violet', 'pink', 'gray', 'orange','b','y']
  colorDict = {}
  i = 0
  for quantity, width in child_rolls:
    colorDict[width] = colors[i % 11]
    print(colorDict)
    i+= 1
  y1 = 0
  for i, roll in enumerate(rolls):
    unused = waste
    small_roll = roll
    x1=0
    x2 = 0
    y2 = y1 + 8
    for j, small_roll in enumerate(small_roll):
      x2 = x2 + small_roll
      width = abs(x1-x2)
      height = abs(y1-y2)
      rect_shape = patches.Rectangle((x1,y1), width, height, facecolor=colorDict[small_roll], label=f'{small_roll}')
      ax.add_patch(rect_shape)
      x1 = x2
    # if len(unused) > 0:
    #   width = unused
    #   rect_shape = patches.Rectangle((x1,y1), width, height, facecolor='black', label='Unused')
    #   ax.add_patch(rect_shape)
    y1 += 10

  plt.show()


def main():
    start=time.time()
    print(start)
    print ("\n\n\nCutting stock problem:")
    child_rolls = gen_data(3)
    parent_rolls = [[10, 120]]
    print (child_rolls)
    parent_width = parent_rolls[0][1]
    print("parent width", parent_width)
    if not checkWidths(demands=child_rolls, parent_width=parent_rolls[0][1]):
        return []
    cuttingStock(parent_rolls,child_rolls)
  
if __name__ == "__main__":
    typer.run(main) 
    
    
   