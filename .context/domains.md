# Domain Reference

> Include this file when working on any domain plugin or adding a new domain.

## Current Domains (all stubs — Phase 1 pending)

### Health (`src/domains/health/`)
- **Tools:** health.log_meal, health.log_exercise, health.log_sleep, health.get_nutrition_summary, health.get_exercise_summary
- **Agents:** health.nutrition_coach (meals + nutrition), health.fitness_advisor (exercise + goals)
- **Events:** health.meal_logged, health.vitals_recorded
- **Memory:** dietary_preference, allergy, fitness_goal, health_metric, supplement
- **Pending models:** MealLog, ExerciseLog, SleepLog, VitalsRecord, HealthGoal

### Finance (`src/domains/finance/`)
- **Tools:** finance.log_transaction, finance.get_spending_summary, finance.get_budget_status, finance.get_investment_summary
- **Agents:** finance.budget_advisor
- **Events:** finance.transaction_logged, finance.budget_updated
- **Memory:** income_source, recurring_expense, financial_goal, investment_preference, budget_rule
- **Pending models:** Transaction, Budget, FinancialGoal

### Productivity (`src/domains/productivity/`)
- **Tools:** productivity.create_task, productivity.complete_task, productivity.list_tasks, productivity.log_habit, productivity.get_daily_summary
- **Agents:** productivity.planner, productivity.focus_coach
- **Events:** productivity.task_created, productivity.task_completed
- **Memory:** work_pattern, productivity_goal, project_context, habit_definition, priority_rule
- **Pending models:** Task, Habit, Project

### Relationships (`src/domains/relationships/`)
- **Tools:** relationships.log_interaction, relationships.create_contact, relationships.get_contact, relationships.schedule_event
- **Agents:** relationships.social_advisor
- **Events:** relationships.interaction_logged, relationships.reminder_due
- **Memory:** contact_detail, relationship_note, social_preference, important_date
- **Pending models:** Contact, Interaction, ImportantDate

### Learning (`src/domains/learning/`)
- **Tools:** learning.add_resource, learning.log_session, learning.get_progress, learning.capture_note
- **Agents:** learning.tutor, learning.study_planner
- **Events:** learning.resource_added, learning.session_logged
- **Memory:** learning_goal, skill_level, learning_preference, book_note, course_progress
- **Pending models:** LearningResource, StudySession, LearningNote

### Home (`src/domains/home/`)
- **Tools:** home.create_task, home.complete_task, home.add_to_shopping_list, home.get_maintenance_schedule
- **Agents:** home.household_manager
- **Events:** home.task_created, home.maintenance_due
- **Memory:** home_layout, appliance_info, maintenance_schedule, shopping_preference, household_rule
- **Pending models:** HouseholdTask, ShoppingList, MaintenanceSchedule

## Adding a New Domain

1. Define requirements in `tests/requirements/{domain}.py`
2. Create `src/domains/{domain}/` with `__init__.py`, `manifest.py`, `models.py`, `router.py`, `README.md`
3. Implement `DomainPlugin` subclass in `__init__.py` with stub handlers
4. Export `plugin = MyPlugin()` as last line
5. Run `pytest tests/arch/ -v -s` to verify wiring
6. Write tests tagged with `@pytest.mark.req("REQ-{DOMAIN}-001")`

See `src/domains/README.md` for the full developer guide.
