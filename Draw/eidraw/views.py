from django.shortcuts import render, redirect
from .models import Person, AgeGroup
import random
from django.db.models import Q

def draw_person(current_person):
    available = Person.objects.filter(is_drawn=False).exclude(id=current_person.id)
    
    if not available:
        return None

    same_group = available.filter(age_group=current_person.age_group)
    if same_group.exists():
        candidates = same_group
    else:
        candidates = available

    drawn = random.choice(candidates)
    
    remaining = Person.objects.filter(has_drawn=False).exclude(id=current_person.id)
    if len(remaining) == 1 and remaining[0].id == drawn.id:
        other_options = candidates.exclude(id=drawn.id)
        if other_options.exists():
            drawn = random.choice(other_options)
        else:
            return None

    current_person.drawn_person = drawn
    current_person.has_drawn = True
    drawn.is_drawn = True
    current_person.save()
    drawn.save()
    return drawn

def register_view(request):
    user_id = request.GET.get('user_id')
    if request.method == 'POST':
        name = request.POST['name']
        age = int(request.POST['age'])
        gender = request.POST['gender']
        extra_info = request.POST.get('extra_info', '')
        age_group = AgeGroup.objects.get(min_age__lte=age, max_age__gte=age)
        Person.objects.create(
            name=name, age=age, gender=gender, extra_info=extra_info,
            age_group=age_group, owner_id=user_id
        )
        return redirect('draw', user_id=user_id)
    return render(request, 'register.html')

def draw_view(request, user_id):
    persons = Person.objects.filter(owner_id=user_id, has_drawn=False)
    if request.method == 'POST':
        person_id = request.POST['person_id']
        person = Person.objects.get(id=person_id, owner_id=user_id)
        drawn = draw_person(person)
        if drawn:
            return redirect('result', person_id=person.id)
        return render(request, 'draw.html', {'error': 'No one available yet', 'persons': persons})
    return render(request, 'draw.html', {'persons': persons})

def result_view(request, person_id):
    person = Person.objects.get(id=person_id)
    drawn = person.drawn_person
    return render(request, 'result.html', {'person': person, 'drawn': drawn})