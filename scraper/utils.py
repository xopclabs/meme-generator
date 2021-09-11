from typing import Dict, Union


StatDict = Dict[str, Union[int, float]]


def print_stats(domain: str, stat: StatDict) -> None:
    print((
            f'{domain}: +{stat["n_posts"]} posts, '
            f'+{stat["n_pics"]} pics ({stat["size"]:.2f} MB)'
    ))


def accumulate_stats(a: StatDict, b: StatDict) -> StatDict:
    for key in a.keys():
        a[key] += b[key]
    return a
