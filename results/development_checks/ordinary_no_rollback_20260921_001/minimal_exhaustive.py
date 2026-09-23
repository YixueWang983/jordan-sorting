import itertools,json
from oracle import oracle
from paper_jordan_sort import paper_jordan_sort_valid
counts={}
for n in range(9):
    counts[n]=0
    for values in itertools.permutations(range(n)):
        if oracle(values)['valid']:
            assert paper_jordan_sort_valid(list(values),execution_mode='minimal')==sorted(values)
            counts[n]+=1
print(json.dumps(dict(max_n=8, valid_permutations=sum(counts.values()), by_n=counts, all_passed=True),indent=2))
