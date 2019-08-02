class Relation:
    """Relation class represents the translation of user imput into a java DAO access"""
    
    def __init__(self, token, modifier, initializer, index):
        self.token = token
        self.modifier = modifier
        self.initializer = initializer
        self.index = index

    def getToken(self):
        return self.token

    def getModifier(self):
        return self.modifier

    def getInitializer(self):
        return initializer

    def getIndex(self):
        return index
    

