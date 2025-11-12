"""Solver module for the Bloom Care scheduling problem."""

from .models import Assignment, Caregiver, Visit


def solve(visits: list[Visit], caregivers: list[Caregiver]) -> list[Assignment]:
    """
    Solve the scheduling problem.

    Args:
        visits: List of visits to be assigned
        caregivers: List of available caregivers

    Returns:
        List of Assignment objects representing which caregiver
          is assigned to which visit
    """
    # 1. Préparer les structures de suivi
    from collections import defaultdict
    import heapq
    assignments = []
    caregiver_hours = defaultdict(float)  # id -> heures assignées
    caregiver_daily_visits = defaultdict(lambda: defaultdict(list))  # id -> day -> [visits]

    # 2. Trier les visites par date de début (priorité aux plus tôt)
    visits_sorted = sorted(visits, key=lambda v: v.start)

    # 3. Pour chaque visite, essayer d'affecter un soignant valide
    for visit in visits_sorted:
        # Lister les soignants éligibles (compétence, disponibilité, pas d'overlap, pas au-delà max heures)
        eligible = []
        for caregiver in caregivers:
            # Compétence requise
            if visit.required_skill not in caregiver.skills:
                continue
            # Disponibilité sur le créneau
            if not any(av.check_availability(visit) for av in caregiver.availability):
                continue
            # Pas d'overlap avec d'autres visites déjà assignées ce jour-là
            day = visit.start.strftime("%A")
            overlap = any(visit.overlaps(v) for v in caregiver_daily_visits[caregiver.id][day])
            if overlap:
                continue
            # Respect du quota d'heures
            visit_hours = (visit.end - visit.start).total_seconds() / 3600.0
            if caregiver_hours[caregiver.id] + visit_hours > caregiver.max_hours:
                continue
            # Ajout à la liste des candidats (on peut pondérer pour bonus: ex. nombre de visites déjà faites pour ce client)
            # Pour la continuité de soin, on favorise le soignant ayant déjà vu ce client
            continuity_bonus = sum(
                v.customer == visit.customer for day_visits in caregiver_daily_visits[caregiver.id].values() for v in day_visits
            )
            # Pour l'efficacité de déplacement, on favorise le soignant déjà dans le même quartier juste avant
            last_same_day = sorted(caregiver_daily_visits[caregiver.id][day], key=lambda v: v.end)
            travel_bonus = 0
            if last_same_day:
                last_visit = last_same_day[-1]
                if last_visit.neighborhood == visit.neighborhood:
                    travel_bonus = 1
            # Score: plus haut = mieux (on veut max continuity et travel)
            score = (continuity_bonus * 2) + travel_bonus
            eligible.append((-score, caregiver_hours[caregiver.id], caregiver.id, caregiver, continuity_bonus, travel_bonus))

        # Trier les candidats: d'abord le score, puis le moins d'heures déjà faites
        if eligible:
            heapq.heapify(eligible)
            _, _, _, chosen, _, _ = heapq.heappop(eligible)
            assignments.append(Assignment(visit_id=visit.id, caregiver_id=chosen.id))
            caregiver_hours[chosen.id] += (visit.end - visit.start).total_seconds() / 3600.0
            caregiver_daily_visits[chosen.id][visit.start.strftime("%A")].append(visit)
        # Sinon, la visite reste non assignée (sera listée dans les violations)

    # Retourner la liste des affectations
    return assignments
