"""Module pour calculer le continuity score maximal possible pour un jeu de visites donné."""

from .models import Visit
from collections import defaultdict

def max_continuity_score(visits: list[Visit]) -> float:
    """
    Calcule le continuity score maximal possible (score parfait) pour un ensemble de visites.
    Cela correspond à la situation où chaque client a un seul soignant pour toutes ses visites.
    """
    # Regrouper les visites par client
    visits_by_customer = defaultdict(list)
    for v in visits:
        visits_by_customer[v.customer].append(v)

    scores = []
    for customer, vlist in visits_by_customer.items():
        total_visits = len(vlist)
        if total_visits == 1:
            scores.append(1.0)
        else:
            # Un seul soignant pour tous : unique_caregivers = 1
            score = 1.0 - (1 / total_visits)
            scores.append(score)
    if not scores:
        return 1.0
    return sum(scores) / len(scores)
