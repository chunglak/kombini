import typing as ty


def remove_duplicates(xs: ty.Iterable) -> ty.List:
    """
    Remove duplicates from iterable while maintaining initial order
    """
    seen: ty.Set = set()
    return [x for x in xs if x not in seen and not seen.add(x)]  #type:ignore


def clear_dict_empty_values(dic: ty.Dict, remove_number=False, remove_bool=False):
    """
    Remove all empty items from a dict recursively
    """
    from numbers import Number

    for k, v in list(dic.items()):
        # We don't remove numbers nor booleans
        if (isinstance(v, Number) and not remove_number) or (
            isinstance(v, bool) and not remove_bool
        ):
            continue
        elif not v:
            del dic[k]
        elif isinstance(dic[k], dict):
            clear_dict_empty_values(dic[k])
        elif isinstance(dic[k], list):
            for e in dic[k]:
                if isinstance(e, dict):
                    clear_dict_empty_values(e)
