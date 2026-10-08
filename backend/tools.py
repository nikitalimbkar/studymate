tasks = []

def create_study_plan(subject, days, hours_per_day):
    """
    Create a personalized study plan based on the subject.
    """

    # Example topic breakdowns
    topic_map = {
        "DBMS": [
            "ER Model + Relational Model",
            "SQL + Queries",
            "Normalization",
            "Transactions + Concurrency",
            "Revision + Mock Test"
        ],

        "Java": [
            "Java Basics + OOP",
            "Arrays + Strings",
            "Collections + Hashing",
            "Recursion + Backtracking",
            "Revision + Coding Practice"
        ],

        "DSA": [
            "Arrays + Strings",
            "Linked List + Stack",
            "Queue + Hashing",
            "Trees + Binary Search",
            "Revision + Coding Practice"
        ]
    }

    # Find topics for the subject
    topics = topic_map.get(
        subject.upper(),
        [f"{subject} - Topic {i}" for i in range(1, days + 1)]
    )

    plan = []

    for day in range(1, days + 1):

        # If days are more than available topics,
        # reuse the last topic.
        topic = topics[min(day - 1, len(topics) - 1)]

        plan.append({
            "day": f"Day {day}",
            "subject": topic,
            "hours": hours_per_day
        })

    return plan
def add_task(task):
    """
    Add a task to the student's task list.
    """

    tasks.append(task)

    return {
        "success": True,
        "task": task,
        "message": f"Task added successfully: {task}"
    }
def get_tasks():
    """
    Get all saved tasks.
    """

    return tasks

def complete_task(task):

    if task in tasks:
        tasks.remove(task)

        return {
            "success": True,
            "message": f"Task completed: {task}"
        }

    return {
        "success": False,
        "message": f"Task not found: {task}"
    }