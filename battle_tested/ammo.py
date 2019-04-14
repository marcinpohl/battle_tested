import gc, sys
from functools import wraps, partial

eprint = partial(print, file=sys.stderr, flush=True)

class standard:
	types = { bool, bytearray, bytes, complex, dict, float, int, list, set, str, tuple }
	containers = { bytearray, dict, dict, list, set, tuple }
	objects = { bool, bytes, complex, float, int, str }
	defaults = [i() for i in types]

class never_repeat_ids(set):
	''' returns an empty iterable if the input argument has already been seen '''
	def __call__(self, fn):
		assert callable(fn), fn
		@wraps(fn)
		def wrapper(arg):
			if id(arg) not in self:
				self.add(id(arg))
				yield from fn(arg)
		wrapper.clear_cache = self.clear
		return wrapper

@never_repeat_ids()
def extract_objects(o):
	type_o = type(o)
	if o is None:
		yield None
	elif type_o in standard.types:
		if type_o in standard.containers:
			if type_o is dict:
				yield {k:v for k,v in o.items() if type(k) in standard.objects and type(v) in standard.objects}
				for k in o:
					yield from extract_objects(k)
					yield from extract_objects(o[k])
			else:
				yield type_o(i for i in o if type(i) in standard.objects)
				for i in o:
					yield from extract_objects(i)
		else:
			if type_o in standard.objects:
				yield o

def ammo_from_gc():
	for o in gc.get_objects():
		if type(o) in standard.types:
			yield from extract_objects(o)
	extract_objects.clear_cache()

def infinite_gc_ammo():
	while 1:
		yield from ammo_from_gc()

if __name__ == '__main__':

	collected_types = set()

	eprint('running through ammo_from_gc to get initial test variables')
	for i,v in enumerate(ammo_from_gc()):
		collected_types.add(type(v))
		eprint(i, type(v).__name__, v)

	eprint('validating that at least one of every standard type was collected')
	for t in standard.types:
		assert t in collected_types, t.__name__ 

	eprint('success!')