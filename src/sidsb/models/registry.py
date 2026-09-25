from .ngram import NgramUnseen
from .rules import RuleViolation

MODELS = {"ngram": NgramUnseen, "rules": RuleViolation}


def build(spec):
    spec = dict(spec)
    return MODELS[spec.pop("type")](**spec)
