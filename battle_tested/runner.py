from itertools import cycle, chain
from collections import defaultdict, deque
from functools import partial

from mutators import mutate
from ammo import infinite_gc_ammo, standard

def fuzz_generator(input_type):
	for i in infinite_gc_ammo():
		yield from mutate(i, input_type)

def runner(fn, input_types):
	fuzz_generators = map(fuzz_generator, input_types)
	for args in zip(*fuzz_generators):
		try:
			yield input_types, True,  args, fn(*args)
		except Exception as ex:
			yield input_types, False, args, ex

def fuzz_test(fn, input_type_combinations):
	test_runners = cycle(runner(fn, combo) for combo in input_type_combinations)

	result_map = defaultdict(
		lambda: {
			True: deque(maxlen=16), 
			False: defaultdict(
				lambda: deque(maxlen=16)
			)
		}
	)

	for tr in test_runners:
		input_types, success, args, output = next(tr)
		if success:
			# store the input, output pair in the successful runs
			result_map[input_types][success].append((args, output))
		else:
			# store the arguments in the deque for that specific exception
			result_map[input_types][success][(type(output), output.args)].append(args)
		# return the current state of the result map to let external logic
		# decide if its necessary to continue fuzzing.
		yield result_map


if __name__ == '__main__':
	fn = lambda a, b: a + b
	for _, v in zip(range(1000000), fuzz_test(fn, ((int, str), (str, str), (int, int)))):
		pass
		#print('-')
		#print(v)

