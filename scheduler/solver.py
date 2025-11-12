"""Solver module for the Bloom Care scheduling problem."""

from .models import Assignment, Caregiver, Visit



from collections import defaultdict

def solve(visits: list[Visit], caregivers: list[Caregiver]) -> list[Assignment]:
    """
    Résout le problème d'affectation des visites aux soignants en maximisant la continuité de soin
    (même soignant pour un client) tout en respectant les contraintes et en gardant un bon travel efficiency.
    """
    assignments = []
    caregiver_hours = defaultdict(float)  # id -> heures assignées
    caregiver_daily_visits = defaultdict(lambda: defaultdict(list))  # id -> day -> [visits]

    visits_by_customer = group_visits_by_customer(visits)

    for customer, customer_visits in visits_by_customer.items():
        customer_visits = sorted(customer_visits, key=lambda v: v.start)
        chosen = find_best_caregiver_for_customer(customer, customer_visits, caregivers, caregiver_hours, caregiver_daily_visits)
        if chosen:
            assign_all_visits_to_caregiver(assignments, customer_visits, chosen, caregiver_hours, caregiver_daily_visits)
        else:
            for visit in customer_visits:
                chosen = find_best_caregiver_for_visit(visit, caregivers, caregiver_hours, caregiver_daily_visits)
                if chosen:
                    assign_visit(assignments, visit, chosen, caregiver_hours, caregiver_daily_visits)
    return assignments


def group_visits_by_customer(visits):
    visits_by_customer = defaultdict(list)
    for v in visits:
        visits_by_customer[v.customer].append(v)
    return visits_by_customer


def find_best_caregiver_for_customer(customer, customer_visits, caregivers, caregiver_hours, caregiver_daily_visits):
    possible_caregivers = []
    for caregiver in caregivers:
        ok = True
        temp_hours = caregiver_hours[caregiver.id]
        temp_daily = {day: list(day_visits) for day, day_visits in caregiver_daily_visits[caregiver.id].items()}
        # Simuler l'affectation de toutes les visites de ce client à ce soignant
        for visit in customer_visits:
            if not is_caregiver_eligible_for_visit(caregiver, visit, temp_hours, temp_daily):
                ok = False
                break
            visit_hours = (visit.end - visit.start).total_seconds() / 3600.0
            temp_hours += visit_hours
            day = visit.start.strftime("%A")
            temp_daily.setdefault(day, []).append(visit)
        if ok:
            # Calculer le nombre de switches de quartier par jour (travel inefficiency)
            switches = 0
            for day, visits_in_day in temp_daily.items():
                if len(visits_in_day) > 1:
                    visits_in_day_sorted = sorted(visits_in_day, key=lambda v: v.start)
                    current_neigh = visits_in_day_sorted[0].neighborhood
                    for v in visits_in_day_sorted[1:]:
                        if v.neighborhood != current_neigh:
                            switches += 1
                            current_neigh = v.neighborhood
            continuity_bonus = sum(
                v.customer == customer for day_visits in caregiver_daily_visits[caregiver.id].values() for v in day_visits
            )
            # On veut minimiser les switches, puis les heures, puis maximiser la continuité
            possible_caregivers.append((switches, caregiver_hours[caregiver.id], -continuity_bonus, caregiver))
    if possible_caregivers:
        possible_caregivers.sort(key=lambda x: (x[0], x[1], x[2]))
        return possible_caregivers[0][3]
    return None


def find_best_caregiver_for_visit(visit, caregivers, caregiver_hours, caregiver_daily_visits):
    eligible = []
    for caregiver in caregivers:
        if not is_caregiver_eligible_for_visit(caregiver, visit, caregiver_hours[caregiver.id], caregiver_daily_visits[caregiver.id]):
            continue
        day = visit.start.strftime("%A")
        last_same_day = sorted(caregiver_daily_visits[caregiver.id][day], key=lambda v: v.end)
        travel_bonus = 0
        if last_same_day:
            last_visit = last_same_day[-1]
            if last_visit.neighborhood == visit.neighborhood:
                travel_bonus = 1
        eligible.append((-travel_bonus, caregiver_hours[caregiver.id], caregiver))
    if eligible:
        eligible.sort(key=lambda x: (x[0], x[1]))
        return eligible[0][2]
    return None


def is_caregiver_eligible_for_visit(caregiver, visit, current_hours, daily_visits):
    if visit.required_skill not in caregiver.skills:
        return False
    if not any(av.check_availability(visit) for av in caregiver.availability):
        return False
    day = visit.start.strftime("%A")
    if any(visit.overlaps(v) for v in daily_visits.get(day, [])):
        return False
    visit_hours = (visit.end - visit.start).total_seconds() / 3600.0
    if current_hours + visit_hours > caregiver.max_hours:
        return False
    return True


def assign_all_visits_to_caregiver(assignments, visits, caregiver, caregiver_hours, caregiver_daily_visits):
    # Regrouper les visites par jour
    visits_by_day = defaultdict(list)
    for visit in visits:
        day = visit.start.strftime("%A")
        visits_by_day[day].append(visit)

    # Pour chaque jour, ordonner les visites pour minimiser les switches de quartier
    ordered_visits = []
    for day, day_visits in visits_by_day.items():
        # Utiliser une liste pour to_assign car Visit n'est pas hashable
        to_assign = list(day_visits)
        if not to_assign:
            continue
        # Commencer par la visite la plus tôt
        current = min(to_assign, key=lambda v: v.start)
        ordered = [current]
        to_assign.remove(current)
        while to_assign:
            # Chercher une visite dans le même quartier qui commence après la précédente
            next_visits = [v for v in to_assign if v.neighborhood == current.neighborhood and v.start >= current.end]
            if next_visits:
                next_visit = min(next_visits, key=lambda v: v.start)
            else:
                # Sinon, prendre la visite la plus tôt possible
                next_visits = [v for v in to_assign if v.start >= current.end]
                if next_visits:
                    next_visit = min(next_visits, key=lambda v: v.start)
                else:
                    # Si aucune visite ne commence après la précédente, prendre n'importe laquelle
                    next_visit = min(to_assign, key=lambda v: v.start)
            ordered.append(next_visit)
            to_assign.remove(next_visit)
            current = next_visit
        ordered_visits.extend(ordered)

    # Réaffecter les visites dans l'ordre optimisé
    for visit in sorted(ordered_visits, key=lambda v: v.start):
        assign_visit(assignments, visit, caregiver, caregiver_hours, caregiver_daily_visits)


def assign_visit(assignments, visit, caregiver, caregiver_hours, caregiver_daily_visits):
    assignments.append(Assignment(visit_id=visit.id, caregiver_id=caregiver.id))
    visit_hours = (visit.end - visit.start).total_seconds() / 3600.0
    caregiver_hours[caregiver.id] += visit_hours
    day = visit.start.strftime("%A")
    caregiver_daily_visits[caregiver.id][day].append(visit)
