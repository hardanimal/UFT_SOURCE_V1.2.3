class Animal(object):
    def __init__(self, name):
        self.name = name


class Ape(Animal):
    pass


class Human(Animal):
    def __init__(self, name, familyname):
        self.familyname = familyname
        super(Human, self).__init__(name)


class Label(object):
    def __init__(self, animal=Ape):
        if(hasattr(animal, "familyname")):
            self.mark = animal.name + "." + animal.familyname
        else:
            self.mark = animal.name

if __name__ == "__main__":
    caesar = Ape("Caesar")
    l = Label(animal=caesar)
    print l.mark

    joe = Human(name="Joe", familyname="Doe")
    l2 = Label(animal=joe)
    print l2.mark
