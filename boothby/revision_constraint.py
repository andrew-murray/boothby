import re

"""
    FIXME:
    So http://ant.apache.org/ivy/history/latest-milestone/settings/version-matchers.html
    contains details of what is supported.

    Notes in order of precedence that I should address
    X) * is nonsense
    X) + is only supported as a terminator [prefix]+
    3) While I don't support version ranges right now
       - [1.0,2.0]
       - ]1.0,2.0[
       - (,2.0]
    4) You can define
       - latest.integration, latest.milestone, latest.release
       - latest being a keyword, and release being a status,
         where the above are pre-defined statuses, but you can define your own
    5) You can define local regex/glob functions in the ivy file, strangely


    Although 3, I don't intend to support in my next code iteration.
    And 4/5 I will probably never support.
    I think this understanding justifies a rewrite of this code.
"""
def contains_dynamic_characters(mod):
    return any(
        (c in mod) for c in "[]()+"
    )

def contains_unsupported_dynamic_characters(mod):
    return any(
        (c in mod) for c in "[]()"
    )

def is_fixed(mod):
    # the characters being checked, are those associated with dynamic
    #  revisions in ivy
    return not bool(contains_dynamic_characters(mod))

def make_constraint_regex(constraint):
    if contains_unsupported_dynamic_characters(constraint):
        raise Exception(
            "Unsupported ivy features used. " +
            "The only dynamic revision constraint currently supported is [prefix]+." +
            ""
        )
    # this will have to be more complicated later, because
    # http://ant.apache.org/ivy/history/latest-milestone/settings/latest-strategies.html
    # though realistically I dont dramatically care about those features either
    # I **think** string order is enough for all my use cases
    # which are x.y.z_b or x.y.z or "some_fixed_revision_with_numbers_and_chars"
    if constraint[-1] == "+":
        return "^" + constraint.replace("+", ".*")+ "$"
    else:
        return "^" + constraint + "$"

def make_constraint_functor(constraint):
    comp = re.compile(make_constraint_regex(constraint))
    return lambda k : bool(comp.match(k))
