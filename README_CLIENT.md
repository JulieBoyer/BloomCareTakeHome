# Bloom Care Scheduler - Client Guide

## How to Run the Code

1. **Prerequisites**
   - Python 3.11 must be installed on your machine.
   - [Poetry](https://python-poetry.org/docs/#installation) must be installed for dependency management.

2. **Install Dependencies**
   In the project directory, run:
   ```sh
   poetry install
   ```

3. **Run the Scheduler**
   Still in the project directory, run:
   ```sh
   poetry run python -m scheduler
   ```
   This will execute the scheduling algorithm and display the results in your terminal.


## What Information Will Be Displayed?

- **Assignments**: For each visit, the assigned caregiver will be shown.
- **Constraint Violations**: If any visits could not be assigned, or if there are issues with availability, overlaps, or maximum hours, these will be listed.
- **Optimization Metrics**:
   - *Continuity Score*: Measures how well the same caregiver is assigned to the same client across multiple visits (1.0 = perfect continuity).
   - *Travel Efficiency Score*: Measures how well the schedule minimizes neighborhood switches for caregivers during a day (1.0 = perfect efficiency).
   - *Maximum Possible Continuity*: The theoretical best continuity score for the given data.
- **Caregiver Schedules**: For each caregiver, a detailed schedule of their assigned visits, total hours, and utilization.

---

## How Does the Solver Work?

The scheduling algorithm is designed to assign caregivers to visits while maximizing continuity of care (the same caregiver for the same client), respecting all constraints, and optimizing travel efficiency. Here is an overview of the logic:

### 1. Grouping Visits by Client
Visits are first grouped by client. The solver tries to assign all visits for a given client to a single caregiver whenever possible, which maximizes the continuity score.

### 2. Assigning All Visits for a Client
For each client, the solver checks if there is a caregiver who can take all of that client's visits without violating any constraints (skills, availability, no overlaps, and maximum hours). If several caregivers are eligible, the one who minimizes neighborhood switches (travel inefficiency) and total assigned hours is chosen.

### 3. Assigning Individual Visits
If no caregiver can take all visits for a client, the solver assigns each visit individually. For each visit, it prioritizes:
- Caregivers who have already seen the client (continuity)
- Caregivers who are already in the same neighborhood on that day (travel efficiency)
- Caregivers with the lowest total assigned hours

### 4. Ordering Visits for Travel Efficiency
When assigning multiple visits to a caregiver in a day, the visits are ordered to minimize neighborhood switches, further improving travel efficiency.

### 5. Constraints Enforced
The solver ensures that:
- Caregivers have the required skills for each visit
- Caregivers are available for the visit time
- No overlapping visits are assigned to the same caregiver
- Caregivers do not exceed their maximum allowed hours

### 6. Output
The result includes:
- The assignment of each visit to a caregiver
- Any constraint violations (unassigned visits, overlaps, etc.)
- Continuity and travel efficiency scores
- Theoretical maximum continuity score for the dataset
- Detailed schedules for each caregiver

This approach provides a good balance between maximizing client-caregiver continuity and minimizing unnecessary travel, while always respecting hard constraints.


