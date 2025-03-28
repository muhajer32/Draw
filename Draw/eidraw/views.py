from django.shortcuts import render, redirect
from .models import Person, AgeGroup, Group, Exclusion
import random
from django.db.models import Q
import logging
from django.utils.translation import activate

logger = logging.getLogger(__name__)

def draw_person(current_person):
    available = Person.objects.filter(group=current_person.group, is_drawn=False).exclude(id=current_person.id)
    exclusions = Exclusion.objects.filter(person=current_person).values_list('exclude_id', flat=True)
    available = available.exclude(id__in=exclusions)
    
    if not available:
        return None

    same_group = available.filter(age_group=current_person.age_group)
    candidates = same_group if same_group.exists() else available
    drawn = random.choice(candidates)
    
    remaining = Person.objects.filter(group=current_person.group, has_drawn=False).exclude(id=current_person.id)
    if len(remaining) == 1 and remaining[0].id == drawn.id:
        other_options = candidates.exclude(id=drawn.id)
        drawn = random.choice(other_options) if other_options.exists() else None

    if drawn:
        current_person.drawn_person = drawn
        current_person.has_drawn = True
        drawn.is_drawn = True
        current_person.save()
        drawn.save()
    return drawn

def home_view(request):
    if request.method == 'POST':
        group_name = request.POST.get('group_name')
        organizer_email = request.POST.get('organizer_email')
        group = Group.objects.create(name=group_name, organizer_email=organizer_email)
        return redirect('register', group_id=group.uuid)
    return render(request, 'home.html')

def register_view(request, group_id):
    group = Group.objects.get(uuid=group_id)
    user_id = request.GET.get('user_id', '').strip() or request.POST.get('user_id', '').strip() or 'anonymous'
    if not request.session.get('language_prompt_shown'):
        request.session['language_prompt_shown'] = True
    if request.method == 'POST' and 'language' in request.POST:
        language = request.POST['language']
        activate(language)
        request.session['django_language'] = language

    registered_persons = Person.objects.filter(group=group, user_id=user_id)
    all_participants = Person.objects.filter(group=group)

    if request.method == 'POST' and 'name' in request.POST:
        name = request.POST['name'].strip()
        user_id = request.POST.get('user_id', '').strip()  # From form
        if Person.objects.filter(group=group, name=name).exists():
            return render(request, 'register.html', {
                'error': f'{name} is already in this group!',
                'group': group,
                'user_id': user_id,
                'registered_persons': registered_persons,
                'all_participants': all_participants
            })
        try:
            age = int(request.POST['age'])
            gender = request.POST['gender']
            wishlist = request.POST.get('wishlist', '')
            age_group = AgeGroup.objects.get(min_age__lte=age, max_age__gte=age)
            person = Person.objects.create(
                group=group, user_id=user_id, name=name, age=age, gender=gender, wishlist=wishlist,
                age_group=age_group
            )
            exclude_names = request.POST.getlist('exclude')
            for exclude_name in exclude_names:
                exclude_person = Person.objects.get(group=group, name=exclude_name)
                Exclusion.objects.create(person=person, exclude=exclude_person)
            logger.info("Registered %s in group %s by %s", name, group.name, user_id)
            return redirect('draw', group_id=group.uuid, user_id=user_id)
        except AgeGroup.DoesNotExist:
            return render(request, 'register.html', {'error': 'No matching age group.', 'group': group, 'user_id': user_id, 'registered_persons': registered_persons, 'all_participants': all_participants})
        except Exception as e:
            logger.error("Error: %s", str(e))
            return render(request, 'register.html', {'error': 'Registration failed.', 'group': group, 'user_id': user_id, 'registered_persons': registered_persons, 'all_participants': all_participants})
    
    if request.method == 'POST' and 'enable_drawing' in request.POST and request.POST.get('organizer_email') == group.organizer_email:
        group.drawing_enabled = True
        group.save()
        logger.info("Drawing enabled for group %s by %s", group.name, group.organizer_email)

    return render(request, 'register.html', {'group': group, 'user_id': user_id, 'registered_persons': registered_persons, 'all_participants': all_participants})

def draw_view(request, group_id, user_id):
    group = Group.objects.get(uuid=group_id)
    if not request.session.get('language_prompt_shown'):
        request.session['language_prompt_shown'] = True
    persons = Person.objects.filter(group=group, user_id=user_id)
    all_participants = Person.objects.filter(group=group)

    if request.method == 'POST' and group.drawing_enabled:
        person_id = request.POST['person_id']
        person = Person.objects.get(id=person_id, group=group, user_id=user_id)
        if not person.has_drawn:
            drawn = draw_person(person)
            if drawn:
                return redirect('result', person_id=person.id)
            return render(request, 'draw.html', {'error': 'No one available.', 'group': group, 'user_id': user_id, 'persons': persons, 'all_participants': all_participants})
        else:
            return redirect('result', person_id=person.id)
    return render(request, 'draw.html', {'group': group, 'user_id': user_id, 'persons': persons, 'all_participants': all_participants})

def result_view(request, person_id):
    person = Person.objects.get(id=person_id)
    group = person.group
    user_id = person.user_id
    if not request.session.get('language_prompt_shown'):
        request.session['language_prompt_shown'] = True
    drawn = person.drawn_person
    registered_persons = Person.objects.filter(group=group, user_id=user_id)
    all_participants = Person.objects.filter(group=group)
    return render(request, 'result.html', {'group': group, 'user_id': user_id, 'person': person, 'drawn': drawn, 'registered_persons': registered_persons, 'all_participants': all_participants})