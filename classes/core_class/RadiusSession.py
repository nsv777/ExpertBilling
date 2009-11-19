from operator import itemgetter, setitem

class RadiusSession(tuple):
    'RadiusSession(id, account_id, sessionid, speed_string, access_type, nas_id)' 

    __slots__ = () 

    _fields = ('id', 'account_id', 'sessionid', 'speed_string', 'access_type', 'nas_id') 

    def __new__(cls, id, account_id, sessionid, speed_string, access_type, nas_id):
        return tuple.__new__(cls, (id, account_id, sessionid, speed_string, access_type, nas_id)) 

    @classmethod
    def _make(cls, iterable, new=tuple.__new__, len=len):
        'Make a new RadiusSession object from a sequence or iterable'
        result = new(cls, iterable)
        if len(result) != 6:
            raise TypeError('Expected 6 arguments, got %d' % len(result))
        return result 

    def __repr__(self):
        return 'RadiusSession(id=%r, account_id=%r, sessionid=%r, speed_string=%r, access_type=%r, nas_id=%r)' % self 

    def _asdict(t):
        'Return a new dict which maps field names to their values'
        return {'id': t[0], 'account_id': t[1], 'sessionid': t[2], 'speed_string': t[3], 'access_type': t[4], 'nas_id': t[5]} 

    def _replace(self, **kwds):
        'Return a new RadiusSession object replacing specified fields with new values'
        result = self._make(map(kwds.pop, ('id', 'account_id', 'sessionid', 'speed_string', 'access_type', 'nas_id'), self))
        if kwds:
            raise ValueError('Got unexpected field names: %r' % kwds.keys())
        return result 

    def __getnewargs__(self):
        return tuple(self) 

    id = property(itemgetter(0))
    account_id = property(itemgetter(1))
    sessionid = property(itemgetter(2))
    speed_string = property(itemgetter(3))
    access_type = property(itemgetter(4))
    nas_id = property(itemgetter(5))