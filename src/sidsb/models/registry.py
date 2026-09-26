from .ngram import NgramUnseen
from .ngram_lm import NgramLM


def _rules(**kw):
    from .rules import RuleViolation
    return RuleViolation(**kw)


def _lstm(**kw):
    from .lstm import LstmLM  # imported lazily so baselines run without torch
    return LstmLM(**kw)


MODELS = {"ngram": NgramUnseen, "ngram_lm": NgramLM, "rules": _rules, "lstm": _lstm}


def build(spec):
    spec = dict(spec)
    return MODELS[spec.pop("type")](**spec)
