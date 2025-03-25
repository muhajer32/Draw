import random
from django.db.models import Q
from .models import *

def draw_person(current_person):
    # Available pool: not drawn yet, not the current person
    available = Person.objects.filter(is_drawn=False).exclude(id=current_person.id)
    
    if not available:
        return None  # No one to draw yet

    # Prefer same age group
    same_group = available.filter(age_group=current_person.age_group)
    if same_group.exists():
        candidates = same_group
    else:
        candidates = available

    # Randomly pick one
    drawn = random.choice(candidates)
    
    # Check if this draw leaves an impossible state (e.g., one person left)
    remaining = Person.objects.filter(has_drawn=False).exclude(id=current_person.id)
    if len(remaining) == 1 and remaining[0].id == drawn.id:
        # Avoid trapping the last person; try another if possible
        other_options = candidates.exclude(id=drawn.id)
        if other_options.exists():
            drawn = random.choice(other_options)
        else:
            return None  # Defer draw until more participants

    # Assign draw
    current_person.drawn_person = drawn
    current_person.has_drawn = True
    drawn.is_drawn = True
    current_person.save()
    drawn.save()
    return drawn