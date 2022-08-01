from gurobipy import *
import gurobipy as gp
from gurobipy import GRB
import typer 
import matplotlib as plt
import time

EPS = 1.e-6

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
    rolls = solveMaster(cut,parent_width,w,q,num_orders)
    print(rolls)
    return cut,parent_width,w,q,num_orders

#CSP Subproblem
def solveSubProblem(solver,x,orders,K,cut,parent_width,w,q,num_orders):
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
        for j in range(int(x[k].X + .5)):
            rolls.append(sorted([w[i] for i in range(num_orders) if cut[k][i]>0 for j in range(cut[k][i])]))
            waste.append(parent_width - sum(rolls[j]))
    rolls.sort() 
    print (len(rolls), "rolls:" )
    print("[[Rolls][Waste]")
    return rolls,waste
    
#CSP Master Problem
def solveMaster(cut,parent_width,w,q,num_orders):
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
    a = solveSubProblem(solver,x,orders,K,cut,parent_width,w,q,num_orders)
    return a

def main():
    start=time.time()
    print ("\n\n\nCutting stock problem:")
    child_rolls = gen_data(3)
    parent_rolls = [[10, 120]]
    print (child_rolls)
    parent_width = parent_rolls[0][1]
    print("parent width", parent_width)
    if not checkWidths(demands=child_rolls, parent_width=parent_rolls[0][1]):
        return []
    cuttingStock(parent_rolls,child_rolls)
    end = time.time()
    print(end-start)

if __name__ == "__main__":
    typer.run(main) 
    
    
   