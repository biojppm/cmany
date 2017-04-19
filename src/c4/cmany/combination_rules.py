import re


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
class CombinationRule:
    """x=exclude / i=include"""

    def __init__(self, x_or_i, what, patterns):
        assert x_or_i in ('x', 'i')
        assert what in (
            'builds_any', 'builds_all',
            'systems', 'architectures', 'compilers', 'build_types', 'variants'
        )
        self.x_or_i = x_or_i
        self.what = what
        self.patterns = patterns

    def is_valid(self, s, a, c, t, v):
        s = s.name
        a = a.name
        c = c.name
        t = t.name
        v = v.name

        result = True
        if self.what in ('builds_any', 'builds_all'):
            matches_all = True
            matches_none = True
            matches_any = False
            for pattern in self.patterns:
                if __class__.pattern_matches(pattern, s, a, c, t, v):
                    matches_any = True
                    matches_none = False
                else:
                    matches_all = False
            if self.x_or_i == 'x':
                if matches_none:
                    result = True
                else:
                    if self.what == 'builds_any':
                        result = not matches_any
                    elif self.what == 'builds_all':
                        result = not matches_all
                    else:
                        raise Exception("never reach this point")
            elif self.x_or_i == 'i':
                if matches_none:
                    result = False
                else:
                    if self.what == 'builds_any':
                        result = matches_any
                    elif self.what == 'builds_all':
                        result = matches_all
                    else:
                        raise Exception("never reach this point")
            return result
        else:
            if self.what == 'systems':
                which = s
            elif self.what == 'architectures':
                which = a
            elif self.what == 'compilers':
                which = c
            elif self.what == 'build_types':
                which = t
            elif self.what == 'variants':
                which = v
            if not isinstance(which, str):
                which = which.name
            #
            in_patterns = which in self.patterns
            if self.x_or_i == 'x':
                result = not in_patterns
            elif self.x_or_i == 'i':
                result = in_patterns
            return result

    @staticmethod
    def pattern_matches(pattern, s, a, c, t, v):
        from .build import Build
        #for i in (s, a, c, t, v):
        #    if re.search(pattern, str(i)):
        #        # print("GOT A MATCH:", self.rule, i)
        #        return True
        s = Build.get_tag(s, a, c, t, v)
        # print(s, type(s))
        if re.search(pattern, s):
            # print("GOT A TAG MATCH:", self.rule, s)
            return True
        # print("NO MATCH:", self.rule, s)
        return False


# -----------------------------------------------------------------------------
class CombinationRules:

    def __init__(self, specs):
        self.rules = []
        for x_or_i, any_or_all, rules in specs:
            crc = CombinationRule(x_or_i, any_or_all, rules)
            self.rules.append(crc)

    def is_valid(self, s, a, c, t, v):
        result = 1
        for r in self.rules:
            result = result & r.is_valid(s, a, c, t, v)
        return result

    def valid_combinations(self, systems, archs, comps, types, variants):
        combs = []
        for s in systems:
            for a in archs:
                for c in comps:
                    for t in types:
                        for v in variants:
                            valid = True
                            if not self.is_valid(s, a, c, t, v):
                                valid = False
                            for item in (s, a, c, t, v):
                                crs = item.combination_rules
                                #for idx, r in enumerate(crs.rules):
                                #    print((s, a, c, t, v), ":", item, ": rule[{}]".format(idx), r.x_or_i, r.what, r.patterns)
                                if not crs.is_valid(s, a, c, t, v):
                                    valid = False
                                    break
                            if valid:
                                combs.append((s, a, c, t, v))
        return combs
