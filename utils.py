def all_casings(*input_strings):
    for input_string in input_strings:
        if not input_string:
            yield ""
        else:
            first = input_string[:1]
            if first.lower() == first.upper():
                for sub_casing in all_casings(input_string[1:]):
                    yield first + sub_casing
            else:
                for sub_casing in all_casings(input_string[1:]):
                    yield first.lower() + sub_casing
                    yield first.upper() + sub_casing


def agree_with_word(num, *forms):
    if len(forms) == 1:
        forms = forms[0], forms[0] + 's'
    return forms[num != 1]
