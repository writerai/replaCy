"""
This module contains predicates which influence what counts as a match
If the predicate (function) returns True, the match will be ignored
"""
import operator
import re
import sys
from typing import Callable, List, Union

from spacy.tokens.doc import Doc

SpacyMatchPredicate = Callable[[Doc, int, int], bool]


def _check_args(x):
    """
    get calling function name to give a nice error message
    """
    caller = sys._getframe(1).f_code.co_name
    if not isinstance(x, (list, str)):
        raise ValueError(f"args of {caller} should be a string or list of strings")


def compose(f, g):
    return lambda doc, start, end: f(g(doc, start, end))


def neg(f):
    # function negation, ex. neg(preceded_by_pos(pos))
    return compose(operator.not_, f)


def succeeded_by_phrase(phrases) -> SpacyMatchPredicate:
    _check_args(phrases)
    if not isinstance(phrases, list):
        phrases = [phrases]

    def _succeeded_by_phrase(doc, start, end):
        if end >= len(doc):
            return False
        return any([doc[end:].text.lower().startswith(p.lower()) for p in phrases])

    return _succeeded_by_phrase


def preceded_by_phrase(phrases) -> SpacyMatchPredicate:
    _check_args(phrases)
    if not isinstance(phrases, list):
        phrases = [phrases]

    def _preceded_by_phrase(doc, start, end):
        if start <= 0:
            return False
        return any([doc[:start].text.lower().endswith(p.lower()) for p in phrases])

    return _preceded_by_phrase


def succeeded_by_pos(pos) -> SpacyMatchPredicate:
    _check_args(pos)
    if not isinstance(pos, list):
        pos = [pos]

    def _succeeded_by_pos(doc, start, end):
        if end >= len(doc):
            return False
        bools = [doc[end].pos_ == p for p in pos]
        return any(bools)

    return _succeeded_by_pos


def preceded_by_pos(pos) -> SpacyMatchPredicate:
    _check_args(pos)
    if not isinstance(pos, list):
        pos = [pos]

    def _preceded_by_pos(doc, start, end):
        if start <= 0:
            return False
        bools = [doc[start - 1].pos_ == p for p in pos]
        return any(bools)

    return _preceded_by_pos


def succeeded_by_lemma(lemma) -> SpacyMatchPredicate:
    _check_args(lemma)
    if not isinstance(lemma, list):
        lemma = [lemma]

    def _succeeded_by_lemma(doc, start, end):
        if end >= len(doc):
            return False
        bools = [doc[end].lemma_ == l for l in lemma]
        return any(bools)

    return _succeeded_by_lemma


def preceded_by_lemma(lemma, distance=1) -> SpacyMatchPredicate:
    _check_args(lemma)
    if not isinstance(lemma, list):
        lemma = [lemma]

    def _preceded_by_lemma(doc, start, end):
        if start < distance:
            return False
        bools = [doc[start - distance].lemma_ == l for l in lemma]
        return any(bools)

    return _preceded_by_lemma


def succeeded_by_dep(dep) -> SpacyMatchPredicate:
    _check_args(dep)
    if not isinstance(dep, list):
        dep = [dep]

    def _succeeded_by_dep(doc, start, end):
        if end >= len(doc):
            return False
        bools = [doc[end].dep_ == d for d in dep]
        return any(bools)

    return _succeeded_by_dep


def preceded_by_dep(dep) -> SpacyMatchPredicate:
    _check_args(dep)
    if not isinstance(dep, list):
        dep = [dep]

    def _preceded_by_dep(doc, start, end):
        if start <= 0:
            return False
        bools = [doc[start - 1].dep_ == d for d in dep]
        return any(bools)

    return _preceded_by_dep


def sentence_has(
    phrases: Union[str, List[str]], case_sensitive=False
) -> SpacyMatchPredicate:
    _check_args(phrases)
    if not isinstance(phrases, list):
        phrases = [phrases]

    def _sentence_has(doc, start, end):
        if case_sensitive:
            return any(p in doc.text for p in phrases)
        return any(p.lower() in doc.text.lower() for p in phrases)

    return _sentence_has


def surrounded_by_phrase(phrase) -> SpacyMatchPredicate:
    def _surrounded_by_hook(doc, start, end):
        if start <= 0 or end >= len(doc):
            return False
        precedes = doc[:start].text.lower().endswith(phrase.lower())
        follows = doc[end:].text.lower().startswith(phrase.lower())
        return precedes and follows

    return _surrounded_by_hook


def part_of_compound() -> SpacyMatchPredicate:
    def _word_is_part_of_compound_hook(doc, start, end):
        head = doc[start]
        is_compound = head.dep_ == "compound"
        is_part_of_compound = any(
            [t.dep_ == "compound" and t.head == head for t in doc]
        )
        return is_compound or is_part_of_compound

    return _word_is_part_of_compound_hook


def relative_x_is_y(
    children_or_ancestors: str, pos_or_dep: str, value: Union[str, List[str]]
) -> SpacyMatchPredicate:
    """
    This hook looks at all the tokens in a matched span to determine
    whether any of the children or the first ancestor have a given .pos_ or
    .dep_. This replaces the implementation of the Dependency Matcher in
    the previous version by looking at token.children or token.ancestors in
    the matched span.

    Example hook:
            {
            "name": "relative_x_is_y",
            "kwargs": {
                "children_or_ancestors": "children",
                "pos_or_dep": "dep",
                "value": "pobj"
            },
            "match_if_predicate_is": false
        }
    """

    if not isinstance(value, list):
        value = [value]

    if not isinstance(children_or_ancestors, str):
        raise TypeError("children_or_ancestors must be a string!")

    if not isinstance(pos_or_dep, str):
        raise TypeError("pos_or_dep must be a string!")

    if children_or_ancestors not in ["children", "ancestors"]:
        raise ValueError(
            "children_or_ancestors must be set to either `children` or `ancestors`"
        )

    if pos_or_dep not in ["pos", "dep", "tag"]:
        raise ValueError("pos_or_dep must be set to either `pos`, `dep`, or `tag`!")

    def _in_children(doc, start, end):
        if end >= len(doc):
            return False
        for val in value:
            match_span = doc[start:end]
            if pos_or_dep == "pos":
                return any(
                    [child.pos_ == val for tok in match_span for child in tok.children]
                )
            elif pos_or_dep == "dep":
                return any([child.dep_ == val for tok in match_span for child in tok.children])
            elif pos_or_dep == "tag":
                return any([child.tag_ == val for tok in match_span for child in tok.children])

    def _in_ancestors(doc, start, end):
        if end >= len(doc):
            return False
        for val in value:
            match_span = doc[start:end]
            if pos_or_dep == "pos":
                for t in match_span:
                    ancestor = list(t.ancestors)[0] if len(list(t.ancestors)) else None
                    if ancestor and ancestor.pos_ == val:
                        return True
                return False
            if pos_or_dep == "dep":
                for t in match_span:
                    ancestor = list(t.ancestors)[0] if len(list(t.ancestors)) else None
                    if ancestor and ancestor.dep_ == val:
                        return True
                return False
            if pos_or_dep == "tag":
                for t in match_span:
                    ancestor = list(t.ancestors)[0] if len(list(t.ancestors)) else None
                    if ancestor and ancestor.tag_ == val:
                        return True
                return False

    if children_or_ancestors == "children":
        return _in_children

    if children_or_ancestors == "ancestors":
        return _in_ancestors


def part_of_phrase(phrase) -> SpacyMatchPredicate:
    def _part_of_phrase(doc, start, end):
        matched = doc[start:end].text.lower()
        parts = phrase.split(matched)
        for i in range(len(parts) - 1):
            firstpart = ""
            secondpart = ""
            for part in parts[: i - 1]:
                firstpart += part
            for part in parts[i + 1 :]:
                secondpart += part
            precedes = doc.text.lower()[: doc[start:end].start_char].endswith(firstpart)
            follows = doc.text.lower()[doc[start:end].end_char :].startswith(secondpart)
            if precedes and follows:
                return True
        return False

    return _part_of_phrase


def succeeded_by_num() -> SpacyMatchPredicate:
    def _succeeded_by_num(doc, start, end):
        if end >= len(doc):
            return False
        return doc[end].like_num or doc[end].pos_ == "NUM" or doc[end].is_digit

    return _succeeded_by_num


def succeeded_by_currency() -> SpacyMatchPredicate:
    def _succeeded_by_currency(doc, start, end):
        if end >= len(doc):
            return False
        return doc[end].is_currency

    return _succeeded_by_currency


def debug_hook(match_name: str) -> SpacyMatchPredicate:
    """
    Don't use this manually.
    if debug is set (i.e. ReplaceMatcher.debug), then run utils.attach_debug_hook on your match_dict when you load it
    it will return a new match_dict with the debug hook attached to each match
    """

    def _print_match(doc: Doc, start: int, end: int):
        print(
            f"DEBUG:    {match_name} matched '{doc[start: end].text}'    token indices {start}:{end}"
        )
        return True

    return _print_match


def preceded_by_space() -> SpacyMatchPredicate:
    def _preceded_by_space(doc, start, end):
        span = doc[start:end]
        return doc.text[span.start_char - 1] == " "

    return _preceded_by_space


def preceded_by_punct() -> SpacyMatchPredicate:
    def _preceded_by_punct(doc, start, end):
        if start == 0:
            return False
        previous_token = doc[start - 1]
        return previous_token.is_punct

    return _preceded_by_punct


def preceded_by_num() -> SpacyMatchPredicate:
    def _preceded_by_number(doc, start, end):
        if start == 0:
            return False
        previous_token = doc[start - 1]
        return (
            previous_token.like_num
            or previous_token.pos_ == "NUM"
            or previous_token.is_digit
        )

    return _preceded_by_number


def preceded_by_currency() -> SpacyMatchPredicate:
    def _preceded_by_currency(doc, start, end):
        if start == 0:
            return False
        previous_token = doc[start - 1]
        return previous_token.is_currency

    return _preceded_by_currency


def preceded_by_token(token) -> SpacyMatchPredicate:
    token_list = token if isinstance(token, list) else [token]

    def _preceded_by_token(doc, start, end):
        if start == 0:
            return False
        previous_token = doc[start - 1]
        return any([previous_token.lower_ == t.lower() for t in token_list])

    return _preceded_by_token


def succeeded_by_token(token) -> SpacyMatchPredicate:
    token_list = token if isinstance(token, list) else [token]

    def _succeeded_by_token(doc, start, end):
        if end == len(doc):
            return False
        next_token = doc[end]
        return any([next_token.lower_ == t.lower() for t in token_list])

    return _succeeded_by_token


def preceded_by_tag(tag) -> SpacyMatchPredicate:
    tag_list = tag if isinstance(tag, list) else [tag]

    def _preceded_by_tag(doc, start, end):
        if start == 0:
            return False
        previous_token = doc[start - 1]
        return any([previous_token.tag_ == t for t in tag_list])

    return _preceded_by_tag


def preceded_by_regex(regex, sensitive=False) -> SpacyMatchPredicate:
    def _preceded_by_regex(doc, start, end):
        if start == 0:
            return False
        previous_token = doc[start - 1]
        flags = 0 if sensitive == True else re.IGNORECASE
        return re.search(regex, previous_token.text, flags) is not None

    return _preceded_by_regex


def succeeded_by_tag(tag) -> SpacyMatchPredicate:
    tag_list = tag if isinstance(tag, list) else [tag]

    def _succeeded_by_tag(doc, start, end):
        if end == len(doc):
            return False
        next_token = doc[end]
        return any([next_token.tag_ == t for t in tag_list])

    return _succeeded_by_tag


def succeeded_by_regex(regex, sensitive=False) -> SpacyMatchPredicate:
    def _succeeded_by_regex(doc, start, end):
        if end == len(doc):
            return False
        next_token = doc[end]
        flags = 0 if sensitive == True else re.IGNORECASE
        return re.search(regex, next_token.text, flags) is not None

    return _succeeded_by_regex


def succeeded_by_same_token() -> SpacyMatchPredicate:
    def _succeeded_by_same_token(doc, start, end):
        if end == len(doc):
            return False
        token = doc[start]
        next_token = doc[end]
        return token.lower_ == next_token.lower_

    return _succeeded_by_same_token


def succeeded_by_punct() -> SpacyMatchPredicate:
    def _succeeded_by_punct(doc, start, end):
        if end == len(doc):
            return False
        next_token = doc[end]
        return next_token.is_punct

    return _succeeded_by_punct


def succeeded_by_word() -> SpacyMatchPredicate:
    def _succeeded_by_word(doc, start, end):
        if end == len(doc):
            return False
        next_token = doc[end]
        return (
            not next_token.is_punct
            and not next_token.is_digit
            and not next_token.is_space
        )

    return _succeeded_by_word


def is_start_of_sentence() -> SpacyMatchPredicate:
    return lambda doc, start, end: doc[start].is_sent_start


def is_end_of_sentence() -> SpacyMatchPredicate:
    return lambda doc, start, end: end == len(doc) or doc[end].is_sent_end


def sentence_ends_with(phrase) -> SpacyMatchPredicate:
    def _sentence_ends_with(doc, start, end):
        return doc[end:].text.lower().strip().endswith(phrase.lower())

    return _sentence_ends_with


# for compatibility with a previous version with spelling errors
# point incorrectly spelled versions to correct versions
# eventually deprecate these
preceeded_by_phrase = preceded_by_phrase
preceeded_by_pos = preceded_by_pos
preceeded_by_dep = preceded_by_dep
