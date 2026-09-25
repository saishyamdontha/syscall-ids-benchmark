from .ngram import NgramUnseen
from .rules import RuleViolation


def _lstm(**kw):
    from .lstm import LstmLM  # imported lazily so baselines run without torch
    return LstmLM(**kw)


MODELS = {"ngram": NgramUnseen, "rules": RuleViolation, "lstm": _lstm}


def build(spec):
    spec = dict(spec)
    return MODELS[spec.pop("type")](**spec)
