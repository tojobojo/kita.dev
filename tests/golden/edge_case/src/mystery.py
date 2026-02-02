# what is this file for?
# created: ???
# author: ???

class Mystery:
    def __init__(self):
        self._state = {}
    
    def update(self, k, v):
        self._state[k] = v
    
    def get(self, k):
        return self._state.get(k)
    
    def clear(self):
        self._state = {}

def mystery_function(a, b, c):
    m = Mystery()
    m.update('a', a)
    m.update('b', b)
    m.update('c', c)
    return m.get('a') + m.get('b') * m.get('c')

# use this somewhere?
CONSTANT = 12345
