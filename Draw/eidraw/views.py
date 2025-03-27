from django.shortcuts import render, redirect
from .models import Person, AgeGroup, Settings
import random
from django.db.models import Q
import logging
from django.utils.translation import activate

logger = logging.getLogger(__name__)

def get_settings():
    settings, created = Settings.objects.get_or_create(id=1)
    return settings


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
    user_id = request.GET.get('user_id', '').strip()
    if not user_id:
        user_id = 'default_user'
        logger.warning("No valid user_id provided in URL, using fallback: %s", user_id)
    
    if not request.session.get('language_prompt_shown'):
        request.session['language_prompt_shown'] = True
    if request.method == 'POST' and 'language' in request.POST:
        language = request.POST['language']
        activate(language)
        request.session['django_language'] = language

    registered_persons = Person.objects.filter(owner_id=user_id)
    all_participants = Person.objects.all()
    settings = get_settings()

    if request.method == 'POST' and 'name' in request.POST:
        name = request.POST['name'].strip()
        if Person.objects.filter(owner_id=user_id, name=name).exists():
            return render(request, 'register.html', {
                'error': f'{name} is already registered under your family!',
                'user_id': user_id,
                'registered_persons': registered_persons,
                'all_participants': all_participants,
                'price_limit': settings.gift_price_limit
            })
        try:
            age = int(request.POST['age'])
            gender = request.POST['gender']
            extra_info = request.POST.get('extra_info', '')
            age_group = AgeGroup.objects.get(min_age__lte=age, max_age__gte=age)
            person = Person.objects.create(
                name=name, age=age, gender=gender, extra_info=extra_info,
                age_group=age_group, owner_id=user_id
            )
            logger.info("Registered %s with user_id %s", name, user_id)
            return redirect('draw', user_id=user_id)
        except AgeGroup.DoesNotExist:
            logger.error("No AgeGroup found for age: %s", age)
            return render(request, 'register.html', {'error': 'No matching age group found. Contact admin.', 'user_id': user_id, 'registered_persons': registered_persons, 'all_participants': all_participants, 'price_limit': settings.gift_price_limit})
        except Exception as e:
            logger.error("Error in registration: %s", str(e))
            return render(request, 'register.html', {'error': 'Registration failed. Try again.', 'user_id': user_id, 'registered_persons': registered_persons, 'all_participants': all_participants, 'price_limit': settings.gift_price_limit})
    
    return render(request, 'register.html', {'user_id': user_id, 'registered_persons': registered_persons, 'all_participants': all_participants, 'price_limit': settings.gift_price_limit})

def draw_view(request, user_id):
    if not request.session.get('language_prompt_shown'):
        request.session['language_prompt_shown'] = True
    persons = Person.objects.filter(owner_id=user_id)
    all_participants = Person.objects.all()
    settings = get_settings()

    if request.method == 'POST' and settings.drawing_enabled:
        person_id = request.POST['person_id']
        person = Person.objects.get(id=person_id, owner_id=user_id)
        if not person.has_drawn:
            drawn = draw_person(person)
            if drawn:
                return redirect('result', person_id=person.id)
            return render(request, 'draw.html', {'error': 'No one available yet', 'persons': persons, 'user_id': user_id, 'all_participants': all_participants, 'drawing_enabled': settings.drawing_enabled, 'price_limit': settings.gift_price_limit})
        else:
            return redirect('result', person_id=person.id)
    return render(request, 'draw.html', {'persons': persons, 'user_id': user_id, 'all_participants': all_participants, 'drawing_enabled': settings.drawing_enabled, 'price_limit': settings.gift_price_limit})

def result_view(request, person_id):
    if not request.session.get('language_prompt_shown'):
        request.session['language_prompt_shown'] = True
    person = Person.objects.get(id=person_id)
    drawn = person.drawn_person
    user_id = person.owner_id
    registered_persons = Person.objects.filter(owner_id=user_id)
    all_participants = Person.objects.all()
    settings = get_settings()
    return render(request, 'result.html', {'person': person, 'drawn': drawn, 'user_id': user_id, 'registered_persons': registered_persons, 'all_participants': all_participants, 'price_limit': settings.gift_price_limit})