from pyobject import *

def f():
    x, y = (1, 2)

    def g():
        z, w = (3, 4)

        def h():
            a, b = (5, 6)
            print(x, y, z, w, a, b)

        h()
        print(x, y, z, w)

    g()
    print(x, y)


def main():
    desc(f.__code__)
    f()

if __name__ == "__main__":main()