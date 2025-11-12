"""Main module for Bloom Care OR Take-home Test."""


from .evaluator import display_caregiver_schedules, evaluate
from .parser import load_caregivers, load_visits
from .solver import solve
from .max_continuity import max_continuity_score


def main() -> None:
    """Main entry point for the application."""
    # Load the data
    visits = load_visits()
    caregivers = load_caregivers()

    print(f"Loaded {len(visits)} visits and {len(caregivers)} caregivers")

    # Solve the scheduling problem
    print("\nSolving scheduling problem...")
    assignments = solve(visits, caregivers)

    print(f"Generated {len(assignments)} assignments")

    # Evaluate the results
    print("\nEvaluating results...")
    evaluation = evaluate(assignments, visits, caregivers)

    # Display results
    print("\n" + "=" * 50)
    print("SCHEDULING RESULTS")
    print("=" * 50)

    print(f"\nAssignments ({len(assignments)}):")
    for assignment in assignments:
        print(f"  {assignment.visit_id} -> {assignment.caregiver_id}")

    # Display constraint violations
    violations = evaluation["constraint_violations"]
    if any(violations.values()):
        print("\nConstraint Violations:")
        for violation_type, violation_list in violations.items():
            if violation_list:
                print(f"  {violation_type}: {len(violation_list)} violations")
    else:
        print("\n✅ All constraints satisfied!")


    # Display optimization metrics
    metrics = evaluation["optimization_metrics"]
    max_continuity = max_continuity_score(visits)
    print("\nOptimization Metrics:")
    print(f"  Continuity Score: {metrics['continuity_score']:.2f} (max possible: {max_continuity:.2f})")
    print(f"  Travel Efficiency Score: {metrics['travel_efficiency_score']:.2f}")

    # Display caregiver schedules
    display_caregiver_schedules(assignments, visits, caregivers)


if __name__ == "__main__":
    main()
