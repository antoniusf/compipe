import math

def add(vec_a, vec_b):
    return [vec_a[0]+vec_b[0], vec_a[1]+vec_b[1]]

def sub(vec_a, vec_b):
    return [vec_a[0]-vec_b[0], vec_a[1]-vec_b[1]]

def mul(vec, sca):
    return [vec[0]*sca, vec[1]*sca]

def inner(vec_a, vec_b):
    return vec_a[0]*vec_b[0]+vec_a[1]*vec_b[1]

def abs(vec):
    return math.sqrt(vec[0]**2+vec[1]**2)

def norm(vec):
    length = abs(vec)
    return mul(vec, 1/length)

def vecint(vec):
    return [int(vec[0]), int(vec[1])]
