def forBC(t):
    if t < 10:
        return "0" + str(t)
    else:
        return str(t)


def format(t):
    """ covert int to string a:bc:d """
    a = t // 60
    t = t - a * 60
    b = t
    return str(a) + ":" + forBC(b)


print format(100)