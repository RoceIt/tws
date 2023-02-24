#!/usr/bin/env python3
#
#  Copyright (c) 2011 Rolf Camps (rolf.camps@scarlet.be)\

import mypy

def main():
    grid = fill_grid()
    solved = solve(grid)
    if solved:
        print_grid(grid)
    else:
        print('can\'t solve')
    
def fill_grid():
    grid=[]
    for row in range(9):
        grid.append([0,0,0,0,0,0,0,0,0])
    while True:
        fill = mypy.get_string('hor, ver, val: ', empty=True)
        if fill:
            h,v,w = fill.split('.')
            grid[int(h)-1][int(v)-1] = int(w)
        else:
            print_grid(grid)
            if mypy.get_bool('y if ok n to change values'):
                break
    return grid

def solve(grid):
    for row_c, row in enumerate(grid):
        for col_c, column in enumerate(row):
            if column == 0:
                for value in valid_values(grid, row_c, col_c):
                    grid[row_c][col_c] = value
                    solved = solve(grid)
                    if solved:
                        return True
                else:
                    grid[row_c][col_c] = 0
                    return False
    else:
        return True

def valid_values(grid, row_c, col_c):
    row_base = (row_c // 3) * 3
    col_base = (col_c // 3) * 3
    values = {1,2,3,4,5,6,7,8,9}
    bad_values = set(grid[row_c])
    for row in range(9):
        if row in [row_base, row_base+1, row_base+2]:
            bad_values |= set(grid[row][col_base:col_base+3])
        bad_values.add(grid[row][col_c])
    return values - bad_values
                    
def print_grid(grid):
    mypy.print_list(grid, 'SOLVED')
    
if __name__ == '__main__':
    main()